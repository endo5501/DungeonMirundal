# dbg_api.py  ── pull スクショ & キー／マウス入力
# 
# 機能制限について:
# - /game/state: GameManagerアクセス制限により全てnull値を返す
# - /game/visible_buttons: UI要素アクセス制限により空配列を返す
# - /input/shortcut_key: ボタン情報取得不可のため実質的に利用不可
# 
# 実用的なエンドポイント:
# - /screenshot: 完全動作
# - /input/key, /input/mouse: 完全動作
# - /ui/hierarchy: WindowManagerから基本情報のみ取得可能
# - /history: 完全動作
import threading
import base64
import io
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

import pygame
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
from fastapi_mcp import FastApiMCP
import uvicorn
from pydantic import BaseModel

# インベントリシステムのインポート
from src.inventory.inventory import inventory_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 拡張ロギング機能のインポート
try:
    from src.debug.enhanced_logger import get_enhanced_logger
    enhanced_logger = get_enhanced_logger("debug_api")
except ImportError:
    enhanced_logger = None

# 定数定義
DEFAULT_PORT = 8765
DEFAULT_HOST = "127.0.0.1"
MAX_SCREENSHOT_SIZE = (1920, 1080)  # 最大スクリーンショットサイズ
JPEG_QUALITY = 70

# Enumとモデル定義
class MouseAction(str, Enum):
    DOWN = "down"
    UP = "up"
    MOVE = "move"

class ScreenshotResponse(BaseModel):
    jpeg: str
    timestamp: str
    size: tuple[int, int]

class InputResponse(BaseModel):
    ok: bool
    message: str = "Success"
    timestamp: str

# FastAPI アプリケーション
app = FastAPI(
    title="Dungeon Game Debug API",
    description="API for debugging and testing the Dungeon game",
    version="1.0.0"
)

# グローバル変数
_screen: Optional[pygame.Surface] = None
_game_manager = None  # GameManagerインスタンスの参照
_screen_lock = threading.Lock()
_input_history: list[Dict[str, Any]] = []
_max_history = 1000

# ヘルパー関数
def get_timestamp() -> str:
    """現在のタイムスタンプを取得"""
    return datetime.now().isoformat()

def get_current_game_manager():
    """現在のGameManagerインスタンスを動的に取得
    
    セーブ・ロード後でも正しいGameManagerインスタンスを取得するため、
    複数の方法でGameManagerへのアクセスを試行する。
    """
    global _game_manager
    
    # 方法1: main.pyから直接取得（最優先・最新インスタンス）
    try:
        import main
        if hasattr(main, 'game_manager') and main.game_manager is not None:
            # インスタンスが変更されている場合はログ出力
            if _game_manager is not main.game_manager:
                if _game_manager is not None:
                    old_address = hex(id(_game_manager))
                    new_address = hex(id(main.game_manager))
                    logger.info(f"GameManager instance changed: {old_address} -> {new_address}")
                _game_manager = main.game_manager  # キャッシュを更新
            logger.debug("Retrieved current GameManager from main.py")
            return main.game_manager
    except (ImportError, AttributeError) as e:
        logger.debug(f"Could not access main.game_manager: {e}")
    
    # 方法2: sys.modulesから取得
    try:
        import sys
        if 'main' in sys.modules:
            main_module = sys.modules['main']
            if hasattr(main_module, 'game_manager') and main_module.game_manager is not None:
                # インスタンスが変更されている場合はログ出力
                if _game_manager is not main_module.game_manager:
                    if _game_manager is not None:
                        old_address = hex(id(_game_manager))
                        new_address = hex(id(main_module.game_manager))
                        logger.info(f"GameManager instance changed via sys.modules: {old_address} -> {new_address}")
                    _game_manager = main_module.game_manager  # キャッシュを更新
                logger.debug("Retrieved current GameManager from sys.modules")
                return main_module.game_manager
    except Exception as e:
        logger.debug(f"Could not access GameManager from sys.modules: {e}")
    
    # 方法3: キャッシュされたインスタンス（最後の手段）
    if _game_manager is not None:
        # GameManagerが有効かチェック
        try:
            if hasattr(_game_manager, 'current_party'):
                logger.warning("Using cached GameManager (may be outdated)")
                return _game_manager
        except Exception as e:
            logger.warning(f"Cached GameManager appears invalid: {e}")
            _game_manager = None
    
    # 全ての方法が失敗した場合
    logger.error("Could not retrieve valid GameManager instance")
    return None

def get_game_manager_debug_info():
    """GameManager取得のデバッグ情報を提供"""
    global _game_manager
    
    debug_info = {
        "cached_manager_exists": _game_manager is not None,
        "cached_manager_type": str(type(_game_manager)) if _game_manager else None,
        "main_module_exists": False,
        "main_manager_exists": False,
        "sys_modules_main_exists": False,
        "retrieval_method_used": None
    }
    
    # main.pyの存在確認
    try:
        import main
        debug_info["main_module_exists"] = True
        debug_info["main_manager_exists"] = hasattr(main, 'game_manager') and main.game_manager is not None
    except ImportError:
        pass
    
    # sys.modulesの確認
    try:
        import sys
        debug_info["sys_modules_main_exists"] = 'main' in sys.modules
    except Exception:
        pass
    
    return debug_info

def _get_hierarchical_ui_elements(ui_manager):
    """UI要素の階層構造を取得"""
    hierarchical_elements = []
    
    try:
        # スプライトグループから要素を取得
        sprite_group = ui_manager.get_sprite_group()
        if hasattr(sprite_group, 'sprites'):
            sprites = sprite_group.sprites()
        else:
            sprites = list(sprite_group)
        
        # 階層構造の構築
        containers = []
        other_elements = []
        
        # まず、コンテナとその他の要素を分類
        for sprite in sprites:
            if hasattr(sprite, 'object_ids'):
                element_info = _extract_element_info(sprite)
                
                # UIContainer系の要素は階層の親として扱う
                if element_info['type'] in ['UIContainer', 'UIPanel']:
                    containers.append(element_info)
                else:
                    other_elements.append(element_info)
        
        # 階層構造を構築
        root_containers = []
        child_containers = []
        
        # 位置とサイズ情報を使用して親子関係を推定
        for container in containers:
            container['children'] = []
            is_child = False
            
            # 他のコンテナに含まれるかチェック
            for other_container in containers:
                if container != other_container and _is_element_inside(container, other_container):
                    other_container.setdefault('children', []).append(container)
                    is_child = True
                    break
            
            if not is_child:
                root_containers.append(container)
            else:
                child_containers.append(container)
        
        # 各コンテナに子要素を割り当て
        for element in other_elements:
            assigned = False
            
            # 最も小さい（具体的な）コンテナに割り当て
            best_container = None
            best_area = float('inf')
            
            for container in containers:
                if _is_element_inside(element, container):
                    container_area = container.get('size', {}).get('width', 0) * container.get('size', {}).get('height', 0)
                    if container_area < best_area and container_area > 0:
                        best_container = container
                        best_area = container_area
            
            if best_container:
                best_container.setdefault('children', []).append(element)
                assigned = True
            
            # どのコンテナにも含まれない場合はルートレベルに追加
            if not assigned:
                hierarchical_elements.append(element)
        
        # ルートコンテナを追加
        hierarchical_elements.extend(root_containers)
        
        return hierarchical_elements
        
    except Exception as e:
        logger.error(f"Error building UI hierarchy: {str(e)}")
        return []

