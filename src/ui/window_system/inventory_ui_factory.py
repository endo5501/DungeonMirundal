"""
InventoryUIFactory クラス

インベントリUI要素作成ファクトリー

Fowler式リファクタリング：Extract Class パターン
"""

import pygame
import pygame_gui
from typing import Dict, List, Any, Optional, Tuple
from src.ui.window_system.inventory_types import (
    InventoryType, ItemSlotInfo, ItemCategory, ItemAction, 
    InventoryStats, InventoryLayout
)
from src.utils.logger import logger


class InventoryUIFactory:
    """
    インベントリUI要素作成ファクトリークラス
    
    UI要素の作成、レイアウト、スタイリングを担当
    """
    
    def __init__(self, layout: InventoryLayout):
        """
        UI ファクトリーを初期化
        
        Args:
            layout: インベントリレイアウト設定
        """
        self.layout = layout
        logger.debug("InventoryUIFactoryを初期化")
    
    def calculate_window_layout(self, total_slots: int, columns_per_row: int, 
                              show_weight: bool = True, show_value: bool = True) -> pygame.Rect:
        """ウィンドウレイアウトを計算"""
        columns, rows = self.layout.calculate_grid_size(total_slots, columns_per_row)
        
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
        
        rect = pygame.Rect(window_x, window_y, window_width, window_height)
        logger.debug(f"ウィンドウレイアウト計算: {rect}")
        
        return rect
    
    def create_main_container(self, rect: pygame.Rect, ui_manager: pygame_gui.UIManager) -> pygame_gui.elements.UIPanel:
        """メインコンテナを作成"""
        container = pygame_gui.elements.UIPanel(
            relative_rect=rect,
            manager=ui_manager
        )
        
        logger.debug(f"メインコンテナ作成: {rect}")
        return container
    
    def create_stats_panel(self, window_rect: pygame.Rect, detail_panel_width: int,
                          container: pygame_gui.elements.UIPanel,
                          ui_manager: pygame_gui.UIManager) -> pygame_gui.elements.UIPanel:
        """統計パネルを作成"""
        stats_rect = pygame.Rect(
            self.layout.grid_padding,
            self.layout.grid_padding,
            window_rect.width - detail_panel_width - self.layout.grid_padding * 3,
            self.layout.stats_panel_height
        )
        
        stats_panel = pygame_gui.elements.UIPanel(
            relative_rect=stats_rect,
            manager=ui_manager,
            container=container
        )
        
        logger.debug("統計パネル作成")
        return stats_panel
    
    def create_stats_display(self, stats: InventoryStats, panel: pygame_gui.elements.UIPanel,
                           ui_manager: pygame_gui.UIManager, show_weight: bool = True, 
                           show_value: bool = True) -> pygame_gui.elements.UILabel:
        """統計表示を作成"""
        # 統計情報テキストを作成
        info_lines = []
        info_lines.append(f"アイテム数: {stats.used_slots}/{stats.total_slots}")
        
        if show_weight:
            weight_text = f"重量: {stats.total_weight:.1f}"
            if stats.weight_limit:
                weight_text += f"/{stats.weight_limit:.1f}"
                if stats.is_overweight:
                    weight_text += " (超過！)"
            info_lines.append(weight_text)
        
        if show_value:
            info_lines.append(f"総価値: {stats.total_value}G")
        
        info_text = " | ".join(info_lines)
        
        # 統計ラベルを作成
        stats_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 
                                     panel.relative_rect.width - 20,
                                     panel.relative_rect.height - 20),
            text=info_text,
            manager=ui_manager,
            container=panel
        )
        
        logger.debug("統計表示作成")
        return stats_label
    
    def create_item_grid(self, window_rect: pygame.Rect, detail_panel_width: int,
                        container: pygame_gui.elements.UIPanel,
                        ui_manager: pygame_gui.UIManager) -> pygame_gui.elements.UIPanel:
        """アイテムグリッドを作成"""
        grid_rect = pygame.Rect(
            self.layout.grid_padding,
            self.layout.grid_padding + self.layout.stats_panel_height + self.layout.grid_padding,
            window_rect.width - detail_panel_width - self.layout.grid_padding * 3,
            window_rect.height - self.layout.stats_panel_height - self.layout.grid_padding * 3
        )
        
        item_grid = pygame_gui.elements.UIPanel(
            relative_rect=grid_rect,
            manager=ui_manager,
            container=container
        )
        
        logger.debug("アイテムグリッド作成")
        return item_grid
    
    def create_slot_buttons(self, total_slots: int, columns_per_row: int,
                          inventory_manager: Any, grid_container: pygame_gui.elements.UIPanel,
                          ui_manager: pygame_gui.UIManager) -> List[pygame_gui.elements.UIButton]:
        """スロットボタンを作成"""
        slot_buttons = []
        
        for i in range(total_slots):
            x, y = self.layout.calculate_grid_position(i, columns_per_row)
            
            slot_rect = pygame.Rect(x, y, self.layout.slot_size, self.layout.slot_size)
            
            # スロット情報を取得
            slot_info = inventory_manager.get_slot_info(i)
            
            # ボタンテキストを作成
            button_text = self._create_slot_button_text(slot_info)
            
            slot_button = pygame_gui.elements.UIButton(
                relative_rect=slot_rect,
                text=button_text,
                manager=ui_manager,
                container=grid_container
            )
            
            # スロットの状態に応じてスタイリング
            self._apply_slot_styling(slot_button, slot_info)
            
            slot_buttons.append(slot_button)
        
        logger.debug(f"スロットボタン作成: {len(slot_buttons)}個")
        return slot_buttons
    
    def _create_slot_button_text(self, slot_info: ItemSlotInfo) -> str:
        """スロットボタンのテキストを作成"""
        if not slot_info.item:
            return ""
        
        # アイテム名（短縮）
        button_text = ""
        if hasattr(slot_info.item, 'name'):
            item_name = slot_info.item.name
            button_text = item_name[:4] if len(item_name) > 4 else item_name
        else:
            button_text = "?"
        
        # 数量表示
        if slot_info.quantity > 1:
            button_text += f"\\n{slot_info.quantity}"
        
        # 装備状態表示
        if slot_info.is_equipped:
            button_text = "[E]" + button_text
        
        # クイックスロット表示
        if slot_info.is_quick_slot and slot_info.quick_slot_index is not None:
            button_text = f"Q{slot_info.quick_slot_index + 1}:" + button_text
        
        return button_text
    
    def _apply_slot_styling(self, button: pygame_gui.elements.UIButton, slot_info: ItemSlotInfo) -> None:
        """スロットのスタイリングを適用"""
        # 装備中のアイテムは背景色を変更
        if slot_info.is_equipped:
            # 装備中スタイル（実装省略）
            pass
        
        # ロックされたアイテムは色を変更
        if slot_info.is_locked:
            # ロックスタイル（実装省略）
            pass
        
        # クイックスロットは枠を表示
        if slot_info.is_quick_slot:
            # クイックスロットスタイル（実装省略）
            pass
    
    def update_slot_button(self, button: pygame_gui.elements.UIButton, slot_info: ItemSlotInfo) -> None:
        """スロットボタンを更新"""
        button_text = self._create_slot_button_text(slot_info)
        button.set_text(button_text)
        self._apply_slot_styling(button, slot_info)
    
    def apply_selection_highlighting(self, buttons: List[pygame_gui.elements.UIButton],
                                   selected_index: Optional[int]) -> None:
        """選択ハイライトを適用"""
        for i, button in enumerate(buttons):
            text = button.text
            
            if i == selected_index:
                if not text.startswith(">>> "):
                    button.set_text(f">>> {text}")
            else:
                if text.startswith(">>> "):
                    button.set_text(text[4:])
        
        if selected_index is not None:
            logger.debug(f"選択ハイライト適用: インデックス {selected_index}")
    
    def create_detail_panel(self, window_rect: pygame.Rect, container: pygame_gui.elements.UIPanel,
                          ui_manager: pygame_gui.UIManager) -> pygame_gui.elements.UIPanel:
        """詳細パネルを作成"""
        detail_rect = pygame.Rect(
            window_rect.width - self.layout.detail_panel_width - self.layout.grid_padding,
            self.layout.grid_padding,
            self.layout.detail_panel_width,
            window_rect.height - self.layout.grid_padding * 2
        )
        
        detail_panel = pygame_gui.elements.UIPanel(
            relative_rect=detail_rect,
            manager=ui_manager,
            container=container
        )
        
        logger.debug("詳細パネル作成")
        return detail_panel
    
    def create_item_detail_display(self, slot_info: ItemSlotInfo, panel: pygame_gui.elements.UIPanel,
                                 ui_manager: pygame_gui.UIManager) -> Optional[pygame_gui.elements.UITextBox]:
        """アイテム詳細表示を作成"""
        if not slot_info.item:
            return None
        
        # アイテム詳細情報を作成
        detail_lines = []
        
        # 基本情報
        if hasattr(slot_info.item, 'name'):
            detail_lines.append(f"<b>{slot_info.item.name}</b>")
        
        if hasattr(slot_info.item, 'description'):
            detail_lines.append(slot_info.item.description)
        
        detail_lines.append("")  # 空行
        
        # 数量
        if slot_info.quantity > 1:
            detail_lines.append(f"数量: {slot_info.quantity}")
        
        # 重量
        if hasattr(slot_info.item, 'weight'):
            detail_lines.append(f"重量: {slot_info.item.weight:.1f}")
        
        # 価値
        if hasattr(slot_info.item, 'value'):
            detail_lines.append(f"価値: {slot_info.item.value}G")
        
        # カテゴリ
        if hasattr(slot_info.item, 'category'):
            detail_lines.append(f"分類: {slot_info.item.category}")
        
        # 装備状態
        if slot_info.is_equipped:
            detail_lines.append("<font color='#00FF00'>装備中</font>")
        
        # ロック状態
        if slot_info.is_locked:
            detail_lines.append("<font color='#FF0000'>ロック中</font>")
        
        detail_text = "<br>".join(detail_lines)
        
        # 詳細テキストボックスを作成
        detail_display = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(10, 10, 
                                     panel.relative_rect.width - 20,
                                     panel.relative_rect.height // 2 - 20),
            html_text=detail_text,
            manager=ui_manager,
            container=panel
        )
        
        logger.debug("アイテム詳細表示作成")
        return detail_display
    
    def create_action_buttons(self, actions: List[ItemAction], panel: pygame_gui.elements.UIPanel,
                            ui_manager: pygame_gui.UIManager) -> Dict[str, pygame_gui.elements.UIButton]:
        """アクションボタンを作成"""
        action_buttons = {}
        
        button_y = panel.relative_rect.height // 2 + 10
        
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
                manager=ui_manager,
                container=panel
            )
            
            # ボタンの有効/無効状態を設定
            if action.enabled:
                action_button.enable()
            else:
                action_button.disable()
            
            action_buttons[action.action_type.value] = action_button
        
        logger.debug(f"アクションボタン作成: {len(action_buttons)}個")
        return action_buttons
    
    def create_filter_controls(self, panel: pygame_gui.elements.UIPanel,
                             ui_manager: pygame_gui.UIManager) -> Dict[str, pygame_gui.core.UIElement]:
        """フィルターコントロールを作成"""
        filter_controls = {}
        
        # カテゴリフィルタードロップダウン
        category_dropdown = pygame_gui.elements.UIDropDownMenu(
            relative_rect=pygame.Rect(10, 10, 150, 30),
            options_list=['全て', '武器', '防具', '消耗品', 'その他', 'クエスト'],
            starting_option='全て',
            manager=ui_manager,
            container=panel
        )
        filter_controls['category_dropdown'] = category_dropdown
        
        # 検索テキストボックス
        search_textbox = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(170, 10, 120, 30),
            manager=ui_manager,
            container=panel
        )
        search_textbox.set_text_length_limit(20)
        filter_controls['search_textbox'] = search_textbox
        
        logger.debug("フィルターコントロール作成")
        return filter_controls
    
    def create_quick_slot_panel(self, quick_slot_count: int, panel: pygame_gui.elements.UIPanel,
                              ui_manager: pygame_gui.UIManager) -> List[pygame_gui.elements.UIButton]:
        """クイックスロットパネルを作成"""
        quick_slot_buttons = []
        
        slot_size = 48
        spacing = 5
        start_x = 10
        start_y = panel.relative_rect.height - (slot_size + 10)
        
        for i in range(quick_slot_count):
            x = start_x + i * (slot_size + spacing)
            
            quick_slot_rect = pygame.Rect(x, start_y, slot_size, slot_size)
            
            quick_button = pygame_gui.elements.UIButton(
                relative_rect=quick_slot_rect,
                text=f"Q{i + 1}",
                manager=ui_manager,
                container=panel
            )
            
            quick_slot_buttons.append(quick_button)
        
        logger.debug(f"クイックスロットパネル作成: {quick_slot_count}個")
        return quick_slot_buttons
    
    def cleanup_ui_elements(self, ui_manager: pygame_gui.UIManager) -> None:
        """UI要素をクリーンアップ"""
        if ui_manager:
            for element in list(ui_manager.get_root_container().elements):
                element.kill()
        
        logger.debug("UI要素クリーンアップ完了")