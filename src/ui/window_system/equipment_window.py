"""
EquipmentWindow クラス

装備管理ウィンドウ
"""

import pygame
import pygame_gui
from typing import Dict, List, Any, Optional, Tuple

from .window import Window
from .equipment_types import (
    EquipmentSlotType, EquipmentConfig, EquipmentSlotInfo, EquipmentActionType, 
    CharacterStats, EquipmentLayout, EquipmentFilter, EquipmentAction,
    EquipmentComparison, EquipmentValidationResult
)
from src.utils.logger import logger


class EquipmentWindow(Window):
    """
    装備ウィンドウクラス
    
    装備の表示、管理、比較を行うウィンドウ
    """
    
    def __init__(self, window_id: str, equipment_config: Dict[str, Any], 
                 parent: Optional[Window] = None, modal: bool = False):
        """
        装備ウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            equipment_config: 装備設定辞書
            parent: 親ウィンドウ
            modal: モーダルウィンドウかどうか
        """
        super().__init__(window_id, parent, modal)
        
        # 設定の検証と変換
        self.equipment_config = self._validate_and_convert_config(equipment_config)
        
        # 装備情報
        self.character = self.equipment_config.character
        self.equipment_slots = self.equipment_config.equipment_slots
        self.inventory = self.equipment_config.inventory
        
        # 選択状態
        self.selected_slot: Optional[str] = None
        self.selected_item: Optional[Any] = None
        
        # フィルター
        self.current_filter: Optional[str] = None
        self.filter = EquipmentFilter()
        
        # 比較モード
        self.comparison_mode: bool = False
        self.comparison_item: Optional[Any] = None
        
        # レイアウト
        self.layout = self.equipment_config.layout
        
        # UI要素
        self.main_container: Optional[pygame_gui.core.UIElement] = None
        self.equipment_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.slot_buttons: List[pygame_gui.elements.UIButton] = []
        self.detail_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.stats_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.character_stats: Optional[CharacterStats] = None
        
        logger.debug(f"EquipmentWindowを初期化: {window_id}")
    
    def _validate_and_convert_config(self, config: Dict[str, Any]) -> EquipmentConfig:
        """設定を検証してEquipmentConfigに変換"""
        if 'character' not in config:
            raise ValueError("Equipment config must contain 'character'")
        if 'equipment_slots' not in config:
            raise ValueError("Equipment config must contain 'equipment_slots'")
        
        equipment_config = EquipmentConfig(
            character=config['character'],
            equipment_slots=config['equipment_slots'],
            inventory=config['inventory'],
            enable_comparison=config.get('enable_comparison', True),
            enable_quick_equip=config.get('enable_quick_equip', True),
            enable_auto_sort=config.get('enable_auto_sort', True),
            show_stat_preview=config.get('show_stat_preview', True),
            show_requirements=config.get('show_requirements', True)
        )
        
        equipment_config.validate()
        return equipment_config
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            self._initialize_ui_manager()
            self._calculate_layout()
            self._create_main_container()
            self._create_equipment_panel()
            self._create_stats_panel()
            self._create_detail_panel()
        
        logger.debug(f"EquipmentWindow UI要素を作成: {self.window_id}")
    
    def _initialize_ui_manager(self) -> None:
        """UIManagerを初期化"""
        screen_width = 1024
        screen_height = 768
        self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
    
    def _calculate_layout(self) -> None:
        """レイアウトを計算"""
        # ウィンドウサイズを計算
        window_width = max(self.layout.window_min_width, 
                          self.layout.detail_panel_width * 2 + self.layout.panel_padding * 3)
        window_height = max(self.layout.window_min_height,
                           self.layout.stats_panel_height + 400 + self.layout.panel_padding * 3)
        
        # 画面中央に配置
        screen_width = 1024
        screen_height = 768
        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2
        
        self.rect = pygame.Rect(window_x, window_y, window_width, window_height)
    
    def _create_main_container(self) -> None:
        """メインコンテナを作成"""
        self.main_container = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager
        )
    
    def _create_equipment_panel(self) -> None:
        """装備パネルを作成"""
        equipment_rect = pygame.Rect(
            self.layout.panel_padding,
            self.layout.panel_padding,
            self.rect.width - self.layout.detail_panel_width - self.layout.panel_padding * 3,
            self.rect.height - self.layout.stats_panel_height - self.layout.panel_padding * 3
        )
        
        self.equipment_panel = pygame_gui.elements.UIPanel(
            relative_rect=equipment_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
        
        self._create_slot_buttons()
    
    def _create_slot_buttons(self) -> None:
        """スロットボタンを作成"""
        self.slot_buttons = []
        
        if hasattr(self.equipment_slots, 'get_all_slots'):
            all_slots = self.equipment_slots.get_all_slots()
            
            # all_slotsが辞書である場合のみ処理
            if hasattr(all_slots, 'items'):
                for slot_type, slot_info in all_slots.items():
                    position = self.layout.calculate_slot_position(EquipmentSlotType(slot_type))
                    
                    slot_rect = pygame.Rect(
                        position[0], position[1], 
                        self.layout.slot_size, self.layout.slot_size
                    )
                    
                    # ボタンテキストを作成
                    button_text = ""
                    if hasattr(slot_info, 'item') and slot_info.item:
                        if hasattr(slot_info.item, 'name'):
                            button_text = slot_info.item.name[:4]
                    
                    slot_button = pygame_gui.elements.UIButton(
                        relative_rect=slot_rect,
                        text=button_text,
                        manager=self.ui_manager,
                        container=self.equipment_panel
                    )
                    
                    self.slot_buttons.append(slot_button)
    
    def _create_stats_panel(self) -> None:
        """統計パネルを作成"""
        stats_rect = pygame.Rect(
            self.layout.panel_padding,
            self.rect.height - self.layout.stats_panel_height - self.layout.panel_padding,
            self.rect.width - self.layout.detail_panel_width - self.layout.panel_padding * 3,
            self.layout.stats_panel_height
        )
        
        self.stats_panel = pygame_gui.elements.UIPanel(
            relative_rect=stats_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
        
        self._update_character_stats()
    
    def _update_character_stats(self) -> None:
        """キャラクター統計を更新"""
        if hasattr(self.character, 'get_total_stats'):
            total_stats = self.character.get_total_stats()
            self.character_stats = CharacterStats(
                total_stats=total_stats
            )
    
    def _create_detail_panel(self) -> None:
        """詳細パネルを作成"""
        detail_rect = pygame.Rect(
            self.rect.width - self.layout.detail_panel_width - self.layout.panel_padding,
            self.layout.panel_padding,
            self.layout.detail_panel_width,
            self.rect.height - self.layout.panel_padding * 2
        )
        
        self.detail_panel = pygame_gui.elements.UIPanel(
            relative_rect=detail_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
    
    def select_equipment_slot(self, slot_type: str) -> bool:
        """装備スロットを選択"""
        if hasattr(self.equipment_slots, 'get_slot'):
            slot = self.equipment_slots.get_slot(slot_type)
            if slot:
                self.selected_slot = slot_type
                self._update_detail_display()
                return True
        return False
    
    def _update_detail_display(self) -> None:
        """詳細表示を更新"""
        # 詳細表示の更新（実装省略）
        pass
    
    def equip_selected_item(self) -> bool:
        """選択されたアイテムを装備"""
        if not self.selected_item or not self.selected_slot:
            return False
        
        if hasattr(self.equipment_slots, 'can_equip'):
            if self.equipment_slots.can_equip(self.selected_item, self.selected_slot):
                self.send_message('item_equipped', {
                    'item_id': getattr(self.selected_item, 'item_id', None),
                    'slot_type': self.selected_slot,
                    'character_id': self.character
                })
                
                logger.debug(f"アイテム装備: {self.selected_item} -> {self.selected_slot}")
                return True
        
        return False
    
    def change_equipment_slot(self, from_slot: str, to_slot: str) -> bool:
        """装備スロット変更"""
        if hasattr(self.equipment_slots, 'swap_equipment'):
            self.equipment_slots.swap_equipment(from_slot, to_slot)
            logger.debug(f"装備スロット変更: {from_slot} -> {to_slot}")
            return True
        return False
    
    def start_comparison_mode(self, slot_type: str, new_item: Any) -> bool:
        """比較モードを開始"""
        if not self.equipment_config.enable_comparison:
            return False
        
        self.comparison_mode = True
        self.comparison_item = new_item
        self.selected_slot = slot_type
        
        logger.debug(f"比較モード開始: {slot_type} with {new_item}")
        return True
    
    def filter_by_slot_type(self, slot_type: str) -> bool:
        """スロットタイプによるフィルタリング"""
        self.current_filter = slot_type
        self.filter.slot_type = EquipmentSlotType(slot_type)
        self._apply_filter()
        
        logger.debug(f"スロットタイプフィルター: {slot_type}")
        return True
    
    def _apply_filter(self) -> None:
        """フィルターを適用"""
        # フィルター適用処理（実装省略）
        pass
    
    def get_filtered_items(self) -> List[Any]:
        """フィルター適用後のアイテム一覧を取得"""
        if hasattr(self.inventory, 'get_items_by_category'):
            all_items = self.inventory.get_items_by_category('equipment')
            return [item for item in all_items if self.filter.matches_item(item)]
        return []
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if not self.ui_manager:
            return False
        
        # pygame-guiにイベントを渡す
        self.ui_manager.process_events(event)
        
        # キーボードイベント
        if event.type == pygame.KEYDOWN:
            return self._handle_keyboard_event(event)
        
        return False
    
    def _handle_keyboard_event(self, event) -> bool:
        """キーボードイベントを処理"""
        if event.key == pygame.K_TAB:
            return self._move_to_next_slot()
        
        return False
    
    def _move_to_next_slot(self) -> bool:
        """次のスロットに移動"""
        if hasattr(self.equipment_slots, 'get_all_slots'):
            all_slots = list(self.equipment_slots.get_all_slots().keys())
            if self.selected_slot in all_slots:
                current_index = all_slots.index(self.selected_slot)
                next_index = (current_index + 1) % len(all_slots)
                self.selected_slot = all_slots[next_index]
                return True
        return False
    
    def quick_equip_item(self, item: Any) -> bool:
        """クイック装備"""
        if not self.equipment_config.enable_quick_equip:
            return False
        
        if hasattr(item, 'equipment_slot'):
            slot_type = item.equipment_slot
            if hasattr(self.equipment_slots, 'can_equip'):
                if self.equipment_slots.can_equip(item, slot_type):
                    self.send_message('item_quick_equipped', {
                        'item_id': getattr(item, 'item_id', None),
                        'slot_type': slot_type
                    })
                    
                    logger.debug(f"クイック装備: {item}")
                    return True
        
        return False
    
    def handle_escape(self) -> bool:
        """ESCキーの処理"""
        self.send_message('equipment_close_requested', {
            'character_id': self.character
        })
        
        logger.debug(f"装備ウィンドウ閉じるリクエスト")
        return True
    
    def can_equip_item(self, item: Any) -> bool:
        """アイテムが装備可能かチェック"""
        if not item:
            return False
        
        # レベル制限チェック
        if hasattr(item, 'required_level') and hasattr(self.character, 'level'):
            if self.character.level < item.required_level:
                return False
        
        return True
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # ボタンリストをクリア
        self.slot_buttons.clear()
        
        # UI要素をクリア
        self.equipment_panel = None
        self.detail_panel = None
        self.stats_panel = None
        
        # pygame-guiの要素を削除
        if self.ui_manager:
            for element in list(self.ui_manager.get_root_container().elements):
                element.kill()
            self.ui_manager = None
        
        logger.debug(f"EquipmentWindow UI要素をクリーンアップ: {self.window_id}")


# EquipmentSlotTypeを直接エクスポート
from .equipment_types import EquipmentSlotType