def _extract_element_info(sprite):
    """UI要素から情報を抽出"""
    element_info = {
        'type': sprite.__class__.__name__,
        'visible': bool(getattr(sprite, 'visible', 0))
    }
    
    # object_id情報
    if hasattr(sprite, 'object_ids'):
        ids = sprite.object_ids
        element_info['object_id'] = ids[0] if ids else 'unknown'
        element_info['object_ids'] = ids
    
    # 位置とサイズ情報
    if hasattr(sprite, 'rect'):
        rect = sprite.rect
        element_info['position'] = {'x': rect.x, 'y': rect.y}
        element_info['size'] = {'width': rect.width, 'height': rect.height}
    
    # 詳細UI情報の拡張
    element_info['details'] = {}
    
    # テキスト情報
    if hasattr(sprite, 'text'):
        element_info['details']['text'] = str(sprite.text)
    
    # 有効/無効状態
    if hasattr(sprite, 'enabled'):
        element_info['details']['enabled'] = bool(sprite.enabled)
    
    # ツールチップ
    if hasattr(sprite, 'tooltip_text') and sprite.tooltip_text:
        element_info['details']['tooltip'] = str(sprite.tooltip_text)
    
    # カスタム属性: メニューアイテムデータ
    if hasattr(sprite, 'menu_item'):
        try:
            menu_item = sprite.menu_item
            if isinstance(menu_item, dict):
                element_info['details']['menu_item'] = menu_item
            else:
                element_info['details']['menu_item'] = str(menu_item)
        except Exception:
            pass
    
    # カスタム属性: menu_item_data
    if hasattr(sprite, 'menu_item_data'):
        try:
            menu_data = sprite.menu_item_data
            if isinstance(menu_data, dict):
                element_info['details']['menu_item_data'] = menu_data
            else:
                element_info['details']['menu_item_data'] = str(menu_data)
        except Exception:
            pass
    
    # ショートカットキー情報
    if hasattr(sprite, 'shortcut_key'):
        element_info['details']['shortcut_key'] = str(sprite.shortcut_key)
    
    # インデックス情報（ボタン番号など）
    if hasattr(sprite, 'button_index'):
        element_info['details']['button_index'] = sprite.button_index
        # 1-9のショートカットキーを自動生成
        if isinstance(sprite.button_index, int) and 0 <= sprite.button_index < 9:
            element_info['details']['auto_shortcut'] = str(sprite.button_index + 1)
    
    # 施設UI専用情報の追加
    _add_facility_ui_info(sprite, element_info)
    
    # 追加属性（存在する場合のみ）
    for attr_name in ['value', 'selected', 'placeholder_text', 'is_focused']:
        if hasattr(sprite, attr_name):
            try:
                attr_value = getattr(sprite, attr_name)
                element_info['details'][attr_name] = attr_value
            except Exception:
                pass
    
    # details が空の場合は削除
    if not element_info['details']:
        del element_info['details']
    
    return element_info

def _add_facility_ui_info(sprite, element_info):
    """施設UI専用の情報を追加"""
    try:
        # ServicePanel関連の情報
        if hasattr(sprite, 'service_id'):
            element_info['details']['service_id'] = sprite.service_id
        
        # FacilityWindow関連の情報
        if hasattr(sprite, 'window_id'):
            element_info['details']['window_id'] = sprite.window_id
        
        # NavigationPanel関連の情報
        if hasattr(sprite, 'menu_items'):
            element_info['details']['menu_items_count'] = len(sprite.menu_items)
        
        # UI要素の破棄状況をチェック
        if hasattr(sprite, 'container'):
            element_info['details']['has_container'] = sprite.container is not None
        
        # UI要素の親子関係
        if hasattr(sprite, 'parent'):
            element_info['details']['has_parent'] = sprite.parent is not None
        
        # メモリリークの可能性を示す情報
        if hasattr(sprite, 'ui_elements'):
            element_info['details']['managed_elements_count'] = len(sprite.ui_elements)
        
    except Exception as e:
        # 施設UI情報の取得に失敗した場合でも、基本情報の取得は続行
        logger.debug(f"Failed to add facility UI info: {e}")
        pass

def _is_element_inside(element, container):
    """要素がコンテナの内部にあるかチェック"""
    try:
        elem_pos = element.get('position', {})
        elem_size = element.get('size', {})
        cont_pos = container.get('position', {})
        cont_size = container.get('size', {})
        
        # 必要な値がすべて存在するかチェック
        if not all([elem_pos.get('x') is not None, elem_pos.get('y') is not None,
                   elem_size.get('width') is not None, elem_size.get('height') is not None,
                   cont_pos.get('x') is not None, cont_pos.get('y') is not None,
                   cont_size.get('width') is not None, cont_size.get('height') is not None]):
            return False
        
        # 境界ボックスの計算
        elem_left = elem_pos['x']
        elem_right = elem_pos['x'] + elem_size['width']
        elem_top = elem_pos['y']
        elem_bottom = elem_pos['y'] + elem_size['height']
        
        cont_left = cont_pos['x']
        cont_right = cont_pos['x'] + cont_size['width']
        cont_top = cont_pos['y']
        cont_bottom = cont_pos['y'] + cont_size['height']
        
        # 要素がコンテナに完全に含まれるかチェック
        return (elem_left >= cont_left and elem_right <= cont_right and
                elem_top >= cont_top and elem_bottom <= cont_bottom)
        
    except Exception:
        return False

def add_to_history(event_type: str, data: Dict[str, Any]) -> None:
    """入力履歴に追加"""
    global _input_history
    _input_history.append({
        "type": event_type,
        "data": data,
        "timestamp": get_timestamp()
    })
    # 履歴サイズの制限
    if len(_input_history) > _max_history:
        _input_history = _input_history[-_max_history:]

@app.get("/screenshot", 
         operation_id="get_screenshot",
         response_model=ScreenshotResponse,
         summary="Get current game screenshot",
         description="Captures the current state of the game screen and returns it as a JPEG image")
