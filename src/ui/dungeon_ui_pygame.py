"""ダンジョン内UIシステム（WindowSystem統合版）"""

from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import pygame

from src.ui.window_system import WindowManager
from src.ui.window_system.battle_ui_window import BattleUIWindow
from src.ui.windows.battle_integration_manager import get_battle_integration_manager, BattleContext
from src.ui.character_status_bar import CharacterStatusBar, create_character_status_bar
from src.ui.small_map_ui_pygame import SmallMapUI
from src.character.party import Party
from src.core.config_manager import config_manager
from src.utils.logger import logger


class DungeonMenuType(Enum):
    """ダンジョンメニュータイプ"""
    MAIN = "main"           # メインメニュー
    INVENTORY = "inventory" # インベントリ
    MAGIC = "magic"         # 魔法
    EQUIPMENT = "equipment" # 装備
    CAMP = "camp"           # キャンプ
    STATUS = "status"       # ステータス
    STATUS_EFFECTS = "status_effects" # 状態効果


class DungeonUIManagerPygame:
    """ダンジョンUI管理クラス（WindowSystem統合版）"""
    
    def __init__(self, screen=None):
        logger.info(config_manager.get_text("dungeon_ui.manager_init_start"))
        
        # Pygame初期化
        if not pygame.get_init():
            pygame.init()
        
        # 画面設定
        self.screen = screen
        if not self.screen:
            # デフォルト画面サイズを取得
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((1024, 768))
        
        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()
        
        # WindowSystem統合
        self.window_manager = WindowManager.get_instance()
        self.battle_ui_window: Optional[BattleUIWindow] = None
        
        # UI状態
        self.is_menu_open = False
        self.current_menu_type = None
        self.current_party = None
        
        # キャラクターステータスバー
        self.character_status_bar: Optional[CharacterStatusBar] = None
        self._initialize_character_status_bar()
        
        # 小地図UI
        self.small_map_ui: Optional[SmallMapUI] = None
        self.dungeon_state = None
        
        # コールバック
        self.callbacks: Dict[str, Callable] = {}
        
        # フォント初期化（安定性を重視）
        try:
            # フォントマネージャーから取得を試行
            from src.ui.font_manager_pygame import font_manager
            self.font_small = font_manager.get_japanese_font(18)
            self.font_medium = font_manager.get_japanese_font(24)
            self.font_large = font_manager.get_japanese_font(36)
            
            # フォールバック
            if not self.font_small:
                self.font_small = font_manager.get_default_font()
            if not self.font_medium:
                self.font_medium = font_manager.get_default_font()
            if not self.font_large:
                self.font_large = font_manager.get_default_font()
        except Exception as e:
            logger.warning(config_manager.get_text("dungeon_ui.font_manager_error").format(error=e))
            # フォールバック：システムデフォルト
            try:
                self.font_small = pygame.font.Font(None, 18)
                self.font_medium = pygame.font.Font(None, 24)
                self.font_large = pygame.font.Font(None, 36)
            except:
                # 最終フォールバック
                self.font_small = pygame.font.SysFont(None, 18)
                self.font_medium = pygame.font.SysFont(None, 24)
                self.font_large = pygame.font.SysFont(None, 36)
        
        # 色設定
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
            'menu_bg': (40, 40, 60, 200),  # 半透明背景
        }
        
        # メニュー設定
        self.menu_width = 300
        self.menu_height = 400
        self.menu_x = (self.screen_width - self.menu_width) // 2
        self.menu_y = (self.screen_height - self.menu_height) // 2
        
        # メニュー項目（英語版で確実に表示）
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
        
        self.selected_menu_index = 0
        
        logger.info(config_manager.get_text("dungeon_ui.manager_init_complete"))
    
    def set_party(self, party: Party):
        """パーティを設定"""
        self.current_party = party
        
        # キャラクターステータスバーにパーティを設定
        if self.character_status_bar:
            self.character_status_bar.set_party(party)
        
        # BattleUIWindowにもパーティを設定
        if self.battle_ui_window:
            # BattleUIWindowの設定更新（実際の実装では適切なメソッドを使用）
            pass
        
        logger.info(config_manager.get_text("dungeon_ui.party_set").format(party_name=party.name))
    
    def set_callback(self, action: str, callback: Callable):
        """コールバックを設定"""
        self.callbacks[action] = callback
        logger.debug(config_manager.get_text("dungeon_ui.callback_set").format(action=action))
    
    def set_dungeon_state(self, dungeon_state):
        """ダンジョン状態を設定"""
        self.dungeon_state = dungeon_state
        logger.debug(f"Setting dungeon state: player at ({dungeon_state.player_position.x}, {dungeon_state.player_position.y})" if dungeon_state.player_position else "No player position")
        
        # 小地図UIを初期化/更新
        if dungeon_state:
            if self.small_map_ui is None:
                logger.info("Creating new SmallMapUI instance")
                # フォントマネージャーのモック（必要に応じて実装）
                font_manager = type('MockFontManager', (), {})()
                self.small_map_ui = SmallMapUI(self.screen, font_manager, dungeon_state)
                logger.info(f"SmallMapUI created - visibility: {self.small_map_ui.is_visible}")
            else:
                # 既存の小地図UIを更新
                self.small_map_ui.update_dungeon_state(dungeon_state)
        
        logger.debug(config_manager.get_text("dungeon_ui.dungeon_state_set"))
    
    def _initialize_character_status_bar(self):
        """キャラクターステータスバーを初期化"""
        try:
            # キャラクターステータスバーを作成
            self.character_status_bar = create_character_status_bar(self.screen_width, self.screen_height)
            
            # 安定した描画のため強制的に表示状態にする
            if self.character_status_bar:
                self.character_status_bar.show()
            
            # 現在のパーティが設定されている場合は設定
            if self.current_party:
                self.character_status_bar.set_party(self.current_party)
            
            logger.info(config_manager.get_text("dungeon_ui.character_status_bar_init"))
            
        except Exception as e:
            logger.error(config_manager.get_text("dungeon_ui.character_status_bar_error").format(error=e))
            self.character_status_bar = None
    
    def show_battle_ui(self, battle_manager, enemies):
        """戦闘UIを表示（WindowSystem統合版）"""
        try:
            # BattleIntegrationManagerを使用した統合戦闘
            battle_integration = get_battle_integration_manager()
            
            # 戦闘コンテキストを作成
            battle_context = BattleContext(
                dungeon_level=getattr(self, 'current_level', 1),
                dungeon_x=getattr(self, 'current_x', 0),
                dungeon_y=getattr(self, 'current_y', 0),
                encounter_type="random_encounter",
                return_callback=self._on_battle_return
            )
            
            # 統合マネージャーで戦闘開始
            success = battle_integration.start_battle(
                party=self.current_party,
                enemies=enemies,
                battle_context=battle_context
            )
            
            if success:
                logger.info("戦闘UIを表示（統合版）")
                return True
            else:
                # フォールバック - 直接BattleUIWindowを使用
                return self._show_battle_ui_fallback(battle_manager, enemies)
                
        except Exception as e:
            logger.error(f"戦闘UI表示エラー: {e}")
            # フォールバック - 直接BattleUIWindowを使用
            return self._show_battle_ui_fallback(battle_manager, enemies)
    
    def _show_battle_ui_fallback(self, battle_manager, enemies):
        """戦闘UI表示のフォールバック実装"""
        try:
            battle_config = self._create_battle_ui_config(battle_manager, enemies)
            
            self.battle_ui_window = BattleUIWindow(
                window_id="dungeon_battle_ui",
                battle_config=battle_config
            )
            
            self.battle_ui_window.create()
            
            logger.info("戦闘UIを表示（フォールバック版）")
            return True
        except Exception as e:
            logger.error(f"戦闘UIフォールバック表示エラー: {e}")
            return False
    
    def _on_battle_return(self, victory: bool, battle_result: dict):
        """戦闘終了後のコールバック"""
        try:
            if victory:
                logger.info("戦闘に勝利しました")
                # 経験値・アイテム獲得処理
                self._handle_battle_victory(battle_result)
            else:
                logger.info("戦闘が終了しました（敗北・逃走）")
                # 敗北・逃走処理
                self._handle_battle_defeat(battle_result)
            
            # ダンジョンUIに復帰
            self._return_to_dungeon_ui()
            
        except Exception as e:
            logger.error(f"戦闘復帰処理エラー: {e}")
    
    def _handle_battle_victory(self, battle_result: dict):
        """戦闘勝利処理"""
        try:
            # 経験値獲得
            exp_gained = battle_result.get('experience_gained', 0)
            if exp_gained > 0:
                logger.info(f"経験値 {exp_gained} を獲得")
                # パーティに経験値を付与（実装に応じて調整）
            
            # アイテム獲得
            items_gained = battle_result.get('items_gained', [])
            if items_gained:
                logger.info(f"アイテム {len(items_gained)} 個を獲得")
                # インベントリに追加（実装に応じて調整）
            
            # ゴールド獲得
            gold_gained = battle_result.get('gold_gained', 0)
            if gold_gained > 0:
                logger.info(f"ゴールド {gold_gained} を獲得")
                # パーティのゴールドに追加（実装に応じて調整）
                
        except Exception as e:
            logger.error(f"戦闘勝利処理エラー: {e}")
    
    def _handle_battle_defeat(self, battle_result: dict):
        """戦闘敗北・逃走処理"""
        try:
            # 敗北・逃走時の処理（実装に応じて調整）
            logger.info("戦闘敗北・逃走処理")
            
        except Exception as e:
            logger.error(f"戦闘敗北処理エラー: {e}")
    
    def _return_to_dungeon_ui(self):
        """ダンジョンUIに復帰"""
        try:
            # ダンジョン画面の状態を復元
            self.is_menu_open = False
            self.current_menu_type = DungeonMenuType.NONE
            
            logger.info("ダンジョンUIに復帰しました")
            
        except Exception as e:
            logger.error(f"ダンジョンUI復帰エラー: {e}")
    
    def _create_battle_ui_config(self, battle_manager=None, enemies=None):
        """BattleUIWindow用設定を作成"""
        return {
            'battle_manager': battle_manager,
            'party': self.current_party,
            'enemies': enemies or [],
            'show_battle_log': True,
            'show_status_effects': True,
            'enable_keyboard_shortcuts': True,
            'enable_animations': True,
            'auto_advance_log': False,
            'log_max_entries': 100
        }
    
    def show_action_menu(self):
        """アクションメニューを表示（BattleUIWindowに委譲）"""
        if self.battle_ui_window:
            try:
                # BattleUIWindowにアクションメニュー表示を委譲
                self.battle_ui_window._show_action_menu()
                return True
            except Exception as e:
                logger.error(f"アクションメニュー表示エラー: {e}")
                return False
        return False
    
    def toggle_main_menu(self):
        """メインメニューの表示/非表示を切り替え"""
        if self.is_menu_open:
            self.close_menu()
        else:
            self.show_main_menu()
    
    def show_main_menu(self):
        """メインメニューを表示"""
        self.is_menu_open = True
        self.current_menu_type = DungeonMenuType.MAIN
        self.selected_menu_index = 0
        logger.info(config_manager.get_text("dungeon_ui.main_menu_shown"))
    
    def close_menu(self):
        """メニューを閉じる"""
        self.is_menu_open = False
        self.current_menu_type = None
        logger.info(config_manager.get_text("dungeon_ui.menu_closed"))
    
    def handle_input(self, event) -> bool:
        """入力処理（WindowSystem版）"""
        # BattleUIWindowが存在する場合、そちらに委譲
        if self.battle_ui_window:
            try:
                return self.battle_ui_window.handle_event(event)
            except Exception as e:
                logger.error(f"BattleUIWindow入力処理エラー: {e}")
        
        # 小地図のイベント処理（メニューが開いていなくても処理）
        if self.small_map_ui:
            if self.small_map_ui.handle_event(event):
                return True
        
        if not self.is_menu_open:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_menu_index = (self.selected_menu_index - 1) % len(self.menu_items)
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_menu_index = (self.selected_menu_index + 1) % len(self.menu_items)
                return True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._execute_menu_action()
                return True
            elif event.key == pygame.K_ESCAPE:
                self.close_menu()
                return True
        
        return False
    
    def _execute_menu_action(self):
        """メニューアクションを実行"""
        if 0 <= self.selected_menu_index < len(self.menu_items):
            action = self.menu_items[self.selected_menu_index]["action"]
            
            if action == "close":
                self.close_menu()
            elif action in self.callbacks:
                self.close_menu()
                self.callbacks[action]()
            else:
                logger.warning(f"未実装のメニューアクション: {action}")
                # 基本的なアクションは閉じるだけ
                self.close_menu()
    
    def render(self):
        """UIを描画"""
        if not self.is_menu_open:
            return
        
        # 半透明背景を描画
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        # メニュー背景を描画
        menu_rect = pygame.Rect(self.menu_x, self.menu_y, self.menu_width, self.menu_height)
        pygame.draw.rect(self.screen, self.colors['dark_gray'], menu_rect)
        pygame.draw.rect(self.screen, self.colors['white'], menu_rect, 2)
        
        # タイトルを描画（英語版で確実に表示）
        title_surface = self.font_large.render("Dungeon Menu", True, self.colors['white'])
        title_rect = title_surface.get_rect(centerx=self.menu_x + self.menu_width // 2, y=self.menu_y + 20)
        self.screen.blit(title_surface, title_rect)
        
        # メニュー項目を描画
        item_height = 35
        start_y = self.menu_y + 80
        
        for i, item in enumerate(self.menu_items):
            y = start_y + i * item_height
            
            # 選択中の項目をハイライト
            if i == self.selected_menu_index:
                highlight_rect = pygame.Rect(self.menu_x + 10, y - 5, self.menu_width - 20, item_height)
                pygame.draw.rect(self.screen, self.colors['blue'], highlight_rect)
            
            # テキストを描画
            text_color = self.colors['white'] if i == self.selected_menu_index else self.colors['light_gray']
            text_surface = self.font_medium.render(item["text"], True, text_color)
            self.screen.blit(text_surface, (self.menu_x + 20, y))
        
        # 操作説明を描画（英語版で確実に表示）
        help_y = self.menu_y + self.menu_height - 60
        help_texts = [
            "Up/Down: Select",
            "Enter/Space: Confirm",
            "ESC: Close"
        ]
        
        for i, help_text in enumerate(help_texts):
            help_surface = self.font_small.render(help_text, True, self.colors['gray'])
            self.screen.blit(help_surface, (self.menu_x + 20, help_y + i * 20))
    
    def render_overlay(self):
        """オーバーレイUI（ステータスバー等）を描画"""
        # 小地図を最初に描画（背景層）
        if self.small_map_ui:
            try:
                if self.small_map_ui.is_visible:
                    self.small_map_ui.render()
                    logger.debug("小地図を描画しました")
                else:
                    logger.debug("小地図は非表示状態です")
            except Exception as e:
                logger.warning(f"小地図UI描画エラー: {e}")
        
        # キャラクターステータスバーを最後に描画（最前面層）
        if self.character_status_bar:
            try:
                # ステータスバー自体のフォントを使用（安定性向上）
                self.character_status_bar.render(self.screen, None)
            except Exception as e:
                logger.warning(f"ダンジョン用キャラクターステータスバー描画エラー: {e}")
    
    def update(self):
        """UI更新"""
        # 現在は特に更新処理なし
        pass
    
    def show_status_bar(self):
        """ステータスバー表示（簡易版）"""
        # 現在は何もしない（将来的にパーティHPなどを表示）
        pass
    
    def update_location(self, location_info: str):  # noqa: ARG002
        """位置情報更新（簡易版）"""
        # 現在は何もしない（位置情報は別途描画）
        pass
    
    def update_party_status(self):
        """パーティステータス更新（簡易版）"""
        # 現在は何もしない（将来的にHP/MPバーなどを表示）
        pass
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            self.close_menu()
            
            # BattleUIWindowのクリーンアップ
            if self.battle_ui_window:
                if hasattr(self.battle_ui_window, 'cleanup_ui'):
                    self.battle_ui_window.cleanup_ui()
                self.battle_ui_window = None
            
            logger.info("DungeonUIManagerPygame リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"クリーンアップ中にエラー: {e}")


# グローバルインスタンス
dungeon_ui_manager_pygame = None

def create_pygame_dungeon_ui(screen=None) -> DungeonUIManagerPygame:
    """Pygame版ダンジョンUI作成"""
    global dungeon_ui_manager_pygame
    if not dungeon_ui_manager_pygame:
        dungeon_ui_manager_pygame = DungeonUIManagerPygame(screen)
    return dungeon_ui_manager_pygame