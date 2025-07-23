"""ダンジョンメニューウィンドウ - WindowSystem用ダンジョン内メニューUI"""

from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import pygame
import pygame_gui

from src.ui.window_system.window import Window
from src.ui.window_system.window_manager import WindowManager
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
    STATUS_EFFECTS = "status_effects"  # 状態効果


class DungeonMenuWindow(Window):
    """ダンジョンメニューウィンドウクラス - WindowSystem準拠"""
    
    def __init__(self, window_id: str, parent: Optional[Window] = None, modal: bool = False):
        """
        ダンジョンメニューウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            parent: 親ウィンドウ
            modal: モーダル表示
        """
        super().__init__(window_id, parent, modal)
        
        # データ管理
        self.current_party: Optional[Party] = None
        self.dungeon_state: Any = None  # ダンジョン状態
        
        # メニュー状態
        self.is_menu_open = False
        self.current_menu_type = DungeonMenuType.MAIN
        self.selected_menu_index = 0
        
        # UI要素
        self.ui_elements: Dict[str, pygame_gui.UIElement] = {}
        self.content_panel: Optional[pygame_gui.elements.UIPanel] = None
        
        # コールバック
        self.callbacks: Dict[str, Callable] = {}
        
        # メニュー設定
        self.menu_width = 300
        self.menu_height = 400
        
        # メニュー項目
        self.menu_items = [
            {"text": "インベントリ", "action": "inventory"},
            {"text": "魔法", "action": "magic"},
            {"text": "装備", "action": "equipment"},
            {"text": "キャンプ", "action": "camp"},
            {"text": "ステータス", "action": "status"},
            {"text": "状態効果", "action": "status_effects"},
            {"text": "地上に戻る", "action": "return_overworld"},
            {"text": "閉じる", "action": "close"}
        ]
        
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
            'menu_bg': (40, 40, 60, 200),
        }
        
        logger.info(f"DungeonMenuWindow作成: {window_id}")

    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            window_manager = WindowManager.get_instance()
            self.ui_manager = window_manager.ui_manager
            self.surface = window_manager.screen
        
        if not self.surface:
            logger.error("画面サーフェスが設定されていません")
            return
        
        # 画面サイズ取得
        self.screen_width = self.surface.get_width()
        self.screen_height = self.surface.get_height()
        
        # メニュー位置計算
        self.menu_x = (self.screen_width - self.menu_width) // 2
        self.menu_y = (self.screen_height - self.menu_height) // 2
        
        # ウィンドウサイズ設定（全画面オーバーレイ）
        self.rect = pygame.Rect(0, 0, self.screen_width, self.screen_height)
        
        # 透明なメインパネル作成
        self.content_panel = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager,
            element_id="dungeon_menu_window_panel"
        )
        self.content_panel.background_colour = pygame.Color(0, 0, 0, 0)  # 透明
        self.ui_elements["main_panel"] = self.content_panel
        
        # フォント初期化
        self._initialize_fonts()
        
        logger.debug(f"DungeonMenuWindow UI要素を作成: {self.window_id}")

    def _initialize_fonts(self) -> None:
        """フォントを初期化"""
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
            logger.warning(f"フォントマネージャーエラー: {e}")
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

    def set_party(self, party: Party) -> None:
        """パーティを設定"""
        self.current_party = party
        logger.debug(f"パーティを設定: {party.name}")

    def set_dungeon_state(self, dungeon_state: Any) -> None:
        """ダンジョン状態を設定"""
        self.dungeon_state = dungeon_state
        logger.debug(f"ダンジョン状態を設定: プレイヤー位置 ({dungeon_state.player_position.x}, {dungeon_state.player_position.y})" if dungeon_state and dungeon_state.player_position else "ダンジョン状態設定（位置情報なし）")

    def set_callback(self, action: str, callback: Callable) -> None:
        """コールバックを設定"""
        self.callbacks[action] = callback
        logger.debug(f"コールバック設定: {action}")

    def toggle_main_menu(self) -> None:
        """メインメニューの表示/非表示を切り替え"""
        if self.is_menu_open:
            self.close_menu()
        else:
            self.show_main_menu()

    def show_main_menu(self) -> None:
        """メインメニューを表示"""
        self.is_menu_open = True
        self.current_menu_type = DungeonMenuType.MAIN
        self.selected_menu_index = 0
        
        if self.state.value == "shown":
            self.create_main_menu()
        
        logger.info("ダンジョンメインメニューを表示")

    def close_menu(self) -> None:
        """メニューを閉じる"""
        self.is_menu_open = False
        self.current_menu_type = None
        
        # メニュー関連のUI要素を削除
        self._clear_menu_elements()
        
        logger.info("ダンジョンメニューを閉じる")

    def create_main_menu(self) -> None:
        """メインメニューのUI要素を作成"""
        if not self.content_panel:
            return
        
        # メニューパネル
        menu_rect = pygame.Rect(self.menu_x, self.menu_y, self.menu_width, self.menu_height)
        menu_panel = pygame_gui.elements.UIPanel(
            relative_rect=menu_rect,
            manager=self.ui_manager,
            container=self.content_panel,
            element_id="dungeon_menu_panel"
        )
        self.ui_elements["menu_panel"] = menu_panel
        
        # タイトル
        title_rect = pygame.Rect(20, 20, self.menu_width - 40, 40)
        title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="ダンジョンメニュー",
            manager=self.ui_manager,
            container=menu_panel
        )
        self.ui_elements["title"] = title_label
        
        # メニュー項目
        item_height = 35
        start_y = 80
        
        for i, item in enumerate(self.menu_items):
            y = start_y + i * item_height
            
            # ボタン
            button_rect = pygame.Rect(20, y, self.menu_width - 40, item_height - 5)
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=item["text"],
                manager=self.ui_manager,
                container=menu_panel,
                object_id=f"menu_item_{item['action']}"
            )
            
            # 選択状態の視覚的表現
            if i == self.selected_menu_index:
                button.background_colour = pygame.Color(*self.colors['blue'])
            
            self.ui_elements[f"menu_item_{i}"] = button
        
        # 操作説明
        help_y = self.menu_height - 80
        help_texts = [
            "↑↓: 選択",
            "Enter/Space: 決定",
            "ESC: 閉じる, P: メニュー表示"
        ]
        
        for i, help_text in enumerate(help_texts):
            help_rect = pygame.Rect(20, help_y + i * 20, self.menu_width - 40, 20)
            help_label = pygame_gui.elements.UILabel(
                relative_rect=help_rect,
                text=help_text,
                manager=self.ui_manager,
                container=menu_panel
            )
            self.ui_elements[f"help_{i}"] = help_label

    def handle_input(self, event: pygame.event.Event) -> bool:
        """入力処理"""
        # メニューが開いていない場合は処理しない
        if not self.is_menu_open:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_menu_index = (self.selected_menu_index - 1) % len(self.menu_items)
                self._update_menu_selection()
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_menu_index = (self.selected_menu_index + 1) % len(self.menu_items)
                self._update_menu_selection()
                return True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.execute_menu_action()
                return True
            elif event.key == pygame.K_ESCAPE:
                self.close_menu()
                # ウィンドウをWindowManagerから削除してダンジョンに戻る
                if hasattr(self, 'window_manager') and self.window_manager:
                    self.window_manager.hide_window(self, remove_from_stack=True)
                
                # DungeonMenuManagerにも通知してcurrent_windowをクリア
                try:
                    from src.ui.windows.dungeon_menu_manager import dungeon_menu_manager
                    dungeon_menu_manager.close_dungeon_menu()
                except Exception as e:
                    logger.warning(f"DungeonMenuManagerクローズ通知エラー: {e}")
                
                return True
        
        return False

    def execute_menu_action(self) -> None:
        """メニューアクションを実行"""
        if 0 <= self.selected_menu_index < len(self.menu_items):
            action = self.menu_items[self.selected_menu_index]["action"]
            
            if action == "close":
                self.close_menu()
            elif action == "return_overworld":
                # 地上に戻る処理
                self.close_menu()
                if "return_overworld" in self.callbacks:
                    self.callbacks["return_overworld"]()
                else:
                    logger.info("地上に戻る機能は未実装")
            elif action in self.callbacks:
                self.close_menu()
                self.callbacks[action]()
            elif action == "camp":
                # キャンプ機能 - 基本的な休憩と状態確認
                self._show_camp_menu()
            elif action in ["inventory", "equipment", "magic", "status", "status_effects"]:
                # 基本サブメニュー - 未実装の場合は通知
                logger.info(f"{action}メニューは現在未実装です（将来的に実装予定）")
                # メニューは閉じずに表示継続
            else:
                logger.warning(f"未実装のメニューアクション: {action}")
                # 基本的なアクションは閉じるだけ
                self.close_menu()

    def _update_menu_selection(self) -> None:
        """メニュー選択状態を更新"""
        # 既存のボタンの色をリセット
        for i in range(len(self.menu_items)):
            button_key = f"menu_item_{i}"
            if button_key in self.ui_elements:
                button = self.ui_elements[button_key]
                if i == self.selected_menu_index:
                    button.background_colour = pygame.Color(*self.colors['blue'])
                else:
                    button.background_colour = pygame.Color(*self.colors['dark_gray'])

    def render(self) -> None:
        """UIを描画（pygame直接描画）"""
        if not self.is_menu_open or not hasattr(self, 'surface'):
            return
        
        # 半透明オーバーレイ
        self.render_menu_background()
        
        # メニュー背景
        self.render_menu_frame()
        
        # メニュー項目
        self.render_menu_items()
        
        # 操作説明
        self.render_help_text()

    def render_menu_background(self) -> None:
        """メニュー背景を描画"""
        # 半透明背景
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.surface.blit(overlay, (0, 0))

    def render_menu_frame(self) -> None:
        """メニューフレームを描画"""
        # メニュー背景
        menu_rect = pygame.Rect(self.menu_x, self.menu_y, self.menu_width, self.menu_height)
        pygame.draw.rect(self.surface, self.colors['dark_gray'], menu_rect)
        pygame.draw.rect(self.surface, self.colors['white'], menu_rect, 2)
        
        # タイトル
        title_surface = self.font_large.render("ダンジョンメニュー", True, self.colors['white'])
        title_rect = title_surface.get_rect(centerx=self.menu_x + self.menu_width // 2, y=self.menu_y + 20)
        self.surface.blit(title_surface, title_rect)

    def render_menu_items(self) -> None:
        """メニュー項目を描画"""
        item_height = 35
        start_y = self.menu_y + 80
        
        for i, item in enumerate(self.menu_items):
            y = start_y + i * item_height
            
            # 選択中の項目をハイライト
            if i == self.selected_menu_index:
                highlight_rect = pygame.Rect(self.menu_x + 10, y - 5, self.menu_width - 20, item_height)
                pygame.draw.rect(self.surface, self.colors['blue'], highlight_rect)
            
            # テキスト
            text_color = self.colors['white'] if i == self.selected_menu_index else self.colors['light_gray']
            text_surface = self.font_medium.render(item["text"], True, text_color)
            self.surface.blit(text_surface, (self.menu_x + 20, y))

    def render_help_text(self) -> None:
        """操作説明を描画"""
        help_y = self.menu_y + self.menu_height - 80
        help_texts = [
            "↑↓: 選択",
            "Enter/Space: 決定",
            "ESC: 閉じる, P: メニュー表示"
        ]
        
        for i, help_text in enumerate(help_texts):
            help_surface = self.font_small.render(help_text, True, self.colors['gray'])
            self.surface.blit(help_surface, (self.menu_x + 20, help_y + i * 20))

    def render_overlay(self) -> None:
        """オーバーレイUI（常時表示要素）を描画"""
        # キャラクターステータスバー
        self.render_character_status_bar()
        
        # 小地図
        self.render_small_map()
        
        # 位置情報
        self.render_location_info()

    def render_character_status_bar(self) -> None:
        """キャラクターステータスバーを描画"""
        if not self.current_party:
            return
        
        try:
            # キャラクターステータスバーの描画
            # 実際の実装では、character_status_barを使用
            status_y = 10
            for i, character in enumerate(self.current_party.get_all_characters()):
                status_text = f"{character.name}: HP {character.current_hp}/{character.max_hp} MP {character.current_mp}/{character.max_mp}"
                status_surface = self.font_small.render(status_text, True, self.colors['white'])
                self.surface.blit(status_surface, (10, status_y + i * 25))
                
        except Exception as e:
            logger.warning(f"キャラクターステータスバー描画エラー: {e}")

    def render_small_map(self) -> None:
        """小地図を描画"""
        if not self.dungeon_state:
            return
        
        try:
            # 小地図の簡易実装
            # 実際の実装では、small_map_uiを使用
            map_x = self.screen_width - 150
            map_y = 10
            map_size = 100
            
            # 地図背景
            map_rect = pygame.Rect(map_x, map_y, map_size, map_size)
            pygame.draw.rect(self.surface, self.colors['dark_gray'], map_rect)
            pygame.draw.rect(self.surface, self.colors['white'], map_rect, 1)
            
            # プレイヤー位置
            if hasattr(self.dungeon_state, 'player_position') and self.dungeon_state.player_position:
                player_x = map_x + map_size // 2
                player_y = map_y + map_size // 2
                pygame.draw.circle(self.surface, self.colors['red'], (player_x, player_y), 3)
                
        except Exception as e:
            logger.warning(f"小地図描画エラー: {e}")

    def render_location_info(self) -> None:
        """位置情報を描画"""
        if not self.dungeon_state:
            return
        
        try:
            location_info = self.get_location_info()
            info_surface = self.font_small.render(location_info, True, self.colors['white'])
            self.surface.blit(info_surface, (10, self.screen_height - 30))
            
        except Exception as e:
            logger.warning(f"位置情報描画エラー: {e}")

    def get_location_info(self) -> str:
        """位置情報を取得"""
        if not self.dungeon_state:
            return "位置情報なし"
        
        try:
            dungeon_name = getattr(self.dungeon_state, 'dungeon_name', 'ダンジョン')
            current_floor = getattr(self.dungeon_state, 'current_floor', 1)
            
            position_text = ""
            if hasattr(self.dungeon_state, 'player_position') and self.dungeon_state.player_position:
                x = self.dungeon_state.player_position.x
                y = self.dungeon_state.player_position.y
                position_text = f" ({x}, {y})"
            
            return f"{dungeon_name} {current_floor}F{position_text}"
            
        except Exception as e:
            logger.warning(f"位置情報取得エラー: {e}")
            return "位置情報エラー"

    def _show_camp_menu(self) -> None:
        """キャンプメニューを表示"""
        if not self.current_party:
            logger.warning("パーティが設定されていないため、キャンプできません")
            return
        
        try:
            # 基本的な休憩処理
            logger.info("ダンジョン内でキャンプを開始...")
            
            # パーティメンバーの状態確認
            party_status = []
            for character in self.current_party.get_all_characters():
                hp_ratio = character.current_hp / max(character.max_hp, 1)
                mp_ratio = character.current_mp / max(character.max_mp, 1)
                status = "良好" if hp_ratio > 0.7 and mp_ratio > 0.7 else "要注意"
                party_status.append(f"{character.name}: {status} (HP:{character.current_hp}/{character.max_hp}, MP:{character.current_mp}/{character.max_mp})")
            
            logger.info("キャンプ中のパーティ状態:")
            for status in party_status:
                logger.info(f"  {status}")
            
            # 簡易的な休憩効果（現在は状態確認のみ）
            logger.info("キャンプ完了。（実際の回復処理は未実装）")
            
        except Exception as e:
            logger.error(f"キャンプ処理エラー: {e}")

    def get_party_status_summary(self) -> str:
        """パーティステータス概要を取得"""
        if not self.current_party:
            return ""
        
        summary_parts = []
        for character in self.current_party.get_all_characters():
            hp_info = f"{character.current_hp}/{character.max_hp}"
            mp_info = f"{character.current_mp}/{character.max_mp}"
            summary_parts.append(f"{character.name}: HP {hp_info} MP {mp_info}")
        
        return " | ".join(summary_parts)

    def is_small_map_available(self) -> bool:
        """小地図が利用可能かどうか"""
        return self.dungeon_state is not None

    def get_player_position(self) -> Optional[Tuple[int, int]]:
        """プレイヤー位置を取得"""
        if self.dungeon_state and hasattr(self.dungeon_state, 'player_position') and self.dungeon_state.player_position:
            return (self.dungeon_state.player_position.x, self.dungeon_state.player_position.y)
        return None

    def _clear_menu_elements(self) -> None:
        """メニュー関連のUI要素をクリア"""
        elements_to_remove = []
        for element_id in self.ui_elements:
            if element_id != "main_panel" and element_id.startswith(("menu_", "help_", "title")):
                elements_to_remove.append(element_id)
        
        for element_id in elements_to_remove:
            element = self.ui_elements[element_id]
            element.kill()
            del self.ui_elements[element_id]

    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        # キーボード入力処理
        return self.handle_input(event)

    def destroy(self) -> None:
        """ウィンドウを破棄"""
        # メニューを閉じる
        self.close_menu()
        
        # UI要素をクリア
        for element_id, element in list(self.ui_elements.items()):
            element.kill()
        self.ui_elements.clear()
        
        if self.content_panel:
            self.content_panel.kill()
            self.content_panel = None
        
        # データをクリア
        self.current_party = None
        self.dungeon_state = None
        self.callbacks.clear()
        
        super().destroy()
        logger.debug(f"DungeonMenuWindowを破棄: {self.window_id}")

    def on_show(self) -> None:
        """表示時の処理"""
        logger.debug(f"DungeonMenuWindowを表示: {self.window_id}")

    def on_hide(self) -> None:
        """非表示時の処理"""
        # メニューが開いている場合は閉じる
        if self.is_menu_open:
            self.close_menu()
        logger.debug(f"DungeonMenuWindowを非表示: {self.window_id}")

    def on_update(self, time_delta: float) -> None:
        """更新処理"""
        # 現在は特に更新処理なし
        pass