def get_screenshot():
    """ゲーム画面のスクリーンショットを取得"""
    with _screen_lock:
        if _screen is None:
            logger.error("Screenshot requested but screen not initialized")
            raise HTTPException(
                status_code=503, 
                detail="Screen not ready. Make sure the game is running."
            )
        
        try:
            # スクリーンサイズの取得
            size = _screen.get_size()
            
            # サイズ制限のチェック
            if size[0] > MAX_SCREENSHOT_SIZE[0] or size[1] > MAX_SCREENSHOT_SIZE[1]:
                logger.warning(f"Screen size {size} exceeds maximum {MAX_SCREENSHOT_SIZE}")
            
            # スクリーンショットの生成
            raw = pygame.image.tobytes(_screen, "RGB")
            img = Image.frombytes("RGB", size, raw)
            
            # JPEG変換
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=JPEG_QUALITY)
            buf.seek(0)
            
            jpeg_data = base64.b64encode(buf.getvalue()).decode()
            
            logger.debug(f"Screenshot captured: size={size}")
            
            return ScreenshotResponse(
                jpeg=jpeg_data,
                timestamp=get_timestamp(),
                size=size
            )
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to capture screenshot: {str(e)}"
            )

@app.post("/input/key",
          operation_id="key_input_key_post",
          response_model=InputResponse,
          summary="Send keyboard input",
          description="Simulates keyboard key press or release")
def send_key_input(code: int, down: bool = True):
    """キーボード入力をゲームに送信"""
    try:
        evt_type = pygame.KEYDOWN if down else pygame.KEYUP
        event = pygame.event.Event(evt_type, key=code, mod=0)  # modifiersフィールドを追加
        pygame.event.post(event)
        
        # 履歴に記録
        add_to_history("key", {
            "code": code,
            "down": down,
            "char": chr(code) if 32 <= code <= 126 else f"<{code}>"
        })
        
        logger.debug(f"Key input: code={code}, down={down}")
        
        return InputResponse(
            ok=True,
            message=f"Key {'pressed' if down else 'released'}: {code}",
            timestamp=get_timestamp()
        )
        
    except Exception as e:
        logger.error(f"Failed to send key input: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send key input: {str(e)}"
        )

@app.post("/input/mouse",
          operation_id="mouse_input_mouse_post",
          response_model=InputResponse,
          summary="Send mouse input",
          description="Simulates mouse movement or button clicks")
def send_mouse_input(x: int, y: int, button: int = 1, action: str = "down"):
    """マウス入力をゲームに送信"""
    try:
        # 画面サイズのチェック
        if _screen:
            size = _screen.get_size()
            if x >= size[0] or y >= size[1]:
                logger.warning(f"Mouse position ({x}, {y}) is outside screen bounds {size}")
        
        if action == "move":
            # マウス移動
            pygame.mouse.set_pos((x, y))
            event = pygame.event.Event(
                pygame.MOUSEMOTION,
                pos=(x, y),
                rel=(0, 0),
                buttons=(0, 0, 0)
            )
        else:
            # マウスボタン
            evt_type = pygame.MOUSEBUTTONDOWN if action == "down" else pygame.MOUSEBUTTONUP
            event = pygame.event.Event(
                evt_type,
                pos=(x, y),
                button=button
            )
        
        pygame.event.post(event)
        
        # 履歴に記録
        add_to_history("mouse", {
            "x": x,
            "y": y,
            "button": button,
            "action": action
        })
        
        logger.debug(f"Mouse input: pos=({x}, {y}), action={action}, button={button}")
        
        return InputResponse(
            ok=True,
            message=f"Mouse {action} at ({x}, {y})",
            timestamp=get_timestamp()
        )
        
    except Exception as e:
        logger.error(f"Failed to send mouse input: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send mouse input: {str(e)}"
        )

# 追加エンドポイント
@app.get("/ui/hierarchy",
         summary="Get UI hierarchy",
         description="Returns the current UI hierarchy including windows and elements")
def get_ui_hierarchy():
    """UI階層情報を取得（拡張版）"""
    try:
        # 詳細な構造を初期化
        hierarchy = {
            'windows': [],
            'ui_elements': [],
            'window_stack': [],
            'window_count': 0,
            'status': 'extended_info_available',
            'debug_info': {}
        }
        
        # WindowManagerから詳細情報を取得
        try:
            from src.ui.window_system import WindowManager
            wm = WindowManager.get_instance()
            hierarchy['window_manager_available'] = wm is not None
            
            if wm:
                # ウィンドウスタック情報（安全にアクセス）
                try:
                    if hasattr(wm, 'window_stack'):
                        stack = getattr(wm, 'window_stack', None)
                        if stack:
                            hierarchy['window_stack'] = [str(w) for w in stack]
                        else:
                            hierarchy['window_stack'] = []
                    else:
                        hierarchy['window_stack'] = 'not_available'
                except Exception as stack_error:
                    hierarchy['window_stack_error'] = str(stack_error)
                
                # 詳細なウィンドウ情報を取得
                try:
                    if hasattr(wm, 'windows'):
                        windows = getattr(wm, 'windows', None)
                        if windows is not None:
                            hierarchy['window_count'] = len(windows)
                            hierarchy['window_ids'] = list(windows.keys())
                            
                            # 各ウィンドウの詳細情報を取得
                            for window_id, window in windows.items():
                                try:
                                    window_info = {
                                        'id': window_id,
                                        'type': window.__class__.__name__,
                                        'visible': getattr(window, 'visible', False),
                                        'exists': window is not None
                                    }
                                    
                                    # WindowState情報を追加
                                    if hasattr(window, 'state'):
                                        state = window.state
                                        window_info['state'] = str(state) if hasattr(state, 'name') else str(state)
                                    
                                    # モーダル情報
                                    if hasattr(window, 'modal'):
                                        window_info['modal'] = window.modal
                                        
                                    # UI要素の表示状態
                                    if hasattr(window, 'ui_manager'):
                                        window_info['has_ui_manager'] = window.ui_manager is not None
                                    
                                    # 位置とサイズ情報
                                    if hasattr(window, 'rect'):
                                        rect = window.rect
                                        window_info['position'] = {'x': rect.x, 'y': rect.y}
                                        window_info['size'] = {'width': rect.width, 'height': rect.height}
                                    
                                    hierarchy['windows'].append(window_info)
                                    
                                except Exception as window_error:
                                    hierarchy['debug_info'][f'window_{window_id}_error'] = str(window_error)
                        else:
                            hierarchy['window_count'] = 0
                            hierarchy['debug_info']['windows_dict_none'] = True
                    else:
                        hierarchy['window_count'] = 'attribute_not_available'
                        hierarchy['debug_info']['no_windows_attribute'] = True
                except Exception as windows_error:
                    hierarchy['windows_error'] = str(windows_error)
                
                # UI要素情報を取得（階層化版）
                try:
                    if hasattr(wm, 'ui_manager') and wm.ui_manager:
                        ui_manager = wm.ui_manager
                        hierarchy['debug_info']['ui_manager_available'] = True
                        
                        # 階層化されたUI要素情報を取得
                        hierarchy['ui_elements'] = _get_hierarchical_ui_elements(ui_manager)
                        
                    else:
                        hierarchy['debug_info']['ui_manager_available'] = False
                except Exception as ui_manager_error:
                    hierarchy['debug_info']['ui_manager_error'] = str(ui_manager_error)
            else:
                hierarchy['error'] = 'WindowManager instance not found'
                    
        except Exception as e:
            logger.warning(f"Error getting UI hierarchy info: {e}")
            hierarchy['error'] = str(e)
        
        logger.info("UI hierarchy fetched successfully (extended)")
        
        return hierarchy
        
    except Exception as e:
        logger.error(f"Failed to get UI hierarchy: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get UI hierarchy: {str(e)}"
        )

