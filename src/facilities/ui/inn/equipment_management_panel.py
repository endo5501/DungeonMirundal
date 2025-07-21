"""装備管理パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
import logging
from ..service_panel import ServicePanel

logger = logging.getLogger(__name__)


class EquipmentManagementPanel(ServicePanel):
    """装備管理パネル
    
    宿屋でのキャラクター装備管理（キャラクター選択→装備概要表示）
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        # UI要素の初期化
        self.character_buttons: List[pygame_gui.elements.UIButton] = []
        self.selected_character_index: Optional[int] = None
        self.back_button: Optional[pygame_gui.elements.UIButton] = None
        self.character_info_label: Optional[pygame_gui.elements.UILabel] = None
        self.equipment_info_label: Optional[pygame_gui.elements.UILabel] = None
        
        # 親クラスの初期化（_create_ui()が呼ばれる）
        super().__init__(rect, parent, controller, "equipment_management", ui_manager)
        
        logger.info("EquipmentManagementPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        try:
            # パーティ情報の取得
            party = None
            if self.controller and self.controller.service and self.controller.service.party:
                party = self.controller.service.party
            
            if not party:
                self._create_no_party_ui()
                return
                
            # タイトル（上部ナビゲーションとの重複を避けるため下にずらす）
            title_rect = pygame.Rect(10, 50, self.rect.width - 20, 40)
            title_label = self._create_label(
                "equipment_title",
                "装備管理 - キャラクター選択",
                title_rect,
                container=self.container
            )
            
            # キャラクターボタンを作成（縦配置、宿屋パネルサイズに最適化）
            y_offset = 100  # より下から開始
            button_height = 45  # 少し小さく
            button_spacing = 55  # 間隔も調整
            
            characters = party.get_all_characters()
            max_visible_chars = min(len(characters), 6)  # 最大6名まで表示
            
            for i, character in enumerate(characters[:max_visible_chars]):
                equipment = character.get_equipment()
                summary = equipment.get_equipment_summary()
                equipped_count = summary['equipped_count']
                
                # キャラクター情報テキスト
                char_text = f"{character.name} ({equipped_count}/4 装備中)"
                
                button_rect = pygame.Rect(10, y_offset + i * button_spacing, self.rect.width - 20, button_height)
                char_button = self._create_button(
                    f"character_{i}",
                    char_text,
                    button_rect,
                    container=self.container,
                    object_id=f"#character_button_{i}"
                )
                self.character_buttons.append(char_button)
            
            # 戻るボタン
            back_rect = pygame.Rect(10, self.rect.height - 50, 100, 35)
            self.back_button = self._create_button(
                "back_button",
                "← 戻る",
                back_rect,
                container=self.container,
                object_id="#back_button"
            )
            
            logger.info(f"EquipmentManagementPanel: Created UI for {len(self.character_buttons)} characters")
            
        except Exception as e:
            logger.error(f"装備管理パネルの作成中にエラー: {e}")
            self._create_error_ui(str(e))
    
    def _create_no_party_ui(self) -> None:
        """パーティがない場合のUI"""
        title_rect = pygame.Rect(10, 50, self.rect.width - 20, 40)
        self._create_label(
            "no_party_title",
            "装備管理",
            title_rect,
            container=self.container
        )
        
        info_rect = pygame.Rect(10, 100, self.rect.width - 20, 100)
        self.character_info_label = self._create_label(
            "no_party_info",
            "パーティが編成されていません。\n\n先にパーティを編成してから\n装備管理をご利用ください。",
            info_rect,
            container=self.container
        )
        
        # 戻るボタン
        back_rect = pygame.Rect(10, self.rect.height - 50, 100, 35)
        self.back_button = self._create_button(
            "back_button",
            "← 戻る",
            back_rect,
            container=self.container,
            object_id="#back_button"
        )
    
    def _create_error_ui(self, error_message: str) -> None:
        """エラー時のUI"""
        title_rect = pygame.Rect(10, 50, self.rect.width - 20, 40)
        self._create_label(
            "error_title",
            "装備管理 - エラー",
            title_rect,
            container=self.container
        )
        
        info_rect = pygame.Rect(10, 100, self.rect.width - 20, 200)
        self.character_info_label = self._create_label(
            "error_info",
            f"装備管理の読み込み中にエラーが発生しました:\n\n{error_message}\n\n後でもう一度お試しください。",
            info_rect,
            container=self.container
        )
        
        # 戻るボタン
        back_rect = pygame.Rect(10, self.rect.height - 50, 100, 35)
        self.back_button = self._create_button(
            "back_button",
            "← 戻る",
            back_rect,
            container=self.container,
            object_id="#back_button"
        )
    
    def _show_character_equipment_detail(self, character_index: int) -> None:
        """キャラクターの装備詳細を表示"""
        try:
            party = self.controller.service.party
            characters = party.get_all_characters()
            
            if character_index >= len(characters):
                logger.warning(f"Invalid character index: {character_index}")
                return
                
            character = characters[character_index]
            self.selected_character_index = character_index
            
            # UIをクリア
            self.ui_element_manager.destroy_all()
            
            # キャラクター詳細UI作成
            self._create_character_detail_ui(character)
            
        except Exception as e:
            logger.error(f"Error showing character equipment detail: {e}")
    
    def _create_character_detail_ui(self, character) -> None:
        """キャラクター装備詳細のUI作成"""
        # タイトル（上部ナビゲーションとの重複を避ける）
        title_rect = pygame.Rect(10, 50, self.rect.width - 20, 40)
        title_text = f"{character.name} の装備"
        self._create_label(
            "character_detail_title",
            title_text,
            title_rect,
            container=self.container
        )
        
        # キャラクター基本情報
        info_rect = pygame.Rect(10, 100, self.rect.width - 20, 50)
        char_info = f"レベル: {character.level}  HP: {character.current_hp}/{character.max_hp}"
        self.character_info_label = self._create_label(
            "character_info",
            char_info,
            info_rect,
            container=self.container
        )
        
        # 装備情報
        equipment = character.get_equipment()
        equipment_text = "現在の装備:\n\n"
        
        # 装備スロットを表示
        from src.equipment.equipment import EquipmentSlot
        for slot in EquipmentSlot:
            equipped_item = equipment.get_equipped_item(slot)
            slot_name = slot.value  # スロット名
            item_name = equipped_item.name if equipped_item else "なし"
            equipment_text += f"{slot_name}: {item_name}\n"
        
        equipment_rect = pygame.Rect(10, 160, self.rect.width - 20, 200)
        self.equipment_info_label = self._create_label(
            "equipment_info",
            equipment_text,
            equipment_rect,
            container=self.container
        )
        
        # 戻るボタン
        back_rect = pygame.Rect(10, self.rect.height - 50, 100, 35)
        self.back_button = self._create_button(
            "back_to_list",
            "← 一覧に戻る",
            back_rect,
            container=self.container,
            object_id="#back_to_list"
        )
    
    def destroy(self) -> None:
        """パネルを破棄"""
        logger.info("EquipmentManagementPanel: Starting destroy process")
        
        # 特定のUI要素を明示的に破棄
        specific_elements = [
            self.back_button,
            self.character_info_label,
            self.equipment_info_label
        ] + self.character_buttons
        
        for element in specific_elements:
            if element and hasattr(element, 'kill'):
                try:
                    element.kill()
                    logger.debug(f"EquipmentManagementPanel: Destroyed element {type(element).__name__}")
                except Exception as e:
                    logger.warning(f"EquipmentManagementPanel: Failed to destroy {type(element).__name__}: {e}")
        
        # 親クラスのdestroy()を呼び出し
        super().destroy()
        
        # 参照をクリア
        self.character_buttons.clear()
        self.back_button = None
        self.character_info_label = None
        self.equipment_info_label = None
        self.selected_character_index = None
        
        logger.info("EquipmentManagementPanel: Destroy completed")
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        logger.info(f"EquipmentManagementPanel: Handling button click - object_id: {getattr(button, 'object_id', 'None')}")
        
        # 戻るボタン
        if button == self.back_button:
            logger.info("EquipmentManagementPanel: Back button clicked")
            if hasattr(button, 'object_id') and button.object_id == "#back_to_list":
                # キャラクター詳細から一覧に戻る
                logger.info("EquipmentManagementPanel: Returning to character list")
                self.selected_character_index = None
                self.ui_element_manager.destroy_all()
                self._create_ui()
                return True
            else:
                # 一覧から宿屋メインに戻る
                logger.info("EquipmentManagementPanel: Returning to inn main")
                if hasattr(self.parent, 'handle_back_action'):
                    self.parent.handle_back_action()
                return True
        
        # キャラクターボタン
        for i, char_button in enumerate(self.character_buttons):
            if button == char_button:
                logger.info(f"EquipmentManagementPanel: Character {i} button clicked")
                self._show_character_equipment_detail(i)
                return True
        
        logger.warning(f"EquipmentManagementPanel: Button click not recognized - button count: {len(self.character_buttons)}, back_button: {self.back_button is not None}")
        return False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        # 現在は親クラスの処理に委任
        return False
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        try:
            # UIを再作成（最新のパーティ情報を反映）
            if self.selected_character_index is None:
                # キャラクター一覧表示中
                self.ui_element_manager.destroy_all()
                self._create_ui()
            else:
                # キャラクター詳細表示中
                party = self.controller.service.party
                characters = party.get_all_characters()
                if self.selected_character_index < len(characters):
                    character = characters[self.selected_character_index]
                    self.ui_element_manager.destroy_all()
                    self._create_character_detail_ui(character)
                else:
                    # 無効なインデックス - 一覧に戻る
                    self.selected_character_index = None
                    self.ui_element_manager.destroy_all()
                    self._create_ui()
                    
            logger.debug("EquipmentManagementPanel: Refreshed UI")
        except Exception as e:
            logger.warning(f"EquipmentManagementPanel: Error refreshing UI: {e}")