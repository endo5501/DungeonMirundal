"""
FacilityMenuWindow クラス

施設メインメニューウィンドウ
"""

import pygame
import pygame_gui
import os
from typing import Dict, List, Any, Optional

from .window import Window
from .facility_menu_types import (
    FacilityType, FacilityConfig, FacilityMenuItem, MenuItemType, 
    PartyInfo, FacilityInteraction, MenuLayout
)
from .facility_menu_manager import FacilityMenuManager
from .facility_menu_ui_factory import FacilityMenuUIFactory
from .facility_menu_validator import FacilityMenuValidator
from src.utils.logger import logger


class FacilityMenuWindow(Window):
    """
    施設メインメニューウィンドウクラス
    
    全施設で共通利用できる汎用的なメニューウィンドウ
    """
    
    def __init__(self, window_id: str, facility_config: Dict[str, Any], 
                 parent: Optional[Window] = None, modal: bool = False):
        """
        施設メニューウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            facility_config: 施設設定辞書
            parent: 親ウィンドウ
            modal: モーダルウィンドウかどうか
        """
        super().__init__(window_id, parent, modal)
        
        # 設定の検証と変換
        self.facility_config = self._validate_and_convert_config(facility_config)
        
        # 施設情報
        self.facility_type = FacilityType(self.facility_config.facility_type)
        self.facility_name = self.facility_config.facility_name
        self.party = self.facility_config.party
        
        # メニュー項目
        self.menu_items = self.facility_config.get_menu_items()
        
        # レイアウト
        self.layout = MenuLayout()
        
        # 抽出されたコンポーネント
        self.menu_manager = FacilityMenuManager(self.facility_type, self.menu_items)
        self.ui_factory = FacilityMenuUIFactory(self.layout)
        self.validator = FacilityMenuValidator(self.facility_type)
        
        # UI要素
        self.main_container: Optional[pygame_gui.core.UIElement] = None
        self.facility_title: Optional[pygame_gui.elements.UILabel] = None
        self.party_info_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.menu_buttons: List[pygame_gui.elements.UIButton] = []
        
        # メッセージハンドラー
        self.message_handler = None
        
        logger.debug(f"FacilityMenuWindowを初期化: {window_id}, {self.facility_type}")
    
    def _validate_and_convert_config(self, config: Dict[str, Any]) -> FacilityConfig:
        """設定を検証してFacilityConfigに変換"""
        if 'facility_type' not in config:
            raise ValueError("Facility config must contain 'facility_type'")
        if 'menu_items' not in config:
            raise ValueError("Facility config must contain 'menu_items'")
        
        facility_config = FacilityConfig(
            facility_type=config['facility_type'],
            facility_name=config.get('facility_name', ''),
            party=config.get('party'),
            menu_items=config['menu_items'],
            show_party_info=config.get('show_party_info', True),
            show_gold=config.get('show_gold', True),
            background_music=config.get('background_music'),
            welcome_message=config.get('welcome_message')
        )
        
        facility_config.validate()
        return facility_config
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            self._initialize_ui_manager()
            
        # Mockの場合はUI作成をスキップ
        if hasattr(self.ui_manager, '_mock_name'):
            logger.debug(f"FacilityMenuWindow MockUIManagerのためUI作成をスキップ: {self.window_id}")
            return
            
        try:
            logger.info(f"FacilityMenuWindow UI作成開始: {self.window_id}")
            self.rect = self.ui_factory.calculate_window_layout(len(self.menu_items), self.facility_config.show_party_info)
            logger.info(f"レイアウト計算完了: {self.rect}")
            
            self.main_container = self.ui_factory.create_main_container(self.rect, self.ui_manager)
            logger.info(f"メインコンテナ作成完了")
            
            self.facility_title = self.ui_factory.create_facility_title(self.facility_type, self.facility_name, self.main_container, self.ui_manager)
            logger.info(f"施設タイトル作成完了")
            
            if self.facility_config.show_party_info:
                self.party_info_panel = self.ui_factory.create_party_info_panel(self.main_container, self.ui_manager, True)
                self._update_party_info_display()
                logger.info(f"パーティ情報パネル作成完了")
                
            self.menu_buttons = self.ui_factory.create_menu_buttons(self.menu_items, self.main_container, self.ui_manager, self.facility_config.show_party_info)
            logger.info(f"メニューボタン作成完了: {len(self.menu_buttons)}個")
            
            # デバッグ: 作成されたUI要素を確認
            if self.ui_manager and hasattr(self.ui_manager, 'get_root_container'):
                element_count = len(self.ui_manager.get_root_container().elements)
                logger.info(f"UIManager内のUI要素総数: {element_count}")
                
                # 各ボタンの状態を確認
                for i, button in enumerate(self.menu_buttons):
                    if button:
                        logger.info(f"ボタン{i}: visible={button.visible}, alive={button.alive}")
            
            self._update_menu_button_states()
            logger.info(f"ボタン状態更新完了")
            
        except Exception as e:
            logger.error(f"FacilityMenuWindow UI作成エラー: {e}")
            import traceback
            logger.error(f"スタックトレース: {traceback.format_exc()}")
            raise  # エラーを再発生させて問題を明確にする
        
        logger.info(f"FacilityMenuWindow UI要素を作成完了: {self.window_id}")
    
    def _initialize_ui_manager(self) -> None:
        """UIManagerを初期化"""
        # WindowManagerの統一されたUIManagerを使用（フォント・テーマが設定済み）
        from .window_manager import WindowManager
        window_manager = WindowManager.get_instance()
        self.ui_manager = window_manager.ui_manager
        
        logger.info(f"FacilityMenuWindow UIManager初期化: window_manager.ui_manager={self.ui_manager}")
        
        if not self.ui_manager:
            # テスト環境フォールバック：テーマなしでUIManagerを作成
            screen_width = 1024
            screen_height = 768
            try:
                # テーマファイルがある場合は使用
                theme_path = "/home/satorue/Dungeon/config/ui_theme.json"
                if os.path.exists(theme_path):
                    self.ui_manager = pygame_gui.UIManager((screen_width, screen_height), theme_path)
                    logger.warning(f"統一UIManagerがないため独自作成（テーマ有り）: {theme_path}")
                else:
                    self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
                    logger.warning(f"統一UIManagerがないため独自作成（テーマ無し）")
            except Exception as e:
                # テスト環境ではMockUIManagerを使用
                from unittest.mock import Mock
                self.ui_manager = Mock()
                logger.warning(f"UIManager初期化エラー、Mockを使用: {e}")
        else:
            logger.info(f"WindowManagerの統一UIManagerを使用: {type(self.ui_manager)}")
    
    
    
    
    
    def _update_party_info_display(self) -> None:
        """パーティ情報表示を更新"""
        if not self.party_info_panel:
            return
        
        # パーティ情報を取得
        party_info = self._get_party_info()
        
        # UIファクトリーを使用して表示を作成
        self.ui_factory.create_party_info_display(party_info, self.party_info_panel, self.ui_manager, self.facility_config.show_gold)
    
    def _get_party_info(self) -> PartyInfo:
        """パーティ情報を取得"""
        member_count = 0
        gold = 0
        max_hp = 0
        current_hp = 0
        
        if self.party:
            # 実際のPartyクラスのプロパティ・メソッドを使用
            member_count = len(self.party.get_all_characters())
            gold = self.party.gold
            
            # HP合計を計算
            for character in self.party.get_all_characters():
                if hasattr(character, 'derived_stats') and character.derived_stats:
                    max_hp += character.derived_stats.max_hp
                    current_hp += character.derived_stats.current_hp
        
        return PartyInfo(
            member_count=member_count,
            gold=gold,
            max_hp=max_hp,
            current_hp=current_hp,
            location=""
        )
    
    
    def _update_menu_button_states(self) -> None:
        """メニューボタンの状態を更新"""
        # 利用可能性をチェック
        self.ui_factory.apply_button_availability(self.menu_buttons, self.menu_items, self.party)
        
        # 選択状態の表示
        self.ui_factory.apply_button_highlighting(self.menu_buttons, self.menu_manager.selected_index)
    
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if not self.ui_manager:
            return False
        
        # pygame-guiにイベントを渡す
        self.ui_manager.process_events(event)
        
        # キーボードイベント
        if event.type == pygame.KEYDOWN:
            return self._handle_keyboard_event(event)
        
        # ボタンクリック処理
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            return self._handle_button_click(event)
        
        return False
    
    def _handle_keyboard_event(self, event) -> bool:
        """キーボードイベントを処理"""
        if event.key == pygame.K_UP:
            return self.move_selection_up()
        elif event.key == pygame.K_DOWN:
            return self.move_selection_down()
        elif event.key == pygame.K_RETURN:
            return self._activate_selected_item()
        
        return False
    
    def _handle_button_click(self, event) -> bool:
        """ボタンクリックを処理"""
        # クリックされたボタンを特定
        for i, button in enumerate(self.menu_buttons):
            if event.ui_element == button:
                self.menu_manager.selected_index = i
                self._update_menu_button_states()
                return self._activate_selected_item()
        
        return False
    
    def move_selection_up(self) -> bool:
        """選択を上に移動"""
        result = self.menu_manager.move_selection_up()
        self._update_menu_button_states()
        return result
    
    def move_selection_down(self) -> bool:
        """選択を下に移動"""
        result = self.menu_manager.move_selection_down()
        self._update_menu_button_states()
        return result
    
    def _activate_selected_item(self) -> bool:
        """選択された項目をアクティベート"""
        selected_item = self.menu_manager.get_selected_item()
        if selected_item:
            return self.select_menu_item(selected_item.item_id)
        
        return False
    
    def select_menu_item(self, item_id: str) -> bool:
        """メニュー項目を選択"""
        # 項目を検索
        selected_item = self.menu_manager.select_item_by_id(item_id)
        if not selected_item:
            return False
        
        # 利用可能性をチェック
        if not self.validator.validate_item_availability(selected_item, self.party):
            logger.warning(f"メニュー項目が利用できません: {item_id}")
            return False
        
        # 項目タイプに応じて処理
        if self.menu_manager.is_exit_item(selected_item):
            return self._handle_exit_selection()
        else:
            return self._handle_menu_selection(selected_item)
    
    def _handle_exit_selection(self) -> bool:
        """「出る」選択を処理"""
        self.send_message('facility_exit_requested', {
            'facility_type': self.facility_type.value
        })
        
        logger.info(f"施設退場リクエスト送信: {self.facility_type}")
        return True
    
    def _handle_menu_selection(self, item: FacilityMenuItem) -> bool:
        """メニュー選択を処理"""
        # インタラクションを記録
        interaction = self.menu_manager.record_interaction('menu_select', item.item_id)
        
        # メッセージを送信
        self.send_message('menu_item_selected', {
            'item_id': item.item_id,
            'facility_type': self.facility_type.value
        })
        
        logger.debug(f"メニュー項目選択: {item.item_id} ({self.facility_type})")
        return True
    
    def handle_escape(self) -> bool:
        """ESCキーの処理"""
        return self._handle_exit_selection()
    
    @property
    def selected_index(self) -> int:
        """現在の選択インデックスを取得（後方互換性のため）"""
        return self.menu_manager.selected_index
    
    @selected_index.setter
    def selected_index(self, value: int) -> None:
        """選択インデックスを設定（後方互換性のため）"""
        self.menu_manager.selected_index = value
    
    def send_message(self, message_type: str, data: Dict[str, Any] = None) -> None:
        """
        メッセージハンドラーにメッセージを送信
        
        Args:
            message_type: メッセージの種類
            data: メッセージデータ
        """
        if self.message_handler:
            self.message_handler(message_type, data or {})
        else:
            # フォールバック：親ウィンドウに送信
            super().send_message(message_type, data)
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # ボタンリストをクリア
        self.menu_buttons.clear()
        
        # UI要素をクリア
        self.facility_title = None
        self.party_info_panel = None
        
        # UIファクトリーを使用してクリーンアップ
        self.ui_factory.cleanup_ui_elements(self.ui_manager)
        self.ui_manager = None
        
        logger.debug(f"FacilityMenuWindow UI要素をクリーンアップ: {self.window_id}")
    
    def disable_ui(self) -> None:
        """UI要素を一時的に無効化（モーダルダイアログ表示時）"""
        if self.main_container:
            self.main_container.hide()
        logger.info(f"FacilityMenuWindow UI要素を無効化: {self.window_id}")
    
    def enable_ui(self) -> None:
        """UI要素を再度有効化（モーダルダイアログ閉じた時）"""
        if self.main_container:
            self.main_container.show()
        logger.info(f"FacilityMenuWindow UI要素を有効化: {self.window_id}")
    
    def hide_ui_elements(self) -> None:
        """UI要素を非表示にする"""
        if self.main_container:
            self.main_container.hide()
        logger.debug(f"FacilityMenuWindow UI要素を非表示: {self.window_id}")
    
    def show_ui_elements(self) -> None:
        """UI要素を表示する"""
        if self.main_container:
            self.main_container.show()
        logger.debug(f"FacilityMenuWindow UI要素を表示: {self.window_id}")