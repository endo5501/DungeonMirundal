"""
PartyFormationWindow クラス

パーティ編成ウィンドウ
"""

import pygame
import pygame_gui
import time
from typing import Dict, List, Any, Optional

from .window import Window
from .party_formation_types import (
    PartyPosition, FormationConfig, FormationValidationResult, 
    CharacterSlot, DragDropState, FormationChange
)
from .party_formation_manager import PartyFormationManager
from .party_formation_ui_factory import PartyFormationUIFactory
from src.utils.logger import logger


class PartyFormationWindow(Window):
    """
    パーティ編成ウィンドウクラス
    
    6ポジション（前衛3、後衛3）でのパーティ編成管理
    """
    
    def __init__(self, window_id: str, formation_config: Dict[str, Any], 
                 parent: Optional[Window] = None, modal: bool = True):
        """
        パーティ編成ウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            formation_config: 編成設定辞書
            parent: 親ウィンドウ
            modal: モーダルウィンドウかどうか
        """
        super().__init__(window_id, parent, modal)
        
        # 設定の検証と変換
        self.formation_config = self._validate_and_convert_config(formation_config)
        
        # Extract Classパターン適用 - 専門クラス
        self.formation_manager = PartyFormationManager(
            self.formation_config.party, 
            self.formation_config.max_party_size
        )
        self.ui_factory: Optional[PartyFormationUIFactory] = None
        
        # パーティオブジェクト（下位互換性のため残存）
        self.party = self.formation_config.party
        self.available_characters = self.formation_config.available_characters
        
        # 編成状態
        self.position_slots: Dict[PartyPosition, CharacterSlot] = {}
        self.focused_position = PartyPosition.FRONT_LEFT
        self.selected_character: Optional[Any] = None
        self.has_pending_changes = False
        
        # ドラッグアンドドロップ状態
        self.drag_drop_state = DragDropState()
        self.drag_source: Optional[PartyPosition] = None
        
        # UI要素
        self.main_container: Optional[pygame_gui.core.UIElement] = None
        self.formation_panel: Optional[pygame_gui.core.UIElement] = None
        self.available_panel: Optional[pygame_gui.core.UIElement] = None
        self.detail_panel: Optional[pygame_gui.core.UIElement] = None
        self.button_panel: Optional[pygame_gui.core.UIElement] = None
        
        # UI要素詳細
        self.available_character_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.character_detail_panel: Optional[pygame_gui.elements.UITextBox] = None
        
        logger.debug(f"PartyFormationWindowを初期化: {window_id}")
    
    def _validate_and_convert_config(self, config: Dict[str, Any]) -> FormationConfig:
        """設定を検証してFormationConfigに変換"""
        if 'party' not in config:
            raise ValueError("Formation config must contain 'party'")
        if 'available_characters' not in config:
            raise ValueError("Formation config must contain 'available_characters'")
        
        formation_config = FormationConfig(
            party=config['party'],
            available_characters=config['available_characters'],
            max_party_size=config.get('max_party_size', 6),
            allow_empty_positions=config.get('allow_empty_positions', True),
            enable_drag_and_drop=config.get('enable_drag_and_drop', True),
            show_character_details=config.get('show_character_details', True),
            title=config.get('title', 'パーティ編成')
        )
        
        formation_config.validate()
        return formation_config
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            self._initialize_ui_manager()
            self._calculate_layout()
            self._create_main_container()
            self._create_formation_panel()
            self._create_available_panel()
            self._create_detail_panel()
            self._create_button_panel()
            self._create_position_slots()
            self._create_available_character_list()
            self._create_action_buttons()
            self._load_current_formation()
        
        logger.debug(f"PartyFormationWindow UI要素を作成: {self.window_id}")
    
    def _initialize_ui_manager(self) -> None:
        """UIManagerを初期化"""
        screen_width = 1024
        screen_height = 768
        self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
    
    def _calculate_layout(self) -> None:
        """パーティ編成画面のレイアウトを計算"""
        formation_width = 800
        formation_height = 600
        
        # 画面中央に配置
        screen_width = 1024
        screen_height = 768
        formation_x = (screen_width - formation_width) // 2
        formation_y = (screen_height - formation_height) // 2
        
        self.rect = pygame.Rect(formation_x, formation_y, formation_width, formation_height)
    
    def _create_main_container(self) -> None:
        """メインコンテナを作成"""
        self.main_container = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager
        )
        
        # Extract Classパターン適用 - UIファクトリを初期化（メインコンテナ作成後）
        self.ui_factory = PartyFormationUIFactory(
            self.ui_manager, self.main_container, self.formation_config
        )
    
    def _create_formation_panel(self) -> None:
        """編成パネルを作成"""
        formation_rect = pygame.Rect(20, 20, 400, 450)
        self.formation_panel = pygame_gui.elements.UIPanel(
            relative_rect=formation_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
        
        # タイトル
        title_rect = pygame.Rect(10, 10, 380, 30)
        self.formation_title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=self.formation_config.title,
            manager=self.ui_manager,
            container=self.formation_panel
        )
    
    def _create_available_panel(self) -> None:
        """利用可能キャラクターパネルを作成"""
        available_rect = pygame.Rect(440, 20, 340, 300)
        self.available_panel = pygame_gui.elements.UIPanel(
            relative_rect=available_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
        
        # タイトル
        title_rect = pygame.Rect(10, 10, 320, 30)
        self.available_title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="利用可能キャラクター",
            manager=self.ui_manager,
            container=self.available_panel
        )
    
    def _create_detail_panel(self) -> None:
        """詳細パネルを作成"""
        if self.formation_config.show_character_details:
            detail_rect = pygame.Rect(440, 340, 340, 130)
            self.detail_panel = pygame_gui.elements.UIPanel(
                relative_rect=detail_rect,
                manager=self.ui_manager,
                container=self.main_container
            )
            
            # タイトル
            title_rect = pygame.Rect(10, 10, 320, 30)
            self.detail_title = pygame_gui.elements.UILabel(
                relative_rect=title_rect,
                text="キャラクター詳細",
                manager=self.ui_manager,
                container=self.detail_panel
            )
    
    def _create_button_panel(self) -> None:
        """ボタンパネルを作成"""
        button_rect = pygame.Rect(20, 520, 760, 60)
        self.button_panel = pygame_gui.elements.UIPanel(
            relative_rect=button_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
    
    def _create_position_slots(self) -> None:
        """パーティポジションスロットを作成"""
        slot_width = 120
        slot_height = 80
        spacing = 10
        
        # ポジション配置計算
        positions_layout = {
            PartyPosition.FRONT_LEFT: (10, 50),
            PartyPosition.FRONT_CENTER: (140, 50),
            PartyPosition.FRONT_RIGHT: (270, 50),
            PartyPosition.BACK_LEFT: (10, 140),
            PartyPosition.BACK_CENTER: (140, 140),
            PartyPosition.BACK_RIGHT: (270, 140)
        }
        
        for position, (x, y) in positions_layout.items():
            slot_rect = pygame.Rect(x, y, slot_width, slot_height)
            
            # スロットボタンを作成
            slot_button = pygame_gui.elements.UIButton(
                relative_rect=slot_rect,
                text=self._get_position_display_name(position),
                manager=self.ui_manager,
                container=self.formation_panel
            )
            
            # CharacterSlotオブジェクトを作成
            character_slot = CharacterSlot(
                position=position,
                character=None,
                ui_element=slot_button
            )
            
            self.position_slots[position] = character_slot
    
    def _create_available_character_list(self) -> None:
        """利用可能キャラクターリストを作成"""
        if self.available_characters:
            character_names = [self._format_character_name(char) for char in self.available_characters]
            
            list_rect = pygame.Rect(10, 50, 320, 200)
            self.available_character_list = pygame_gui.elements.UISelectionList(
                relative_rect=list_rect,
                item_list=character_names,
                manager=self.ui_manager,
                container=self.available_panel
            )
    
    def _create_action_buttons(self) -> None:
        """アクションボタンを作成"""
        button_width = 100
        button_height = 30
        button_spacing = 20
        
        # キャンセルボタン（左端）
        cancel_rect = pygame.Rect(20, 15, button_width, button_height)
        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=cancel_rect,
            text='キャンセル',
            manager=self.ui_manager,
            container=self.button_panel
        )
        
        # 適用ボタン（右端）
        apply_x = self.button_panel.relative_rect.width - button_width - 20
        apply_rect = pygame.Rect(apply_x, 15, button_width, button_height)
        self.apply_button = pygame_gui.elements.UIButton(
            relative_rect=apply_rect,
            text='適用',
            manager=self.ui_manager,
            container=self.button_panel
        )
        
        # リセットボタン（中央）
        reset_x = (apply_x - button_width - button_spacing)
        reset_rect = pygame.Rect(reset_x, 15, button_width, button_height)
        self.reset_button = pygame_gui.elements.UIButton(
            relative_rect=reset_rect,
            text='リセット',
            manager=self.ui_manager,
            container=self.button_panel
        )
    
    def _load_current_formation(self) -> None:
        """現在のパーティ編成を読み込み"""
        for position in PartyPosition:
            character = self.party.get_character_at_position(position)
            if character:
                self.position_slots[position].character = character
                self._update_slot_display(position)
    
    def _get_position_display_name(self, position: PartyPosition) -> str:
        """ポジションの表示名を取得"""
        position_names = {
            PartyPosition.FRONT_LEFT: "前衛左",
            PartyPosition.FRONT_CENTER: "前衛中",
            PartyPosition.FRONT_RIGHT: "前衛右",
            PartyPosition.BACK_LEFT: "後衛左",
            PartyPosition.BACK_CENTER: "後衛中",
            PartyPosition.BACK_RIGHT: "後衛右"
        }
        return position_names.get(position, str(position))
    
    def _format_character_name(self, character: Any) -> str:
        """キャラクター名をフォーマット"""
        if hasattr(character, 'name') and hasattr(character, 'character_class') and hasattr(character, 'level'):
            return f"{character.name} ({character.character_class} Lv.{character.level})"
        elif hasattr(character, 'name'):
            return character.name
        else:
            return str(character)
    
    def _update_slot_display(self, position: PartyPosition) -> None:
        """スロット表示を更新"""
        slot = self.position_slots[position]
        if slot.character:
            display_text = f"{self._get_position_display_name(position)}\n{self._format_character_name(slot.character)}"
        else:
            display_text = self._get_position_display_name(position)
        
        if slot.ui_element:
            slot.ui_element.set_text(display_text)
    
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
        
        # ドラッグアンドドロップ処理
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            return self._handle_drag_start(event)
        
        # リスト選択処理
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            return self._handle_list_selection(event)
        
        return False
    
    def _handle_keyboard_event(self, event) -> bool:
        """キーボードイベントを処理"""
        if event.key == pygame.K_RETURN:
            return self.apply_formation()
        elif event.key == pygame.K_RIGHT:
            return self._move_focus_right()
        elif event.key == pygame.K_LEFT:
            return self._move_focus_left()
        elif event.key == pygame.K_UP:
            return self._move_focus_up()
        elif event.key == pygame.K_DOWN:
            return self._move_focus_down()
        
        return False
    
    def _handle_button_click(self, event) -> bool:
        """ボタンクリックを処理"""
        if hasattr(self, 'apply_button') and event.ui_element == self.apply_button:
            return self.apply_formation()
        elif hasattr(self, 'cancel_button') and event.ui_element == self.cancel_button:
            return self.cancel_formation()
        elif hasattr(self, 'reset_button') and event.ui_element == self.reset_button:
            return self._reset_formation()
        
        # ポジションスロットクリック
        for position, slot in self.position_slots.items():
            if event.ui_element == slot.ui_element:
                return self._handle_position_click(position)
        
        return False
    
    def _handle_drag_start(self, event) -> bool:
        """ドラッグ開始を処理"""
        if not self.formation_config.enable_drag_and_drop:
            return False
        
        # ポジションスロットからのドラッグ
        for position, slot in self.position_slots.items():
            if event.ui_element == slot.ui_element and slot.character:
                self.drag_drop_state.start_drag(position, slot.character)
                self.drag_source = position
                return True
        
        return False
    
    def _handle_list_selection(self, event) -> bool:
        """リスト選択を処理"""
        if event.ui_element == self.available_character_list:
            selected_text = event.text
            # テキストからキャラクターを特定
            for character in self.available_characters:
                if self._format_character_name(character) == selected_text:
                    self.select_character(character)
                    return True
        
        return False
    
    def _handle_position_click(self, position: PartyPosition) -> bool:
        """ポジションクリックを処理"""
        slot = self.position_slots[position]
        
        if self.selected_character and slot.is_empty:
            # 選択されたキャラクターをポジションに追加
            return self.add_character_to_position(self.selected_character, position)
        elif slot.character:
            # 配置されたキャラクターを選択
            self.select_character(slot.character)
            return True
        
        return False
    
    def _move_focus_right(self) -> bool:
        """フォーカスを右に移動"""
        current_index = self.focused_position.index
        next_positions = [pos for pos in PartyPosition if pos.index > current_index]
        if next_positions:
            self.focused_position = next_positions[0]
            return True
        return False
    
    def _move_focus_left(self) -> bool:
        """フォーカスを左に移動"""
        current_index = self.focused_position.index
        prev_positions = [pos for pos in PartyPosition if pos.index < current_index]
        if prev_positions:
            self.focused_position = prev_positions[-1]
            return True
        return False
    
    def _move_focus_up(self) -> bool:
        """フォーカスを上に移動"""
        if self.focused_position.is_back_row:
            # 後衛から前衛に移動
            if self.focused_position == PartyPosition.BACK_LEFT:
                self.focused_position = PartyPosition.FRONT_LEFT
            elif self.focused_position == PartyPosition.BACK_CENTER:
                self.focused_position = PartyPosition.FRONT_CENTER
            elif self.focused_position == PartyPosition.BACK_RIGHT:
                self.focused_position = PartyPosition.FRONT_RIGHT
            return True
        return False
    
    def _move_focus_down(self) -> bool:
        """フォーカスを下に移動"""
        if self.focused_position.is_front_row:
            # 前衛から後衛に移動
            if self.focused_position == PartyPosition.FRONT_LEFT:
                self.focused_position = PartyPosition.BACK_LEFT
            elif self.focused_position == PartyPosition.FRONT_CENTER:
                self.focused_position = PartyPosition.BACK_CENTER
            elif self.focused_position == PartyPosition.FRONT_RIGHT:
                self.focused_position = PartyPosition.BACK_RIGHT
            return True
        return False
    
    def add_character_to_position(self, character: Any, position: PartyPosition) -> bool:
        """キャラクターをポジションに追加"""
        # Extract Classパターン適用 - 編成管理を専門クラスに委譲
        if self.formation_manager.add_character_to_position(character, position):
            # UI更新
            slot = self.position_slots[position]
            slot.character = character
            self._update_slot_display(position)
            
            self.has_pending_changes = True
            return True
        
        return False
    
    def remove_character_from_position(self, position: PartyPosition) -> bool:
        """キャラクターをポジションから削除"""
        # Extract Classパターン適用 - 編成管理を専門クラスに委譲
        if self.formation_manager.remove_character_from_position(position):
            # UI更新
            slot = self.position_slots[position]
            slot.character = None
            self._update_slot_display(position)
            
            self.has_pending_changes = True
            return True
        
        return False
    
    def move_character(self, from_position: PartyPosition, to_position: PartyPosition) -> bool:
        """キャラクターを移動"""
        # Extract Classパターン適用 - 編成管理を専門クラスに委譲
        if self.formation_manager.move_character(from_position, to_position):
            # UI更新
            from_slot = self.position_slots[from_position]
            to_slot = self.position_slots[to_position]
            
            character = from_slot.character
            from_slot.character = None
            to_slot.character = character
            
            self._update_slot_display(from_position)
            self._update_slot_display(to_position)
            
            self.has_pending_changes = True
            return True
        
        return False
    
    def select_character(self, character: Any) -> None:
        """キャラクターを選択"""
        self.selected_character = character
        
        # 詳細表示を更新
        if self.formation_config.show_character_details:
            self._update_character_details(character)
        
        logger.debug(f"キャラクター選択: {character}")
    
    def _update_character_details(self, character: Any) -> None:
        """キャラクター詳細表示を更新"""
        if not self.detail_panel:
            return
        
        # 詳細情報をフォーマット
        details = self._format_character_details(character)
        
        # 既存の詳細表示を削除
        if self.character_detail_panel:
            self.character_detail_panel.kill()
        
        # 新しい詳細表示を作成
        detail_rect = pygame.Rect(10, 50, 320, 70)
        self.character_detail_panel = pygame_gui.elements.UITextBox(
            relative_rect=detail_rect,
            html_text=details,
            manager=self.ui_manager,
            container=self.detail_panel
        )
    
    def _format_character_details(self, character: Any) -> str:
        """キャラクター詳細をフォーマット"""
        lines = []
        
        if hasattr(character, 'name'):
            lines.append(f"<b>名前:</b> {character.name}")
        
        if hasattr(character, 'character_class'):
            lines.append(f"<b>職業:</b> {character.character_class}")
        
        if hasattr(character, 'level'):
            lines.append(f"<b>レベル:</b> {character.level}")
        
        if hasattr(character, 'stats'):
            lines.append("<b>ステータス:</b>")
            for stat_name, stat_value in character.stats.items():
                lines.append(f"  {stat_name}: {stat_value}")
        
        return "<br>".join(lines) if lines else "情報なし"
    
    def validate_formation(self) -> bool:
        """パーティ編成を検証"""
        # Extract Classパターン適用 - 検証ロジックを専門クラスに委譲
        validation_result = self.formation_manager.validate_formation()
        return validation_result.is_valid
    
    def apply_formation(self) -> bool:
        """パーティ編成を適用"""
        if not self.validate_formation():
            return False
        
        # 適用メッセージを送信
        self.send_message('formation_applied', {
            'party': self.party
        })
        
        self.has_pending_changes = False
        logger.info(f"パーティ編成を適用: {self.party}")
        return True
    
    def cancel_formation(self) -> bool:
        """パーティ編成をキャンセル"""
        # キャンセルメッセージを送信
        self.send_message('formation_cancelled')
        
        self.has_pending_changes = False
        logger.debug("パーティ編成がキャンセルされました")
        return True
    
    def _reset_formation(self) -> bool:
        """パーティ編成をリセット"""
        # 全ポジションをクリア
        for position in PartyPosition:
            slot = self.position_slots[position]
            if slot.character:
                self.remove_character_from_position(position)
        
        logger.debug("パーティ編成をリセットしました")
        return True
    
    def handle_escape(self) -> bool:
        """ESCキーの処理"""
        return self.cancel_formation()
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # ポジションスロットをクリア
        self.position_slots.clear()
        
        # リストをクリア
        self.available_character_list = None
        
        # pygame-guiの要素を削除
        if self.ui_manager:
            for element in list(self.ui_manager.get_root_container().elements):
                element.kill()
            self.ui_manager = None
        
        logger.debug(f"PartyFormationWindow UI要素をクリーンアップ: {self.window_id}")