@app.get("/history",
         summary="Get input history",
         description="Returns the history of recent input events")
def get_input_history(limit: int = 100):
    """最近の入力履歴を取得"""
    return {
        "history": _input_history[-limit:],
        "total": len(_input_history),
        "limit": limit
    }

@app.get("/status",
         summary="Get server status",
         description="Returns the current status of the debug server")
def get_server_status():
    """サーバーの状態を取得"""
    return {
        "screen_ready": _screen is not None,
        "screen_size": _screen.get_size() if _screen else None,
        "history_count": len(_input_history),
        "timestamp": get_timestamp()
    }

@app.get("/game/state",
         summary="Get game state",
         description="Returns the current game state including active windows and facilities")
def get_game_state():
    """ゲームの現在の状態を取得"""
    try:
        # GameManagerのインスタンスを取得
        game_manager = _game_manager
        
        game_state = {
            "current_state": None,
            "current_facility": None,
            "active_window": None,
            "window_stack": [],
            "timestamp": get_timestamp()
        }
        
        # ゲーム状態を取得
        if hasattr(game_manager, 'current_state'):
            game_state["current_state"] = str(game_manager.current_state)
        
        # 現在の施設を取得
        if hasattr(game_manager, 'overworld_manager') and game_manager.overworld_manager:
            if hasattr(game_manager.overworld_manager, 'facility_registry'):
                fm = game_manager.overworld_manager.facility_registry
                if hasattr(fm, 'current_facility') and fm.current_facility:
                    game_state["current_facility"] = fm.current_facility
        
        # WindowManagerから情報を取得
        if hasattr(game_manager, 'window_manager') and game_manager.window_manager:
            wm = game_manager.window_manager
            if hasattr(wm, 'get_active_window'):
                active = wm.get_active_window()
                if active:
                    game_state["active_window"] = {
                        "id": active.window_id if hasattr(active, 'window_id') else str(active),
                        "type": type(active).__name__
                    }
            
            if hasattr(wm, 'window_stack'):
                game_state["window_stack"] = [
                    {
                        "id": w.window_id if hasattr(w, 'window_id') else str(w),
                        "type": type(w).__name__
                    } for w in wm.window_stack
                ]
        
        logger.info(f"Game state fetched: {game_state}")
        return game_state
        
    except Exception as e:
        logger.error(f"Failed to get game state: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get game state: {str(e)}"
        )

@app.get("/game/visible_buttons",
         summary="Get visible buttons",
         description="Returns information about currently visible buttons on screen")
def get_visible_buttons():
    """現在表示されているボタンの情報を取得"""
    try:
        buttons = []
        
        # GameManagerのインスタンスを取得
        try:
            from main import game_manager
            logger.info(f"GameManager found: {game_manager is not None}")
        except ImportError as e:
            logger.error(f"Failed to import game_manager: {e}")
            return {"buttons": [], "count": 0, "timestamp": get_timestamp()}
        
        if hasattr(game_manager, 'window_manager') and game_manager.window_manager:
            wm = game_manager.window_manager
            if hasattr(wm, 'ui_manager') and wm.ui_manager:
                # 安全にボタン情報を取得（pygame-guiには直接アクセスしない）
                logger.info("Attempting to get button information safely")
        
        # ボタンにショートカットキー番号を割り当て
        for i, button in enumerate(buttons):
            if i < 9:  # 1-9の数字キーのみ対応
                button["shortcut_key"] = str(i + 1)
            else:
                button["shortcut_key"] = None
        
        return {
            "buttons": buttons,
            "count": len(buttons),
            "timestamp": get_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to get visible buttons: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get visible buttons: {str(e)}"
        )

@app.post("/input/shortcut_key",
          operation_id="shortcut_key_input_post",
          response_model=InputResponse,
          summary="Click button by shortcut key",
          description="Clicks a button using its assigned shortcut key number (1-9)")
def click_button_by_shortcut_key(key: str):
    """ショートカットキーでボタンをクリック"""
    try:
        # 入力値の検証
        if not key.isdigit() or not (1 <= int(key) <= 9):
            raise HTTPException(
                status_code=400,
                detail="Shortcut key must be a number between 1 and 9"
            )
        
        # 現在表示されているボタンを取得
        buttons_info = get_visible_buttons()
        buttons = buttons_info.get("buttons", [])
        
        # 指定されたキー番号のボタンを検索
        target_button = None
        for button in buttons:
            if button.get("shortcut_key") == key:
                target_button = button
                break
        
        if not target_button:
            raise HTTPException(
                status_code=404,
                detail=f"No button found for shortcut key '{key}'"
            )
        
        # ボタンの中心座標を取得
        center = target_button.get("center", {})
        x, y = center.get("x"), center.get("y")
        
        if x is None or y is None:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid button coordinates for shortcut key '{key}'"
            )
        
        # マウスクリックをシミュレート
        click_event_down = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=(x, y),
            button=1
        )
        click_event_up = pygame.event.Event(
            pygame.MOUSEBUTTONUP,
            pos=(x, y),
            button=1
        )
        
        pygame.event.post(click_event_down)
        pygame.event.post(click_event_up)
        
        # 履歴に記録
        add_to_history("shortcut_key", {
            "key": key,
            "button_text": target_button.get("text", ""),
            "x": x,
            "y": y
        })
        
        button_text = target_button.get("text", "")
        logger.info(f"Shortcut key {key} clicked button '{button_text}' at ({x}, {y})")
        
        return InputResponse(
            ok=True,
            message=f"Button '{button_text}' clicked via shortcut key {key}",
            timestamp=get_timestamp()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to click button by shortcut key: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to click button by shortcut key: {str(e)}"
        )

@app.delete("/history",
            response_model=InputResponse,
            summary="Clear input history",
            description="Clears all recorded input history")
def clear_history():
    """入力履歴をクリア"""
    global _input_history
    count = len(_input_history)
    _input_history = []
    logger.info(f"Cleared {count} history entries")
    
    return InputResponse(
        ok=True,
        message=f"Cleared {count} history entries",
        timestamp=get_timestamp()
    )

# 拡張ロギング機能エンドポイント
@app.post("/debug/log", 
          summary="Add debug log entry",
          description="Adds a custom debug log entry with context")
