"""商店サービス"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..core.facility_service import FacilityService, MenuItem
from ..core.service_result import ServiceResult, ResultType
from .service_utils import (
    ServiceResultFactory,
    PartyMemberUtility,
    ConfirmationFlowUtility,
    CostCalculationUtility,
    ActionExecutorMixin
)
# 正しいインポートパスに修正
try:
    from src.core.game_manager import GameManager as Game
except ImportError:
    Game = None

from src.character.party import Party
from src.character.character import Character

# アイテム・インベントリシステムのインポート
from src.items.item import item_manager, Item, ItemInstance
from src.inventory.inventory import inventory_manager, Inventory

logger = logging.getLogger(__name__)


class ShopService(FacilityService, ActionExecutorMixin):
    """商店サービス
    
    アイテムの購入、売却、鑑定などの機能を提供する。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__("shop")
        # GameManagerはシングルトンではないため、必要時に別途設定
        self.game = None
        self.item_manager = item_manager
        
        # コントローラー参照（後で設定される）
        self._controller = None
        
        # 商店の在庫
        self._shop_inventory: Dict[str, Dict[str, Any]] = {}
        self._last_stock_refresh: Optional[datetime] = None
        self._stock_refresh_interval = timedelta(days=1)  # 1日ごとに在庫更新
        
        # 売却レート
        self.sell_rate = 0.5  # アイテム価値の50%で買い取り
        
        # 鑑定料金
        self.identify_cost = self.item_manager.get_identification_cost()
        
        logger.info("ShopService initialized")
    
    def set_controller(self, controller):
        """コントローラーを設定"""
        self._controller = controller
    
    def get_menu_items(self) -> List[MenuItem]:
        """メニュー項目を取得"""
        items = []
        
        # 購入
        items.append(MenuItem(
            id="buy",
            label="購入",
            description="アイテムを購入します",
            enabled=True,
            service_type="panel"
        ))
        
        # 売却
        items.append(MenuItem(
            id="sell",
            label="売却",
            description="アイテムを売却します",
            enabled=True,  # 常に有効にしてアイテムがなくても表示
            service_type="panel"
        ))
        
        # 鑑定
        items.append(MenuItem(
            id="identify",
            label="鑑定",
            description="未鑑定のアイテムを鑑定します",
            enabled=True,  # 常に有効にしてアイテムがなくても表示
            service_type="panel"  # actionからpanelに変更
        ))
        
        # 退出
        items.append(MenuItem(
            id="exit",
            label="商店を出る",
            description="商店から退出します",
            enabled=True,
            service_type="action"
        ))
        
        return items
    
    def can_execute(self, action_id: str) -> bool:
        """アクション実行可能かチェック"""
        valid_actions = ["buy", "sell", "identify", "exit"]
        return action_id in valid_actions
    
    def execute_action(self, action_id: str, params: Dict[str, Any]) -> ServiceResult:
        """アクションを実行"""
        action_map = {
            "buy": self._handle_buy,
            "sell": self._handle_sell,
            "identify": self._handle_identify,
            "exit": lambda p: ServiceResultFactory.success("商店から退出しました")
        }
        
        return self.execute_with_error_handling(action_map, action_id, params)
    
    # 購入関連
    
    def _handle_buy(self, params: Dict[str, Any]) -> ServiceResult:
        """購入を処理"""
        item_id = params.get("item_id")
        category = params.get("category")
        
        if not item_id:
            # カテゴリ別商品リストを表示
            return self._get_shop_inventory(category)
        
        # 確認→実行フローを使用
        return ConfirmationFlowUtility.handle_confirmation_flow(
            params,
            lambda p: self._confirm_purchase(p.get("item_id"), p.get("quantity", 1)),
            lambda p: self._execute_purchase(p.get("item_id"), p.get("quantity", 1))
        )
    
    def _get_shop_inventory(self, category: Optional[str] = None) -> ServiceResult:
        """商店在庫を取得"""
        # 在庫を更新（必要に応じて）
        self._refresh_inventory_if_needed()
        
        # カテゴリ別にフィルタ
        if category:
            items = {k: v for k, v in self._shop_inventory.items() 
                    if v.get("category") == category}
        else:
            items = self._shop_inventory
        
        # カテゴリ一覧
        categories = [
            {"id": "weapons", "name": "武器", "icon": "⚔️"},
            {"id": "armor", "name": "防具", "icon": "🛡️"},
            {"id": "items", "name": "アイテム", "icon": "🧪"},
            {"id": "special", "name": "特殊", "icon": "✨"}
        ]
        
        return ServiceResult(
            success=True,
            message="商店在庫",
            data={
                "items": items,
                "categories": categories,
                "selected_category": category,
                "party_gold": self.party.gold if self.party else 0
            }
        )
    
    def _refresh_inventory_if_needed(self) -> None:
        """必要に応じて在庫を更新"""
        now = datetime.now()
        
        if (self._last_stock_refresh is None or 
            now - self._last_stock_refresh > self._stock_refresh_interval):
            self._generate_shop_inventory()
            self._last_stock_refresh = now
    
    def _generate_shop_inventory(self) -> None:
        """商店在庫を生成"""
        self._shop_inventory = {}
        
        # カテゴリマッピング
        category_mapping = {
            "weapon": "weapons",
            "armor": "armor", 
            "consumable": "items",
            "spellbook": "special",
            "tool": "special",
            "treasure": "special"
        }
        
        # 在庫設定
        stock_settings = {
            "weapon": {"min": 2, "max": 5},
            "armor": {"min": 1, "max": 3},
            "consumable": {"min": 10, "max": 30},
            "spellbook": {"min": 1, "max": 2},
            "tool": {"min": 3, "max": 8},
            "treasure": {"min": 1, "max": 2}
        }
        
        # 全アイテムから商店で販売するものを選定
        for item_id, item in self.item_manager.items.items():
            # 特別なアイテムは販売しない
            if item.rarity.value in ["epic", "legendary"]:
                continue
                
            category = category_mapping.get(item.item_type.value, "special")
            stock_setting = stock_settings.get(item.item_type.value, {"min": 1, "max": 3})
            
            # 在庫数をランダムに決定（ここでは固定値）
            if item.item_type.value == "consumable":
                stock = 20
            elif item.item_type.value in ["weapon", "armor"]:
                stock = 3
            else:
                stock = 2
                
            self._shop_inventory[item_id] = {
                "name": item.get_name(),
                "category": category,
                "price": item.price,
                "stock": stock,
                "description": item.get_description(),
                "item_type": item.item_type.value,
                "rarity": item.rarity.value,
                "item_object": item
            }
    
    def _confirm_purchase(self, item_id: str, quantity: int) -> ServiceResult:
        """購入確認"""
        if item_id not in self._shop_inventory:
            return ServiceResultFactory.error("そのアイテムは取り扱っていません")
        
        item = self._shop_inventory[item_id]
        total_cost = item["price"] * quantity
        
        # 在庫チェック
        if quantity > item["stock"]:
            return ServiceResultFactory.error(
                f"在庫が不足しています（在庫: {item['stock']}個）",
                result_type=ResultType.WARNING
            )
        
        # 所持金チェック
        if self.party and self.party.gold < total_cost:
            return ServiceResultFactory.error(
                f"所持金が不足しています（必要: {total_cost} G）",
                result_type=ResultType.WARNING
            )
        
        return ServiceResultFactory.confirm(
            f"{item['name']}を{quantity}個購入しますか？（{total_cost} G）",
            data={
                "item_id": item_id,
                "quantity": quantity,
                "total_cost": total_cost,
                "action": "buy"
            }
        )
    
    def _execute_purchase(self, item_id: str, quantity: int) -> ServiceResult:
        """購入を実行"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        if item_id not in self._shop_inventory:
            return ServiceResult(False, "そのアイテムは取り扱っていません")
        
        item = self._shop_inventory[item_id]
        total_cost = item["price"] * quantity
        
        # 最終チェック
        if quantity > item["stock"]:
            return ServiceResult(False, "在庫が不足しています")
        
        if self.party.gold < total_cost:
            return ServiceResult(False, "所持金が不足しています")
        
        # 購入処理
        self.party.gold -= total_cost
        self._shop_inventory[item_id]["stock"] -= quantity
        
        # アイテムインスタンスを作成
        item_instance = self.item_manager.create_item_instance(item_id, quantity)
        if not item_instance:
            return ServiceResult(False, "アイテムの作成に失敗しました")
        
        # パーティインベントリに追加
        party_inventory = inventory_manager.get_party_inventory()
        if not party_inventory:
            # パーティインベントリがない場合は作成
            party_inventory = inventory_manager.create_party_inventory(self.party.party_id)
        
        if not party_inventory.add_item(item_instance):
            # インベントリに追加できない場合は返金
            self.party.gold += total_cost
            self._shop_inventory[item_id]["stock"] += quantity
            return ServiceResult(False, "インベントリが満杯のため購入できません")
        
        return ServiceResult(
            success=True,
            message=f"{item['name']}を{quantity}個購入しました（{total_cost} G）",
            result_type=ResultType.SUCCESS,
            data={
                "item_id": item_id,
                "quantity": quantity,
                "remaining_gold": self.party.gold
            }
        )
    
    # 売却関連
    
    def _handle_sell(self, params: Dict[str, Any]) -> ServiceResult:
        """売却を処理"""
        item_id = params.get("item_id")
        
        if not item_id:
            # 売却可能アイテムリストを表示
            return self._get_sellable_items()
        
        # 確認→実行フローを使用
        return ConfirmationFlowUtility.handle_confirmation_flow(
            params,
            lambda p: self._confirm_sell(p.get("item_id"), p.get("quantity", 1)),
            lambda p: self._execute_sell(p.get("item_id"), p.get("quantity", 1))
        )
    
    def _get_sellable_items(self) -> ServiceResult:
        """売却可能アイテムを取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        sellable_items = []
        
        # パーティインベントリから売却可能アイテムを収集
        party_inventory = inventory_manager.get_party_inventory()
        if party_inventory:
            for slot_index, item_instance in party_inventory.get_all_items():
                item = self.item_manager.get_item_info(item_instance)
                if item:
                    # 重要アイテムでない場合は売却可能
                    sell_price = self.item_manager.get_sell_price(item_instance)
                    sellable_items.append({
                        "slot_index": slot_index,
                        "item_id": item_instance.item_id,
                        "name": item.get_name(),
                        "display_name": self.item_manager.get_item_display_name(item_instance),
                        "quantity": item_instance.quantity,
                        "base_price": item.price,
                        "sell_price": sell_price,
                        "owner_type": "party",
                        "owner_id": "party",  # パーティアイテムのowner_idを追加
                        "owner_name": "パーティ",
                        "condition": item_instance.condition,
                        "identified": item_instance.identified
                    })
        
        # キャラクターインベントリからも収集
        for member in self.party.members:
            if member.is_alive():
                char_inventory = inventory_manager.get_character_inventory(member.character_id)
                if char_inventory:
                    for slot_index, item_instance in char_inventory.get_all_items():
                        item = self.item_manager.get_item_info(item_instance)
                        if item:
                            sell_price = self.item_manager.get_sell_price(item_instance)
                            sellable_items.append({
                                "slot_index": slot_index,
                                "item_id": item_instance.item_id,
                                "name": item.get_name(),
                                "display_name": self.item_manager.get_item_display_name(item_instance),
                                "quantity": item_instance.quantity,
                                "base_price": item.price,
                                "sell_price": sell_price,
                                "owner_type": "character",
                                "owner_id": member.character_id,
                                "owner_name": member.name,
                                "condition": item_instance.condition,
                                "identified": item_instance.identified
                            })
        
        return ServiceResult(
            success=True,
            message="売却可能アイテム",
            data={
                "items": sellable_items,
                "sell_rate": self.sell_rate,
                "party_gold": self.party.gold
            }
        )
    
    def _confirm_sell(self, item_id: str, quantity: int) -> ServiceResult:
        """売却確認"""
        # 売却可能アイテムから該当アイテムを検索
        sellable_result = self._get_sellable_items()
        if not sellable_result.success:
            return sellable_result
        
        sellable_items = sellable_result.data.get("items", [])
        target_item = None
        
        for item_info in sellable_items:
            if item_info["item_id"] == item_id:
                target_item = item_info
                break
        
        if not target_item:
            return ServiceResultFactory.error("そのアイテムは売却できません")
        
        if quantity > target_item["quantity"]:
            return ServiceResultFactory.error(
                f"所持数が不足しています（所持: {target_item['quantity']}個）",
                result_type=ResultType.WARNING
            )
        
        unit_price = target_item["sell_price"] // target_item["quantity"]
        total_price = unit_price * quantity
        
        return ServiceResultFactory.confirm(
            f"{target_item['display_name']}を{quantity}個売却しますか？（{total_price} G）",
            data={
                "item_id": item_id,
                "quantity": quantity,
                "total_price": total_price,
                "slot_index": target_item["slot_index"],
                "owner_type": target_item["owner_type"],
                "owner_id": target_item.get("owner_id"),
                "action": "sell"
            }
        )
    
    def _execute_sell(self, item_id: str, quantity: int) -> ServiceResult:
        """売却を実行"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        # 売却確認で取得した情報を再度取得
        confirm_result = self._confirm_sell(item_id, quantity)
        if not confirm_result.success:
            return confirm_result
        
        sell_data = confirm_result.data
        slot_index = sell_data["slot_index"]
        owner_type = sell_data["owner_type"]
        owner_id = sell_data.get("owner_id")
        total_price = sell_data["total_price"]
        
        # インベントリからアイテムを削除
        if owner_type == "party":
            party_inventory = inventory_manager.get_party_inventory()
            if not party_inventory:
                return ServiceResult(False, "パーティインベントリが存在しません")
            
            removed_item = party_inventory.remove_item(slot_index, quantity)
        elif owner_type == "character":
            char_inventory = inventory_manager.get_character_inventory(owner_id)
            if not char_inventory:
                return ServiceResult(False, "キャラクターインベントリが存在しません")
            
            removed_item = char_inventory.remove_item(slot_index, quantity)
        else:
            return ServiceResult(False, "不正な所有者タイプです")
        
        if not removed_item:
            return ServiceResult(False, "アイテムの削除に失敗しました")
        
        # 代金を受け取る
        self.party.gold += total_price
        
        # 表示名を取得
        display_name = self.item_manager.get_item_display_name(removed_item)
        
        return ServiceResult(
            success=True,
            message=f"{display_name}を売却しました（{total_price} G）",
            result_type=ResultType.SUCCESS,
            data={
                "item_id": item_id,
                "quantity": quantity,
                "earned": total_price,
                "new_gold": self.party.gold,
                "item_name": display_name
            }
        )
    
    # 鑑定関連
    
    def _handle_identify(self, params: Dict[str, Any]) -> ServiceResult:
        """鑑定を処理"""
        item_id = params.get("item_id")
        
        if not item_id:
            # 未鑑定アイテムリストを表示
            return self._get_unidentified_items()
        
        # 確認→実行フローを使用
        return ConfirmationFlowUtility.handle_confirmation_flow(
            params,
            lambda p: self._confirm_identify(p.get("item_id")),
            lambda p: self._execute_identify(p.get("item_id"))
        )
    
    def _get_unidentified_items(self) -> ServiceResult:
        """未鑑定アイテムを取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        unidentified_items = []
        
        # パーティインベントリから未鑑定アイテムを収集
        party_inventory = inventory_manager.get_party_inventory()
        if party_inventory:
            for slot_index, item_instance in party_inventory.get_all_items():
                if not item_instance.identified:
                    item = self.item_manager.get_item_info(item_instance)
                    if item:
                        unidentified_items.append({
                            "slot_index": slot_index,
                            "item_id": item_instance.item_id,
                            "instance_id": item_instance.instance_id,
                            "display_name": self.item_manager.get_item_display_name(item_instance),
                            "quantity": item_instance.quantity,
                            "owner_type": "party"
                        })
        
        # キャラクターインベントリからも収集
        for member in self.party.members:
            if member.is_alive():
                char_inventory = inventory_manager.get_character_inventory(member.character_id)
                if char_inventory:
                    for slot_index, item_instance in char_inventory.get_all_items():
                        if not item_instance.identified:
                            item = self.item_manager.get_item_info(item_instance)
                            if item:
                                unidentified_items.append({
                                    "slot_index": slot_index,
                                    "item_id": item_instance.item_id,
                                    "instance_id": item_instance.instance_id,
                                    "display_name": self.item_manager.get_item_display_name(item_instance),
                                    "quantity": item_instance.quantity,
                                    "owner_type": "character",
                                    "owner_id": member.character_id,
                                    "owner_name": member.name
                                })
        
        if not unidentified_items:
            return ServiceResult(
                success=True,
                message="未鑑定のアイテムはありません",
                result_type=ResultType.INFO
            )
        
        return ServiceResult(
            success=True,
            message="未鑑定アイテム",
            data={
                "items": unidentified_items,
                "identify_cost": self.identify_cost,
                "party_gold": self.party.gold
            }
        )
    
    def _confirm_identify(self, item_id: str) -> ServiceResult:
        """鑑定確認"""
        if self.party and self.party.gold < self.identify_cost:
            return ServiceResult(
                success=False,
                message=f"鑑定料金が不足しています（必要: {self.identify_cost} G）",
                result_type=ResultType.WARNING
            )
        
        # 未鑑定アイテムから該当アイテムを検索
        unidentified_result = self._get_unidentified_items()
        if not unidentified_result.success:
            return unidentified_result
        
        unidentified_items = unidentified_result.data.get("items", [])
        target_item = None
        
        for item_info in unidentified_items:
            if item_info["item_id"] == item_id or item_info["instance_id"] == item_id:
                target_item = item_info
                break
        
        if not target_item:
            return ServiceResultFactory.error("そのアイテムは鑑定できません")
        
        return ServiceResultFactory.confirm(
            f"{target_item['display_name']}を鑑定しますか？（{self.identify_cost} G）",
            data={
                "item_id": item_id,
                "instance_id": target_item["instance_id"],
                "slot_index": target_item["slot_index"],
                "owner_type": target_item["owner_type"],
                "owner_id": target_item.get("owner_id"),
                "cost": self.identify_cost,
                "action": "identify"
            }
        )
    
    def _execute_identify(self, item_id: str) -> ServiceResult:
        """鑑定を実行"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        if self.party.gold < self.identify_cost:
            return ServiceResult(False, "鑑定料金が不足しています")
        
        # 鑑定確認で取得した情報を再度取得
        confirm_result = self._confirm_identify(item_id)
        if not confirm_result.success:
            return confirm_result
        
        identify_data = confirm_result.data
        instance_id = identify_data["instance_id"]
        slot_index = identify_data["slot_index"]
        owner_type = identify_data["owner_type"]
        owner_id = identify_data.get("owner_id")
        
        # インベントリからアイテムインスタンスを取得
        item_instance = None
        if owner_type == "party":
            party_inventory = inventory_manager.get_party_inventory()
            if party_inventory and slot_index < len(party_inventory.slots):
                slot = party_inventory.slots[slot_index]
                if not slot.is_empty() and slot.item_instance.instance_id == instance_id:
                    item_instance = slot.item_instance
        elif owner_type == "character":
            char_inventory = inventory_manager.get_character_inventory(owner_id)
            if char_inventory and slot_index < len(char_inventory.slots):
                slot = char_inventory.slots[slot_index]
                if not slot.is_empty() and slot.item_instance.instance_id == instance_id:
                    item_instance = slot.item_instance
        
        if not item_instance:
            return ServiceResult(False, "アイテムが見つかりません")
        
        if item_instance.identified:
            return ServiceResult(False, "このアイテムは既に鑑定済みです")
        
        # 料金を支払う
        self.party.gold -= self.identify_cost
        
        # 鑑定実行
        old_display_name = self.item_manager.get_item_display_name(item_instance)
        success = self.item_manager.identify_item(item_instance)
        
        if not success:
            # 失敗した場合は返金
            self.party.gold += self.identify_cost
            return ServiceResult(False, "鑑定に失敗しました")
        
        # 鑑定後の表示名を取得
        new_display_name = self.item_manager.get_item_display_name(item_instance)
        item = self.item_manager.get_item_info(item_instance)
        identified_name = item.get_name() if item else "不明なアイテム"
        
        return ServiceResult(
            success=True,
            message=f"鑑定完了！「{identified_name}」でした",
            result_type=ResultType.SUCCESS,
            data={
                "item_id": item_instance.item_id,
                "instance_id": item_instance.instance_id,
                "old_name": old_display_name,
                "identified_name": identified_name,
                "new_display_name": new_display_name,
                "remaining_gold": self.party.gold
            }
        )
    
    # ヘルパーメソッド
    
    def _has_items_to_sell(self) -> bool:
        """売却可能なアイテムがあるかチェック"""
        if not self.party:
            return False
        
        # パーティインベントリをチェック
        party_inventory = inventory_manager.get_party_inventory()
        if party_inventory:
            for _, item_instance in party_inventory.get_all_items():
                return True  # アイテムがあれば売却可能
        
        # キャラクターインベントリをチェック
        for member in self.party.members:
            if member.is_alive():
                char_inventory = inventory_manager.get_character_inventory(member.character_id)
                if char_inventory:
                    for _, item_instance in char_inventory.get_all_items():
                        return True  # アイテムがあれば売却可能
        
        return False
    
    def _has_unidentified_items(self) -> bool:
        """未鑑定アイテムがあるかチェック"""
        if not self.party:
            return False
        
        # パーティインベントリをチェック
        party_inventory = inventory_manager.get_party_inventory()
        if party_inventory:
            for _, item_instance in party_inventory.get_all_items():
                if not item_instance.identified:
                    return True
        
        # キャラクターインベントリをチェック
        for member in self.party.members:
            if member.is_alive():
                char_inventory = inventory_manager.get_character_inventory(member.character_id)
                if char_inventory:
                    for _, item_instance in char_inventory.get_all_items():
                        if not item_instance.identified:
                            return True
        
        return False
    
    def create_service_panel(self, service_id: str, rect, parent, ui_manager):
        """商店専用のサービスパネルを作成"""
        logger.info(f"[DEBUG] ShopService.create_service_panel called: service_id={service_id}")
        try:
            if service_id == "buy":
                # 購入パネル
                from src.facilities.ui.shop.buy_panel import BuyPanel
                return BuyPanel(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
                
            elif service_id == "sell":
                # 売却パネル
                from src.facilities.ui.shop.sell_panel import SellPanel
                return SellPanel(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
                
            elif service_id == "identify":
                # 鑑定パネル
                from src.facilities.ui.shop.identify_panel import IdentifyPanel
                return IdentifyPanel(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
                
        except ImportError as e:
            logger.error(f"Failed to import shop panel: {e}")
            
        # フォールバック：Noneを返してgenericパネルを使用
        return None