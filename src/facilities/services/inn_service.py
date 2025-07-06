"""宿屋サービス"""

import logging
from typing import List, Dict, Any, Optional
from ..core.facility_service import FacilityService, MenuItem
from ..core.service_result import ServiceResult, ResultType
from .service_utils import (
    ServiceResultFactory,
    PartyMemberUtility,
    ItemOperationUtility,
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

# モデルクラスは必要に応じて後で実装
ItemModel = None
SpellModel = None

logger = logging.getLogger(__name__)


class InnService(FacilityService, ActionExecutorMixin):
    """宿屋サービス
    
    休憩、冒険準備、アイテム保管などの機能を提供する。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__("inn")
        # GameManagerはシングルトンではないため、必要時に別途設定
        self.game = None
        self.item_model = ItemModel() if ItemModel else None
        self.spell_model = SpellModel() if SpellModel else None
        
        # 休憩料金の基本価格
        self.base_rest_cost = 10
        
        logger.info("InnService initialized")
    
    def get_menu_items(self) -> List[MenuItem]:
        """メニュー項目を取得"""
        items = []
        
        # 休憩
        items.append(MenuItem(
            id="rest",
            label="休憩する",
            description="パーティを休ませてHPとMPを回復します",
            enabled=self._can_rest(),
            service_type="action"
        ))
        
        # 冒険準備
        items.append(MenuItem(
            id="adventure_prep",
            label="冒険準備",
            description="冒険の準備を整えます",
            enabled=self.party is not None,
            service_type="panel"
        ))
        
        # アイテム保管
        items.append(MenuItem(
            id="storage",
            label="アイテム保管",
            description="アイテムを保管庫に預けます",
            enabled=True,
            service_type="panel"
        ))
        
        # パーティ名変更
        items.append(MenuItem(
            id="party_name",
            label="パーティ名変更",
            description="パーティの名前を変更します",
            enabled=self.party is not None,
            service_type="action"
        ))
        
        # 退出
        items.append(MenuItem(
            id="exit",
            label="宿屋を出る",
            description="宿屋から退出します",
            enabled=True,
            service_type="action"
        ))
        
        return items
    
    def can_execute(self, action_id: str) -> bool:
        """アクション実行可能かチェック"""
        valid_actions = ["rest", "adventure_prep", "storage", "party_name", "exit"]
        return action_id in valid_actions
    
    def execute_action(self, action_id: str, params: Dict[str, Any]) -> ServiceResult:
        """アクションを実行"""
        logger.info(f"Executing action: {action_id} with params: {params}")
        
        try:
            if action_id == "rest":
                return self._handle_rest(params)
            elif action_id == "adventure_prep":
                return self._handle_adventure_prep(params)
            elif action_id == "storage":
                return self._handle_storage(params)
            elif action_id == "party_name":
                return self._handle_party_name_change(params)
            elif action_id == "exit":
                return ServiceResult(True, "宿屋から退出しました")
            else:
                return ServiceResult(False, f"不明なアクション: {action_id}")
                
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return ServiceResult(False, f"エラーが発生しました: {str(e)}")
    
    # 休憩関連
    
    def _handle_rest(self, params: Dict[str, Any]) -> ServiceResult:
        """休憩を処理"""
        if not self.party:
            return ServiceResult(False, "パーティが編成されていません", result_type=ResultType.ERROR)
        
        # 確認が必要な場合
        if not params.get("confirmed", False):
            cost = self._calculate_rest_cost()
            return ServiceResult(
                success=True,
                message=f"休憩料金は {cost} Gです。休憩しますか？",
                result_type=ResultType.CONFIRM,
                data={"cost": cost, "action": "rest"}
            )
        
        # 休憩を実行
        cost = self._calculate_rest_cost()
        
        # 所持金チェック
        if self.party.gold < cost:
            return ServiceResult(
                success=False,
                message="所持金が足りません",
                result_type=ResultType.WARNING
            )
        
        # 料金を支払い
        self.party.gold -= cost
        
        # 全メンバーを回復
        healed_count = 0
        for member in self.party.members:
            if member.is_alive():
                # HP/MPを全回復
                old_hp = member.hp
                old_mp = member.mp
                member.hp = member.max_hp
                member.mp = member.max_mp
                
                # 状態異常も回復（毒、麻痺など軽度のもの）
                if member.status in ["poison", "paralysis"]:
                    member.status = "normal"
                
                if old_hp < member.max_hp or old_mp < member.max_mp:
                    healed_count += 1
        
        if healed_count > 0:
            return ServiceResult(
                success=True,
                message=f"パーティは休憩して回復しました（{cost} G支払い）",
                result_type=ResultType.SUCCESS,
                data={"healed_count": healed_count, "cost": cost}
            )
        else:
            return ServiceResult(
                success=True,
                message="パーティは既に万全の状態です",
                result_type=ResultType.INFO
            )
    
    def _calculate_rest_cost(self) -> int:
        """休憩料金を計算"""
        if not self.party:
            return 0
        
        # パーティの平均レベルに基づいて計算
        total_level = sum(member.level for member in self.party.members if member.is_alive())
        avg_level = total_level // max(1, len([m for m in self.party.members if m.is_alive()]))
        
        # 基本料金 * 平均レベル
        return self.base_rest_cost * avg_level
    
    def _can_rest(self) -> bool:
        """休憩可能かチェック"""
        if not self.party:
            return False
        
        # 生存メンバーがいて、回復が必要な場合
        for member in self.party.members:
            if hasattr(member, 'derived_stats') and member.derived_stats:
                # 新しい統計システム
                if (member.derived_stats.current_hp < member.derived_stats.max_hp or 
                    member.derived_stats.current_mp < member.derived_stats.max_mp):
                    return True
            elif hasattr(member, 'status') and member.status != "normal":
                return True
        
        return False
    
    # 冒険準備関連
    
    def _handle_adventure_prep(self, params: Dict[str, Any]) -> ServiceResult:
        """冒険準備を処理"""
        sub_action = params.get("sub_action")
        
        if sub_action == "item_management":
            return self._handle_item_management(params)
        elif sub_action == "spell_management":
            return self._handle_spell_management(params)
        elif sub_action == "equipment_management":
            return self._handle_equipment_management(params)
        else:
            # 冒険準備のメインパネルを表示
            return ServiceResult(
                success=True,
                message="冒険準備画面を表示します",
                data={
                    "panel_type": "adventure_prep",
                    "sub_services": [
                        {
                            "id": "item_management",
                            "label": "アイテム管理",
                            "description": "アイテムの整理と配分"
                        },
                        {
                            "id": "spell_management",
                            "label": "魔法管理",
                            "description": "魔法の装備と管理"
                        },
                        {
                            "id": "equipment_management",
                            "label": "装備管理",
                            "description": "装備の変更と最適化"
                        }
                    ]
                }
            )
    
    def _handle_item_management(self, params: Dict[str, Any]) -> ServiceResult:
        """アイテム管理を処理"""
        action_map = {
            "transfer": self._transfer_item,
            "use": self._use_item,
            "discard": self._discard_item
        }
        default_action = self._get_party_items
        return self._handle_management_action(params, action_map, default_action)
    
    def _handle_spell_management(self, params: Dict[str, Any]) -> ServiceResult:
        """魔法管理を処理"""
        action_map = {
            "equip": self._equip_spell,
            "unequip": self._unequip_spell
        }
        default_action = self._get_party_spells
        return self._handle_management_action(params, action_map, default_action)
    
    def _handle_equipment_management(self, params: Dict[str, Any]) -> ServiceResult:
        """装備管理を処理"""
        action_map = {
            "equip": self._equip_item,
            "unequip": self._unequip_item,
            "optimize": self._optimize_equipment
        }
        default_action = self._get_party_equipment
        return self._handle_management_action(params, action_map, default_action)
    
    def _handle_management_action(self, params: Dict[str, Any], 
                                action_map: Dict[str, callable],
                                default_action: callable) -> ServiceResult:
        """管理アクションの共通ハンドラー"""
        action = params.get("action")
        
        if action and action in action_map:
            return action_map[action](params)
        else:
            return default_action()
    
    # アイテム保管関連
    
    def _handle_storage(self, params: Dict[str, Any]) -> ServiceResult:
        """アイテム保管を処理"""
        action = params.get("action")
        
        if action == "deposit":
            # アイテムを預ける
            return self._deposit_item(params)
        elif action == "withdraw":
            # アイテムを引き出す
            return self._withdraw_item(params)
        else:
            # 保管庫の内容を表示
            return self._get_storage_contents()
    
    def _deposit_item(self, params: Dict[str, Any]) -> ServiceResult:
        """アイテムを預ける"""
        return ItemOperationUtility.handle_item_operation(
            params, "deposit", "預けました"
        )
    
    def _withdraw_item(self, params: Dict[str, Any]) -> ServiceResult:
        """アイテムを引き出す"""
        return ItemOperationUtility.handle_item_operation(
            params, "withdraw", "引き出しました"
        )
    
    def _get_storage_contents(self) -> ServiceResult:
        """保管庫の内容を取得"""
        # TODO: 保管庫システムの実装
        # 現在は仮のデータを返す
        storage_items = []
        
        return ServiceResult(
            success=True,
            message="保管庫の内容",
            data={
                "items": storage_items,
                "capacity": 100,
                "used": len(storage_items)
            }
        )
    
    # パーティ名変更関連
    
    def _handle_party_name_change(self, params: Dict[str, Any]) -> ServiceResult:
        """パーティ名変更を処理"""
        new_name = params.get("name")
        
        if not new_name:
            # 名前入力画面を表示
            return ServiceResult(
                success=True,
                message="新しいパーティ名を入力してください",
                data={
                    "current_name": self.party.name if self.party else "未設定",
                    "input_required": True
                }
            )
        
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        # 名前の検証
        if len(new_name) < 1 or len(new_name) > 20:
            return ServiceResult(
                success=False,
                message="パーティ名は1～20文字で入力してください",
                result_type=ResultType.WARNING
            )
        
        # 名前を変更
        old_name = self.party.name
        self.party.name = new_name
        
        return ServiceResult(
            success=True,
            message=f"パーティ名を「{old_name}」から「{new_name}」に変更しました",
            result_type=ResultType.SUCCESS
        )
    
    # ヘルパーメソッド
    
    def _get_party_items(self) -> ServiceResult:
        """パーティの全アイテムを取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        items_by_character = {}
        for member in self.party.members:
            if member.is_alive():
                items_by_character[member.id] = {
                    "name": member.name,
                    "items": member.inventory.get_all_items()
                }
        
        return ServiceResult(
            success=True,
            message="パーティのアイテム一覧",
            data={"items_by_character": items_by_character}
        )
    
    def _get_party_spells(self) -> ServiceResult:
        """パーティの全魔法を取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        spells_by_character = {}
        for member in self.party.members:
            if member.is_alive() and member.can_use_magic():
                spells_by_character[member.id] = {
                    "name": member.name,
                    "learned_spells": member.get_learned_spells(),
                    "equipped_spells": member.get_equipped_spells()
                }
        
        return ServiceResult(
            success=True,
            message="パーティの魔法一覧",
            data={"spells_by_character": spells_by_character}
        )
    
    def _get_party_equipment(self) -> ServiceResult:
        """パーティの全装備を取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        equipment_by_character = {}
        for member in self.party.members:
            if member.is_alive():
                equipment_by_character[member.id] = {
                    "name": member.name,
                    "equipment": member.get_equipment(),
                    "stats": {
                        "ac": member.ac,
                        "attack": member.attack_bonus,
                        "defense": member.defense_bonus
                    }
                }
        
        return ServiceResult(
            success=True,
            message="パーティの装備一覧",
            data={"equipment_by_character": equipment_by_character}
        )
    
    def _transfer_item(self, params: Dict[str, Any]) -> ServiceResult:
        """アイテムを転送"""
        # TODO: 実装
        return ServiceResult(True, "アイテム転送機能は実装中です", result_type=ResultType.INFO)
    
    def _use_item(self, params: Dict[str, Any]) -> ServiceResult:
        """アイテムを使用"""
        # TODO: 実装
        return ServiceResult(True, "アイテム使用機能は実装中です", result_type=ResultType.INFO)
    
    def _discard_item(self, params: Dict[str, Any]) -> ServiceResult:
        """アイテムを破棄"""
        # TODO: 実装
        return ServiceResult(True, "アイテム破棄機能は実装中です", result_type=ResultType.INFO)
    
    def _equip_spell(self, params: Dict[str, Any]) -> ServiceResult:
        """魔法を装備"""
        # TODO: 実装
        return ServiceResult(True, "魔法装備機能は実装中です", result_type=ResultType.INFO)
    
    def _unequip_spell(self, params: Dict[str, Any]) -> ServiceResult:
        """魔法を外す"""
        # TODO: 実装
        return ServiceResult(True, "魔法解除機能は実装中です", result_type=ResultType.INFO)
    
    def _equip_item(self, params: Dict[str, Any]) -> ServiceResult:
        """装備を着ける"""
        # TODO: 実装
        return ServiceResult(True, "装備変更機能は実装中です", result_type=ResultType.INFO)
    
    def _unequip_item(self, params: Dict[str, Any]) -> ServiceResult:
        """装備を外す"""
        # TODO: 実装
        return ServiceResult(True, "装備解除機能は実装中です", result_type=ResultType.INFO)
    
    def _optimize_equipment(self, params: Dict[str, Any]) -> ServiceResult:
        """装備を最適化"""
        # TODO: 実装
        return ServiceResult(True, "装備最適化機能は実装中です", result_type=ResultType.INFO)