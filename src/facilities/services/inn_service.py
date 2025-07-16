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
        
        # コントローラーへの参照（後で設定される）
        self._controller = None
        
        # 宿屋倉庫管理
        from src.overworld.inn_storage import inn_storage_manager
        self.storage_manager = inn_storage_manager
        
        logger.info("InnService initialized")
    
    def set_controller(self, controller):
        """コントローラーを設定"""
        self._controller = controller
    
    def get_menu_items(self) -> List[MenuItem]:
        """メニュー項目を取得"""
        items = []
        
        # アイテム管理（旧：アイテム保管）
        items.append(MenuItem(
            id="storage",
            label="アイテム管理",
            description="アイテムを保管庫に預けます",
            enabled=True,
            service_type="panel"
        ))
        
        # アイテム装備
        items.append(MenuItem(
            id="equipment",
            label="アイテム装備",
            description="キャラクターの装備を変更します",
            enabled=self.party is not None,
            service_type="panel"
        ))
        
        # 魔術/祈祷
        items.append(MenuItem(
            id="spell_management",
            label="魔術/祈祷",
            description="魔術・祈祷スロットを管理します",
            enabled=self.party is not None,
            service_type="panel"
        ))
        
        # パーティ名変更
        items.append(MenuItem(
            id="party_name",
            label="パーティ名変更",
            description="パーティの名前を変更します",
            enabled=self.party is not None,
            service_type="panel"
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
        valid_actions = ["storage", "party_name", "exit"]
        return action_id in valid_actions
    
    def execute_action(self, action_id: str, params: Dict[str, Any]) -> ServiceResult:
        """アクションを実行"""
        logger.info(f"Executing action: {action_id} with params: {params}")
        
        try:
            if action_id == "adventure_prep":
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
    
    
    # 冒険準備関連
    
    def _handle_adventure_prep(self, params: Dict[str, Any]) -> ServiceResult:
        """冒険準備を処理"""
        # 冒険準備パネルの表示はUI側で処理されるため、成功を返すだけ
        return ServiceResult(
            success=True,
            message="冒険準備画面を表示します",
            result_type=ResultType.SUCCESS
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
            return self._deposit_item(params)
        elif action == "withdraw":
            return self._withdraw_item(params)
        elif action == "get_inventory":
            return self._get_inventory_items(params)
        else:
            # アクションが指定されていない場合はパネル表示のためのメッセージ
            return ServiceResult(
                success=True,
                message="アイテム保管画面を表示します",
                result_type=ResultType.SUCCESS
            )
    
    def _deposit_item(self, params: Dict[str, Any]) -> ServiceResult:
        """アイテムを預ける"""
        item_id = params.get("item_id")
        quantity = params.get("quantity", 1)
        
        if not item_id:
            return ServiceResult(False, "アイテムIDが指定されていません")
        
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        # パーティからアイテムを検索
        item_found = False
        item_name = ""
        
        for member in self.party.members:
            if hasattr(member, 'inventory') and member.inventory:
                for item in member.inventory.get_all_items():
                    if item.id == item_id:
                        item_found = True
                        item_name = item.name
                        
                        # 数量チェック
                        available_quantity = getattr(item, 'quantity', 1)
                        if quantity > available_quantity:
                            return ServiceResult(
                                False, 
                                f"指定された数量（{quantity}）が所持数（{available_quantity}）を超えています"
                            )
                        
                        # アイテムを保管庫に移動
                        try:
                            # 宿屋保管庫に追加
                            self.storage_manager.add_item(item_id, item_name, quantity)
                            
                            # メンバーのインベントリから削除
                            member.inventory.remove_item(item_id, quantity)
                            
                            return ServiceResult(
                                success=True,
                                message=f"{item_name}を{quantity}個預けました",
                                result_type=ResultType.SUCCESS
                            )
                        except Exception as e:
                            logger.error(f"Failed to deposit item: {e}")
                            return ServiceResult(
                                False,
                                f"アイテムの預け入れに失敗しました: {str(e)}"
                            )
        
        if not item_found:
            return ServiceResult(False, "指定されたアイテムが見つかりません")
        
        return ServiceResult(False, "アイテムの預け入れに失敗しました")
    
    def _withdraw_item(self, params: Dict[str, Any]) -> ServiceResult:
        """アイテムを引き出す"""
        item_id = params.get("item_id")
        quantity = params.get("quantity", 1)
        
        if not item_id:
            return ServiceResult(False, "アイテムIDが指定されていません")
        
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        # 保管庫からアイテムを検索
        try:
            storage_items = self.storage_manager.get_all_items()
            item_found = False
            item_name = ""
            
            for storage_item in storage_items:
                if storage_item.get("id") == item_id:
                    item_found = True
                    item_name = storage_item.get("name", item_id)
                    
                    # 数量チェック
                    available_quantity = storage_item.get("quantity", 1)
                    if quantity > available_quantity:
                        return ServiceResult(
                            False,
                            f"指定された数量（{quantity}）が保管数（{available_quantity}）を超えています"
                        )
                    
                    # 最初のアクティブなメンバーのインベントリに追加
                    target_member = None
                    for member in self.party.members:
                        if member.is_alive() and hasattr(member, 'inventory'):
                            target_member = member
                            break
                    
                    if not target_member:
                        return ServiceResult(
                            False,
                            "アイテムを受け取れるメンバーがいません"
                        )
                    
                    # アイテムを移動
                    try:
                        # 保管庫から削除
                        self.storage_manager.remove_item(item_id, quantity)
                        
                        # メンバーのインベントリに追加
                        target_member.inventory.add_item(item_id, quantity)
                        
                        return ServiceResult(
                            success=True,
                            message=f"{item_name}を{quantity}個引き出しました（{target_member.name}が受け取りました）",
                            result_type=ResultType.SUCCESS
                        )
                    except Exception as e:
                        logger.error(f"Failed to withdraw item: {e}")
                        return ServiceResult(
                            False,
                            f"アイテムの引き出しに失敗しました: {str(e)}"
                        )
            
            if not item_found:
                return ServiceResult(False, "指定されたアイテムが保管庫に見つかりません")
                
        except Exception as e:
            logger.error(f"Failed to access storage: {e}")
            return ServiceResult(
                False,
                f"保管庫へのアクセスに失敗しました: {str(e)}"
            )
        
        return ServiceResult(False, "アイテムの引き出しに失敗しました")
    
    def _get_inventory_items(self, params: Dict[str, Any]) -> ServiceResult:
        """インベントリアイテムを取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        inventory_items = []
        
        # 全メンバーのアイテムを収集
        for member in self.party.members:
            if hasattr(member, 'inventory') and member.inventory:
                for item in member.inventory.get_all_items():
                    inventory_items.append({
                        "id": item.id,
                        "name": item.name,
                        "quantity": getattr(item, 'quantity', 1),
                        "stackable": getattr(item, 'stackable', True),
                        "owner": member.name
                    })
        
        # アイテムがない場合はデモデータを返す
        if not inventory_items:
            inventory_items = [
                {"id": "demo_potion", "name": "ポーション", "quantity": 5, "stackable": True, "owner": "Demo"},
                {"id": "demo_ether", "name": "エーテル", "quantity": 3, "stackable": True, "owner": "Demo"},
                {"id": "demo_sword", "name": "鉄の剣", "quantity": 1, "stackable": False, "owner": "Demo"}
            ]
        
        return ServiceResult(
            success=True,
            message="インベントリを取得しました",
            data={"items": inventory_items},
            result_type=ResultType.SUCCESS
        )
    
    def _get_storage_contents(self) -> ServiceResult:
        """保管庫の内容を取得"""
        try:
            storage_items = self.storage_manager.get_all_items()
            
            return ServiceResult(
                success=True,
                message="保管庫の内容",
                data={
                    "items": storage_items,
                    "capacity": 100,
                    "used": len(storage_items)
                }
            )
        except Exception as e:
            logger.error(f"Failed to get storage contents: {e}")
            # フォールバック: 空の保管庫を返す
            return ServiceResult(
                success=True,
                message="保管庫の内容",
                data={
                    "items": [],
                    "capacity": 100,
                    "used": 0
                }
            )
    
    # パーティ名変更関連
    
    def _handle_party_name_change(self, params: Dict[str, Any]) -> ServiceResult:
        """パーティ名変更を処理"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません", result_type=ResultType.ERROR)
        
        new_name = params.get("name")
        
        if not new_name:
            # 名前入力が必要な場合
            return ServiceResult(
                success=True,
                message="新しいパーティ名を入力してください",
                result_type=ResultType.INPUT,
                data={
                    "current_name": self.party.name,
                    "input_type": "text",
                    "input_prompt": "新しいパーティ名",
                    "max_length": 20,
                    "action": "party_name"
                }
            )
        
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
        
        logger.info(f"パーティ名を変更: {old_name} -> {new_name}")
        
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
    
    def create_service_panel(self, service_id: str, rect: 'pygame.Rect', parent: 'pygame_gui.elements.UIPanel',
                           ui_manager: 'pygame_gui.UIManager') -> Optional['ServicePanel']:
        """宿屋専用のサービスパネルを作成"""
        try:
            if service_id == "storage":
                # アイテム管理パネル（旧：アイテム保管パネル）
                from src.facilities.ui.inn.storage_panel import StoragePanel
                return StoragePanel(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
                
            elif service_id == "equipment":
                # アイテム装備パネル
                from src.facilities.ui.inn.equipment_management_panel import EquipmentManagementPanel
                return EquipmentManagementPanel(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
                
            elif service_id == "spell_management":
                # 魔術/祈祷パネル
                from src.facilities.ui.inn.spell_management_panel import SpellManagementPanel
                return SpellManagementPanel(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
                
            elif service_id == "party_name":
                # パーティ名変更パネル
                logger.info(f"Creating PartyNamePanel with controller: {self._controller}")
                logger.info(f"Controller service: {getattr(self._controller, 'service', 'None')}")
                logger.info(f"Service party: {getattr(getattr(self._controller, 'service', None), 'party', 'None')}")
                from src.facilities.ui.inn.party_name_panel import PartyNamePanel
                return PartyNamePanel(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
                
        except Exception as e:
            logger.error(f"Failed to create inn panel for {service_id}: {e}")
            # デバッグ用に詳細なエラー情報を記録
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # 未対応のサービスまたは失敗時は汎用パネルを使用
        return None