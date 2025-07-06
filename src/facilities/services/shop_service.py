"""商店サービス"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..core.facility_service import FacilityService, MenuItem
from ..core.service_result import ServiceResult, ResultType
# 正しいインポートパスに修正
try:
    from src.core.game_manager import GameManager as Game
except ImportError:
    Game = None

from src.character.party import Party
from src.character.character import Character

# モデルクラスは必要に応じて後で実装
ItemModel = None
Item = None

logger = logging.getLogger(__name__)


class ShopService(FacilityService):
    """商店サービス
    
    アイテムの購入、売却、鑑定などの機能を提供する。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__("shop")
        # GameManagerはシングルトンではないため、必要時に別途設定
        self.game = None
        self.item_model = ItemModel() if ItemModel else None
        
        # 商店の在庫
        self._shop_inventory: Dict[str, Dict[str, Any]] = {}
        self._last_stock_refresh: Optional[datetime] = None
        self._stock_refresh_interval = timedelta(days=1)  # 1日ごとに在庫更新
        
        # 売却レート
        self.sell_rate = 0.5  # アイテム価値の50%で買い取り
        
        # 鑑定料金
        self.identify_cost = 100
        
        logger.info("ShopService initialized")
    
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
            enabled=self._has_items_to_sell(),
            service_type="panel"
        ))
        
        # 鑑定
        items.append(MenuItem(
            id="identify",
            label="鑑定",
            description="未鑑定のアイテムを鑑定します",
            enabled=self._has_unidentified_items(),
            service_type="action"
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
        logger.info(f"Executing action: {action_id} with params: {params}")
        
        try:
            if action_id == "buy":
                return self._handle_buy(params)
            elif action_id == "sell":
                return self._handle_sell(params)
            elif action_id == "identify":
                return self._handle_identify(params)
            elif action_id == "exit":
                return ServiceResult(True, "商店から退出しました")
            else:
                return ServiceResult(False, f"不明なアクション: {action_id}")
                
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return ServiceResult(False, f"エラーが発生しました: {str(e)}")
    
    # 購入関連
    
    def _handle_buy(self, params: Dict[str, Any]) -> ServiceResult:
        """購入を処理"""
        item_id = params.get("item_id")
        quantity = params.get("quantity", 1)
        category = params.get("category")
        
        if not item_id:
            # カテゴリ別商品リストを表示
            return self._get_shop_inventory(category)
        
        # 購入確認
        if not params.get("confirmed", False):
            return self._confirm_purchase(item_id, quantity)
        
        # 購入実行
        return self._execute_purchase(item_id, quantity)
    
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
        # TODO: 実際のアイテムデータベースから生成
        # 現在は仮のデータ
        self._shop_inventory = {
            "iron_sword": {
                "name": "鉄の剣",
                "category": "weapons",
                "price": 200,
                "stock": 5,
                "description": "標準的な鉄製の剣。攻撃力+5",
                "item_type": "weapon",
                "stats": {"attack": 5}
            },
            "steel_sword": {
                "name": "鋼の剣",
                "category": "weapons",
                "price": 500,
                "stock": 2,
                "description": "高品質な鋼製の剣。攻撃力+10",
                "item_type": "weapon",
                "stats": {"attack": 10}
            },
            "leather_armor": {
                "name": "革の鎧",
                "category": "armor",
                "price": 150,
                "stock": 3,
                "description": "軽い革製の鎧。防御力+3",
                "item_type": "armor",
                "stats": {"defense": 3}
            },
            "chain_mail": {
                "name": "チェインメイル",
                "category": "armor",
                "price": 400,
                "stock": 2,
                "description": "鎖帷子。防御力+7",
                "item_type": "armor",
                "stats": {"defense": 7}
            },
            "potion": {
                "name": "ポーション",
                "category": "items",
                "price": 50,
                "stock": 20,
                "description": "HPを50回復する",
                "item_type": "consumable",
                "effect": {"hp_restore": 50}
            },
            "hi_potion": {
                "name": "ハイポーション",
                "category": "items",
                "price": 150,
                "stock": 10,
                "description": "HPを150回復する",
                "item_type": "consumable",
                "effect": {"hp_restore": 150}
            },
            "ether": {
                "name": "エーテル",
                "category": "items",
                "price": 100,
                "stock": 15,
                "description": "MPを30回復する",
                "item_type": "consumable",
                "effect": {"mp_restore": 30}
            },
            "antidote": {
                "name": "解毒剤",
                "category": "items",
                "price": 30,
                "stock": 10,
                "description": "毒状態を回復する",
                "item_type": "consumable",
                "effect": {"cure_poison": True}
            },
            "magic_scroll": {
                "name": "魔法の巻物",
                "category": "special",
                "price": 1000,
                "stock": 1,
                "description": "一度だけ強力な魔法を使える",
                "item_type": "special"
            }
        }
    
    def _confirm_purchase(self, item_id: str, quantity: int) -> ServiceResult:
        """購入確認"""
        if item_id not in self._shop_inventory:
            return ServiceResult(False, "そのアイテムは取り扱っていません")
        
        item = self._shop_inventory[item_id]
        total_cost = item["price"] * quantity
        
        # 在庫チェック
        if quantity > item["stock"]:
            return ServiceResult(
                success=False,
                message=f"在庫が不足しています（在庫: {item['stock']}個）",
                result_type=ResultType.WARNING
            )
        
        # 所持金チェック
        if self.party and self.party.gold < total_cost:
            return ServiceResult(
                success=False,
                message=f"所持金が不足しています（必要: {total_cost} G）",
                result_type=ResultType.WARNING
            )
        
        return ServiceResult(
            success=True,
            message=f"{item['name']}を{quantity}個購入しますか？（{total_cost} G）",
            result_type=ResultType.CONFIRM,
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
        
        # TODO: 実際のアイテムをパーティに追加
        # 現在は仮の処理
        
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
        quantity = params.get("quantity", 1)
        
        if not item_id:
            # 売却可能アイテムリストを表示
            return self._get_sellable_items()
        
        # 売却確認
        if not params.get("confirmed", False):
            return self._confirm_sell(item_id, quantity)
        
        # 売却実行
        return self._execute_sell(item_id, quantity)
    
    def _get_sellable_items(self) -> ServiceResult:
        """売却可能アイテムを取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        sellable_items = []
        
        # パーティメンバーの全アイテムを収集
        for member in self.party.members:
            if member.is_alive() and hasattr(member, 'inventory'):
                for item in member.inventory.get_all_items():
                    # 重要アイテムは売却不可
                    if not item.is_key_item():
                        sell_price = int(item.value * self.sell_rate)
                        sellable_items.append({
                            "id": item.id,
                            "name": item.name,
                            "quantity": getattr(item, 'quantity', 1),
                            "base_price": item.value,
                            "sell_price": sell_price,
                            "owner_id": member.id,
                            "owner_name": member.name
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
        # TODO: 実際のアイテム情報を取得
        # 現在は仮の処理
        item_name = "アイテム"
        sell_price = 25  # 仮の価格
        total_price = sell_price * quantity
        
        return ServiceResult(
            success=True,
            message=f"{item_name}を{quantity}個売却しますか？（{total_price} G）",
            result_type=ResultType.CONFIRM,
            data={
                "item_id": item_id,
                "quantity": quantity,
                "total_price": total_price,
                "action": "sell"
            }
        )
    
    def _execute_sell(self, item_id: str, quantity: int) -> ServiceResult:
        """売却を実行"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        # TODO: 実際の売却処理
        # 現在は仮の処理
        sell_price = 25
        total_price = sell_price * quantity
        
        self.party.gold += total_price
        
        return ServiceResult(
            success=True,
            message=f"アイテムを{quantity}個売却しました（{total_price} G）",
            result_type=ResultType.SUCCESS,
            data={
                "quantity": quantity,
                "earned": total_price,
                "new_gold": self.party.gold
            }
        )
    
    # 鑑定関連
    
    def _handle_identify(self, params: Dict[str, Any]) -> ServiceResult:
        """鑑定を処理"""
        item_id = params.get("item_id")
        
        if not item_id:
            # 未鑑定アイテムリストを表示
            return self._get_unidentified_items()
        
        # 鑑定確認
        if not params.get("confirmed", False):
            return self._confirm_identify(item_id)
        
        # 鑑定実行
        return self._execute_identify(item_id)
    
    def _get_unidentified_items(self) -> ServiceResult:
        """未鑑定アイテムを取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        unidentified_items = []
        
        # TODO: 実際の未鑑定アイテムを収集
        # 現在は仮のデータ
        unidentified_items = [
            {
                "id": "unknown_ring",
                "display_name": "？？？の指輪",
                "owner_id": "char1",
                "owner_name": "Hero"
            }
        ]
        
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
        
        return ServiceResult(
            success=True,
            message=f"このアイテムを鑑定しますか？（{self.identify_cost} G）",
            result_type=ResultType.CONFIRM,
            data={
                "item_id": item_id,
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
        
        # 料金を支払う
        self.party.gold -= self.identify_cost
        
        # TODO: 実際の鑑定処理
        # 現在は仮の処理
        identified_name = "力の指輪"
        
        return ServiceResult(
            success=True,
            message=f"鑑定完了！「{identified_name}」でした",
            result_type=ResultType.SUCCESS,
            data={
                "item_id": item_id,
                "identified_name": identified_name,
                "remaining_gold": self.party.gold
            }
        )
    
    # ヘルパーメソッド
    
    def _has_items_to_sell(self) -> bool:
        """売却可能なアイテムがあるかチェック"""
        if not self.party:
            return False
        
        for member in self.party.members:
            # 新しいインベントリシステムと古いリストシステムの両方に対応
            if hasattr(member, 'inventory'):
                if hasattr(member.inventory, 'get_all_items'):
                    # 新しいインベントリシステム
                    try:
                        for item in member.inventory.get_all_items():
                            if not item.is_key_item():
                                return True
                    except Exception:
                        pass
                elif isinstance(member.inventory, list) and len(member.inventory) > 0:
                    # 古いリストシステム
                    return True
        
        return False
    
    def _has_unidentified_items(self) -> bool:
        """未鑑定アイテムがあるかチェック"""
        if not self.party:
            return False
        
        # TODO: 実際の未鑑定アイテムチェック
        # 現在は仮の実装
        return True