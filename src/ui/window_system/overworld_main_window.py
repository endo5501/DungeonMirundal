"""
地上部メインウィンドウ

OverworldManagerの9箇所のレガシーメニューを統合し、地上部の全機能を提供する核心Window
"""

from typing import Dict, List, Optional, Any, Callable
import pygame
import pygame_gui
from enum import Enum

from .window import Window, WindowState
from src.character.party import Party
from src.core.config_manager import config_manager
from src.core.save_manager import save_manager
from src.utils.logger import logger


class OverworldMenuType(Enum):
    """地上部メニューの種類"""
    MAIN = "main"                    # メインメニュー（施設・ダンジョン入口）
    SETTINGS = "settings"            # 設定メニュー（ESCキー）
    PARTY_STATUS = "party_status"    # パーティ状況表示
    SAVE_LOAD = "save_load"          # セーブ・ロード
    GAME_SETTINGS = "game_settings"  # ゲーム設定


class OverworldMainWindow(Window):
    """
    地上部メインウィンドウ
    
    OverworldManagerの以下9箇所のレガシーメニューを統合:
    1. main_menu - 施設アクセス（guild, inn, shop, temple, magic_guild）
    2. location_menu - ダンジョン入口アクセス
    3. settings_menu - パーティ状況、セーブ・ロード、設定画面
    4. party_status_menu - パーティ詳細表示
    5. save_slot_menu - セーブスロット選択
    6. load_game_menu - ロードゲーム選択
    7. party_overview_dialog - パーティ全体情報
    8. character_details_dialog - キャラクター詳細
    9. confirmation_dialog - 確認ダイアログ
    """
    
    def __init__(self, window_id: str, config: Dict[str, Any], parent: Optional[Window] = None, **kwargs):
        """
        地上部メインウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            config: メニュー設定辞書
                - menu_type: メニューの種類
                - title: タイトル  
                - menu_items: メニュー項目リスト
                - party: 現在のパーティ
                - show_party_info: パーティ情報表示フラグ
                - show_gold: ゴールド表示フラグ
            parent: 親ウィンドウ（オプション）
            **kwargs: その他のウィンドウ引数
        """
        super().__init__(window_id, modal=False, parent=parent)
        
        self.config = config
        self.current_menu_type = OverworldMenuType(config.get('menu_type', 'main'))
        self.party = config.get('party')
        self.show_party_info = config.get('show_party_info', False)
        self.show_gold = config.get('show_gold', False)
        
        # UI要素
        self.title_label: Optional[pygame_gui.elements.UILabel] = None
        self.menu_items: List[pygame_gui.elements.UIButton] = []
        self.party_info_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.party_labels: List[pygame_gui.elements.UILabel] = []
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        
        # 操作状態
        self.selected_index = 0
        self.menu_stack: List[Dict[str, Any]] = []  # メニュー階層管理
        
        # メッセージハンドラー
        self.message_handler: Optional[Callable[[str, Dict[str, Any]], bool]] = None
        
        logger.info(f"OverworldMainWindow作成: {window_id}, menu_type: {self.current_menu_type.value}")
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.surface:
            # デフォルトサーフェスサイズを設定
            screen_size = pygame.display.get_surface().get_size()
            self.surface = pygame.Surface(screen_size)
            self.rect = self.surface.get_rect()
        
        # WindowManagerのUIManagerを取得（フォント・テーマが設定済み）
        from .window_manager import WindowManager
        window_manager = WindowManager.get_instance()
        self.ui_manager = window_manager.ui_manager
        
        logger.info(f"OverworldMainWindow UIManager初期化: window_manager.ui_manager={self.ui_manager}")
        
        if not self.ui_manager:
            # フォールバック：新しいUIManagerを作成
            self.ui_manager = pygame_gui.UIManager(self.surface.get_size())
            logger.warning(f"統一UIManagerがないため独自作成: size={self.surface.get_size()}")
        else:
            logger.info(f"WindowManagerの統一UIManagerを使用: {type(self.ui_manager)}")
        
        # メニュータイプに応じてUI作成
        if self.current_menu_type == OverworldMenuType.MAIN:
            self._create_main_menu()
        elif self.current_menu_type == OverworldMenuType.SETTINGS:
            self._create_settings_menu()
        elif self.current_menu_type == OverworldMenuType.PARTY_STATUS:
            self._create_party_status_menu()
        elif self.current_menu_type == OverworldMenuType.SAVE_LOAD:
            self._create_save_load_menu()
        elif self.current_menu_type == OverworldMenuType.GAME_SETTINGS:
            self._create_game_settings_menu()
        
        logger.debug(f"OverworldMainWindow UI作成完了: {self.window_id}")
    
    def _create_main_menu(self) -> None:
        """メインメニューUI作成"""
        title = self.config.get('title', config_manager.get_text("overworld.surface_map"))
        menu_items = self.config.get('menu_items', [])
        
        # タイトル
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(0, 20, 800, 50),
            text=title,
            manager=self.ui_manager
        )
        
        # メニュー項目
        y_offset = 100
        for i, item in enumerate(menu_items):
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(50, y_offset + i * 60, 300, 50),
                text=item.get('label', ''),
                manager=self.ui_manager
            )
            button.menu_item_data = item  # カスタム属性でデータを保持
            self.menu_items.append(button)
        
        # パーティ情報パネル
        if self.show_party_info and self.party:
            self._create_party_info_panel()
        
        # ゴールド表示
        if self.show_gold and self.party:
            self._create_gold_display()
        
        # デバッグ: 作成されたUI要素を確認
        if self.ui_manager and hasattr(self.ui_manager, 'get_root_container'):
            element_count = len(self.ui_manager.get_root_container().elements)
            logger.info(f"OverworldMainWindow UIManager内のUI要素総数: {element_count}")
            
            # 各ボタンの状態を確認
            for i, button in enumerate(self.menu_items):
                if button:
                    logger.info(f"地上メニューボタン{i}: visible={button.visible}, alive={button.alive}")
    
    def _create_settings_menu(self) -> None:
        """設定メニューUI作成"""
        categories = self.config.get('categories', [])
        
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(0, 20, 800, 50),
            text=config_manager.get_text("menu.settings"),
            manager=self.ui_manager
        )
        
        # 設定項目
        y_offset = 100
        for category in categories:
            fields = category.get('fields', [])
            for i, field in enumerate(fields):
                button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(50, y_offset + i * 60, 300, 50),
                    text=field.get('name', ''),
                    manager=self.ui_manager
                )
                button.menu_item_data = field
                self.menu_items.append(button)
                y_offset += 60
    
    def _create_party_status_menu(self) -> None:
        """パーティ状況メニューUI作成"""
        if not self.party:
            return
        
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(0, 20, 800, 50),
            text="パーティ状況",
            manager=self.ui_manager
        )
        
        # パーティ全体情報ボタン
        overview_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(50, 100, 300, 50),
            text="パーティ全体情報",
            manager=self.ui_manager
        )
        overview_button.menu_item_data = {'action': 'party_overview'}
        self.menu_items.append(overview_button)
        
        # 各キャラクターボタン
        y_offset = 170
        for i, character in enumerate(self.party.get_all_characters()):
            char_info = f"{character.name} (Lv.{character.experience.level})"
            char_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(50, y_offset + i * 60, 300, 50),
                text=char_info,
                manager=self.ui_manager
            )
            char_button.menu_item_data = {'action': 'character_details', 'character': character}
            self.menu_items.append(char_button)
        
        # 戻るボタン
        back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(50, y_offset + len(self.party.get_all_characters()) * 60, 300, 50),
            text=config_manager.get_text("menu.back"),
            manager=self.ui_manager
        )
        back_button.menu_item_data = {'action': 'back'}
        self.menu_items.append(back_button)
    
    def _create_save_load_menu(self) -> None:
        """セーブ・ロードメニューUI作成"""
        operation = self.config.get('operation', 'save')
        max_slots = self.config.get('max_slots', 5)
        
        title = "セーブスロット選択" if operation == 'save' else "セーブデータ選択"
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(0, 20, 800, 50),
            text=title,
            manager=self.ui_manager
        )
        
        # 実際のセーブスロット情報を取得
        save_slots = save_manager.get_save_slots()
        save_slot_info = {slot.slot_id: slot for slot in save_slots}
        
        # スロット一覧
        for slot_id in range(1, max_slots + 1):
            if slot_id in save_slot_info:
                slot = save_slot_info[slot_id]
                slot_text = f"スロット {slot_id}: {slot.name} (Lv.{slot.party_level}) [{slot.last_saved.strftime('%m/%d %H:%M')}]"
            else:
                slot_text = f"スロット {slot_id}: [空]"
            
            slot_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(50, 80 + slot_id * 60, 500, 50),
                text=slot_text,
                manager=self.ui_manager
            )
            slot_button.menu_item_data = {'action': operation, 'slot_id': slot_id}
            self.menu_items.append(slot_button)
        
        # 戻るボタン
        back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(50, 80 + (max_slots + 1) * 60, 300, 50),
            text=config_manager.get_text("menu.back"),
            manager=self.ui_manager
        )
        back_button.menu_item_data = {'action': 'back'}
        self.menu_items.append(back_button)
    
    def _create_game_settings_menu(self) -> None:
        """ゲーム設定メニューUI作成"""
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(0, 20, 800, 50),
            text="ゲーム設定",
            manager=self.ui_manager
        )
        
        # 設定項目（実装簡略化）
        settings_items = [
            "言語設定",
            "音量設定", 
            "画面設定",
            "キー設定"
        ]
        
        for i, item in enumerate(settings_items):
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(50, 100 + i * 60, 300, 50),
                text=item,
                manager=self.ui_manager
            )
            button.menu_item_data = {'action': 'setting_item', 'setting': item}
            self.menu_items.append(button)
        
        # 戻るボタン
        back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(50, 100 + len(settings_items) * 60, 300, 50),
            text=config_manager.get_text("menu.back"),
            manager=self.ui_manager
        )
        back_button.menu_item_data = {'action': 'back'}
        self.menu_items.append(back_button)
    
    def _create_party_info_panel(self) -> None:
        """パーティ情報パネル作成"""
        if not self.party:
            return
        
        # パーティ情報パネル
        self.party_info_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(400, 100, 350, 400),
            manager=self.ui_manager
        )
        
        # パーティ名
        party_name_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 330, 30),
            text=f"パーティ: {self.party.name}",
            manager=self.ui_manager,
            container=self.party_info_panel
        )
        self.party_labels.append(party_name_label)
        
        # メンバー一覧
        y_offset = 50
        for i, character in enumerate(self.party.get_all_characters()[:3]):  # 最大3人表示
            char_info = f"{character.name} Lv.{character.experience.level}"
            char_info += f" HP:{character.derived_stats.current_hp}/{character.derived_stats.max_hp}"
            char_info += f" [{character.status.value}]"
            
            char_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(10, y_offset + i * 40, 330, 35),
                text=char_info,
                manager=self.ui_manager,
                container=self.party_info_panel
            )
            self.party_labels.append(char_label)
    
    def _create_gold_display(self) -> None:
        """ゴールド表示作成"""
        if not self.party:
            return
        
        self.gold_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(400, 520, 200, 30),
            text=f"ゴールド: {self.party.gold}G",
            manager=self.ui_manager
        )
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理"""
        if self.state != WindowState.SHOWN:
            return False
        
        # pygame-guiイベント処理
        if self.ui_manager:
            handled = self.ui_manager.process_events(event)
            if handled:
                return True
        
        # ボタンクリック処理
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for button in self.menu_items:
                if event.ui_element == button:
                    return self._handle_button_click(button)
        
        # キーボード操作
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return self.handle_escape()
            elif event.key == pygame.K_UP:
                return self._navigate_menu(-1)
            elif event.key == pygame.K_DOWN:
                return self._navigate_menu(1)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self._activate_selected_item()
        
        return False
    
    def _handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリック処理"""
        if not hasattr(button, 'menu_item_data'):
            return False
        
        item_data = button.menu_item_data
        return self._process_menu_action(item_data)
    
    def _process_menu_action(self, item_data: Dict[str, Any]) -> bool:
        """メニューアクション処理"""
        action = item_data.get('action')
        item_type = item_data.get('type')
        
        # 施設アクセス
        if item_type == 'facility':
            facility_id = item_data.get('facility_id')
            return self._send_message('menu_item_selected', {
                'item_id': facility_id,
                'facility_id': facility_id
            })
        
        # ダンジョン入口
        elif item_data.get('id') == 'dungeon_entrance':
            return self._send_message('menu_item_selected', {
                'item_id': 'dungeon_entrance'
            })
        
        # 設定メニューアクション
        elif action in ['party_status', 'save_game', 'load_game', 'back']:
            return self._send_message('menu_item_selected', {
                'item_id': action
            })
        
        # パーティ関連アクション
        elif action == 'party_overview':
            return self._send_message('party_overview_requested', {})
        
        elif action == 'character_details':
            character = item_data.get('character')
            return self._send_message('character_details_requested', {
                'character': character
            })
        
        # セーブ・ロードアクション
        elif action in ['save', 'load']:
            slot_id = item_data.get('slot_id')
            return self._send_message('save_load_requested', {
                'operation': action,
                'slot_id': slot_id
            })
        
        # ゲーム設定アクション
        elif action == 'setting_item':
            setting = item_data.get('setting')
            return self._send_message('setting_requested', {
                'setting': setting
            })
        
        return False
    
    def _navigate_menu(self, direction: int) -> bool:
        """メニューナビゲーション"""
        if not self.menu_items:
            return False
        
        old_index = self.selected_index
        self.selected_index = (self.selected_index + direction) % len(self.menu_items)
        
        # 選択状態の視覚的更新（実装簡略化）
        logger.debug(f"メニュー選択: {old_index} -> {self.selected_index}")
        
        return True
    
    def _activate_selected_item(self) -> bool:
        """選択されたアイテムを実行"""
        if not self.menu_items or self.selected_index >= len(self.menu_items):
            return False
        
        selected_button = self.menu_items[self.selected_index]
        return self._handle_button_click(selected_button)
    
    def handle_escape(self) -> bool:
        """ESCキー処理"""
        # メニュー階層がある場合は戻る
        if self.menu_stack:
            return self._go_back()
        
        # メインメニューの場合は設定メニューを表示
        if self.current_menu_type == OverworldMenuType.MAIN:
            return self._send_message('settings_menu_requested', {})
        
        # その他の場合は戻る
        return self._send_message('back_requested', {})
    
    def _go_back(self) -> bool:
        """前のメニューに戻る"""
        if not self.menu_stack:
            return False
        
        previous_config = self.menu_stack.pop()
        self._transition_to_menu(previous_config)
        return True
    
    def _transition_to_menu(self, new_config: Dict[str, Any]) -> None:
        """メニュー遷移"""
        # 現在のUI要素をクリーンアップ
        self.cleanup_ui()
        
        # 新しい設定で再作成
        self.config = new_config
        self.current_menu_type = OverworldMenuType(new_config.get('menu_type', 'main'))
        self.create()
    
    def _send_message(self, message_type: str, data: Dict[str, Any]) -> bool:
        """メッセージ送信"""
        if self.message_handler:
            return self.message_handler(message_type, data)
        
        # フォールバック：親ウィンドウにメッセージ送信
        if self.parent:
            self.send_message(message_type, data)
            return True
        
        logger.warning(f"メッセージハンドラーが設定されていません: {message_type}")
        return False
    
    def show_menu(self, menu_type: OverworldMenuType, config: Dict[str, Any]) -> None:
        """指定されたメニューを表示"""
        # 現在の設定をスタックに保存
        current_config = {
            'menu_type': self.current_menu_type.value,
            'title': self.config.get('title', ''),
            'menu_items': self.config.get('menu_items', []),
            'party': self.party,
            'show_party_info': self.show_party_info,
            'show_gold': self.show_gold
        }
        self.menu_stack.append(current_config)
        
        # 新しいメニューに遷移
        new_config = config.copy()
        new_config['menu_type'] = menu_type.value
        self._transition_to_menu(new_config)
    
    def hide_menu(self, menu_type: OverworldMenuType) -> bool:
        """指定されたメニューを非表示にし、前の状態に戻る"""
        # 現在のメニューが指定されたタイプと一致しない場合は何もしない
        if self.current_menu_type != menu_type:
            logger.warning(f"hide_menu: 現在のメニューが {self.current_menu_type.value} で、要求された {menu_type.value} と異なります")
            return False
        
        # スタックが空の場合は何もしない
        if not self.menu_stack:
            logger.warning("hide_menu: メニュースタックが空です")
            return False
        
        # 前の状態を復元
        previous_config = self.menu_stack.pop()
        self._transition_to_menu(previous_config)
        
        logger.info(f"hide_menu: {menu_type.value} を非表示にし、{self.current_menu_type.value} に戻りました")
        return True
    
    def update_party_info(self, party: Party) -> None:
        """パーティ情報更新"""
        self.party = party
        
        # パーティ情報パネルの更新
        if self.show_party_info and self.party_info_panel:
            # 既存のラベルをクリア
            for label in self.party_labels:
                label.kill()
            self.party_labels.clear()
            
            # パーティ情報を再作成
            self._create_party_info_panel()
        
        # ゴールド表示の更新
        if self.show_gold and self.gold_label:
            self.gold_label.set_text(f"ゴールド: {self.party.gold}G")
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # 個別要素のクリーンアップ
        if self.title_label:
            self.title_label.kill()
            self.title_label = None
        
        for button in self.menu_items:
            button.kill()
        self.menu_items.clear()
        
        if self.party_info_panel:
            self.party_info_panel.kill()
            self.party_info_panel = None
        
        for label in self.party_labels:
            label.kill()
        self.party_labels.clear()
        
        if self.gold_label:
            self.gold_label.kill()
            self.gold_label = None
        
        # 親クラスのクリーンアップ
        super().cleanup_ui()
    
    def hide_ui_elements(self) -> None:
        """UI要素を非表示にする"""
        if self.title_label:
            self.title_label.hide()
        
        for button in self.menu_items:
            button.hide()
        
        if self.party_info_panel:
            self.party_info_panel.hide()
        
        if self.gold_label:
            self.gold_label.hide()
        
        logger.info(f"OverworldMainWindow UI要素を非表示: {self.window_id}")
    
    def show_ui_elements(self) -> None:
        """UI要素を表示する"""
        if self.title_label:
            self.title_label.show()
        
        for button in self.menu_items:
            button.show()
        
        if self.party_info_panel:
            self.party_info_panel.show()
        
        if self.gold_label:
            self.gold_label.show()
        
        logger.info(f"OverworldMainWindow UI要素を表示: {self.window_id}")
    
    def get_current_menu_type(self) -> OverworldMenuType:
        """現在のメニュータイプを取得"""
        return self.current_menu_type
    
    def get_menu_stack_depth(self) -> int:
        """メニュー階層の深さを取得"""
        return len(self.menu_stack)
    
    def __str__(self) -> str:
        return f"OverworldMainWindow({self.window_id}, {self.current_menu_type.value}, stack_depth={len(self.menu_stack)})"