def add_debug_log(level: str, message: str, context: Dict[str, Any] = None):
    """カスタムデバッグログエントリを追加"""
    try:
        if enhanced_logger:
            if context:
                enhanced_logger.push_context(context)
            
            log_level = getattr(logging, level.upper(), logging.INFO)
            enhanced_logger.log_with_context(log_level, message)
            
            if context:
                enhanced_logger.pop_context()
            
            return {
                "ok": True,
                "message": f"Debug log added: {message}",
                "timestamp": get_timestamp()
            }
        else:
            # フォールバック
            logger.log(getattr(logging, level.upper(), logging.INFO), message)
            return {
                "ok": True,
                "message": f"Log added (fallback): {message}",
                "timestamp": get_timestamp()
            }
    except Exception as e:
        logger.error(f"Failed to add debug log: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add debug log: {str(e)}"
        )

@app.get("/debug/middleware/status", 
         summary="Get middleware status",
         description="Returns the status of debug middleware instances")
def get_middleware_status():
    """デバッグミドルウェアの状態を取得"""
    try:
        # グローバルなミドルウェアインスタンスの状態を確認
        # （実際の実装では、ゲームクラスからミドルウェア情報を取得）
        return {
            "middleware_available": True,
            "enhanced_logging": enhanced_logger is not None,
            "timestamp": get_timestamp()
        }
    except Exception as e:
        logger.error(f"Failed to get middleware status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get middleware status: {str(e)}"
        )

@app.get("/party/info",
         summary="Get party information",
         description="Returns current party members and gold")
def get_party_info():
    """現在のパーティ情報を取得"""
    try:
        # GameManagerのインスタンスを動的に取得（セーブ・ロード対応）
        game_manager = get_current_game_manager()
        
        party_info = {
            "party_exists": False,
            "party_name": None,
            "party_id": None,
            "gold": 0,
            "characters": [],
            "character_count": 0,
            "timestamp": get_timestamp()
        }
        
        if game_manager and hasattr(game_manager, 'current_party') and game_manager.current_party:
            party = game_manager.current_party
            party_info["party_exists"] = True
            party_info["party_name"] = getattr(party, 'name', 'Unknown Party')
            party_info["party_id"] = getattr(party, 'party_id', 'Unknown ID')
            party_info["gold"] = getattr(party, 'gold', 0)
            
            # パーティメンバーの基本情報を取得
            if hasattr(party, 'get_all_characters'):
                characters = party.get_all_characters()
                party_info["character_count"] = len(characters)
                
                for char in characters:
                    char_info = {
                        "character_id": getattr(char, 'character_id', 'Unknown ID'),
                        "name": getattr(char, 'name', 'Unknown'),
                        "level": 1,  # デフォルト値
                        "hp": 0,
                        "max_hp": 0,
                        "status": "unknown"
                    }
                    
                    # レベル情報
                    if hasattr(char, 'experience') and hasattr(char.experience, 'level'):
                        char_info["level"] = char.experience.level
                    
                    # HP情報
                    if hasattr(char, 'derived_stats'):
                        stats = char.derived_stats
                        if hasattr(stats, 'current_hp'):
                            char_info["hp"] = stats.current_hp
                        if hasattr(stats, 'max_hp'):
                            char_info["max_hp"] = stats.max_hp
                    
                    # ステータス情報
                    if hasattr(char, 'status'):
                        if hasattr(char.status, 'value'):
                            char_info["status"] = char.status.value
                        else:
                            char_info["status"] = str(char.status)
                    
                    party_info["characters"].append(char_info)
                
        logger.info(f"Party info fetched: {party_info['character_count']} characters, {party_info['gold']} gold")
        return party_info
        
    except Exception as e:
        logger.error(f"Failed to get party info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get party info: {str(e)}"
        )

@app.get("/debug/game_manager",
         summary="Debug game manager access",
         description="Returns detailed debug information about game_manager access")
def debug_game_manager_access():
    """GameManagerアクセスのデバッグ情報を取得"""
    try:
        debug_info = {
            "timestamp": get_timestamp(),
            "game_manager_import_success": False,
            "game_manager_exists": False,
            "game_manager_type": None,
            "game_manager_attributes": [],
            "current_party_exists": False,
            "current_party_type": None,
            "error_details": None,
            "retrieval_debug": get_game_manager_debug_info()
        }
        
        try:
            # 動的取得を使用してデバッグ
            game_manager = get_current_game_manager()
            debug_info["game_manager_import_success"] = True
            debug_info["game_manager_exists"] = game_manager is not None
            
            if game_manager is not None:
                debug_info["game_manager_type"] = str(type(game_manager))
                debug_info["game_manager_attributes"] = [attr for attr in dir(game_manager) if not attr.startswith('_')]
                
                if hasattr(game_manager, 'current_party'):
                    debug_info["current_party_exists"] = game_manager.current_party is not None
                    if game_manager.current_party is not None:
                        debug_info["current_party_type"] = str(type(game_manager.current_party))
                        
                        # パーティの詳細情報
                        party = game_manager.current_party
                        debug_info["party_details"] = {
                            "name": getattr(party, 'name', 'Unknown'),
                            "party_id": getattr(party, 'party_id', 'Unknown'),
                            "has_members": hasattr(party, 'members'),
                            "has_get_all_characters": hasattr(party, 'get_all_characters'),
                            "party_type": str(type(party))
                        }
                        
                        # メンバー数の取得を複数の方法で試行
                        try:
                            if hasattr(party, 'members'):
                                members = party.members
                                debug_info["party_details"]["members_count"] = len(members)
                                debug_info["party_details"]["members_type"] = str(type(members))
                            else:
                                debug_info["party_details"]["members_count"] = 0
                                debug_info["party_details"]["members_access_error"] = "No members attribute"
                        except Exception as members_error:
                            debug_info["party_details"]["members_count"] = 0
                            debug_info["party_details"]["members_error"] = str(members_error)
                        
                        if hasattr(party, 'get_all_characters'):
                            try:
                                characters = party.get_all_characters()
                                debug_info["party_details"]["characters_from_method"] = len(characters)
                            except Exception as char_error:
                                debug_info["party_details"]["characters_method_error"] = str(char_error)
                
        except ImportError as import_error:
            debug_info["error_details"] = f"Import error: {str(import_error)}"
        except Exception as general_error:
            debug_info["error_details"] = f"General error: {str(general_error)}"
            
        return debug_info
        
    except Exception as e:
        logger.error(f"Failed to debug game manager access: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to debug game manager access: {str(e)}"
        )

@app.get("/party/character/{character_index}",
         summary="Get character details",
         description="Returns detailed information about a specific party member")
