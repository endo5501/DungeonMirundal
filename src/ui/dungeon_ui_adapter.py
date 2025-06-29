"""ダンジョンUI移行アダプタ - 旧UIMenuから新WindowSystemへの橋渡し"""

from typing import Dict, Optional, Callable, Any
from src.ui.windows.dungeon_menu_manager import dungeon_menu_manager
from src.character.party import Party
from src.utils.logger import logger


class DungeonUIManagerAdapter:
    """
    ダンジョンUI移行アダプタクラス
    
    旧dungeon_ui_pygame.pyのインターフェースを維持しながら、
    内部では新しいWindowSystemベースのダンジョンUIを使用する
    """
    
    def __init__(self, screen=None):
        """
        アダプタを初期化
        
        Args:
            screen: 画面サーフェス（互換性のため保持）
        """
        self.screen = screen
        self.current_party: Optional[Party] = None
        self.dungeon_state: Any = None
        self.callbacks: Dict[str, Callable] = {}
        
        # 画面サイズ
        if screen:
            self.screen_width = screen.get_width()
            self.screen_height = screen.get_height()
        else:
            self.screen_width = 1024
            self.screen_height = 768
        
        # UI状態（互換性のため）
        self.is_menu_open = False
        self.current_menu_type = None
        self.selected_menu_index = 0
        
        # 色設定（互換性のため）
        self.colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'gray': (128, 128, 128),
            'dark_gray': (64, 64, 64),
            'light_gray': (192, 192, 192),
            'blue': (0, 100, 200),
            'dark_blue': (0, 50, 100),
            'green': (0, 150, 0),
            'red': (200, 0, 0),
            'menu_bg': (40, 40, 60, 200),
        }
        
        # メニュー設定（互換性のため）
        self.menu_width = 300
        self.menu_height = 400
        self.menu_x = (self.screen_width - self.menu_width) // 2
        self.menu_y = (self.screen_height - self.menu_height) // 2
        
        # メニュー項目（互換性のため）
        self.menu_items = [
            {"text": "Inventory", "action": "inventory"},
            {"text": "Magic", "action": "magic"},
            {"text": "Equipment", "action": "equipment"},
            {"text": "Camp", "action": "camp"},
            {"text": "Status", "action": "status"},
            {"text": "Effects", "action": "status_effects"},
            {"text": "Return to Surface", "action": "return_overworld"},
            {"text": "Close", "action": "close"}
        ]
        
        # 新しいWindowSystemベースのメニューを初期化
        self._create_new_menu()
        
        logger.info("DungeonUIManagerAdapter初期化完了")
    
    def _create_new_menu(self) -> None:
        """新しいWindowSystemベースのメニューを作成"""
        try:
            # ダンジョンメニューを作成
            dungeon_menu_manager.create_dungeon_menu(self.screen)
            
            # 既存のコールバックを設定
            for action, callback in self.callbacks.items():
                dungeon_menu_manager.set_callback(action, callback)
            
            # パーティとダンジョン状態を設定
            if self.current_party:
                dungeon_menu_manager.set_party(self.current_party)
            if self.dungeon_state:
                dungeon_menu_manager.set_dungeon_state(self.dungeon_state)
                
        except Exception as e:
            logger.error(f"アダプタ: 新メニュー作成エラー - {e}")
    
    def set_party(self, party: Party) -> None:
        """パーティを設定（旧インターフェース互換）"""
        self.current_party = party
        dungeon_menu_manager.set_party(party)
        logger.info(f"アダプタ: パーティ設定 - {party.name}")
    
    def set_callback(self, action: str, callback: Callable) -> None:
        """コールバックを設定（旧インターフェース互換）"""
        self.callbacks[action] = callback
        dungeon_menu_manager.set_callback(action, callback)
        logger.debug(f"アダプタ: コールバック設定 - {action}")
    
    def set_dungeon_state(self, dungeon_state: Any) -> None:
        """ダンジョン状態を設定（旧インターフェース互換）"""
        self.dungeon_state = dungeon_state
        dungeon_menu_manager.set_dungeon_state(dungeon_state)
        logger.debug("アダプタ: ダンジョン状態設定")
    
    def toggle_main_menu(self) -> None:
        """メインメニューの表示/非表示を切り替え（旧インターフェース互換）"""
        try:
            dungeon_menu_manager.toggle_main_menu()
            # 状態を同期
            self.is_menu_open = dungeon_menu_manager.is_menu_open()
        except Exception as e:
            logger.error(f"アダプタ: メニュートグルエラー - {e}")
    
    def show_main_menu(self) -> None:
        """メインメニューを表示（旧インターフェース互換）"""
        try:
            dungeon_menu_manager.show_main_menu()
            self.is_menu_open = True
            self.current_menu_type = "main"
            logger.info("アダプタ: メインメニュー表示")
        except Exception as e:
            logger.error(f"アダプタ: メインメニュー表示エラー - {e}")
    
    def close_menu(self) -> None:
        """メニューを閉じる（旧インターフェース互換）"""
        try:
            dungeon_menu_manager.close_menu()
            self.is_menu_open = False
            self.current_menu_type = None
            logger.info("アダプタ: メニュー閉じる")
        except Exception as e:
            logger.error(f"アダプタ: メニュー閉じるエラー - {e}")
    
    def handle_input(self, event) -> bool:
        """入力処理（旧インターフェース互換）"""
        try:
            result = dungeon_menu_manager.handle_input(event)
            # 状態を同期
            self.is_menu_open = dungeon_menu_manager.is_menu_open()
            return result
        except Exception as e:
            logger.error(f"アダプタ: 入力処理エラー - {e}")
            return False
    
    def render(self) -> None:
        """UIを描画（旧インターフェース互換）"""
        try:
            dungeon_menu_manager.render()
        except Exception as e:
            logger.error(f"アダプタ: UI描画エラー - {e}")
    
    def render_overlay(self) -> None:
        """オーバーレイUIを描画（旧インターフェース互換）"""
        try:
            dungeon_menu_manager.render_overlay()
        except Exception as e:
            logger.error(f"アダプタ: オーバーレイ描画エラー - {e}")
    
    def update(self) -> None:
        """UI更新（旧インターフェース互換）"""
        try:
            dungeon_menu_manager.update()
        except Exception as e:
            logger.error(f"アダプタ: UI更新エラー - {e}")
    
    def cleanup(self) -> None:
        """リソースのクリーンアップ（旧インターフェース互換）"""
        try:
            dungeon_menu_manager.cleanup()
            self.callbacks.clear()
            self.current_party = None
            self.dungeon_state = None
            logger.info("アダプタ: リソースクリーンアップ完了")
        except Exception as e:
            logger.error(f"アダプタ: クリーンアップエラー - {e}")
    
    # 以下、旧インターフェースで使用されていた他のメソッドも必要に応じて実装
    def show_status_bar(self) -> None:
        """ステータスバー表示（旧インターフェース互換）"""
        # 現在は何もしない（新システムでは常時表示）
        pass
    
    def update_location(self, location_info: str) -> None:
        """位置情報更新（旧インターフェース互換）"""
        # 現在は何もしない（新システムでは自動取得）
        pass
    
    def update_party_status(self) -> None:
        """パーティステータス更新（旧インターフェース互換）"""
        # 現在は何もしない（新システムでは自動更新）
        pass
    
    def _execute_menu_action(self) -> None:
        """メニューアクション実行（旧インターフェース内部メソッド）"""
        # 新システムで自動処理されるため、何もしない
        pass
    
    def _initialize_character_status_bar(self) -> None:
        """キャラクターステータスバー初期化（旧インターフェース内部メソッド）"""
        # 新システムで自動処理されるため、何もしない
        pass
    
    # プロパティでアクセスできるようにする（旧コードとの互換性）
    @property
    def character_status_bar(self):
        """キャラクターステータスバー（互換性のため）"""
        return None  # 新システムでは直接アクセス不要
    
    @property
    def small_map_ui(self):
        """小地図UI（互換性のため）"""
        return None  # 新システムでは直接アクセス不要


# 旧システムとの互換性を保つためのファクトリ関数
def create_pygame_dungeon_ui(screen=None) -> DungeonUIManagerAdapter:
    """
    Pygame版ダンジョンUI作成（互換性関数）
    
    Args:
        screen: 画面サーフェス
        
    Returns:
        DungeonUIManagerAdapter: アダプタインスタンス
    """
    return DungeonUIManagerAdapter(screen)


# グローバル変数（旧システムとの互換性）
dungeon_ui_manager_pygame = None


def get_dungeon_ui_manager() -> DungeonUIManagerAdapter:
    """
    ダンジョンUIマネージャーを取得（シングルトン的アクセス）
    
    Returns:
        DungeonUIManagerAdapter: ダンジョンUIマネージャー
    """
    global dungeon_ui_manager_pygame
    if not dungeon_ui_manager_pygame:
        dungeon_ui_manager_pygame = create_pygame_dungeon_ui()
    return dungeon_ui_manager_pygame