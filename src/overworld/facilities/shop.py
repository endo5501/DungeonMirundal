"""商店"""

import pygame
from typing import List, Optional
from src.overworld.base_facility import BaseFacility, FacilityType
from src.items.item import Item, ItemInstance, ItemType, item_manager
from src.ui.base_ui_pygame import UIMenu, ui_manager
from src.ui.selection_list_ui import ItemSelectionList, CustomSelectionList, SelectionListData
# NOTE: panda3D UI components removed - using pygame-based UI now
from src.core.config_manager import config_manager
from src.utils.logger import logger

# 商店施設定数
ITEM_LIST_RECT_X = 100
ITEM_LIST_RECT_Y = 100
ITEM_LIST_RECT_WIDTH = 600
ITEM_LIST_RECT_HEIGHT_LARGE = 500
ITEM_LIST_RECT_HEIGHT_SMALL = 400


class Shop(BaseFacility):
    """商店"""
    
    def __init__(self):
        super().__init__(
            facility_id="shop",
            facility_type=FacilityType.SHOP,
            name_key="facility.shop"
        )
        
        # 商店の在庫
        self.inventory: List[str] = []
        self.item_manager = item_manager
        
        # UI要素
        self.item_selection_list: Optional[ItemSelectionList] = None
        self.sell_source_selection_list: Optional['CustomSelectionList'] = None
        self.character_sell_list: Optional[ItemSelectionList] = None
        self.storage_sell_list: Optional[ItemSelectionList] = None
        
        # 基本在庫を設定
        self._setup_basic_inventory()
    
    def _setup_basic_inventory(self):
        """基本在庫の設定"""
        # 武器
        self.inventory.extend([
            "dagger", "short_sword", "long_sword", "mace", "staff", "bow"
        ])
        
        # 防具
        self.inventory.extend([
            "cloth_robe", "leather_armor", "chain_mail", "plate_armor"
        ])
        
        # 消耗品
        self.inventory.extend([
            "healing_potion", "mana_potion", "antidote", "return_scroll",
            "torch", "lockpick"
        ])
    
    def _setup_menu_items(self, menu: UIMenu):
        """商店固有のメニュー項目を設定"""
        menu.add_menu_item(
            config_manager.get_text("shop.menu.buy_items"),
            self._show_buy_menu
        )
        
        menu.add_menu_item(
            config_manager.get_text("shop.menu.sell_items"),
            self._show_sell_menu
        )
        
        menu.add_menu_item(
            config_manager.get_text("shop.menu.talk_shopkeeper"),
            self._talk_to_shopkeeper
        )
    
    def _on_enter(self):
        """商店入場時の処理"""
        logger.info(config_manager.get_text("shop.messages.entered_shop"))
    
    def _on_exit(self):
        """商店退場時の処理"""
        self._cleanup_all_ui()
        logger.info(config_manager.get_text("shop.messages.left_shop"))
    
    def _cleanup_all_ui(self):
        """全てのUI要素をクリーンアップ"""
        self._hide_selection_list()
        self._hide_sell_source_selection()
        self._hide_character_sell_list()
        self._hide_storage_sell_list()
    
    def _handle_ui_selection_events(self, event: pygame.event.Event) -> bool:
        """UISelectionListのイベント処理をオーバーライド"""
        # アイテム購入リスト
        if self.item_selection_list and self.item_selection_list.handle_event(event):
            return True
        
        # 売却元選択リスト
        if self.sell_source_selection_list and self.sell_source_selection_list.handle_event(event):
            return True
        
        # キャラクター売却リスト
        if self.character_sell_list and self.character_sell_list.handle_event(event):
            return True
        
        # 宿屋倉庫売却リスト
        if self.storage_sell_list and self.storage_sell_list.handle_event(event):
            return True
        
        return False
    
    def _show_buy_menu(self):
        """購入メニューをUISelectionListで表示"""
        if not self.current_party:
            self._show_error_message(config_manager.get_text("shop.messages.no_party_set"))
            return
        
        # 全アイテムを取得
        available_items = []
        for item_id in self.inventory:
            item = self.item_manager.get_item(item_id)
            if item:
                available_items.append(item)
        
        if not available_items:
            self._show_error_message(config_manager.get_text("shop.purchase.no_stock").format(category="全アイテム"))
            return
        
        # UISelectionListを使用
        list_rect = pygame.Rect(ITEM_LIST_RECT_X, ITEM_LIST_RECT_Y, ITEM_LIST_RECT_WIDTH, ITEM_LIST_RECT_HEIGHT_LARGE)
        
        # pygame_gui_managerが存在しない場合（テスト環境など）は処理をスキップ
        if not self._check_pygame_gui_manager():
            self._show_error_message("購入メニューの表示に失敗しました。")
            return
        
        self.item_selection_list = ItemSelectionList(
            relative_rect=list_rect,
            manager=ui_manager.pygame_gui_manager,
            title=config_manager.get_text("shop.purchase.title")
        )
        
        # アイテムを追加
        for item in available_items:
            display_name = self._format_item_display_name(item)
            self.item_selection_list.add_item_data(item, display_name)
        
        # コールバック設定
        self.item_selection_list.on_item_selected = self._on_item_selected_for_purchase
        self.item_selection_list.on_item_details = self._show_item_details
        
        # 表示
        self.item_selection_list.show()
    
    def _on_item_selected_for_purchase(self, item: Item):
        """購入用アイテム選択時のコールバック"""
        self._hide_selection_list()
        self._show_item_details(item)
    
    def _hide_selection_list(self):
        """選択リストを非表示"""
        if hasattr(self, 'item_selection_list') and self.item_selection_list:
            self.item_selection_list.hide()
            self.item_selection_list.kill()
            self.item_selection_list = None
    
    def _show_category_items(self, item_type: ItemType):
        """カテゴリ別アイテム一覧を表示"""
        category_key = f"shop.purchase.categories.{item_type.value.lower()}"
        category_name = config_manager.get_text(category_key)
        category_menu = UIMenu(f"{item_type.value}_menu", 
                              config_manager.get_text("shop.purchase.category_list_title").format(category=category_name))
        
        # 在庫から該当カテゴリのアイテムを取得
        available_items = []
        for item_id in self.inventory:
            item = self.item_manager.get_item(item_id)
            if item and item.item_type == item_type:
                available_items.append(item)
        
        if not available_items:
            category_key = f"shop.purchase.categories.{item_type.value.lower()}"
            category_name = config_manager.get_text(category_key)
            self._show_error_message(config_manager.get_text("shop.purchase.no_stock").format(category=category_name))
            return
        
        for item in available_items:
            item_info = f"{item.get_name()} - {item.price}G"
            category_menu.add_menu_item(
                item_info,
                self._show_item_details,
                [item]
            )
        
        category_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._show_buy_menu
        )
        
        self._show_submenu(category_menu)
    
    def _show_item_details(self, item: Item):
        """アイテムの詳細と購入確認"""
        if not self.current_party:
            return
        
        # アイテム詳細情報を作成
        details = f"【{item.get_name()}】\n\n"
        details += f"{config_manager.get_text('shop.purchase.description_label')}: {item.get_description()}\n"
        details += f"{config_manager.get_text('shop.purchase.price_label')}: {item.price}G\n"
        details += f"{config_manager.get_text('shop.purchase.weight_label')}: {item.weight}\n"
        details += f"{config_manager.get_text('shop.purchase.rarity_label')}: {item.rarity.value}\n"
        
        if item.is_weapon():
            details += f"{config_manager.get_text('shop.purchase.attack_power_label')}: {item.get_attack_power()}\n"
            details += f"{config_manager.get_text('shop.purchase.attribute_label')}: {item.get_attribute()}\n"
        elif item.is_armor():
            details += f"{config_manager.get_text('shop.purchase.defense_label')}: {item.get_defense()}\n"
        elif item.is_consumable():
            details += f"{config_manager.get_text('shop.purchase.effect_type_label')}: {item.get_effect_type()}\n"
            if item.get_effect_value() > 0:
                details += f"{config_manager.get_text('shop.purchase.effect_value_label')}: {item.get_effect_value()}\n"
        
        if item.usable_classes:
            details += f"{config_manager.get_text('shop.purchase.usable_classes_label')}: {', '.join(item.usable_classes)}\n"
        
        details += f"\n{config_manager.get_text('shop.purchase.current_gold_label')}: {self.current_party.gold}G\n"
        
        # 購入可能かチェック
        if self.current_party.gold >= item.price:
            details += f"\n{config_manager.get_text('shop.purchase.purchase_confirm')}"
            
            self._show_dialog(
                "item_detail_dialog",
                config_manager.get_text("shop.purchase.item_details_title"),
                details,
                buttons=[
                    {
                        'text': config_manager.get_text("shop.purchase.purchase_button"),
                        'command': lambda: self._buy_item(item)
                    },
                    {
                        'text': config_manager.get_text("menu.back"),
                        'command': self._close_dialog_and_return_to_buy_menu
                    }
                ]
            )
        else:
            details += f"\n{config_manager.get_text('shop.purchase.gold_insufficient_note')}"
            
            self._show_dialog(
                "item_detail_dialog",
                config_manager.get_text("shop.purchase.item_details_title"),
                details,
                buttons=[
                    {
                        'text': config_manager.get_text("menu.back"),
                        'command': self._close_dialog_and_return_to_buy_menu
                    }
                ]
            )
    
    def _buy_item(self, item: Item):
        """アイテム購入処理"""
        if not self.current_party:
            return
        
        self._close_dialog()
        
        # ゴールドチェック
        if self.current_party.gold < item.price:
            self._show_error_message(config_manager.get_text("shop.messages.insufficient_gold"))
            return
        
        # アイテムインスタンス作成
        instance = self.item_manager.create_item_instance(item.item_id)
        if not instance:
            self._show_error_message(config_manager.get_text("shop.messages.item_creation_failed"))
            return
        
        # 購入処理
        self.current_party.gold -= item.price
        
        # 宿屋倉庫にアイテムを直接搬入
        from src.overworld.inn_storage import inn_storage_manager
        storage = inn_storage_manager.get_storage()
        success = storage.add_item(instance)
        if not success:
            # 宿屋倉庫が満杯の場合の処理
            self.current_party.gold += item.price  # ゴールドを戻す
            self._show_error_message("宿屋の倉庫が満杯です。倉庫を整理してください。")
            return
        
        success_message = f"{item.get_name()}を購入し、宿屋の倉庫に搬入しました。\n残りゴールド: {self.current_party.gold}G"
        
        logger.info(f"アイテム購入: {item.item_id} ({item.price}G)")
        
        # 購入一覧画面（サブメニュー）を閉じる
        ui_manager.hide_menu("shop_buy_menu")
        
        # 成功メッセージを表示（ダイアログを閉じた時にメインメニューが自動表示される）
        self._show_success_message(success_message)
    
    
    def _format_item_display_name(self, item: Item) -> str:
        """アイテム表示名をフォーマット"""
        category_icon = {
            ItemType.WEAPON: "[W]",      # 武器 (Weapon)
            ItemType.ARMOR: "[A]",       # 防具 (Armor)
            ItemType.CONSUMABLE: "[C]",  # 消耗品 (Consumable)
            ItemType.TOOL: "[T]"         # 道具 (Tool)
        }.get(item.item_type, "[I]")     # アイテム (Item)
        
        return f"{category_icon} {item.get_name()} - {item.price}G"
    
    def _cleanup_shop_ui(self):
        """商店UIのクリーンアップ（pygame版では不要）"""
        # pygame版ではUIMenuが自動的に管理されるため、特別なクリーンアップは不要
        pass
    
    def _cleanup_and_return_to_main(self):
        """UIをクリーンアップしてメインメニューに戻る"""
        # pygame版では単純にメインメニューに戻る
        self._show_main_menu()
    
    def _close_dialog_and_return_to_buy_menu(self):
        """ダイアログを閉じて購入メニューに戻る"""
        self._close_dialog()
        self._show_buy_menu()
    
    def _show_sell_menu(self):
        """売却メニューを表示（新しいアイテム管理システム対応）"""
        if not self.current_party:
            self._show_error_message(config_manager.get_text("shop.messages.no_party_set"))
            return
        
        # 売却可能なアイテムを全体から取得
        sellable_items = self._get_all_sellable_items()
        
        if not sellable_items:
            self._show_dialog(
                "no_items_dialog",
                config_manager.get_text("shop.sell.title"),
                "売却可能なアイテムがありません。\\n\\n"
                "キャラクターが所持しているアイテムまたは\\n"
                "宿屋倉庫のアイテムを売却できます。\\n\\n"
                "※アイテムは鑑定済みで価格が設定されている\\n"
                "必要があります。",
                buttons=[
                    {
                        'text': config_manager.get_text("menu.back"),
                        'command': self._close_dialog
                    }
                ]
            )
            return
        
        # 売却元選択メニューを表示
        self._show_sell_source_selection(sellable_items)
    
    def _get_all_sellable_items(self):
        """全ての売却可能アイテムを取得（キャラクター個人 + 宿屋倉庫）"""
        sellable_items = []
        
        # キャラクター個人のインベントリから取得
        for character in self.current_party.get_all_characters():
            char_inventory = character.get_inventory()
            for i, slot in enumerate(char_inventory.slots):
                if not slot.is_empty():
                    item_instance = slot.item_instance
                    item = self.item_manager.get_item(item_instance.item_id)
                    if item and item.price > 0 and item_instance.identified:
                        sellable_items.append(("character", character, i, item_instance, item))
        
        # 宿屋倉庫から取得
        try:
            from src.overworld.inn_storage import inn_storage_manager
            storage = inn_storage_manager.get_storage()
            for slot_index, item_instance in storage.get_all_items():
                item = self.item_manager.get_item(item_instance.item_id)
                if item and item.price > 0 and item_instance.identified:
                    sellable_items.append(("storage", None, slot_index, item_instance, item))
        except Exception as e:
            logger.warning(f"宿屋倉庫からのアイテム取得に失敗: {e}")
        
        return sellable_items
    
    def _show_sell_source_selection(self, sellable_items):
        """売却元選択メニューを表示（UISelectionList使用）"""
        # アイテムを売却元でグループ化
        character_items = {}
        storage_items = []
        
        for source, character, index, item_instance, item in sellable_items:
            if source == "character":
                if character.name not in character_items:
                    character_items[character.name] = []
                character_items[character.name].append((character, index, item_instance, item))
            else:
                storage_items.append((index, item_instance, item))
        
        # UISelectionListを使用した売却元選択
        import pygame
        list_rect = pygame.Rect(ITEM_LIST_RECT_X, ITEM_LIST_RECT_Y, ITEM_LIST_RECT_WIDTH, ITEM_LIST_RECT_HEIGHT_SMALL)
        
        from src.ui.selection_list_ui import CustomSelectionList, SelectionListData
        
        self.sell_source_selection_list = CustomSelectionList(
            relative_rect=list_rect,
            manager=ui_manager.pygame_gui_manager,
            title="売却元選択"
        )
        
        # キャラクター別売却項目を追加
        for char_name, items in character_items.items():
            display_text = f"{char_name} の所持品 ({len(items)}個)"
            source_data = SelectionListData(
                display_text=display_text,
                data=("character", items, char_name),
                callback=lambda data=("character", items, char_name): self._on_sell_source_selected(data)
            )
            self.sell_source_selection_list.add_item(source_data)
        
        # 宿屋倉庫売却項目を追加
        if storage_items:
            display_text = f"宿屋倉庫 ({len(storage_items)}個)"
            source_data = SelectionListData(
                display_text=display_text,
                data=("storage", storage_items),
                callback=lambda data=("storage", storage_items): self._on_sell_source_selected(data)
            )
            self.sell_source_selection_list.add_item(source_data)
        
        # 表示
        self.sell_source_selection_list.show()
    
    def _on_sell_source_selected(self, source_data):
        """売却元選択時のコールバック"""
        source_type = source_data[0]
        if source_type == "character":
            _, items, char_name = source_data
            self._hide_sell_source_selection()
            self._show_character_sellable_items_list(items, char_name)
        elif source_type == "storage":
            _, items = source_data
            self._hide_sell_source_selection()
            self._show_storage_sellable_items_list(items)
    
    def _hide_sell_source_selection(self):
        """売却元選択リストを非表示"""
        if hasattr(self, 'sell_source_selection_list') and self.sell_source_selection_list:
            self.sell_source_selection_list.hide()
            self.sell_source_selection_list.kill()
            self.sell_source_selection_list = None
    
    def _show_character_sellable_items_list(self, items, char_name):
        """キャラクター所持アイテム売却メニュー（UISelectionList）"""
        list_rect = pygame.Rect(ITEM_LIST_RECT_X, ITEM_LIST_RECT_Y, ITEM_LIST_RECT_WIDTH, ITEM_LIST_RECT_HEIGHT_LARGE)
        
        # pygame_gui_managerが存在しない場合（テスト環境など）は処理をスキップ
        if not self._check_pygame_gui_manager():
            self._show_error_message("売却メニューの表示に失敗しました。")
            return
        
        self.character_sell_list = ItemSelectionList(
            relative_rect=list_rect,
            manager=ui_manager.pygame_gui_manager,
            title=f"{char_name} のアイテム売却"
        )
        
        # アイテムを追加
        for character, index, item_instance, item in items:
            display_name = self._format_sellable_item_display_name(item_instance, item)
            self.character_sell_list.add_item_data(
                (character, index, item_instance, item), 
                display_name
            )
        
        # コールバック設定
        self.character_sell_list.on_item_selected = self._on_character_item_selected_for_sell
        
        # 表示
        self.character_sell_list.show()
    
    def _show_storage_sellable_items_list(self, items):
        """宿屋倉庫アイテム売却メニュー（UISelectionList）"""
        list_rect = pygame.Rect(ITEM_LIST_RECT_X, ITEM_LIST_RECT_Y, ITEM_LIST_RECT_WIDTH, ITEM_LIST_RECT_HEIGHT_LARGE)
        
        # pygame_gui_managerが存在しない場合（テスト環境など）は処理をスキップ
        if not self._check_pygame_gui_manager():
            self._show_error_message("売却メニューの表示に失敗しました。")
            return
        
        self.storage_sell_list = ItemSelectionList(
            relative_rect=list_rect,
            manager=ui_manager.pygame_gui_manager,
            title="宿屋倉庫アイテム売却"
        )
        
        # アイテムを追加
        for index, item_instance, item in items:
            display_name = self._format_sellable_item_display_name(item_instance, item)
            self.storage_sell_list.add_item_data(
                (index, item_instance, item), 
                display_name
            )
        
        # コールバック設定
        self.storage_sell_list.on_item_selected = self._on_storage_item_selected_for_sell
        
        # 表示
        self.storage_sell_list.show()
    
    def _on_character_item_selected_for_sell(self, item_data):
        """キャラクターアイテム売却選択時のコールバック"""
        character, slot_index, item_instance, item = item_data
        self._hide_character_sell_list()
        self._show_character_item_sell_confirmation(character, slot_index, item_instance, item)
    
    def _on_storage_item_selected_for_sell(self, item_data):
        """宿屋倉庫アイテム売却選択時のコールバック"""
        slot_index, item_instance, item = item_data
        self._hide_storage_sell_list()
        self._show_storage_item_sell_confirmation(slot_index, item_instance, item)
    
    def _hide_character_sell_list(self):
        """キャラクター売却リストを非表示"""
        if hasattr(self, 'character_sell_list') and self.character_sell_list:
            self.character_sell_list.hide()
            self.character_sell_list.kill()
            self.character_sell_list = None
    
    def _hide_storage_sell_list(self):
        """宿屋倉庫売却リストを非表示"""
        if hasattr(self, 'storage_sell_list') and self.storage_sell_list:
            self.storage_sell_list.hide()
            self.storage_sell_list.kill()
            self.storage_sell_list = None
    
    def _show_character_sellable_items(self, items, char_name):
        """キャラクター所持アイテム売却メニュー"""
        char_sell_menu = UIMenu("character_sell_menu", f"{char_name} のアイテム売却")
        
        for character, index, item_instance, item in items:
            display_name = self._format_sellable_item_display_name(item_instance, item)
            char_sell_menu.add_menu_item(
                display_name,
                self._show_character_item_sell_confirmation,
                [character, index, item_instance, item]
            )
        
        char_sell_menu.add_back_button(
            config_manager.get_text("menu.back"),
            self._show_sell_menu
        )
        
        self._show_submenu(char_sell_menu)
    
    def _show_storage_sellable_items(self, items):
        """宿屋倉庫アイテム売却メニュー"""
        storage_sell_menu = UIMenu("storage_sell_menu", "宿屋倉庫アイテム売却")
        
        for index, item_instance, item in items:
            display_name = self._format_sellable_item_display_name(item_instance, item)
            storage_sell_menu.add_menu_item(
                display_name,
                self._show_storage_item_sell_confirmation,
                [index, item_instance, item]
            )
        
        storage_sell_menu.add_back_button(
            config_manager.get_text("menu.back"),
            self._show_sell_menu
        )
        
        self._show_submenu(storage_sell_menu)
    
    def _show_character_item_sell_confirmation(self, character, slot_index, item_instance, item):
        """キャラクター所持アイテム売却確認"""
        sell_price = max(1, item.price // 2)
        self._show_sell_confirmation_for_character_item(character, slot_index, item_instance, item, sell_price)
    
    def _show_storage_item_sell_confirmation(self, slot_index, item_instance, item):
        """宿屋倉庫アイテム売却確認"""
        sell_price = max(1, item.price // 2)
        self._show_sell_confirmation_for_storage_item(slot_index, item_instance, item, sell_price)
    
    def _show_sell_confirmation_for_character_item(self, character, slot_index, item_instance, item, sell_price):
        """キャラクターアイテム売却確認ダイアログ"""
        details = f"【{item.get_name()}の売却】\\n\\n"
        details += f"所持者: {character.name}\\n"
        details += f"{config_manager.get_text('shop.purchase.description_label')}: {item.get_description()}\\n"
        details += f"{config_manager.get_text('shop.sell.purchase_price_label')}: {item.price}G\\n"
        details += f"{config_manager.get_text('shop.sell.sell_price_label')}: {sell_price}G\\n"
        
        if item_instance.quantity > 1:
            details += f"{config_manager.get_text('shop.sell.quantity_label')}: {item_instance.quantity}\\n"
            details += f"{config_manager.get_text('shop.sell.total_if_all_label')}: {sell_price * item_instance.quantity}G\\n"
        
        details += f"\\n{config_manager.get_text('shop.sell.current_gold_label')}: {self.current_party.gold}G\\n"
        details += f"{config_manager.get_text('shop.sell.after_sell_label')}: {self.current_party.gold + (sell_price * item_instance.quantity)}G\\n"
        details += f"\\n売却しますか？"
        
        # コンテキストを保存（戻るボタン用）
        self._current_character_for_sell = character
        
        self._show_dialog(
            "character_item_sell_confirm_dialog",
            f"{item.get_name()}の売却確認",
            details,
            buttons=[
                {
                    'text': config_manager.get_text("shop.sell.sell_button"),
                    'command': lambda: self._sell_character_item(character, slot_index, item_instance, item, sell_price, item_instance.quantity)
                },
                {
                    'text': config_manager.get_text("menu.back"),
                    'command': self._back_to_character_sell_list_from_confirmation
                }
            ]
        )
    
    def _show_sell_confirmation_for_storage_item(self, slot_index, item_instance, item, sell_price):
        """宿屋倉庫アイテム売却確認ダイアログ"""
        details = f"【{item.get_name()}の売却】\\n\\n"
        details += f"所持場所: 宿屋倉庫\\n"
        details += f"{config_manager.get_text('shop.purchase.description_label')}: {item.get_description()}\\n"
        details += f"{config_manager.get_text('shop.sell.purchase_price_label')}: {item.price}G\\n"
        details += f"{config_manager.get_text('shop.sell.sell_price_label')}: {sell_price}G\\n"
        
        if item_instance.quantity > 1:
            details += f"{config_manager.get_text('shop.sell.quantity_label')}: {item_instance.quantity}\\n"
            details += f"{config_manager.get_text('shop.sell.total_if_all_label')}: {sell_price * item_instance.quantity}G\\n"
        
        details += f"\\n{config_manager.get_text('shop.sell.current_gold_label')}: {self.current_party.gold}G\\n"
        details += f"{config_manager.get_text('shop.sell.after_sell_label')}: {self.current_party.gold + (sell_price * item_instance.quantity)}G\\n"
        details += f"\\n売却しますか？"
        
        self._show_dialog(
            "storage_item_sell_confirm_dialog",
            f"{item.get_name()}の売却確認",
            details,
            buttons=[
                {
                    'text': config_manager.get_text("shop.sell.sell_button"),
                    'command': lambda: self._sell_storage_item(slot_index, item_instance, item, sell_price, item_instance.quantity)
                },
                {
                    'text': config_manager.get_text("menu.back"),
                    'command': self._back_to_storage_sell_list_from_confirmation
                }
            ]
        )
    
    def _sell_character_item(self, character, slot_index, item_instance, item, sell_price, quantity):
        """キャラクターのアイテムを売却"""
        if not self.current_party:
            return
        
        self._close_dialog()
        
        try:
            char_inventory = character.get_inventory()
            
            # アイテムを削除
            if quantity == item_instance.quantity:
                # 全数売却
                removed_item = char_inventory.remove_item(slot_index, quantity)
            else:
                # 一部売却
                item_instance.quantity -= quantity
                removed_item = True
            
            if removed_item:
                # ゴールドを追加
                total_price = sell_price * quantity
                self.current_party.gold += total_price
                
                # 成功メッセージ
                success_message = f"{character.name}が{item.get_name()}x{quantity}を売却しました。\\n\\n"
                success_message += f"売却金額: {total_price}G\\n"
                success_message += f"残りゴールド: {self.current_party.gold}G"
                
                self._show_success_message(success_message)
                logger.info(f"キャラクターアイテム売却: {character.name} - {item.item_id} x{quantity} ({total_price}G)")
            else:
                self._show_error_message("アイテムの売却に失敗しました")
                
        except Exception as e:
            logger.error(f"キャラクターアイテム売却エラー: {e}")
            self._show_error_message(f"売却処理に失敗しました: {str(e)}")
    
    def _sell_storage_item(self, slot_index, _, item, sell_price, quantity):
        """宿屋倉庫のアイテムを売却"""
        if not self.current_party:
            return
        
        self._close_dialog()
        
        try:
            from src.overworld.inn_storage import inn_storage_manager
            storage = inn_storage_manager.get_storage()
            
            # アイテムを削除
            removed_item = storage.remove_item(slot_index, quantity)
            
            if removed_item:
                # ゴールドを追加
                total_price = sell_price * quantity
                self.current_party.gold += total_price
                
                # 成功メッセージ
                success_message = f"宿屋倉庫から{item.get_name()}x{quantity}を売却しました。\\n\\n"
                success_message += f"売却金額: {total_price}G\\n"
                success_message += f"残りゴールド: {self.current_party.gold}G"
                
                self._show_success_message(success_message)
                logger.info(f"宿屋倉庫アイテム売却: {item.item_id} x{quantity} ({total_price}G)")
            else:
                self._show_error_message("アイテムの売却に失敗しました")
                
        except Exception as e:
            logger.error(f"宿屋倉庫アイテム売却エラー: {e}")
            self._show_error_message(f"売却処理に失敗しました: {str(e)}")
    
    
    def _format_sellable_item_display_name(self, item_instance, item: Item) -> str:
        """売却アイテム表示名をフォーマット"""
        category_icon = {
            ItemType.WEAPON: "[W]",      # 武器 (Weapon)
            ItemType.ARMOR: "[A]",       # 防具 (Armor)
            ItemType.CONSUMABLE: "[C]",  # 消耗品 (Consumable)
            ItemType.TOOL: "[T]"         # 道具 (Tool)
        }.get(item.item_type, "[I]")     # アイテム (Item)
        
        # 売却価格を計算（購入価格の50%）
        sell_price = max(1, item.price // 2)
        
        item_info = f"{category_icon} {item.get_name()}"
        if item_instance.quantity > 1:
            item_info += f" x{item_instance.quantity}"
        item_info += f" - {sell_price}G"
        if item_instance.quantity > 1:
            item_info += f" (各{sell_price}G)"
        
        return item_info
    
    def _show_sell_confirmation_from_list(self, slot, item_instance, item):
        """売却確認ダイアログを表示（DirectScrolledListから呼び出し）"""
        sell_price = max(1, item.price // 2)
        self._show_sell_confirmation(slot, item_instance, item, sell_price)
    
    
    def _talk_to_shopkeeper(self):
        """商店主人との会話"""
        messages = [
            (
                config_manager.get_text("shop.shopkeeper.about_shop_title"),
                config_manager.get_text("shop.shopkeeper.about_shop_message")
            ),
            (
                config_manager.get_text("shop.shopkeeper.equipment_advice_title"),
                config_manager.get_text("shop.shopkeeper.equipment_advice_message")
            ),
            (
                config_manager.get_text("shop.shopkeeper.special_equipment_title"),
                config_manager.get_text("shop.shopkeeper.special_equipment_message")
            ),
            (
                config_manager.get_text("shop.shopkeeper.pricing_title"),
                config_manager.get_text("shop.shopkeeper.pricing_message")
            )
        ]
        
        # ランダムにメッセージを選択
        import random
        title, message = random.choice(messages)
        
        self._show_dialog(
            "shopkeeper_dialog",
            f"{config_manager.get_text('shop.shopkeeper.title')} - {title}",
            message,
            buttons=[
                {
                    'text': config_manager.get_text("menu.back"),
                    'command': self._close_dialog
                }
            ],
            width=550,  # 商店主人との会話内容表示に適切な幅
            height=350  # 会話メッセージ表示に適切な高さ
        )
    
    def _show_submenu(self, submenu: UIMenu):
        """サブメニューを表示"""
        # メインメニューを隠す
        if self.main_menu:
            ui_manager.hide_menu(self.main_menu.menu_id)
        
        ui_manager.add_menu(submenu)
        ui_manager.show_menu(submenu.menu_id, modal=True)
    
    def _back_to_main_menu_from_submenu(self, submenu: UIMenu):
        """サブメニューからメインメニューに戻る"""
        ui_manager.hide_menu(submenu.menu_id)
        
        
        if self.main_menu:
            ui_manager.show_menu(self.main_menu.menu_id)
    
    def add_item_to_inventory(self, item_id: str):
        """在庫にアイテムを追加"""
        if item_id not in self.inventory:
            self.inventory.append(item_id)
            logger.info(f"商店在庫に追加: {item_id}")
    
    def remove_item_from_inventory(self, item_id: str):
        """在庫からアイテムを削除"""
        if item_id in self.inventory:
            self.inventory.remove(item_id)
            logger.info(f"商店在庫から削除: {item_id}")
    
    def _show_sell_confirmation(self, slot, item_instance: ItemInstance, item: Item, sell_price: int):
        """売却確認ダイアログを表示"""
        if not self.current_party:
            return
        
        # アイテム詳細情報を作成
        details = f"【{item.get_name()}】\n\n"
        details += f"{config_manager.get_text('shop.purchase.description_label')}: {item.get_description()}\n"
        details += f"{config_manager.get_text('shop.sell.purchase_price_label')}: {item.price}G\n"
        details += f"{config_manager.get_text('shop.sell.sell_price_label')}: {sell_price}G\n"
        
        if item_instance.quantity > 1:
            details += f"{config_manager.get_text('shop.sell.quantity_label')}: {item_instance.quantity}\n"
            details += f"{config_manager.get_text('shop.sell.total_if_all_label')}: {sell_price * item_instance.quantity}G\n"
        
        details += f"\n{config_manager.get_text('shop.sell.current_gold_label')}: {self.current_party.gold}G\n"
        details += f"{config_manager.get_text('shop.sell.after_sell_label')}: {self.current_party.gold + (sell_price * item_instance.quantity)}G\n"
        
        if item_instance.quantity > 1:
            details += f"\n{config_manager.get_text('shop.sell.quantity_select_prompt')}"
            
            # 数量選択メニューを表示
            quantity_menu = UIMenu("sell_quantity_menu", config_manager.get_text("shop.sell.quantity_select_title"))
            
            # 1個ずつ、半分、全部のオプションを追加
            quantity_menu.add_menu_item(
                config_manager.get_text("shop.sell.sell_one"),
                self._sell_item,
                [slot, item_instance, item, sell_price, 1]
            )
            
            if item_instance.quantity >= 2:
                half_quantity = item_instance.quantity // 2
                quantity_menu.add_menu_item(
                    config_manager.get_text("shop.sell.sell_half").format(count=half_quantity),
                    self._sell_item,
                    [slot, item_instance, item, sell_price, half_quantity]
                )
            
            quantity_menu.add_menu_item(
                config_manager.get_text("shop.sell.sell_all").format(count=item_instance.quantity),
                self._sell_item,
                [slot, item_instance, item, sell_price, item_instance.quantity]
            )
            
            quantity_menu.add_menu_item(
                config_manager.get_text("menu.back"),
                self._show_sell_menu
            )
            
            self._show_submenu(quantity_menu)
        else:
            details += f"\n{config_manager.get_text('shop.sell.sell_confirm')}"
            
            self._show_dialog(
                "sell_confirmation_dialog",
                config_manager.get_text("shop.sell.confirmation_title"),
                details,
                buttons=[
                    {
                        'text': config_manager.get_text("shop.sell.sell_button"),
                        'command': lambda: self._sell_item(slot, item_instance, item, sell_price, 1)
                    },
                    {
                        'text': config_manager.get_text("menu.back"),
                        'command': self._back_to_sell_menu_from_confirmation
                    }
                ]
            )
    
    def _sell_item(self, slot, item_instance: ItemInstance, item: Item, sell_price: int, quantity: int):
        """アイテム売却処理"""
        if not self.current_party:
            return
        
        self._close_dialog()
        
        # 数量チェック
        if quantity > item_instance.quantity:
            self._show_error_message(config_manager.get_text("shop.messages.invalid_quantity"))
            return
        
        # パーティインベントリを取得
        party_inventory = self.current_party.get_party_inventory()
        if not party_inventory:
            self._show_error_message(config_manager.get_text("shop.messages.no_party_inventory"))
            return
        
        # 売却処理
        total_price = sell_price * quantity
        
        if quantity == item_instance.quantity:
            # 全部売却の場合、スロットを空にする
            slot.remove_item()
        else:
            # 一部売却の場合、数量を減らす
            item_instance.quantity -= quantity
        
        # ゴールドを追加
        self.current_party.gold += total_price
        
        # 成功メッセージ
        if quantity > 1:
            success_message = config_manager.get_text("shop.sell.sell_success_multiple").format(
                                                      item_name=item.get_name(), 
                                                      count=quantity,
                                                      price=total_price, 
                                                      gold=self.current_party.gold)
        else:
            success_message = config_manager.get_text("shop.sell.sell_success").format(
                                                      item_name=item.get_name(), 
                                                      price=total_price, 
                                                      gold=self.current_party.gold)
        
        logger.info(f"アイテム売却: {item.item_id} x{quantity} ({total_price}G)")
        
        # 売却一覧画面（サブメニュー）を閉じる
        ui_manager.hide_menu("shop_sell_menu")
        
        # 成功メッセージを表示（ダイアログを閉じた時にメインメニューが自動表示される）
        self._show_success_message(success_message)
    
    def get_inventory_items(self) -> List[Item]:
        """在庫アイテム一覧を取得"""
        items = []
        for item_id in self.inventory:
            item = self.item_manager.get_item(item_id)
            if item:
                items.append(item)
        return items
    
    def _back_to_character_sell_list_from_confirmation(self):
        """キャラクター売却確認ダイアログから売却リストに戻る"""
        self._close_dialog()
        # キャラクター売却リストを再表示
        # 注意: この関数は現在のコンテキストに依存する
        if hasattr(self, '_current_character_for_sell') and self._current_character_for_sell:
            self._show_character_sellable_items_list(self._current_character_for_sell)
    
    def _back_to_storage_sell_list_from_confirmation(self):
        """宿屋倉庫売却確認ダイアログから売却リストに戻る"""
        self._close_dialog()
        # 宿屋倉庫売却リストを再表示
        self._show_storage_sellable_items_list()
    
    def _back_to_sell_menu_from_confirmation(self):
        """売却確認ダイアログから売却メニューに戻る（旧システム用）"""
        self._close_dialog()
        self._show_sell_menu()