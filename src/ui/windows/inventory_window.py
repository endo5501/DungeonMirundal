"""インベントリウィンドウ - WindowSystem用インベントリ管理UI"""

from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import pygame
import pygame_gui

from src.ui.window_system.window import Window
from src.ui.window_system.window_manager import WindowManager
from src.inventory.inventory import Inventory, InventorySlot, InventorySlotType
from src.items.item import Item, ItemInstance, item_manager
from src.items.item_usage import item_usage_manager, UsageResult
from src.character.party import Party
from src.character.character import Character
from src.core.config_manager import config_manager
from src.utils.logger import logger


class InventoryViewMode(Enum):
    """インベントリ表示モード"""
    PARTY_OVERVIEW = "party_overview"           # パーティ概要
    INVENTORY_CONTENTS = "inventory_contents"   # インベントリ内容
    ITEM_DETAILS = "item_details"              # アイテム詳細
    ITEM_ACTIONS = "item_actions"              # アイテムアクション
    INVENTORY_MANAGEMENT = "inventory_management"  # インベントリ管理
    TRANSFER_MODE = "transfer_mode"            # 移動モード


class InventoryAction(Enum):
    """インベントリアクション"""
    VIEW = "view"           # 表示
    USE = "use"             # 使用
    TRANSFER = "transfer"   # 移動
    DROP = "drop"           # 破棄
    SORT = "sort"           # 整理