def get_character_details(character_index: int):
    """パーティメンバーの詳細情報を取得"""
    try:
        # GameManagerのインスタンスを動的に取得（セーブ・ロード対応）
        game_manager = get_current_game_manager()
        
        character_info = {
            "character_exists": False,
            "character_index": character_index,
            "timestamp": get_timestamp()
        }
        
        if game_manager and hasattr(game_manager, 'current_party') and game_manager.current_party:
            party = game_manager.current_party
            
            if hasattr(party, 'get_all_characters'):
                characters = party.get_all_characters()
                
                if 0 <= character_index < len(characters):
                    char = characters[character_index]
                    character_info["character_exists"] = True
                    
                    # 基本情報
                    character_info["character_id"] = getattr(char, 'character_id', 'Unknown ID')
                    character_info["name"] = getattr(char, 'name', 'Unknown')
                    character_info["race"] = getattr(char, 'race', 'Unknown')
                    character_info["character_class"] = getattr(char, 'character_class', 'Unknown')
                    
                    # レベル・経験値情報
                    if hasattr(char, 'experience'):
                        exp = char.experience
                        character_info["level"] = getattr(exp, 'level', 1)
                        character_info["experience"] = getattr(exp, 'current_exp', 0)
                        character_info["next_level_exp"] = getattr(exp, 'next_level_exp', 0)
                    
                    # ステータス情報
                    character_info["stats"] = {}
                    if hasattr(char, 'base_stats'):
                        base_stats = char.base_stats
                        for stat_name in ['strength', 'intelligence', 'piety', 'vitality', 'agility', 'luck']:
                            if hasattr(base_stats, stat_name):
                                character_info["stats"][stat_name] = getattr(base_stats, stat_name)
                    
                    # HP/MP情報
                    if hasattr(char, 'derived_stats'):
                        derived = char.derived_stats
                        character_info["hp"] = getattr(derived, 'current_hp', 0)
                        character_info["max_hp"] = getattr(derived, 'max_hp', 0)
                        character_info["mp"] = getattr(derived, 'current_mp', 0)
                        character_info["max_mp"] = getattr(derived, 'max_mp', 0)
                    
                    # 状態情報
                    if hasattr(char, 'status'):
                        status = char.status
                        if hasattr(status, 'value'):
                            character_info["condition"] = status.value
                        else:
                            character_info["condition"] = str(status)
                        character_info["is_alive"] = hasattr(char, 'is_alive') and char.is_alive()
                    
                    # 装備・アイテム情報
                    character_info["equipment"] = []
                    character_info["inventory"] = []
                    character_info["inventory_count"] = 0
                    
                    # 装備中のアイテム
                    if hasattr(char, 'equipment') and hasattr(char.equipment, 'equipped_items'):
                        equipped = char.equipment.equipped_items
                        for slot, item in equipped.items():
                            if item:
                                equipment_item = {
                                    "slot": slot,
                                    "item_name": getattr(item, 'name', 'Unknown Item'),
                                    "item_id": getattr(item, 'item_id', 'Unknown ID'),
                                    "equipped": True
                                }
                                
                                # アイテムの詳細情報を追加
                                if hasattr(item, 'item_type'):
                                    equipment_item["item_type"] = getattr(item.item_type, 'value', str(item.item_type))
                                if hasattr(item, 'description'):
                                    equipment_item["description"] = item.description
                                if hasattr(item, 'stats_modifier'):
                                    equipment_item["stats_modifier"] = item.stats_modifier
                                
                                character_info["equipment"].append(equipment_item)
                    
                    # 所持品（インベントリ）- 新しいインベントリシステムを使用
                    # キャラクターIDを取得
                    char_id = getattr(char, 'character_id', None)
                    logger.info(f"DBG_API: Getting inventory for character_id={char_id}")
                    
                    if char_id:
                        # 新しいインベントリシステムから取得
                        char_inventory = inventory_manager.get_character_inventory(char_id)
                        
                        # インベントリが存在しない場合は作成
                        if not char_inventory:
                            logger.info(f"DBG_API: Creating inventory for character_id={char_id}")
                            char_inventory = inventory_manager.create_character_inventory(char_id)
                        
                        if char_inventory:
                            logger.info(f"DBG_API: Found character inventory for {char_id}")
                            inventory_items = []
                            
                            # get_all_items()メソッドを使用してアイテムを取得
                            for slot_index, item_instance in char_inventory.get_all_items():
                                inventory_items.append((slot_index, item_instance))
                            
                            character_info["inventory_count"] = len(inventory_items)
                            logger.info(f"DBG_API: Character {char_id} has {len(inventory_items)} items")
                            
                            # 各アイテムの詳細情報を取得
                            for slot_index, item_instance in inventory_items:
                                # アイテムマネージャーからアイテム情報を取得
                                from src.items.item import item_manager
                                item = item_manager.get_item(item_instance.item_id)
                                
                                if item:
                                    inventory_item = {
                                        "item_name": item.get_name(),
                                        "item_id": item_instance.item_id,
                                        "equipped": False,
                                        "slot_index": slot_index,
                                        "quantity": item_instance.quantity,
                                        "identified": item_instance.identified,
                                        "condition": item_instance.condition
                                    }
                                    
                                    # アイテムの詳細情報を追加
                                    if hasattr(item, 'item_type'):
                                        inventory_item["item_type"] = item.item_type.value
                                    
                                    if hasattr(item, 'description'):
                                        inventory_item["description"] = item.get_description()
                                    
                                    if hasattr(item, 'price'):
                                        inventory_item["value"] = item.price
                                    
                                    # アイテムが装備可能かどうか
                                    equipable_types = ['weapon', 'armor', 'shield', 'helmet', 'accessory']
                                    inventory_item["equipable"] = item.item_type.value in equipable_types
                                    
                                    character_info["inventory"].append(inventory_item)
                                else:
                                    # アイテム情報が取得できない場合の最小限の情報
                                    inventory_item = {
                                        "item_name": f"Unknown Item ({item_instance.item_id})",
                                        "item_id": item_instance.item_id,
                                        "equipped": False,
                                        "slot_index": slot_index,
                                        "quantity": item_instance.quantity,
                                        "identified": item_instance.identified,
                                        "condition": item_instance.condition
                                    }
                                    character_info["inventory"].append(inventory_item)
                        else:
                            # インベントリが存在しない場合
                            character_info["inventory_count"] = 0
                            logger.debug(f"No inventory found for character {char_id}")
                    else:
                        # キャラクターIDが取得できない場合
                        character_info["inventory_count"] = 0
                        logger.warning("Character ID not found, cannot retrieve inventory")
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Character index {character_index} not found. Party has {len(characters)} characters."
                    )
        else:
            raise HTTPException(
                status_code=404,
                detail="No active party found"
            )
        
        logger.info(f"Character details fetched for index {character_index}")
        return character_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get character details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get character details: {str(e)}"
        )

@app.get("/adventure/list",
         summary="Get adventure guild character list",
         description="Returns list of all characters registered in the adventure guild")
