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
_screen_lock = threading.Lock()
_input_history: list[Dict[str, Any]] = []
_max_history = 1000

# ヘルパー関数
def get_timestamp() -> str:
    """現在のタイムスタンプを取得"""
    return datetime.now().isoformat()

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
            
            logger.info(f"Screenshot captured: size={size}")
            
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
        event = pygame.event.Event(evt_type, key=code)
        pygame.event.post(event)
        
        # 履歴に記録
        add_to_history("key", {
            "code": code,
            "down": down,
            "char": chr(code) if 32 <= code <= 126 else f"<{code}>"
        })
        
        logger.info(f"Key input: code={code}, down={down}")
        
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
        
        logger.info(f"Mouse input: pos=({x}, {y}), action={action}, button={button}")
        
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
    """UI階層情報を取得（最小限の実装）"""
    try:
        # 最小限の構造を初期化
        hierarchy = {
            'window_stack': [],
            'window_count': 0,
            'status': 'minimal_info_only'
        }
        
        # WindowManagerから最小限の情報のみ取得
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
                
                # ウィンドウ数の取得（安全にアクセス）
                try:
                    if hasattr(wm, 'windows'):
                        windows = getattr(wm, 'windows', None)
                        if windows is not None:
                            hierarchy['window_count'] = len(windows)
                            # ウィンドウIDリストも安全に取得
                            try:
                                hierarchy['window_ids'] = list(windows.keys())
                            except Exception:
                                hierarchy['window_ids'] = 'enumeration_failed'
                        else:
                            hierarchy['window_count'] = 0
                    else:
                        hierarchy['window_count'] = 'attribute_not_available'
                except Exception as windows_error:
                    hierarchy['windows_error'] = str(windows_error)
            else:
                hierarchy['error'] = 'WindowManager instance not found'
                    
        except Exception as e:
            logger.warning(f"Error getting basic window info: {e}")
            hierarchy['error'] = str(e)
        
        logger.info("UI hierarchy fetched successfully (minimal)")
        
        return {
            "hierarchy": hierarchy,
            "timestamp": get_timestamp()
        }
        
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
        from main import game_manager
        
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
        
        # pygame_guiのUIManagerから情報を取得
        from src.ui.window_system import WindowManager
        
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
                ui_manager = wm.ui_manager
                
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

# サーバー起動関数
def _run_server():
    """サーバーを起動"""
    logger.info(f"Starting debug server on {DEFAULT_HOST}:{DEFAULT_PORT}")
    uvicorn.run(app, host=DEFAULT_HOST, port=DEFAULT_PORT, log_level="warning")

def start(screen: pygame.Surface, port: int = DEFAULT_PORT):
    """
    デバッグサーバーを起動
    
    Args:
        screen: pygame.Surfaceオブジェクト
        port: サーバーポート（デフォルト: 8765）
    """
    global _screen, DEFAULT_PORT
    
    with _screen_lock:
        _screen = screen
    
    DEFAULT_PORT = port
    logger.info(f"Initializing debug server with screen size: {screen.get_size()}")
    
    # MCPを初期化
    setup_mcp()
    
    # サーバーをデーモンスレッドで起動
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()
    
    logger.info("Debug server thread started")

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