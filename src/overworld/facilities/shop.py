"""商店"""

from typing import Dict, List, Optional, Any
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.party import Party
from src.items.item import Item, ItemManager, ItemInstance, ItemType, item_manager
from src.ui.base_ui import UIMenu, UIDialog, ui_manager
from direct.gui.DirectGui import DirectScrolledList, DirectButton, DirectFrame, DirectLabel
from panda3d.core import Vec3
from src.core.config_manager import config_manager
from src.utils.logger import logger


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
            config_manager.get_text("shop.menu.check_inventory"),
            self._show_inventory
        )
        
        menu.add_menu_item(
            config_manager.get_text("shop.menu.talk_shopkeeper"),
            self._talk_to_shopkeeper
        )
    
    def _on_enter(self):
        """商店入場時の処理"""
        logger.info(config_manager.get_text("shop.messages.entered_shop"))
        
        # 入場時のメッセージ
        welcome_message = config_manager.get_text("shop.welcome_message")
        
        self._show_dialog(
            "shop_welcome_dialog",
            config_manager.get_text("shop.shopkeeper.title"),
            welcome_message
        )
    
    def _on_exit(self):
        """商店退場時の処理"""
        logger.info(config_manager.get_text("shop.messages.left_shop"))
    
    def _show_buy_menu(self):
        """購入メニューをDirectScrolledListで表示"""
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
        
        self._show_item_scrolled_list(
            available_items,
            config_manager.get_text("shop.purchase.title"),
            self._show_item_details,
            "shop_buy_list"
        )
    
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
            
            dialog = UIDialog(
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
                        'command': self._close_dialog
                    }
                ]
            )
        else:
            details += f"\n{config_manager.get_text('shop.purchase.gold_insufficient_note')}"
            
            dialog = UIDialog(
                "item_detail_dialog",
                config_manager.get_text("shop.purchase.item_details_title"),
                details,
                buttons=[
                    {
                        'text': config_manager.get_text("menu.back"),
                        'command': self._close_dialog
                    }
                ]
            )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
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
        
        # パーティインベントリにアイテム追加
        party_inventory = self.current_party.get_party_inventory()
        if party_inventory:
            success = party_inventory.add_item(instance)
            if not success:
                # インベントリが満杯の場合の処理
                self.current_party.gold += item.price  # ゴールドを戻す
                self._show_error_message(config_manager.get_text("shop.messages.inventory_full"))
                return
        
        success_message = config_manager.get_text("shop.purchase.purchase_success").format(
                                                  item_name=item.get_name(), 
                                                  gold=self.current_party.gold)
        self._show_success_message(success_message)
        
        logger.info(f"アイテム購入: {item.item_id} ({item.price}G)")
    
    def _show_item_scrolled_list(self, items: List[Item], title: str, 
                                on_item_selected: callable, ui_id: str):
        """DirectScrolledListでアイテム一覧を表示"""
        # 既存のUIがあれば削除
        if hasattr(self, 'shop_ui_elements'):
            self._cleanup_shop_ui()
        
        # フォント取得
        try:
            from src.ui.font_manager import font_manager
            font = font_manager.get_default_font()
        except:
            font = None
        
        # 背景フレーム
        background = DirectFrame(
            frameColor=(0, 0, 0, 0.8),
            frameSize=(-1.5, 1.5, -1.2, 1.0),
            pos=(0, 0, 0)
        )
        
        # タイトル
        title_label = DirectLabel(
            text=title,
            scale=0.08,
            pos=(0, 0, 0.8),
            text_fg=(1, 1, 0, 1),
            frameColor=(0, 0, 0, 0),
            text_font=font
        )
        
        # アイテムリスト用のボタンを作成
        item_buttons = []
        for item in items:
            display_name = self._format_item_display_name(item)
            
            item_button = DirectButton(
                text=display_name,
                scale=0.05,
                text_scale=0.9,
                text_align=0,  # 左寄せ
                command=lambda selected_item=item: on_item_selected(selected_item),
                frameColor=(0.3, 0.5, 0.3, 0.8),
                text_fg=(1, 1, 1, 1),
                text_font=font,
                relief=1,  # RAISED
                borderWidth=(0.01, 0.01)
            )
            item_buttons.append(item_button)
        
        # DirectScrolledListを作成
        scrolled_list = DirectScrolledList(
            frameSize=(-1.2, 1.2, -0.6, 0.6),
            frameColor=(0.2, 0.2, 0.3, 0.9),
            pos=(0, 0, 0.1),
            numItemsVisible=8,  # 一度に表示するアイテム数
            items=item_buttons,
            itemFrame_frameSize=(-1.1, 1.1, -0.05, 0.05),
            itemFrame_pos=(0, 0, 0),
            decButton_pos=(-1.15, 0, -0.65),
            incButton_pos=(1.15, 0, -0.65),
            decButton_text="▲",
            incButton_text="▼",
            decButton_scale=0.05,
            incButton_scale=0.05,
            decButton_text_fg=(1, 1, 1, 1),
            incButton_text_fg=(1, 1, 1, 1)
        )
        
        # 戻るボタン
        back_button = DirectButton(
            text=config_manager.get_text("menu.back"),
            scale=0.06,
            pos=(0, 0, -0.9),
            command=self._cleanup_and_return_to_main,
            frameColor=(0.7, 0.2, 0.2, 0.8),
            text_fg=(1, 1, 1, 1),
            text_font=font,
            relief=1,
            borderWidth=(0.01, 0.01)
        )
        
        # UI要素を保存
        self.shop_ui_elements = {
            'background': background,
            'title': title_label,
            'scrolled_list': scrolled_list,
            'back_button': back_button,
            'ui_id': ui_id
        }
    
    def _format_item_display_name(self, item: Item) -> str:
        """アイテム表示名をフォーマット"""
        category_icon = {
            ItemType.WEAPON: "⚔",
            ItemType.ARMOR: "🛡",
            ItemType.CONSUMABLE: "🧪",
            ItemType.TOOL: "🔧"
        }.get(item.item_type, "📦")
        
        return f"{category_icon} {item.get_name()} - {item.price}G"
    
    def _cleanup_shop_ui(self):
        """商店UIのクリーンアップ"""
        if hasattr(self, 'shop_ui_elements'):
            for element in self.shop_ui_elements.values():
                if hasattr(element, 'destroy'):
                    element.destroy()
            delattr(self, 'shop_ui_elements')
    
    def _cleanup_and_return_to_main(self):
        """UIをクリーンアップしてメインメニューに戻る"""
        self._cleanup_shop_ui()
        self._show_main_menu()
    
    def _show_sell_menu(self):
        """売却メニューをDirectScrolledListで表示"""
        if not self.current_party:
            self._show_error_message(config_manager.get_text("shop.messages.no_party_set"))
            return
        
        # パーティインベントリを取得
        party_inventory = self.current_party.get_party_inventory()
        if not party_inventory:
            self._show_error_message(config_manager.get_text("shop.messages.no_party_inventory"))
            return
        
        # 売却可能なアイテムを取得
        sellable_items = []
        for slot in party_inventory.slots:
            if not slot.is_empty():
                item_instance = slot.item_instance
                item = self.item_manager.get_item(item_instance.item_id)
                if item and item.price > 0 and item_instance.identified:  # 鑑定済みかつ価格設定アイテムのみ売却可能
                    sellable_items.append((slot, item_instance, item))
        
        if not sellable_items:
            self._show_dialog(
                "no_items_dialog",
                config_manager.get_text("shop.sell.title"),
                config_manager.get_text("shop.messages.no_sellable_items")
            )
            return
        
        self._show_sellable_items_scrolled_list(sellable_items)
    
    def _show_sellable_items_scrolled_list(self, sellable_items: List[tuple]):
        """売却可能アイテムをDirectScrolledListで表示"""
        # 既存のUIがあれば削除
        if hasattr(self, 'shop_ui_elements'):
            self._cleanup_shop_ui()
        
        # フォント取得
        try:
            from src.ui.font_manager import font_manager
            font = font_manager.get_default_font()
        except:
            font = None
        
        # 背景フレーム
        background = DirectFrame(
            frameColor=(0, 0, 0, 0.8),
            frameSize=(-1.5, 1.5, -1.2, 1.0),
            pos=(0, 0, 0)
        )
        
        # タイトル
        title_label = DirectLabel(
            text=config_manager.get_text("shop.sell.title"),
            scale=0.08,
            pos=(0, 0, 0.8),
            text_fg=(1, 1, 0, 1),
            frameColor=(0, 0, 0, 0),
            text_font=font
        )
        
        # アイテムリスト用のボタンを作成
        item_buttons = []
        for slot, item_instance, item in sellable_items:
            display_name = self._format_sellable_item_display_name(item_instance, item)
            
            item_button = DirectButton(
                text=display_name,
                scale=0.05,
                text_scale=0.9,
                text_align=0,  # 左寄せ
                command=lambda s=slot, ii=item_instance, i=item: self._show_sell_confirmation_from_list(s, ii, i),
                frameColor=(0.5, 0.3, 0.3, 0.8),
                text_fg=(1, 1, 1, 1),
                text_font=font,
                relief=1,  # RAISED
                borderWidth=(0.01, 0.01)
            )
            item_buttons.append(item_button)
        
        # DirectScrolledListを作成
        scrolled_list = DirectScrolledList(
            frameSize=(-1.2, 1.2, -0.6, 0.6),
            frameColor=(0.2, 0.2, 0.3, 0.9),
            pos=(0, 0, 0.1),
            numItemsVisible=8,  # 一度に表示するアイテム数
            items=item_buttons,
            itemFrame_frameSize=(-1.1, 1.1, -0.05, 0.05),
            itemFrame_pos=(0, 0, 0),
            decButton_pos=(-1.15, 0, -0.65),
            incButton_pos=(1.15, 0, -0.65),
            decButton_text="▲",
            incButton_text="▼",
            decButton_scale=0.05,
            incButton_scale=0.05,
            decButton_text_fg=(1, 1, 1, 1),
            incButton_text_fg=(1, 1, 1, 1)
        )
        
        # 戻るボタン
        back_button = DirectButton(
            text=config_manager.get_text("menu.back"),
            scale=0.06,
            pos=(0, 0, -0.9),
            command=self._cleanup_and_return_to_main,
            frameColor=(0.7, 0.2, 0.2, 0.8),
            text_fg=(1, 1, 1, 1),
            text_font=font,
            relief=1,
            borderWidth=(0.01, 0.01)
        )
        
        # UI要素を保存
        self.shop_ui_elements = {
            'background': background,
            'title': title_label,
            'scrolled_list': scrolled_list,
            'back_button': back_button,
            'ui_id': 'shop_sell_list'
        }
    
    def _format_sellable_item_display_name(self, item_instance, item: Item) -> str:
        """売却アイテム表示名をフォーマット"""
        category_icon = {
            ItemType.WEAPON: "⚔",
            ItemType.ARMOR: "🛡",
            ItemType.CONSUMABLE: "🧪",
            ItemType.TOOL: "🔧"
        }.get(item.item_type, "📦")
        
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
    
    def _show_inventory(self):
        """在庫確認を表示"""
        inventory_text = config_manager.get_text("shop.inventory.list_title") + "\n\n"
        
        # カテゴリ別に在庫を表示
        categories = {
            ItemType.WEAPON: config_manager.get_text("shop.purchase.categories.weapons"),
            ItemType.ARMOR: config_manager.get_text("shop.purchase.categories.armor"), 
            ItemType.CONSUMABLE: config_manager.get_text("shop.purchase.categories.consumables"),
            ItemType.TOOL: config_manager.get_text("shop.purchase.categories.tools")
        }
        
        for item_type, category_name in categories.items():
            inventory_text += config_manager.get_text("shop.inventory.category_header").format(category=category_name) + "\n"
            
            category_items = []
            for item_id in self.inventory:
                item = self.item_manager.get_item(item_id)
                if item and item.item_type == item_type:
                    category_items.append(item)
            
            if category_items:
                for item in category_items:
                    inventory_text += f"  {item.get_name()} - {item.price}G\n"
            else:
                inventory_text += f"  {config_manager.get_text('shop.inventory.no_stock')}\n"
            
            inventory_text += "\n"
        
        self._show_dialog(
            "inventory_dialog",
            config_manager.get_text("shop.inventory.title"),
            inventory_text
        )
    
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
            message
        )
    
    def _show_submenu(self, submenu: UIMenu):
        """サブメニューを表示"""
        # メインメニューを隠す
        if self.main_menu:
            ui_manager.hide_element(self.main_menu.element_id)
        
        ui_manager.register_element(submenu)
        ui_manager.show_element(submenu.element_id, modal=True)
    
    def _back_to_main_menu_from_submenu(self, submenu: UIMenu):
        """サブメニューからメインメニューに戻る"""
        ui_manager.hide_element(submenu.element_id)
        ui_manager.unregister_element(submenu.element_id)
        
        if self.main_menu:
            ui_manager.show_element(self.main_menu.element_id)
    
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
            
            dialog = UIDialog(
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
                        'command': self._close_dialog
                    }
                ]
            )
            
            ui_manager.register_element(dialog)
            ui_manager.show_element(dialog.element_id, modal=True)
    
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
        
        self._show_success_message(success_message)
        
        logger.info(f"アイテム売却: {item.item_id} x{quantity} ({total_price}G)")
        
        # 売却メニューに戻る
        self._show_sell_menu()
    
    def get_inventory_items(self) -> List[Item]:
        """在庫アイテム一覧を取得"""
        items = []
        for item_id in self.inventory:
            item = self.item_manager.get_item(item_id)
            if item:
                items.append(item)
        return items