def get_adventure_guild_list():
    """冒険者ギルドに登録されたキャラクター一覧を取得"""
    try:
        # GameManagerのインスタンスを動的に取得（セーブ・ロード対応）
        game_manager = get_current_game_manager()
        
        guild_info = {
            "guild_characters_count": 0,
            "guild_characters": [],
            "timestamp": get_timestamp()
        }
        
        if game_manager and hasattr(game_manager, 'get_guild_characters'):
            guild_characters = game_manager.get_guild_characters()
            guild_info["guild_characters_count"] = len(guild_characters)
            
            for char in guild_characters:
                char_info = {
                    "character_id": getattr(char, 'character_id', 'Unknown ID'),
                    "name": getattr(char, 'name', 'Unknown'),
                    "race": getattr(char, 'race', 'Unknown'),
                    "character_class": getattr(char, 'character_class', 'Unknown'),
                    "level": 1,
                    "hp": 0,
                    "max_hp": 0,
                    "status": "unknown"
                }
                
                # レベル情報
                if hasattr(char, 'experience') and hasattr(char.experience, 'level'):
                    char_info["level"] = char.experience.level
                
                # HP情報
                if hasattr(char, 'derived_stats'):
                    stats = char.derived_stats
                    if hasattr(stats, 'current_hp'):
                        char_info["hp"] = stats.current_hp
                    if hasattr(stats, 'max_hp'):
                        char_info["max_hp"] = stats.max_hp
                
                # ステータス情報
                if hasattr(char, 'status'):
                    if hasattr(char.status, 'value'):
                        char_info["status"] = char.status.value
                    else:
                        char_info["status"] = str(char.status)
                
                guild_info["guild_characters"].append(char_info)
        
        logger.info(f"Adventure guild list fetched: {guild_info['guild_characters_count']} characters")
        return guild_info
        
    except Exception as e:
        logger.error(f"Failed to get adventure guild list: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get adventure guild list: {str(e)}"
        )

@app.get("/debug/facility-ui",
         summary="Get facility UI debug information",
         description="Returns detailed debug information about facility UI structure")
def get_facility_ui_debug():
    """施設UI専用のデバッグ情報を取得"""
    try:
        debug_info = {
            "timestamp": get_timestamp(),
            "facility_windows": [],
            "service_panels": [],
            "navigation_panels": [],
            "ui_memory_issues": [],
            "destruction_analysis": {}
        }
        
        # WindowManagerから詳細情報を取得
        try:
            from src.ui.window_system import WindowManager
            wm = WindowManager.get_instance()
            
            if wm and hasattr(wm, 'ui_manager') and wm.ui_manager:
                # 施設UI専用の分析を実行
                debug_info.update(_analyze_facility_ui_structure(wm.ui_manager))
                
                # パネル破棄状況の診断
                debug_info["destruction_analysis"] = _diagnose_panel_destruction(wm.ui_manager)
                
                # メモリリークの可能性を分析
                debug_info["ui_memory_issues"] = _detect_ui_memory_issues(wm.ui_manager)
                
            else:
                debug_info["error"] = "WindowManager or UIManager not available"
                
        except Exception as e:
            debug_info["error"] = str(e)
            logger.error(f"Failed to analyze facility UI: {e}")
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Failed to get facility UI debug info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get facility UI debug info: {str(e)}"
        )

def _analyze_facility_ui_structure(ui_manager):
    """施設UI専用の構造分析"""
    analysis = {
        "facility_windows": [],
        "service_panels": [],
        "navigation_panels": [],
        "ui_element_counts": {}
    }
    
    try:
        # スプライトグループから要素を取得
        sprite_group = ui_manager.get_sprite_group()
        sprites = sprite_group.sprites() if hasattr(sprite_group, 'sprites') else list(sprite_group)
        
        # 施設UI要素の分類
        for sprite in sprites:
            element_type = sprite.__class__.__name__
            
            # 要素タイプ別のカウント
            if element_type not in analysis["ui_element_counts"]:
                analysis["ui_element_counts"][element_type] = 0
            analysis["ui_element_counts"][element_type] += 1
            
            # FacilityWindow の検出
            if "FacilityWindow" in element_type or hasattr(sprite, 'window_id'):
                facility_window = {
                    "type": element_type,
                    "window_id": getattr(sprite, 'window_id', 'unknown'),
                    "visible": bool(getattr(sprite, 'visible', 0)),
                    "has_main_panel": hasattr(sprite, 'main_panel'),
                    "current_service_id": getattr(sprite, 'current_service_id', None),
                    "service_panel_count": len(getattr(sprite, 'service_panels', {}))
                }
                analysis["facility_windows"].append(facility_window)
            
            # ServicePanel の検出
            elif "ServicePanel" in element_type or hasattr(sprite, 'service_id'):
                service_panel = {
                    "type": element_type,
                    "service_id": getattr(sprite, 'service_id', 'unknown'),
                    "visible": bool(getattr(sprite, 'visible', 0)),
                    "has_container": hasattr(sprite, 'container'),
                    "ui_elements_count": len(getattr(sprite, 'ui_elements', [])),
                    "container_valid": getattr(sprite, 'container', None) is not None
                }
                analysis["service_panels"].append(service_panel)
            
            # NavigationPanel の検出
            elif "NavigationPanel" in element_type or hasattr(sprite, 'menu_items'):
                navigation_panel = {
                    "type": element_type,
                    "visible": bool(getattr(sprite, 'visible', 0)),
                    "menu_items_count": len(getattr(sprite, 'menu_items', [])),
                    "has_buttons": hasattr(sprite, 'buttons')
                }
                analysis["navigation_panels"].append(navigation_panel)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze facility UI structure: {e}")
        return analysis

def _diagnose_panel_destruction(ui_manager):
    """パネル破棄の完全性を診断"""
    diagnosis = {
        "orphaned_elements": [],
        "incomplete_destructions": [],
        "memory_leak_indicators": [],
        "destruction_completeness": "unknown"
    }
    
    try:
        # スプライトグループから要素を取得
        sprite_group = ui_manager.get_sprite_group()
        sprites = sprite_group.sprites() if hasattr(sprite_group, 'sprites') else list(sprite_group)
        
        for sprite in sprites:
            element_info = {
                "type": sprite.__class__.__name__,
                "object_id": getattr(sprite, 'object_ids', ['unknown'])[0] if hasattr(sprite, 'object_ids') else 'unknown'
            }
            
            # 孤立要素の検出
            if hasattr(sprite, 'container'):
                container = sprite.container
                if container is None:
                    element_info["issue"] = "container is None"
                    diagnosis["orphaned_elements"].append(element_info)
                elif not hasattr(container, 'rect'):
                    element_info["issue"] = "container has no rect"
                    diagnosis["orphaned_elements"].append(element_info)
            
            # 不完全な破棄の検出
            if hasattr(sprite, 'ui_elements'):
                ui_elements = sprite.ui_elements
                if isinstance(ui_elements, list) and len(ui_elements) > 0:
                    # ui_elements リストに要素が残っている場合
                    dead_elements = []
                    for elem in ui_elements:
                        if not hasattr(elem, 'rect') or not hasattr(elem, 'visible'):
                            dead_elements.append(str(type(elem)))
                    
                    if dead_elements:
                        element_info["dead_elements"] = dead_elements
                        diagnosis["incomplete_destructions"].append(element_info)
            
            # メモリリークの兆候
            if hasattr(sprite, 'parent') and sprite.parent is not None:
                # 親要素が存在するが、親のコンテナが無効な場合
                parent = sprite.parent
                if hasattr(parent, 'container') and parent.container is None:
                    element_info["issue"] = "parent container is None"
                    diagnosis["memory_leak_indicators"].append(element_info)
        
        # 全体的な破棄の完全性を評価
        total_issues = (len(diagnosis["orphaned_elements"]) + 
                       len(diagnosis["incomplete_destructions"]) + 
                       len(diagnosis["memory_leak_indicators"]))
        
        if total_issues == 0:
            diagnosis["destruction_completeness"] = "excellent"
        elif total_issues < 3:
            diagnosis["destruction_completeness"] = "good"
        elif total_issues < 10:
            diagnosis["destruction_completeness"] = "moderate"
        else:
            diagnosis["destruction_completeness"] = "poor"
        
        return diagnosis
        
    except Exception as e:
        logger.error(f"Failed to diagnose panel destruction: {e}")
        diagnosis["error"] = str(e)
        return diagnosis