class InventoryWindow(Window):
    """インベントリウィンドウクラス - WindowSystem準拠"""
    
    def __init__(self, window_id: str, parent: Optional[Window] = None, modal: bool = True):
        """
        インベントリウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            parent: 親ウィンドウ
            modal: モーダル表示
        """
        super().__init__(window_id, parent, modal)
        
        # データ管理
        self.current_party: Optional[Party] = None
        self.current_character: Optional[Character] = None
        self.current_inventory: Optional[Inventory] = None
        self.selected_slot: Optional[int] = None
        self.transfer_source: Optional[Tuple[Inventory, int]] = None
        
        # 表示モード
        self.current_mode = InventoryViewMode.PARTY_OVERVIEW
        self.inventory_type = "character"  # "character", "party", "shared"
        
        # フィルタリング・検索
        self.current_filter: Optional[str] = None
        self.search_query: Optional[str] = None
        self.filtered_items: List[Tuple[int, ItemInstance]] = []
        
        # UI要素
        self.ui_elements: Dict[str, pygame_gui.UIElement] = {}
        self.content_panel: Optional[pygame_gui.elements.UIPanel] = None
        
        # コールバック
        self.callback_on_close: Optional[Callable] = None
        
        logger.info(f"InventoryWindow作成: {window_id}")

    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            window_manager = WindowManager.get_instance()
            self.ui_manager = window_manager.ui_manager
            self.surface = window_manager.screen
        
        if not self.surface:
            logger.error("画面サーフェスが設定されていません")
            return
        
        # ウィンドウサイズ設定
        screen_rect = self.surface.get_rect()
        self.rect = pygame.Rect(
            screen_rect.width // 10,
            screen_rect.height // 10,
            screen_rect.width * 4 // 5,
            screen_rect.height * 4 // 5
        )
        
        # メインパネル作成
        self.content_panel = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager,
            element_id="inventory_window_panel"
        )
        self.ui_elements["main_panel"] = self.content_panel
        
        # 現在のモードに応じてコンテンツを作成
        self._create_content_for_current_mode()
        
        logger.debug(f"InventoryWindow UI要素を作成: {self.window_id}")

    def _create_content_for_current_mode(self) -> None:
        """現在のモードに応じてコンテンツを作成"""
        if self.current_mode == InventoryViewMode.PARTY_OVERVIEW:
            self.create_party_inventory_overview()
        elif self.current_mode == InventoryViewMode.INVENTORY_CONTENTS:
            self.create_inventory_contents()
        elif self.current_mode == InventoryViewMode.ITEM_ACTIONS:
            self.create_item_actions()
        elif self.current_mode == InventoryViewMode.INVENTORY_MANAGEMENT:
            self.create_inventory_management()

    def set_party(self, party: Party) -> None:
        """パーティを設定"""
        self.current_party = party
        logger.debug(f"パーティを設定: {party.name}")

    def show_party_inventory_overview(self) -> None:
        """パーティインベントリ概要を表示"""
        self.current_mode = InventoryViewMode.PARTY_OVERVIEW
        if self.state.value == "shown":
            self._clear_content()
            self.create_party_inventory_overview()

    def create_party_inventory_overview(self) -> None:
        """パーティインベントリ概要のUI要素を作成"""
        if not self.content_panel or not self.current_party:
            return
        
        # タイトル
        title_rect = pygame.Rect(20, 20, 400, 30)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=config_manager.get_text("inventory.party_title"),
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        y_offset = 60
        
        # パーティ共有インベントリ
        shared_rect = pygame.Rect(20, y_offset, 300, 35)
        shared_button = pygame_gui.elements.UIButton(
            relative_rect=shared_rect,
            text=config_manager.get_text("inventory.shared_items"),
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="shared_inventory_button"
        )
        self.ui_elements["shared_inventory_button"] = shared_button
        y_offset += 45
        
        # 各キャラクターのインベントリ
        for i, character in enumerate(self.current_party.get_all_characters()):
            char_info = config_manager.get_text("inventory_ui.character_items").format(
                character_name=character.name
            )
            
            button_rect = pygame.Rect(20, y_offset + i * 40, 350, 35)
            char_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=char_info,
                manager=self.ui_manager,
                container=self.content_panel,
                object_id=f"char_inventory_button_{i}"
            )
            self.ui_elements[f"char_inventory_button_{i}"] = char_button
        
        # アイテム管理ボタン
        management_y = y_offset + len(self.current_party.get_all_characters()) * 40 + 20
        management_rect = pygame.Rect(20, management_y, 250, 35)
        management_button = pygame_gui.elements.UIButton(
            relative_rect=management_rect,
            text=config_manager.get_text("inventory.item_management"),
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="inventory_management_button"
        )
        self.ui_elements["inventory_management_button"] = management_button
        
        # 閉じるボタン
        close_rect = pygame.Rect(self.rect.width - 120, self.rect.height - 50, 100, 35)
        close_button = pygame_gui.elements.UIButton(
            relative_rect=close_rect,
            text=config_manager.get_text("common.close"),
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="close_button"
        )
        self.ui_elements["close_button"] = close_button

    def show_inventory_contents(self, inventory: Inventory, title: str, inventory_type: str = "character") -> None:
        """インベントリ内容を表示"""
        self.current_inventory = inventory
        self.inventory_type = inventory_type
        self.current_mode = InventoryViewMode.INVENTORY_CONTENTS
        
        if self.state.value == "shown":
            self._clear_content()
            self.create_inventory_contents()

    def create_inventory_contents(self) -> None:
        """インベントリ内容のUI要素を作成"""
        if not self.content_panel or not self.current_inventory:
            return
        
        # タイトル
        title_text = f"{self.inventory_type}インベントリ"
        title_rect = pygame.Rect(20, 20, 400, 30)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=title_text,
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        # インベントリ統計
        stats_text = self._get_inventory_stats_text()
        stats_rect = pygame.Rect(20, 55, 500, 20)
        stats_label = pygame_gui.elements.UILabel(
            relative_rect=stats_rect,
            text=stats_text,
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["stats"] = stats_label
        
        # フィルタリング・検索ツール
        self._create_filter_tools()
        
        # アイテムグリッド表示
        self._create_item_grid()
        
        # 操作ボタン
        self._create_action_buttons()

    def _create_filter_tools(self) -> None:
        """フィルタリング・検索ツールを作成"""
        # フィルタボタン
        filter_rect = pygame.Rect(20, 85, 120, 30)
        filter_button = pygame_gui.elements.UIButton(
            relative_rect=filter_rect,
            text="フィルタ",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="filter_button"
        )
        self.ui_elements["filter_button"] = filter_button
        
        # 検索ボックス
        search_rect = pygame.Rect(150, 85, 200, 30)
        search_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=search_rect,
            manager=self.ui_manager,
            container=self.content_panel,
            placeholder_text="アイテム名で検索..."
        )
        self.ui_elements["search_entry"] = search_entry
        
        # 検索ボタン
        search_button_rect = pygame.Rect(360, 85, 80, 30)
        search_button = pygame_gui.elements.UIButton(
            relative_rect=search_button_rect,
            text="検索",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="search_button"
        )
        self.ui_elements["search_button"] = search_button

    def _create_item_grid(self) -> None:
        """アイテムグリッドを作成"""
        grid_start_y = 125
        slot_size = 60
        slots_per_row = 8
        
        items = self.filtered_items if self.filtered_items else self._get_all_items()
        
        for i, (slot_index, item_instance) in enumerate(items):
            if item_instance:
                row = i // slots_per_row
                col = i % slots_per_row
                
                x = 20 + col * (slot_size + 5)
                y = grid_start_y + row * (slot_size + 5)
                
                # アイテムボタン
                item_rect = pygame.Rect(x, y, slot_size, slot_size)
                item_text = self._get_item_display_text(item_instance)
                
                item_button = pygame_gui.elements.UIButton(
                    relative_rect=item_rect,
                    text=item_text,
                    manager=self.ui_manager,
                    container=self.content_panel,
                    object_id=f"item_button_{slot_index}"
                )
                self.ui_elements[f"item_button_{slot_index}"] = item_button

    def _create_action_buttons(self) -> None:
        """操作ボタンを作成"""
        button_y = self.rect.height - 100
        
        # 整理ボタン
        sort_rect = pygame.Rect(20, button_y, 100, 35)
        sort_button = pygame_gui.elements.UIButton(
            relative_rect=sort_rect,
            text="整理",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="sort_button"
        )
        self.ui_elements["sort_button"] = sort_button
        
        # 統計ボタン
        stats_rect = pygame.Rect(130, button_y, 100, 35)
        stats_button = pygame_gui.elements.UIButton(
            relative_rect=stats_rect,
            text="統計",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="stats_button"
        )
        self.ui_elements["stats_button"] = stats_button
        
        # 戻るボタン
        back_rect = pygame.Rect(self.rect.width - 120, button_y, 100, 35)
        back_button = pygame_gui.elements.UIButton(
            relative_rect=back_rect,
            text="戻る",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="back_button"
        )
        self.ui_elements["back_button"] = back_button

    def show_item_actions(self, slot_index: int, item_instance: ItemInstance) -> None:
        """アイテムアクションを表示"""
        self.selected_slot = slot_index
        self.current_mode = InventoryViewMode.ITEM_ACTIONS
        
        if self.state.value == "shown":
            self._clear_content()
            self.create_item_actions()

    def create_item_actions(self) -> None:
        """アイテムアクションのUI要素を作成"""
        if not self.content_panel or self.selected_slot is None:
            return
        
        slot = self.current_inventory.slots[self.selected_slot]
        if slot.is_empty():
            return
        
        item_instance = slot.item_instance
        item = item_manager.get_item(item_instance.item_id)
        
        # タイトル
        title_text = f"アイテム操作: {item.get_name() if item else '不明'}"
        title_rect = pygame.Rect(20, 20, 400, 30)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=title_text,
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        y_offset = 60
        
        # 詳細表示ボタン
        detail_rect = pygame.Rect(20, y_offset, 150, 35)
        detail_button = pygame_gui.elements.UIButton(
            relative_rect=detail_rect,
            text="詳細を見る",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="detail_button"
        )
        self.ui_elements["detail_button"] = detail_button
        y_offset += 45
        
        # 使用ボタン（使用可能な場合）
        if item and item.is_usable():
            use_rect = pygame.Rect(20, y_offset, 150, 35)
            use_button = pygame_gui.elements.UIButton(
                relative_rect=use_rect,
                text="使用する",
                manager=self.ui_manager,
                container=self.content_panel,
                object_id="use_button"
            )
            self.ui_elements["use_button"] = use_button
            y_offset += 45
        
        # 移動ボタン
        transfer_rect = pygame.Rect(20, y_offset, 150, 35)
        transfer_button = pygame_gui.elements.UIButton(
            relative_rect=transfer_rect,
            text="移動する",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="transfer_button"
        )
        self.ui_elements["transfer_button"] = transfer_button
        y_offset += 45
        
        # 破棄ボタン
        drop_rect = pygame.Rect(20, y_offset, 150, 35)
        drop_button = pygame_gui.elements.UIButton(
            relative_rect=drop_rect,
            text="破棄する",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="drop_button"
        )
        self.ui_elements["drop_button"] = drop_button
        y_offset += 45
        
        # 戻るボタン
        back_rect = pygame.Rect(20, y_offset + 20, 100, 35)
        back_button = pygame_gui.elements.UIButton(
            relative_rect=back_rect,
            text="戻る",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="back_button"
        )
        self.ui_elements["back_button"] = back_button

    def create_inventory_management(self) -> None:
        """インベントリ管理のUI要素を作成"""
        if not self.content_panel:
            return
        
        # タイトル
        title_rect = pygame.Rect(20, 20, 400, 30)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="インベントリ管理",
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        # 管理オプション
        y_offset = 60
        
        sort_all_rect = pygame.Rect(20, y_offset, 200, 35)
        sort_all_button = pygame_gui.elements.UIButton(
            relative_rect=sort_all_rect,
            text="全アイテム整理",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="sort_all_button"
        )
        self.ui_elements["sort_all_button"] = sort_all_button
        
        # 戻るボタン
        back_rect = pygame.Rect(20, y_offset + 60, 100, 35)
        back_button = pygame_gui.elements.UIButton(
            relative_rect=back_rect,
            text="戻る",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="back_button"
        )
        self.ui_elements["back_button"] = back_button

    def use_item(self, item_instance: ItemInstance, slot_index: int) -> None:
        """アイテムを使用"""
        if not self.current_character:
            self.show_message("使用者が設定されていません")
            return
        
        try:
            result = item_usage_manager.use_item(
                item_instance, 
                self.current_character, 
                quantity=1
            )
            
            if result.success:
                # インベントリから消費量を減らす
                if result.quantity_consumed > 0:
                    self.current_inventory.remove_item(slot_index, result.quantity_consumed)
                
                self.show_message(result.message)
                self.refresh_view()
            else:
                self.show_message(f"使用失敗: {result.message}")
                
        except Exception as e:
            logger.error(f"アイテム使用エラー: {e}")
            self.show_message("アイテムの使用に失敗しました")

    def transfer_item_to_slot(self, target_slot: int) -> None:
        """アイテムを指定スロットに移動"""
        if not self.transfer_source or not self.current_inventory:
            return
        
        source_inventory, source_slot = self.transfer_source
        
        try:
            # 同一インベントリ内での移動
            if source_inventory == self.current_inventory:
                success = self.current_inventory.transfer_item(source_slot, target_slot)
                if success:
                    self.show_message("アイテムを移動しました")
                    self.refresh_view()
                else:
                    self.show_message("アイテムの移動に失敗しました")
            
            self.transfer_source = None
            
        except Exception as e:
            logger.error(f"アイテム移動エラー: {e}")
            self.show_message("アイテムの移動に失敗しました")

    def drop_item(self, item_instance: ItemInstance, slot_index: int) -> None:
        """アイテムを破棄"""
        try:
            quantity = item_instance.quantity
            success = self.current_inventory.remove_item(slot_index, quantity)
            
            if success:
                item = item_manager.get_item(item_instance.item_id)
                item_name = item.get_name() if item else "アイテム"
                self.show_message(f"{item_name}を破棄しました")
                self.refresh_view()
            else:
                self.show_message("アイテムの破棄に失敗しました")
                
        except Exception as e:
            logger.error(f"アイテム破棄エラー: {e}")
            self.show_message("アイテムの破棄に失敗しました")

    def sort_inventory(self) -> None:
        """インベントリを整理"""
        if not self.current_inventory:
            return
        
        try:
            self.current_inventory.sort_items()
            self.show_message("インベントリを整理しました")
            self.refresh_view()
            
        except Exception as e:
            logger.error(f"インベントリ整理エラー: {e}")
            self.show_message("インベントリの整理に失敗しました")

    def show_inventory_statistics(self) -> None:
        """インベントリ統計を表示"""
        if not self.current_inventory:
            return
        
        stats_text = self._generate_inventory_statistics()
        self.show_dialog("インベントリ統計", stats_text)

    def filter_items_by_type(self, item_type: str) -> None:
        """アイテムタイプでフィルタリング"""
        self.current_filter = item_type
        self.filtered_items = self._filter_items_by_type(item_type)
        self.refresh_filtered_view()

    def search_items_by_name(self, search_query: str) -> None:
        """アイテム名で検索"""
        self.search_query = search_query
        self.filtered_items = self._search_items_by_name(search_query)
        self.refresh_filtered_view()

    def show_item_details(self, item_instance: ItemInstance, item: Item) -> None:
        """アイテム詳細を表示"""
        details_text = self._generate_item_details_text(item_instance, item)
        self.show_dialog("アイテム詳細", details_text)

    def show_dialog(self, title: str, message: str) -> None:
        """ダイアログを表示"""
        logger.info(f"ダイアログ表示: {title} - {message}")

    def show_message(self, message: str) -> None:
        """メッセージを表示"""
        logger.info(f"メッセージ表示: {message}")

    def refresh_view(self) -> None:
        """ビューを更新"""
        if self.state.value == "shown":
            self._clear_content()
            self._create_content_for_current_mode()

    def refresh_filtered_view(self) -> None:
        """フィルタリングされたビューを更新"""
        if self.current_mode == InventoryViewMode.INVENTORY_CONTENTS:
            # アイテムグリッドのみ再作成
            self._clear_item_grid()
            self._create_item_grid()

    def _get_inventory_stats_text(self) -> str:
        """インベントリ統計テキストを取得"""
        if not self.current_inventory:
            return ""
        
        total_weight = self.current_inventory.get_total_weight()
        max_weight = self.current_inventory.get_max_weight()
        item_count = self.current_inventory.get_item_count()
        max_items = self.current_inventory.get_max_items()
        
        return f"重量: {total_weight:.1f}/{max_weight}kg | アイテム: {item_count}/{max_items}"

    def _get_item_display_text(self, item_instance: ItemInstance) -> str:
        """アイテム表示テキストを取得"""
        item = item_manager.get_item(item_instance.item_id)
        if not item:
            return "???"
        
        if item_instance.identified:
            name = item.get_name()
            if item_instance.quantity > 1:
                return f"{name} x{item_instance.quantity}"
            return name
        else:
            return f"未鑑定の{item.item_type.value}"

    def _get_all_items(self) -> List[Tuple[int, ItemInstance]]:
        """全アイテムを取得"""
        if not self.current_inventory:
            return []
        
        items = []
        for i, slot in enumerate(self.current_inventory.slots):
            if not slot.is_empty():
                items.append((i, slot.item_instance))
        return items

    def _filter_items_by_type(self, item_type: str) -> List[Tuple[int, ItemInstance]]:
        """アイテムタイプでフィルタリング"""
        filtered = []
        for i, slot in enumerate(self.current_inventory.slots):
            if not slot.is_empty():
                item = item_manager.get_item(slot.item_instance.item_id)
                if item and item.item_type.value == item_type:
                    filtered.append((i, slot.item_instance))
        return filtered

    def _search_items_by_name(self, search_query: str) -> List[Tuple[int, ItemInstance]]:
        """アイテム名で検索"""
        results = []
        query_lower = search_query.lower()
        
        for i, slot in enumerate(self.current_inventory.slots):
            if not slot.is_empty():
                item = item_manager.get_item(slot.item_instance.item_id)
                if item and query_lower in item.get_name().lower():
                    results.append((i, slot.item_instance))
        return results

    def _generate_inventory_statistics(self) -> str:
        """インベントリ統計を生成"""
        if not self.current_inventory:
            return "統計情報がありません"
        
        stats = f"【インベントリ統計】\\n\\n"
        stats += f"総重量: {self.current_inventory.get_total_weight():.1f}kg\\n"
        stats += f"最大重量: {self.current_inventory.get_max_weight()}kg\\n"
        stats += f"アイテム数: {self.current_inventory.get_item_count()}\\n"
        stats += f"最大アイテム数: {self.current_inventory.get_max_items()}\\n"
        
        # アイテムタイプ別集計
        type_counts = {}
        for slot in self.current_inventory.slots:
            if not slot.is_empty():
                item = item_manager.get_item(slot.item_instance.item_id)
                if item:
                    item_type = item.item_type.value
                    type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        if type_counts:
            stats += "\\n【アイテムタイプ別】\\n"
            for item_type, count in type_counts.items():
                stats += f"{item_type}: {count}個\\n"
        
        return stats

    def _generate_item_details_text(self, item_instance: ItemInstance, item: Item) -> str:
        """アイテム詳細テキストを生成"""
        if not item_instance.identified:
            return f"【未鑑定のアイテム】\\n\\n種類: {item.item_type.value}\\n\\nこのアイテムは鑑定が必要です。"
        
        details = f"【{item.get_name()}】\\n\\n"
        details += f"説明: {item.get_description()}\\n"
        details += f"種類: {item.item_type.value}\\n"
        details += f"重量: {item.weight}\\n"
        details += f"価値: {item.price}G\\n"
        
        if item_instance.quantity > 1:
            details += f"所持数: {item_instance.quantity}\\n"
        
        details += f"状態: {int(item_instance.condition * 100)}%\\n"
        
        if item.is_usable():
            details += "\\nこのアイテムは使用可能です。"
        
        return details

    def _clear_content(self) -> None:
        """コンテンツをクリア"""
        for element_id, element in list(self.ui_elements.items()):
            if element_id != "main_panel":
                element.kill()
                del self.ui_elements[element_id]

    def _clear_item_grid(self) -> None:
        """アイテムグリッドをクリア"""
        to_remove = []
        for element_id in self.ui_elements:
            if element_id.startswith("item_button_"):
                to_remove.append(element_id)
        
        for element_id in to_remove:
            self.ui_elements[element_id].kill()
            del self.ui_elements[element_id]

    def set_close_callback(self, callback: Callable) -> None:
        """閉じるコールバックを設定"""
        self.callback_on_close = callback

    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            return self._handle_button_press(event)
        return False

    def _handle_button_press(self, event: pygame.event.Event) -> bool:
        """ボタン押下イベントを処理"""
        element_id = getattr(event.ui_object_id, 'object_id', '') if hasattr(event, 'ui_object_id') else ''
        
        # パーティ概要でのボタン処理
        if self.current_mode == InventoryViewMode.PARTY_OVERVIEW:
            if element_id == 'shared_inventory_button':
                shared_inventory = self.current_party.get_party_inventory()
                self.show_inventory_contents(shared_inventory, "パーティ共有アイテム", "party")
                return True
            elif element_id.startswith('char_inventory_button_'):
                index = int(element_id.split('_')[-1])
                characters = self.current_party.get_all_characters()
                if 0 <= index < len(characters):
                    char_inventory = characters[index].get_inventory()
                    self.current_character = characters[index]
                    self.show_inventory_contents(char_inventory, f"{characters[index].name}のアイテム", "character")
                return True
            elif element_id == 'inventory_management_button':
                self.current_mode = InventoryViewMode.INVENTORY_MANAGEMENT
                self.refresh_view()
                return True
            elif element_id == 'close_button':
                self.hide()
                if self.callback_on_close:
                    self.callback_on_close()
                return True
        
        # インベントリ内容でのボタン処理
        elif self.current_mode == InventoryViewMode.INVENTORY_CONTENTS:
            if element_id.startswith('item_button_'):
                slot_index = int(element_id.split('_')[-1])
                slot = self.current_inventory.slots[slot_index]
                if not slot.is_empty():
                    self.show_item_actions(slot_index, slot.item_instance)
                return True
            elif element_id == 'sort_button':
                self.sort_inventory()
                return True
            elif element_id == 'stats_button':
                self.show_inventory_statistics()
                return True
            elif element_id == 'back_button':
                self.show_party_inventory_overview()
                return True
        
        # アイテムアクションでのボタン処理
        elif self.current_mode == InventoryViewMode.ITEM_ACTIONS:
            if element_id == 'detail_button':
                slot = self.current_inventory.slots[self.selected_slot]
                item = item_manager.get_item(slot.item_instance.item_id)
                self.show_item_details(slot.item_instance, item)
                return True
            elif element_id == 'use_button':
                slot = self.current_inventory.slots[self.selected_slot]
                self.use_item(slot.item_instance, self.selected_slot)
                return True
            elif element_id == 'transfer_button':
                self.transfer_source = (self.current_inventory, self.selected_slot)
                self.show_message("移動先のスロットを選択してください")
                return True
            elif element_id == 'drop_button':
                slot = self.current_inventory.slots[self.selected_slot]
                self.drop_item(slot.item_instance, self.selected_slot)
                return True
            elif element_id == 'back_button':
                self.show_inventory_contents(self.current_inventory, "", self.inventory_type)
                return True
        
        return False

    def destroy(self) -> None:
        """ウィンドウを破棄"""
        self._clear_content()
        
        if self.content_panel:
            self.content_panel.kill()
            self.content_panel = None
        
        self.current_party = None
        self.current_character = None
        self.current_inventory = None
        self.selected_slot = None
        self.transfer_source = None
        
        super().destroy()
        logger.debug(f"InventoryWindowを破棄: {self.window_id}")

    def on_show(self) -> None:
        """表示時の処理"""
        logger.debug(f"InventoryWindowを表示: {self.window_id}")

    def on_hide(self) -> None:
        """非表示時の処理"""
        logger.debug(f"InventoryWindowを非表示: {self.window_id}")

    def on_update(self, time_delta: float) -> None:
        """更新処理"""
        pass