"""
InventoryWindow クラス

インベントリ管理ウィンドウ
"""

import pygame
import pygame_gui
from typing import Dict, List, Any, Optional, Tuple

from .window import Window
from .inventory_types import (
    InventoryType, InventoryConfig, ItemSlotInfo, ItemCategory, 
    ItemActionType, InventoryStats, InventoryLayout, InventoryFilter,
    QuickSlotAssignment, ItemAction
)
from src.utils.logger import logger


class InventoryWindow(Window):
    """
    インベントリウィンドウクラス
    
    アイテムの表示、管理、操作を行うウィンドウ
    """
    
    def __init__(self, window_id: str, inventory_config: Dict[str, Any], 
                 parent: Optional[Window] = None, modal: bool = False):
        """
        インベントリウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            inventory_config: インベントリ設定辞書
            parent: 親ウィンドウ
            modal: モーダルウィンドウかどうか
        """
        super().__init__(window_id, parent, modal)
        
        # 設定の検証と変換
        self.inventory_config = self._validate_and_convert_config(inventory_config)
        
        # インベントリ情報
        self.inventory_type = InventoryType(self.inventory_config.inventory_type)
        self.inventory = self.inventory_config.inventory
        self.character = self.inventory_config.character
        self.party = self.inventory_config.party
        
        # 選択状態
        self.selected_slot_index: Optional[int] = None
        self.dragging_slot_index: Optional[int] = None
        
        # フィルター
        self.current_filter = ItemCategory.ALL
        self.filter = InventoryFilter()
        
        # クイックスロット
        self.quick_slots: Dict[int, int] = {}  # quick_slot_index -> inventory_slot_index
        
        # レイアウト
        self.layout = InventoryLayout()
        
        # UI要素
        self.main_container: Optional[pygame_gui.core.UIElement] = None
        self.item_grid: Optional[pygame_gui.core.UIElement] = None
        self.slot_buttons: List[pygame_gui.elements.UIButton] = []
        self.detail_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.stats_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.action_buttons: Dict[ItemActionType, pygame_gui.elements.UIButton] = {}
        
        logger.debug(f"InventoryWindowを初期化: {window_id}, {self.inventory_type}")
    
    def _validate_and_convert_config(self, config: Dict[str, Any]) -> InventoryConfig:
        """設定を検証してInventoryConfigに変換"""
        if 'inventory_type' not in config:
            raise ValueError("Inventory config must contain 'inventory_type'")
        if 'inventory' not in config:
            raise ValueError("Inventory config must contain 'inventory'")
        
        inventory_config = InventoryConfig(
            inventory_type=config['inventory_type'],
            inventory=config['inventory'],
            character=config.get('character'),
            party=config.get('party'),
            weight_limit=config.get('weight_limit'),
            allow_sorting=config.get('allow_sorting', True),
            allow_dropping=config.get('allow_dropping', True),
            enable_filtering=config.get('enable_filtering', True),
            enable_quick_slots=config.get('enable_quick_slots', False),
            quick_slot_count=config.get('quick_slot_count', 4),
            columns_per_row=config.get('columns_per_row', 5),
            show_weight=config.get('show_weight', True),
            show_value=config.get('show_value', True),
            show_item_count=config.get('show_item_count', True),
            target_inventory=config.get('target_inventory')
        )
        
        inventory_config.validate()
        return inventory_config
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            self._initialize_ui_manager()
            self._calculate_layout()
            self._create_main_container()
            self._create_stats_panel()
            self._create_item_grid()
            self._create_detail_panel()
            self._create_action_buttons()
            if self.inventory_config.enable_quick_slots:
                self._create_quick_slots()
            if self.inventory_config.enable_filtering:
                self._create_filter_controls()
        
        logger.debug(f"InventoryWindow UI要素を作成: {self.window_id}")
    
    def _initialize_ui_manager(self) -> None:
        """UIManagerを初期化"""
        screen_width = 1024
        screen_height = 768
        self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
    
    def _calculate_layout(self) -> None:
        """レイアウトを計算"""
        # インベントリスロット数に応じてウィンドウサイズを調整
        total_slots = self.inventory.capacity if hasattr(self.inventory, 'capacity') else len(self.inventory.slots)
        columns, rows = self.layout.calculate_grid_size(total_slots, self.inventory_config.columns_per_row)
        
        # グリッドサイズからウィンドウサイズを計算
        grid_width = columns * (self.layout.slot_size + self.layout.slot_spacing) + self.layout.grid_padding * 2
        grid_height = rows * (self.layout.slot_size + self.layout.slot_spacing) + self.layout.grid_padding * 2
        
        # 詳細パネルを含めた全体サイズ
        window_width = grid_width + self.layout.detail_panel_width + self.layout.grid_padding
        window_height = max(self.layout.window_height, 
                           grid_height + self.layout.stats_panel_height + self.layout.grid_padding * 2)
        
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
    
    def _create_stats_panel(self) -> None:
        """統計パネルを作成"""
        stats_rect = pygame.Rect(
            self.layout.grid_padding,
            self.layout.grid_padding,
            self.rect.width - self.layout.detail_panel_width - self.layout.grid_padding * 3,
            self.layout.stats_panel_height
        )
        
        self.stats_panel = pygame_gui.elements.UIPanel(
            relative_rect=stats_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
        
        self._update_stats_display()
    
    def _update_stats_display(self) -> None:
        """統計表示を更新"""
        if not self.stats_panel:
            return
        
        stats = self._calculate_inventory_stats()
        
        # 統計情報テキストを作成
        info_lines = []
        info_lines.append(f"アイテム数: {stats.used_slots}/{stats.total_slots}")
        
        if self.inventory_config.show_weight:
            weight_text = f"重量: {stats.total_weight:.1f}"
            if stats.weight_limit:
                weight_text += f"/{stats.weight_limit:.1f}"
                if stats.is_overweight:
                    weight_text += " (超過！)"
            info_lines.append(weight_text)
        
        if self.inventory_config.show_value:
            info_lines.append(f"総価値: {stats.total_value}G")
        
        info_text = " | ".join(info_lines)
        
        # 統計ラベルを作成
        stats_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 
                                     self.stats_panel.relative_rect.width - 20,
                                     self.stats_panel.relative_rect.height - 20),
            text=info_text,
            manager=self.ui_manager,
            container=self.stats_panel
        )
    
    def _calculate_inventory_stats(self) -> InventoryStats:
        """インベントリ統計を計算"""
        total_items = 0
        total_weight = 0.0
        total_value = 0
        used_slots = 0
        
        if hasattr(self.inventory, 'slots'):
            for slot in self.inventory.slots:
                if hasattr(slot, 'item') and slot.item:
                    used_slots += 1
                    quantity = getattr(slot, 'quantity', 1)
                    total_items += quantity
                    
                    if hasattr(slot.item, 'weight'):
                        total_weight += slot.item.weight * quantity
                    if hasattr(slot.item, 'value'):
                        total_value += slot.item.value * quantity
        
        total_slots = self.inventory.capacity if hasattr(self.inventory, 'capacity') else len(self.inventory.slots)
        
        return InventoryStats(
            total_items=total_items,
            total_weight=total_weight,
            total_value=total_value,
            used_slots=used_slots,
            total_slots=total_slots,
            weight_limit=self.inventory_config.weight_limit
        )
    
    def _create_item_grid(self) -> None:
        """アイテムグリッドを作成"""
        grid_rect = pygame.Rect(
            self.layout.grid_padding,
            self.layout.grid_padding + self.layout.stats_panel_height + self.layout.grid_padding,
            self.rect.width - self.layout.detail_panel_width - self.layout.grid_padding * 3,
            self.rect.height - self.layout.stats_panel_height - self.layout.grid_padding * 3
        )
        
        self.item_grid = pygame_gui.elements.UIPanel(
            relative_rect=grid_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
        
        self._create_slot_buttons()
    
    def _create_slot_buttons(self) -> None:
        """スロットボタンを作成"""
        self.slot_buttons = []
        
        total_slots = self.inventory.capacity if hasattr(self.inventory, 'capacity') else len(self.inventory.slots)
        
        for i in range(total_slots):
            x, y = self.layout.calculate_grid_position(i, self.inventory_config.columns_per_row)
            
            slot_rect = pygame.Rect(x, y, self.layout.slot_size, self.layout.slot_size)
            
            # スロット情報を取得
            slot_info = self._get_slot_info(i)
            
            # ボタンテキストを作成
            button_text = ""
            if slot_info.item:
                button_text = slot_info.item.name[:4] if hasattr(slot_info.item, 'name') else "?"
                if slot_info.quantity > 1:
                    button_text += f"\n{slot_info.quantity}"
            
            slot_button = pygame_gui.elements.UIButton(
                relative_rect=slot_rect,
                text=button_text,
                manager=self.ui_manager,
                container=self.item_grid
            )
            
            self.slot_buttons.append(slot_button)
    
    def _get_slot_info(self, slot_index: int) -> ItemSlotInfo:
        """スロット情報を取得"""
        if hasattr(self.inventory, 'slots') and slot_index < len(self.inventory.slots):
            slot = self.inventory.slots[slot_index]
            return ItemSlotInfo(
                slot_index=slot_index,
                item=getattr(slot, 'item', None),
                quantity=getattr(slot, 'quantity', 0),
                is_equipped=getattr(slot, 'is_equipped', False),
                is_locked=getattr(slot, 'is_locked', False)
            )
        
        return ItemSlotInfo(slot_index=slot_index, item=None)
    
    def _create_detail_panel(self) -> None:
        """詳細パネルを作成"""
        detail_rect = pygame.Rect(
            self.rect.width - self.layout.detail_panel_width - self.layout.grid_padding,
            self.layout.grid_padding,
            self.layout.detail_panel_width,
            self.rect.height - self.layout.grid_padding * 2
        )
        
        self.detail_panel = pygame_gui.elements.UIPanel(
            relative_rect=detail_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
    
    def _create_action_buttons(self) -> None:
        """アクションボタンを作成"""
        # 利用可能なアクションを決定
        actions = self._get_available_actions()
        
        button_y = self.detail_panel.relative_rect.height - (len(actions) * (self.layout.action_button_height + 5)) - 10
        
        for i, action in enumerate(actions):
            button_rect = pygame.Rect(
                10,
                button_y + i * (self.layout.action_button_height + 5),
                self.layout.detail_panel_width - 20,
                self.layout.action_button_height
            )
            
            action_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=action.label,
                manager=self.ui_manager,
                container=self.detail_panel
            )
            
            self.action_buttons[action.action_type] = action_button
    
    def _get_available_actions(self) -> List[ItemAction]:
        """利用可能なアクションを取得"""
        actions = []
        
        # 基本アクション
        actions.append(ItemAction(ItemActionType.USE, "使用"))
        actions.append(ItemAction(ItemActionType.EQUIP, "装備"))
        actions.append(ItemAction(ItemActionType.EXAMINE, "調べる"))
        
        if self.inventory_config.allow_dropping:
            actions.append(ItemAction(ItemActionType.DROP, "捨てる", confirm_required=True))
        
        if self.inventory_config.target_inventory:
            actions.append(ItemAction(ItemActionType.TRANSFER, "転送", requires_target=True))
        
        return actions
    
    def _create_quick_slots(self) -> None:
        """クイックスロットを作成"""
        # クイックスロットUIの作成（実装省略）
        pass
    
    def _create_filter_controls(self) -> None:
        """フィルターコントロールを作成"""
        # フィルターUIの作成（実装省略）
        pass
    
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
        if self.selected_slot_index is not None:
            if event.key == pygame.K_RIGHT:
                return self._move_selection(1, 0)
            elif event.key == pygame.K_LEFT:
                return self._move_selection(-1, 0)
            elif event.key == pygame.K_DOWN:
                return self._move_selection(0, 1)
            elif event.key == pygame.K_UP:
                return self._move_selection(0, -1)
            elif event.key == pygame.K_RETURN:
                return self._activate_selected_slot()
        else:
            # 最初の選択
            if event.key in [pygame.K_RIGHT, pygame.K_LEFT, pygame.K_DOWN, pygame.K_UP]:
                self.selected_slot_index = 0
                self._update_selection_display()
                return True
        
        return False
    
    def _handle_button_click(self, event) -> bool:
        """ボタンクリックを処理"""
        # スロットボタンのクリック
        for i, button in enumerate(self.slot_buttons):
            if event.ui_element == button:
                return self.select_item_slot(i)
        
        # アクションボタンのクリック
        for action_type, button in self.action_buttons.items():
            if event.ui_element == button:
                return self._handle_action(action_type)
        
        return False
    
    def _move_selection(self, dx: int, dy: int) -> bool:
        """選択を移動"""
        if self.selected_slot_index is None:
            return False
        
        columns = self.inventory_config.columns_per_row
        total_slots = len(self.slot_buttons)
        
        # 現在の位置
        current_row = self.selected_slot_index // columns
        current_col = self.selected_slot_index % columns
        
        # 新しい位置
        new_col = current_col + dx
        new_row = current_row + dy
        
        # 境界チェック
        if new_col < 0 or new_col >= columns:
            return False
        if new_row < 0:
            return False
        
        new_index = new_row * columns + new_col
        if new_index >= total_slots:
            return False
        
        self.selected_slot_index = new_index
        self._update_selection_display()
        return True
    
    def _activate_selected_slot(self) -> bool:
        """選択されたスロットをアクティベート"""
        if self.selected_slot_index is not None:
            slot_info = self._get_slot_info(self.selected_slot_index)
            if slot_info.item:
                return self.use_selected_item()
        return False
    
    def select_item_slot(self, slot_index: int) -> bool:
        """アイテムスロットを選択"""
        if 0 <= slot_index < len(self.slot_buttons):
            self.selected_slot_index = slot_index
            self._update_selection_display()
            self._update_detail_display()
            return True
        return False
    
    def _update_selection_display(self) -> None:
        """選択表示を更新"""
        for i, button in enumerate(self.slot_buttons):
            if i == self.selected_slot_index:
                # 選択状態の表示（実装省略）
                pass
            else:
                # 非選択状態の表示（実装省略）
                pass
    
    def _update_detail_display(self) -> None:
        """詳細表示を更新"""
        if self.selected_slot_index is None:
            return
        
        slot_info = self._get_slot_info(self.selected_slot_index)
        if not slot_info.item:
            # 空スロットの表示
            return
        
        # アイテム詳細の表示（実装省略）
    
    def _handle_action(self, action_type: ItemActionType) -> bool:
        """アクションを処理"""
        if action_type == ItemActionType.USE:
            return self.use_selected_item()
        elif action_type == ItemActionType.EQUIP:
            return self._equip_selected_item()
        elif action_type == ItemActionType.DROP:
            return self._drop_selected_item()
        elif action_type == ItemActionType.TRANSFER:
            return self.transfer_selected_item()
        elif action_type == ItemActionType.EXAMINE:
            return self._examine_selected_item()
        
        return False
    
    def use_selected_item(self) -> bool:
        """選択されたアイテムを使用"""
        if self.selected_slot_index is None:
            return False
        
        slot_info = self._get_slot_info(self.selected_slot_index)
        if not slot_info.item:
            return False
        
        # 使用可能かチェック
        if hasattr(slot_info.item, 'is_consumable') and slot_info.item.is_consumable():
            self.send_message('item_used', {
                'item_id': getattr(slot_info.item, 'item_id', None),
                'inventory_type': self.inventory_type.value,
                'slot_index': self.selected_slot_index
            })
            
            logger.debug(f"アイテム使用: スロット {self.selected_slot_index}")
            return True
        
        return False
    
    def _equip_selected_item(self) -> bool:
        """選択されたアイテムを装備"""
        # 装備処理（実装省略）
        return False
    
    def _drop_selected_item(self) -> bool:
        """選択されたアイテムを捨てる"""
        # 破棄処理（実装省略）
        return False
    
    def _examine_selected_item(self) -> bool:
        """選択されたアイテムを調べる"""
        # 調査処理（実装省略）
        return False
    
    def move_item(self, from_slot: int, to_slot: int) -> bool:
        """アイテムを移動"""
        if hasattr(self.inventory, 'can_move_item') and self.inventory.can_move_item(from_slot, to_slot):
            self.inventory.move_item(from_slot, to_slot)
            self._refresh_display()
            
            logger.debug(f"アイテム移動: {from_slot} -> {to_slot}")
            return True
        
        return False
    
    def sort_items(self) -> bool:
        """アイテムをソート"""
        if not self.inventory_config.allow_sorting:
            return False
        
        if hasattr(self.inventory, 'sort_items'):
            self.inventory.sort_items()
            self._refresh_display()
            
            self.send_message('inventory_sorted', {
                'inventory_type': self.inventory_type.value
            })
            
            logger.debug("インベントリをソート")
            return True
        
        return False
    
    def set_filter(self, category: str) -> bool:
        """フィルターを設定"""
        if not self.inventory_config.enable_filtering:
            return False
        
        try:
            self.current_filter = category
            self.filter.category = ItemCategory(category) if category != 'all' else ItemCategory.ALL
            self._apply_filter()
            
            logger.debug(f"フィルター設定: {category}")
            return True
        except ValueError:
            return False
    
    def _apply_filter(self) -> None:
        """フィルターを適用"""
        # フィルター適用処理（実装省略）
        pass
    
    def assign_to_quick_slot(self, slot_index: int, quick_slot_index: int) -> bool:
        """クイックスロットに割り当て"""
        if not self.inventory_config.enable_quick_slots:
            return False
        
        if 0 <= quick_slot_index < self.inventory_config.quick_slot_count:
            self.quick_slots[quick_slot_index] = slot_index
            
            logger.debug(f"クイックスロット割り当て: スロット {slot_index} -> クイックスロット {quick_slot_index}")
            return True
        
        return False
    
    def transfer_selected_item(self) -> bool:
        """選択されたアイテムを転送"""
        if self.selected_slot_index is None:
            return False
        
        if not self.inventory_config.target_inventory:
            return False
        
        slot_info = self._get_slot_info(self.selected_slot_index)
        if not slot_info.item:
            return False
        
        # 転送可能かチェック
        if hasattr(self.inventory_config.target_inventory, 'can_add_item'):
            if self.inventory_config.target_inventory.can_add_item(slot_info.item):
                self.send_message('item_transfer_requested', {
                    'item_id': getattr(slot_info.item, 'item_id', None),
                    'source_inventory': self.inventory_type.value,
                    'target_inventory': 'target',
                    'slot_index': self.selected_slot_index
                })
                
                logger.debug(f"アイテム転送リクエスト: スロット {self.selected_slot_index}")
                return True
        
        return False
    
    def handle_escape(self) -> bool:
        """ESCキーの処理"""
        self.send_message('inventory_close_requested', {
            'inventory_type': self.inventory_type.value
        })
        
        logger.debug(f"インベントリ閉じるリクエスト: {self.inventory_type}")
        return True
    
    def _refresh_display(self) -> None:
        """表示を更新"""
        # ボタンテキストを更新
        for i, button in enumerate(self.slot_buttons):
            slot_info = self._get_slot_info(i)
            
            button_text = ""
            if slot_info.item:
                button_text = slot_info.item.name[:4] if hasattr(slot_info.item, 'name') else "?"
                if slot_info.quantity > 1:
                    button_text += f"\n{slot_info.quantity}"
            
            button.set_text(button_text)
        
        # 統計を更新
        self._update_stats_display()
        
        # 詳細を更新
        if self.selected_slot_index is not None:
            self._update_detail_display()
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # ボタンリストをクリア
        self.slot_buttons.clear()
        self.action_buttons.clear()
        
        # UI要素をクリア
        self.item_grid = None
        self.detail_panel = None
        self.stats_panel = None
        
        # pygame-guiの要素を削除
        if self.ui_manager:
            for element in list(self.ui_manager.get_root_container().elements):
                element.kill()
            self.ui_manager = None
        
        logger.debug(f"InventoryWindow UI要素をクリーンアップ: {self.window_id}")