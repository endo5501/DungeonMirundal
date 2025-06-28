"""
PartyFormationUIFactory クラス

パーティ編成UI要素作成専門クラス
"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List, Tuple
from .party_formation_types import PartyPosition, FormationConfig, CharacterSlot
from src.utils.logger import logger


class PartyFormationUIFactory:
    """
    パーティ編成UI要素ファクトリクラス
    
    UI要素の作成と配置を担当
    """
    
    def __init__(self, ui_manager: pygame_gui.UIManager, 
                 main_container: pygame_gui.core.UIElement,
                 config: FormationConfig):
        """
        PartyFormationUIFactoryを初期化
        
        Args:
            ui_manager: UIManager
            main_container: メインコンテナ
            config: 編成設定
        """
        self.ui_manager = ui_manager
        self.main_container = main_container
        self.config = config
        
        # レイアウト定数
        self.SLOT_WIDTH = 120
        self.SLOT_HEIGHT = 80
        self.SLOT_SPACING = 10
        self.PANEL_PADDING = 20
    
    def create_formation_panel(self, rect: pygame.Rect) -> pygame_gui.elements.UIPanel:
        """
        編成パネルを作成
        
        Args:
            rect: パネルのRect
            
        Returns:
            pygame_gui.elements.UIPanel: 編成パネル
        """
        panel = pygame_gui.elements.UIPanel(
            relative_rect=rect,
            manager=self.ui_manager,
            container=self.main_container
        )
        
        # タイトル
        title_rect = pygame.Rect(10, 10, rect.width - 20, 30)
        title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=self.config.title,
            manager=self.ui_manager,
            container=panel
        )
        
        return panel
    
    def create_position_slots(self, formation_panel: pygame_gui.elements.UIPanel) -> Dict[PartyPosition, CharacterSlot]:
        """
        パーティポジションスロットを作成
        
        Args:
            formation_panel: 編成パネル
            
        Returns:
            Dict[PartyPosition, CharacterSlot]: ポジションスロット辞書
        """
        position_slots = {}
        
        # ポジション配置計算
        positions_layout = self._calculate_position_layout()
        
        for position, (x, y) in positions_layout.items():
            slot_rect = pygame.Rect(x, y, self.SLOT_WIDTH, self.SLOT_HEIGHT)
            
            # スロットボタンを作成
            slot_button = pygame_gui.elements.UIButton(
                relative_rect=slot_rect,
                text=self._get_position_display_name(position),
                manager=self.ui_manager,
                container=formation_panel
            )
            
            # CharacterSlotオブジェクトを作成
            character_slot = CharacterSlot(
                position=position,
                character=None,
                ui_element=slot_button
            )
            
            position_slots[position] = character_slot
        
        return position_slots
    
    def create_available_characters_panel(self, rect: pygame.Rect) -> Tuple[pygame_gui.elements.UIPanel, pygame_gui.elements.UISelectionList]:
        """
        利用可能キャラクターパネルを作成
        
        Args:
            rect: パネルのRect
            
        Returns:
            Tuple[UIPanel, UISelectionList]: パネルとリスト
        """
        panel = pygame_gui.elements.UIPanel(
            relative_rect=rect,
            manager=self.ui_manager,
            container=self.main_container
        )
        
        # タイトル
        title_rect = pygame.Rect(10, 10, rect.width - 20, 30)
        title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="利用可能キャラクター",
            manager=self.ui_manager,
            container=panel
        )
        
        # キャラクターリスト
        character_list = None
        if self.config.available_characters:
            character_names = [self._format_character_name(char) for char in self.config.available_characters]
            
            list_rect = pygame.Rect(10, 50, rect.width - 20, rect.height - 60)
            character_list = pygame_gui.elements.UISelectionList(
                relative_rect=list_rect,
                item_list=character_names,
                manager=self.ui_manager,
                container=panel
            )
        
        return panel, character_list
    
    def create_character_detail_panel(self, rect: pygame.Rect) -> Tuple[pygame_gui.elements.UIPanel, pygame_gui.elements.UITextBox]:
        """
        キャラクター詳細パネルを作成
        
        Args:
            rect: パネルのRect
            
        Returns:
            Tuple[UIPanel, UITextBox]: パネルと詳細表示
        """
        if not self.config.show_character_details:
            return None, None
        
        panel = pygame_gui.elements.UIPanel(
            relative_rect=rect,
            manager=self.ui_manager,
            container=self.main_container
        )
        
        # タイトル
        title_rect = pygame.Rect(10, 10, rect.width - 20, 30)
        title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="キャラクター詳細",
            manager=self.ui_manager,
            container=panel
        )
        
        # 詳細表示エリア
        detail_rect = pygame.Rect(10, 50, rect.width - 20, rect.height - 60)
        detail_text_box = pygame_gui.elements.UITextBox(
            relative_rect=detail_rect,
            html_text="キャラクターを選択してください",
            manager=self.ui_manager,
            container=panel
        )
        
        return panel, detail_text_box
    
    def create_action_buttons(self, button_panel: pygame_gui.elements.UIPanel) -> Dict[str, pygame_gui.elements.UIButton]:
        """
        アクションボタンを作成
        
        Args:
            button_panel: ボタンパネル
            
        Returns:
            Dict[str, UIButton]: ボタン辞書
        """
        buttons = {}
        button_positions = self._calculate_button_positions(button_panel.relative_rect)
        
        # キャンセルボタン
        cancel_rect = button_positions['cancel']
        buttons['cancel'] = pygame_gui.elements.UIButton(
            relative_rect=cancel_rect,
            text='キャンセル',
            manager=self.ui_manager,
            container=button_panel
        )
        
        # 適用ボタン
        apply_rect = button_positions['apply']
        buttons['apply'] = pygame_gui.elements.UIButton(
            relative_rect=apply_rect,
            text='適用',
            manager=self.ui_manager,
            container=button_panel
        )
        
        # リセットボタン
        reset_rect = button_positions['reset']
        buttons['reset'] = pygame_gui.elements.UIButton(
            relative_rect=reset_rect,
            text='リセット',
            manager=self.ui_manager,
            container=button_panel
        )
        
        return buttons
    
    def update_slot_display(self, slot: CharacterSlot) -> None:
        """
        スロット表示を更新
        
        Args:
            slot: 更新するスロット
        """
        if slot.character:
            display_text = f"{self._get_position_display_name(slot.position)}\n{self._format_character_name(slot.character)}"
        else:
            display_text = self._get_position_display_name(slot.position)
        
        if slot.ui_element:
            slot.ui_element.set_text(display_text)
        
        # 選択状態の表示更新
        self._update_slot_selection_appearance(slot)
    
    def update_character_details(self, character: Any, detail_text_box: pygame_gui.elements.UITextBox) -> None:
        """
        キャラクター詳細を更新
        
        Args:
            character: キャラクター
            detail_text_box: 詳細表示テキストボックス
        """
        if not detail_text_box:
            return
        
        details = self._format_character_details(character)
        detail_text_box.set_text(details)
    
    def set_slot_focus(self, slot: CharacterSlot, focused: bool) -> None:
        """
        スロットのフォーカス状態を設定
        
        Args:
            slot: スロット
            focused: フォーカス状態
        """
        slot.is_selected = focused
        self._update_slot_selection_appearance(slot)
    
    def _calculate_position_layout(self) -> Dict[PartyPosition, Tuple[int, int]]:
        """ポジション配置を計算"""
        return {
            PartyPosition.FRONT_LEFT: (10, 50),
            PartyPosition.FRONT_CENTER: (140, 50),
            PartyPosition.FRONT_RIGHT: (270, 50),
            PartyPosition.BACK_LEFT: (10, 140),
            PartyPosition.BACK_CENTER: (140, 140),
            PartyPosition.BACK_RIGHT: (270, 140)
        }
    
    def _calculate_button_positions(self, container_rect: pygame.Rect) -> Dict[str, pygame.Rect]:
        """ボタン配置を計算"""
        button_width = 100
        button_height = 30
        button_spacing = 20
        
        # キャンセルボタン（左端）
        cancel_rect = pygame.Rect(20, 15, button_width, button_height)
        
        # 適用ボタン（右端）
        apply_x = container_rect.width - button_width - 20
        apply_rect = pygame.Rect(apply_x, 15, button_width, button_height)
        
        # リセットボタン（中央）
        reset_x = apply_x - button_width - button_spacing
        reset_rect = pygame.Rect(reset_x, 15, button_width, button_height)
        
        return {
            'cancel': cancel_rect,
            'apply': apply_rect,
            'reset': reset_rect
        }
    
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
    
    def _update_slot_selection_appearance(self, slot: CharacterSlot) -> None:
        """スロットの選択状態表示を更新"""
        if not slot.ui_element:
            return
        
        # フォーカス状態に応じた外観変更
        # 実際の実装では色やボーダーを変更
        current_text = slot.ui_element.text
        
        if slot.is_selected:
            # 選択状態の表示（例：テキストにマークを付加）
            if not current_text.startswith(">>> "):
                slot.ui_element.set_text(f">>> {current_text}")
        else:
            # 非選択状態の表示
            if current_text.startswith(">>> "):
                slot.ui_element.set_text(current_text[4:])
    
    def destroy_ui_elements(self, elements: List[Any]) -> None:
        """UI要素を破棄"""
        for element in elements:
            if element and hasattr(element, 'kill'):
                element.kill()