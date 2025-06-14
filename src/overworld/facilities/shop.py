"""商店"""

from typing import Dict, List, Optional, Any
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.party import Party
from src.items.item import Item, ItemManager, ItemInstance, ItemType, item_manager
from src.ui.base_ui import UIMenu, UIDialog, ui_manager
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
            "アイテム購入",
            self._show_buy_menu
        )
        
        menu.add_menu_item(
            "アイテム売却",
            self._show_sell_menu
        )
        
        menu.add_menu_item(
            "在庫確認",
            self._show_inventory
        )
        
        menu.add_menu_item(
            "商店の主人と話す",
            self._talk_to_shopkeeper
        )
    
    def _on_enter(self):
        """商店入場時の処理"""
        logger.info("商店に入りました")
        
        # 入場時のメッセージ
        welcome_message = (
            "「いらっしゃい！\n"
            "当店では冒険に必要な\n"
            "あらゆる装備を取り揃えています。\n\n"
            "武器、防具、消耗品まで、\n"
            "品質と価格に自信があります！\n\n"
            "何かお探しの品はありますか？」"
        )
        
        self._show_dialog(
            "shop_welcome_dialog",
            "商店の主人",
            welcome_message
        )
    
    def _on_exit(self):
        """商店退場時の処理"""
        logger.info("商店から出ました")
    
    def _show_buy_menu(self):
        """購入メニューを表示"""
        if not self.current_party:
            self._show_error_message("パーティが設定されていません")
            return
        
        buy_menu = UIMenu("buy_menu", "アイテム購入")
        
        # カテゴリ別に表示
        categories = [
            (ItemType.WEAPON, "武器"),
            (ItemType.ARMOR, "防具"),
            (ItemType.CONSUMABLE, "消耗品"),
            (ItemType.TOOL, "道具"),
        ]
        
        for item_type, category_name in categories:
            buy_menu.add_menu_item(
                category_name,
                self._show_category_items,
                [item_type]
            )
        
        buy_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [buy_menu]
        )
        
        self._show_submenu(buy_menu)
    
    def _show_category_items(self, item_type: ItemType):
        """カテゴリ別アイテム一覧を表示"""
        category_menu = UIMenu(f"{item_type.value}_menu", f"{item_type.value}一覧")
        
        # 在庫から該当カテゴリのアイテムを取得
        available_items = []
        for item_id in self.inventory:
            item = self.item_manager.get_item(item_id)
            if item and item.item_type == item_type:
                available_items.append(item)
        
        if not available_items:
            self._show_error_message(f"{item_type.value}の在庫がありません")
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
        details += f"説明: {item.get_description()}\n"
        details += f"価格: {item.price}G\n"
        details += f"重量: {item.weight}\n"
        details += f"希少度: {item.rarity.value}\n"
        
        if item.is_weapon():
            details += f"攻撃力: {item.get_attack_power()}\n"
            details += f"属性: {item.get_attribute()}\n"
        elif item.is_armor():
            details += f"防御力: {item.get_defense()}\n"
        elif item.is_consumable():
            details += f"効果: {item.get_effect_type()}\n"
            if item.get_effect_value() > 0:
                details += f"効果値: {item.get_effect_value()}\n"
        
        if item.usable_classes:
            details += f"使用可能クラス: {', '.join(item.usable_classes)}\n"
        
        details += f"\n現在のゴールド: {self.current_party.gold}G\n"
        
        # 購入可能かチェック
        if self.current_party.gold >= item.price:
            details += "\n購入しますか？"
            
            dialog = UIDialog(
                "item_detail_dialog",
                "アイテム詳細",
                details,
                buttons=[
                    {
                        'text': "購入する",
                        'command': lambda: self._buy_item(item)
                    },
                    {
                        'text': "戻る",
                        'command': self._close_dialog
                    }
                ]
            )
        else:
            details += "\n※ ゴールドが不足しています"
            
            dialog = UIDialog(
                "item_detail_dialog",
                "アイテム詳細",
                details,
                buttons=[
                    {
                        'text': "戻る",
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
            self._show_error_message("ゴールドが不足しています")
            return
        
        # アイテムインスタンス作成
        instance = self.item_manager.create_item_instance(item.item_id)
        if not instance:
            self._show_error_message("アイテムの作成に失敗しました")
            return
        
        # 購入処理
        self.current_party.gold -= item.price
        
        # TODO: Phase 4でインベントリシステム実装後、パーティにアイテム追加
        # self.current_party.add_item(instance)
        
        success_message = f"{item.get_name()} を購入しました！\n残りゴールド: {self.current_party.gold}G"
        self._show_success_message(success_message)
        
        logger.info(f"アイテム購入: {item.item_id} ({item.price}G)")
    
    def _show_sell_menu(self):
        """売却メニューを表示"""
        # TODO: Phase 4でインベントリシステム実装後に実装
        self._show_dialog(
            "sell_menu_dialog",
            "アイテム売却",
            "申し訳ありません。\n"
            "アイテム売却機能は\n"
            "インベントリシステムの実装後に\n"
            "提供予定です。\n\n"
            "しばらくお待ちください。"
        )
    
    def _show_inventory(self):
        """在庫確認を表示"""
        inventory_text = "【商店在庫一覧】\n\n"
        
        # カテゴリ別に在庫を表示
        categories = {
            ItemType.WEAPON: "武器",
            ItemType.ARMOR: "防具", 
            ItemType.CONSUMABLE: "消耗品",
            ItemType.TOOL: "道具"
        }
        
        for item_type, category_name in categories.items():
            inventory_text += f"【{category_name}】\n"
            
            category_items = []
            for item_id in self.inventory:
                item = self.item_manager.get_item(item_id)
                if item and item.item_type == item_type:
                    category_items.append(item)
            
            if category_items:
                for item in category_items:
                    inventory_text += f"  {item.get_name()} - {item.price}G\n"
            else:
                inventory_text += "  在庫なし\n"
            
            inventory_text += "\n"
        
        self._show_dialog(
            "inventory_dialog",
            "在庫確認",
            inventory_text
        )
    
    def _talk_to_shopkeeper(self):
        """商店主人との会話"""
        messages = [
            (
                "商店について",
                "「この店は代々続く老舗です。\n"
                "品質には絶対の自信がありますよ！\n"
                "どんな冒険にも対応できる\n"
                "装備を取り揃えています。」"
            ),
            (
                "装備のアドバイス",
                "「冒険の成功は装備で決まります。\n"
                "武器は攻撃力、防具は守備力を\n"
                "よく確認してください。\n"
                "消耗品も忘れずに！」"
            ),
            (
                "特別な装備",
                "「たまに珍しい装備も入荷します。\n"
                "運が良ければ、レアなアイテムに\n"
                "出会えるかもしれませんね。\n"
                "こまめにチェックしてください！」"
            ),
            (
                "価格について",
                "「当店の価格は適正価格です。\n"
                "品質を考えれば、むしろお得ですよ。\n"
                "冒険者の皆さんを応援したいので、\n"
                "利益は最小限に抑えています。」"
            )
        ]
        
        # ランダムにメッセージを選択
        import random
        title, message = random.choice(messages)
        
        self._show_dialog(
            "shopkeeper_dialog",
            f"商店の主人 - {title}",
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
    
    def get_inventory_items(self) -> List[Item]:
        """在庫アイテム一覧を取得"""
        items = []
        for item_id in self.inventory:
            item = self.item_manager.get_item(item_id)
            if item:
                items.append(item)
        return items