def _detect_ui_memory_issues(ui_manager):
    """UIメモリ問題の検出"""
    issues = []
    
    try:
        # スプライトグループから要素を取得
        sprite_group = ui_manager.get_sprite_group()
        sprites = sprite_group.sprites() if hasattr(sprite_group, 'sprites') else list(sprite_group)
        
        # 要素タイプ別のカウント
        type_counts = {}
        for sprite in sprites:
            element_type = sprite.__class__.__name__
            type_counts[element_type] = type_counts.get(element_type, 0) + 1
        
        # 異常に多い要素タイプを検出
        for element_type, count in type_counts.items():
            if count > 50:  # 閾値: 50個を超える同じタイプの要素
                issues.append({
                    "type": "excessive_elements",
                    "element_type": element_type,
                    "count": count,
                    "severity": "high" if count > 100 else "medium"
                })
        
        # 重複する object_id の検出
        object_ids = {}
        for sprite in sprites:
            if hasattr(sprite, 'object_ids') and sprite.object_ids:
                obj_id = sprite.object_ids[0]
                if obj_id != 'unknown':
                    object_ids[obj_id] = object_ids.get(obj_id, 0) + 1
        
        for obj_id, count in object_ids.items():
            if count > 1:
                issues.append({
                    "type": "duplicate_object_ids",
                    "object_id": obj_id,
                    "count": count,
                    "severity": "medium"
                })
        
        return issues
        
    except Exception as e:
        logger.error(f"Failed to detect UI memory issues: {e}")
        return [{"type": "detection_error", "error": str(e)}]

@app.get("/debug/ui-snapshot",
         summary="Create UI snapshot",
         description="Creates a snapshot of the current UI state for comparison")
def create_ui_snapshot():
    """現在のUI状態のスナップショットを作成"""
    try:
        snapshot = {
            "timestamp": get_timestamp(),
            "ui_elements": [],
            "element_count": 0,
            "facility_ui_count": 0
        }
        
        # WindowManagerから詳細情報を取得
        try:
            from src.ui.window_system import WindowManager
            wm = WindowManager.get_instance()
            
            if wm and hasattr(wm, 'ui_manager') and wm.ui_manager:
                # 階層化されたUI要素情報を取得
                snapshot["ui_elements"] = _get_hierarchical_ui_elements(wm.ui_manager)
                snapshot["element_count"] = len(snapshot["ui_elements"])
                
                # 施設UI要素の数をカウント
                for element in snapshot["ui_elements"]:
                    if _is_facility_ui_element(element):
                        snapshot["facility_ui_count"] += 1
                
            else:
                snapshot["error"] = "WindowManager or UIManager not available"
                
        except Exception as e:
            snapshot["error"] = str(e)
            logger.error(f"Failed to create UI snapshot: {e}")
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Failed to create UI snapshot: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create UI snapshot: {str(e)}"
        )

def _is_facility_ui_element(element):
    """要素が施設UI要素かどうかを判定"""
    element_type = element.get('type', '')
    
    # 施設UI関連のクラス名をチェック
    facility_ui_types = [
        'FacilityWindow', 'ServicePanel', 'NavigationPanel',
        'BuyPanel', 'SellPanel', 'StoragePanel', 'IdentifyPanel',
        'CharacterListPanel', 'PartyFormationPanel', 'CharacterCreationWizard'
    ]
    
    for ui_type in facility_ui_types:
        if ui_type in element_type:
            return True
    
    # 詳細情報から判定
    details = element.get('details', {})
    if 'service_id' in details or 'window_id' in details:
        return True
    
    return False

# サーバー起動関数
def _run_server():
    """サーバーを起動"""
    logger.debug(f"Starting debug server on {DEFAULT_HOST}:{DEFAULT_PORT}")
    uvicorn.run(app, host=DEFAULT_HOST, port=DEFAULT_PORT, log_level="warning")

def start(screen: pygame.Surface, game_manager=None, port: int = DEFAULT_PORT):
    """
    デバッグサーバーを起動
    
    Args:
        screen: pygame.Surfaceオブジェクト
        game_manager: GameManagerインスタンス（オプション）
        port: サーバーポート（デフォルト: 8765）
    """
    global _screen, _game_manager, DEFAULT_PORT
    
    with _screen_lock:
        _screen = screen
        if game_manager is not None:
            # 新しいGameManagerインスタンスが渡された場合
            if _game_manager is not game_manager:
                if _game_manager is not None:
                    old_address = hex(id(_game_manager))
                    new_address = hex(id(game_manager))
                    logger.debug(f"Debug server GameManager updated: {old_address} -> {new_address}")
                else:
                    logger.debug(f"Debug server GameManager initialized: {hex(id(game_manager))}")
                _game_manager = game_manager
    
    DEFAULT_PORT = port
    logger.debug(f"Initializing debug server with screen size: {screen.get_size()}")
    if game_manager:
        logger.debug(f"Debug server initialized with GameManager: {type(game_manager)} at {hex(id(game_manager))}")
    else:
        logger.warning("Debug server initialized without GameManager - some features may not work")
    
    # MCPを初期化
    setup_mcp()
    
    # サーバーをデーモンスレッドで起動
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()
    
    logger.debug("Debug server thread started")

# MCP設定を起動関数内に移動
def setup_mcp():
    """MCP設定を初期化"""
    mcp = FastApiMCP(
        app,
        name="dungeon-msp",
        description="Dungeon game debugging and testing MCP server")
    mcp.mount()
    return mcp

# エラーハンドラー
@app.exception_handler(Exception)
async def general_exception_handler(_, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "timestamp": get_timestamp()
        }
    )