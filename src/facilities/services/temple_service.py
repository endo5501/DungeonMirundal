"""教会サービス"""

import logging
from typing import List, Dict, Any, Optional
from ..core.facility_service import FacilityService, MenuItem
from ..core.service_result import ServiceResult, ResultType
# 正しいインポートパスに修正
try:
    from src.core.game_manager import GameManager as Game
except ImportError:
    Game = None

from src.character.party import Party
from src.character.character import Character

logger = logging.getLogger(__name__)


class TempleService(FacilityService):
    """教会サービス
    
    治療、蘇生、状態異常回復、祝福、寄付などの機能を提供する。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__("temple")
        # GameManagerはシングルトンではないため、必要時に別途設定
        self.game = None
        
        # 料金設定
        self.heal_cost_per_level = 10  # レベルあたりの治療費
        self.resurrect_cost_per_level = 100  # レベルあたりの蘇生費
        self.blessing_cost = 500  # 祝福の固定料金
        
        # 状態異常治療の料金
        self.cure_costs = {
            "poison": 50,      # 毒
            "paralysis": 100,  # 麻痺
            "petrification": 500,  # 石化
            "curse": 200,      # 呪い
            "sleep": 30,       # 睡眠
            "silence": 80      # 沈黙
        }
        
        logger.info("TempleService initialized")
    
    def get_menu_items(self) -> List[MenuItem]:
        """メニュー項目を取得"""
        items = []
        
        # 治療
        items.append(MenuItem(
            id="heal",
            label="治療",
            description="キャラクターを治療します",
            enabled=self._has_injured_members(),
            service_type="action"
        ))
        
        # 蘇生
        items.append(MenuItem(
            id="resurrect",
            label="蘇生",
            description="死亡したキャラクターを蘇生させます",
            enabled=self._has_dead_members(),
            service_type="action"
        ))
        
        # 状態回復
        items.append(MenuItem(
            id="cure",
            label="状態回復",
            description="状態異常を回復します",
            enabled=self._has_status_ailments(),
            service_type="panel"
        ))
        
        # 祝福
        items.append(MenuItem(
            id="blessing",
            label="祝福",
            description="パーティに祝福を与えます",
            enabled=self.party is not None,
            service_type="action"
        ))
        
        # 寄付
        items.append(MenuItem(
            id="donation",
            label="寄付",
            description="教会に寄付をします",
            enabled=self.party is not None and self.party.gold > 0,
            service_type="action"
        ))
        
        # 退出
        items.append(MenuItem(
            id="exit",
            label="教会を出る",
            description="教会から退出します",
            enabled=True,
            service_type="action"
        ))
        
        return items
    
    def can_execute(self, action_id: str) -> bool:
        """アクション実行可能かチェック"""
        if action_id == "heal":
            return self._has_injured_members()
        elif action_id == "resurrect":
            return self._has_dead_members()
        elif action_id == "cure":
            return self._has_status_ailments()
        elif action_id == "blessing":
            return self.party is not None
        elif action_id == "donation":
            return self.party is not None and self.party.gold > 0
        elif action_id == "exit":
            return True
        else:
            return False
    
    def execute_action(self, action_id: str, params: Dict[str, Any]) -> ServiceResult:
        """アクションを実行"""
        logger.info(f"Executing action: {action_id} with params: {params}")
        
        try:
            if action_id == "heal":
                return self._handle_heal(params)
            elif action_id == "resurrect":
                return self._handle_resurrect(params)
            elif action_id == "cure":
                return self._handle_cure(params)
            elif action_id == "blessing":
                return self._handle_blessing(params)
            elif action_id == "donation":
                return self._handle_donation(params)
            elif action_id == "exit":
                return ServiceResult(True, "教会から退出しました")
            else:
                return ServiceResult(False, f"不明なアクション: {action_id}")
                
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return ServiceResult(False, f"エラーが発生しました: {str(e)}")
    
    # 治療関連
    
    def _handle_heal(self, params: Dict[str, Any]) -> ServiceResult:
        """治療を処理"""
        character_id = params.get("character_id")
        
        if not character_id:
            # 治療対象の選択画面
            return self._get_healable_members()
        
        # 治療確認
        if not params.get("confirmed", False):
            return self._confirm_heal(character_id)
        
        # 治療実行
        return self._execute_heal(character_id)
    
    def _get_healable_members(self) -> ServiceResult:
        """治療可能なメンバーを取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        healable_members = []
        
        for member in self.party.members:
            if member.is_alive() and member.hp < member.max_hp:
                cost = self._calculate_heal_cost(member)
                healable_members.append({
                    "id": member.id,
                    "name": member.name,
                    "level": member.level,
                    "hp": f"{member.hp}/{member.max_hp}",
                    "cost": cost
                })
        
        if not healable_members:
            return ServiceResult(
                success=True,
                message="治療が必要なメンバーはいません",
                result_type=ResultType.INFO
            )
        
        return ServiceResult(
            success=True,
            message="治療対象を選択してください",
            data={
                "members": healable_members,
                "party_gold": self.party.gold
            }
        )
    
    def _confirm_heal(self, character_id: str) -> ServiceResult:
        """治療確認"""
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResult(False, "キャラクターが見つかりません")
        
        cost = self._calculate_heal_cost(character)
        
        if self.party and self.party.gold < cost:
            return ServiceResult(
                success=False,
                message=f"治療費が不足しています（必要: {cost} G）",
                result_type=ResultType.WARNING
            )
        
        damage = character.max_hp - character.hp
        
        return ServiceResult(
            success=True,
            message=f"{character.name}を治療しますか？\nHP: {character.hp}/{character.max_hp} (回復量: {damage})\n費用: {cost} G",
            result_type=ResultType.CONFIRM,
            data={
                "character_id": character_id,
                "cost": cost,
                "action": "heal"
            }
        )
    
    def _execute_heal(self, character_id: str) -> ServiceResult:
        """治療を実行"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResult(False, "キャラクターが見つかりません")
        
        cost = self._calculate_heal_cost(character)
        
        if self.party.gold < cost:
            return ServiceResult(False, "治療費が不足しています")
        
        # 治療実行
        old_hp = character.hp
        character.hp = character.max_hp
        self.party.gold -= cost
        
        return ServiceResult(
            success=True,
            message=f"{character.name}のHPが{old_hp}から{character.max_hp}に回復しました",
            result_type=ResultType.SUCCESS,
            data={
                "healed_amount": character.max_hp - old_hp,
                "remaining_gold": self.party.gold
            }
        )
    
    def _calculate_heal_cost(self, character: Character) -> int:
        """治療費を計算"""
        damage = character.max_hp - character.hp
        if damage == 0:
            return 0
        
        # レベル * 10Gを基本料金として、ダメージ割合で調整
        base_cost = character.level * self.heal_cost_per_level
        damage_ratio = damage / character.max_hp
        
        return int(base_cost * damage_ratio)
    
    # 蘇生関連
    
    def _handle_resurrect(self, params: Dict[str, Any]) -> ServiceResult:
        """蘇生を処理"""
        character_id = params.get("character_id")
        
        if not character_id:
            # 蘇生対象の選択画面
            return self._get_dead_members()
        
        # 蘇生確認
        if not params.get("confirmed", False):
            return self._confirm_resurrect(character_id)
        
        # 蘇生実行
        return self._execute_resurrect(character_id)
    
    def _get_dead_members(self) -> ServiceResult:
        """死亡メンバーを取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        dead_members = []
        
        for member in self.party.members:
            if member.status in ["dead", "ashes"]:
                cost = self._calculate_resurrect_cost(member)
                dead_members.append({
                    "id": member.id,
                    "name": member.name,
                    "level": member.level,
                    "status": member.status,
                    "cost": cost,
                    "vitality": member.vitality
                })
        
        if not dead_members:
            return ServiceResult(
                success=True,
                message="蘇生が必要なメンバーはいません",
                result_type=ResultType.INFO
            )
        
        return ServiceResult(
            success=True,
            message="蘇生対象を選択してください",
            data={
                "members": dead_members,
                "party_gold": self.party.gold
            }
        )
    
    def _confirm_resurrect(self, character_id: str) -> ServiceResult:
        """蘇生確認"""
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResult(False, "キャラクターが見つかりません")
        
        cost = self._calculate_resurrect_cost(character)
        
        if self.party and self.party.gold < cost:
            return ServiceResult(
                success=False,
                message=f"蘇生費用が不足しています（必要: {cost} G）",
                result_type=ResultType.WARNING
            )
        
        # 生命力チェック
        if character.vitality <= 0:
            return ServiceResult(
                success=False,
                message=f"{character.name}は生命力が尽きているため蘇生できません",
                result_type=ResultType.ERROR
            )
        
        return ServiceResult(
            success=True,
            message=f"{character.name}を蘇生させますか？\n費用: {cost} G\n生命力が1減少します（現在: {character.vitality}）",
            result_type=ResultType.CONFIRM,
            data={
                "character_id": character_id,
                "cost": cost,
                "action": "resurrect"
            }
        )
    
    def _execute_resurrect(self, character_id: str) -> ServiceResult:
        """蘇生を実行"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResult(False, "キャラクターが見つかりません")
        
        cost = self._calculate_resurrect_cost(character)
        
        if self.party.gold < cost:
            return ServiceResult(False, "蘇生費用が不足しています")
        
        if character.vitality <= 0:
            return ServiceResult(False, "生命力が尽きているため蘇生できません")
        
        # 蘇生実行
        character.status = "normal"
        character.hp = 1  # HP1で復活
        character.vitality -= 1  # 生命力減少
        self.party.gold -= cost
        
        return ServiceResult(
            success=True,
            message=f"{character.name}が蘇生しました（生命力: {character.vitality + 1}→{character.vitality}）",
            result_type=ResultType.SUCCESS,
            data={
                "remaining_gold": self.party.gold,
                "new_vitality": character.vitality
            }
        )
    
    def _calculate_resurrect_cost(self, character: Character) -> int:
        """蘇生費用を計算"""
        base_cost = character.level * self.resurrect_cost_per_level
        
        # 灰状態は追加料金
        if character.status == "ashes":
            base_cost = int(base_cost * 1.5)
        
        return base_cost
    
    # 状態回復関連
    
    def _handle_cure(self, params: Dict[str, Any]) -> ServiceResult:
        """状態回復を処理"""
        character_id = params.get("character_id")
        status_type = params.get("status_type")
        
        if not character_id:
            # 状態異常を持つメンバーの選択画面
            return self._get_afflicted_members()
        
        if not status_type:
            # 回復する状態異常の選択画面
            return self._get_character_ailments(character_id)
        
        # 回復確認
        if not params.get("confirmed", False):
            return self._confirm_cure(character_id, status_type)
        
        # 回復実行
        return self._execute_cure(character_id, status_type)
    
    def _get_afflicted_members(self) -> ServiceResult:
        """状態異常を持つメンバーを取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        afflicted_members = []
        
        for member in self.party.members:
            if member.is_alive() and member.status != "normal":
                afflicted_members.append({
                    "id": member.id,
                    "name": member.name,
                    "level": member.level,
                    "status": member.status,
                    "status_name": self._get_status_name(member.status)
                })
        
        if not afflicted_members:
            return ServiceResult(
                success=True,
                message="状態異常のメンバーはいません",
                result_type=ResultType.INFO
            )
        
        return ServiceResult(
            success=True,
            message="治療対象を選択してください",
            data={
                "members": afflicted_members,
                "panel_type": "cure"
            }
        )
    
    def _get_character_ailments(self, character_id: str) -> ServiceResult:
        """キャラクターの状態異常を取得"""
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResult(False, "キャラクターが見つかりません")
        
        if character.status == "normal":
            return ServiceResult(
                success=True,
                message=f"{character.name}は健康です",
                result_type=ResultType.INFO
            )
        
        # 治療可能な状態異常と料金
        cost = self.cure_costs.get(character.status, 100)
        
        return ServiceResult(
            success=True,
            message="状態異常を選択してください",
            data={
                "character_id": character_id,
                "character_name": character.name,
                "status": character.status,
                "status_name": self._get_status_name(character.status),
                "cost": cost,
                "party_gold": self.party.gold if self.party else 0
            }
        )
    
    def _confirm_cure(self, character_id: str, status_type: str) -> ServiceResult:
        """状態回復確認"""
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResult(False, "キャラクターが見つかりません")
        
        cost = self.cure_costs.get(status_type, 100)
        
        if self.party and self.party.gold < cost:
            return ServiceResult(
                success=False,
                message=f"治療費が不足しています（必要: {cost} G）",
                result_type=ResultType.WARNING
            )
        
        status_name = self._get_status_name(status_type)
        
        return ServiceResult(
            success=True,
            message=f"{character.name}の{status_name}を治療しますか？（{cost} G）",
            result_type=ResultType.CONFIRM,
            data={
                "character_id": character_id,
                "status_type": status_type,
                "cost": cost,
                "action": "cure"
            }
        )
    
    def _execute_cure(self, character_id: str, status_type: str) -> ServiceResult:
        """状態回復を実行"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResult(False, "キャラクターが見つかりません")
        
        cost = self.cure_costs.get(status_type, 100)
        
        if self.party.gold < cost:
            return ServiceResult(False, "治療費が不足しています")
        
        # 状態回復実行
        old_status = character.status
        character.status = "normal"
        self.party.gold -= cost
        
        status_name = self._get_status_name(old_status)
        
        return ServiceResult(
            success=True,
            message=f"{character.name}の{status_name}が治りました",
            result_type=ResultType.SUCCESS,
            data={
                "remaining_gold": self.party.gold
            }
        )
    
    # 祝福関連
    
    def _handle_blessing(self, params: Dict[str, Any]) -> ServiceResult:
        """祝福を処理"""
        if not params.get("confirmed", False):
            return self._confirm_blessing()
        
        return self._execute_blessing()
    
    def _confirm_blessing(self) -> ServiceResult:
        """祝福確認"""
        if self.party and self.party.gold < self.blessing_cost:
            return ServiceResult(
                success=False,
                message=f"祝福の費用が不足しています（必要: {self.blessing_cost} G）",
                result_type=ResultType.WARNING
            )
        
        return ServiceResult(
            success=True,
            message=f"パーティに祝福を与えますか？（{self.blessing_cost} G）\n次の戦闘で有利な効果を得られます",
            result_type=ResultType.CONFIRM,
            data={
                "cost": self.blessing_cost,
                "action": "blessing"
            }
        )
    
    def _execute_blessing(self) -> ServiceResult:
        """祝福を実行"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        if self.party.gold < self.blessing_cost:
            return ServiceResult(False, "祝福の費用が不足しています")
        
        # 祝福実行
        self.party.gold -= self.blessing_cost
        
        # TODO: 実際の祝福効果を実装
        # 現在は仮の実装
        
        return ServiceResult(
            success=True,
            message="パーティは神の祝福を受けました！\n次の戦闘で有利な効果を得られます",
            result_type=ResultType.SUCCESS,
            data={
                "remaining_gold": self.party.gold,
                "duration": "next_battle"
            }
        )
    
    # 寄付関連
    
    def _handle_donation(self, params: Dict[str, Any]) -> ServiceResult:
        """寄付を処理"""
        amount = params.get("amount")
        
        if not amount:
            # 寄付金額の入力画面
            return ServiceResult(
                success=True,
                message="寄付する金額を入力してください",
                data={
                    "party_gold": self.party.gold if self.party else 0,
                    "input_required": True
                }
            )
        
        # 寄付確認
        if not params.get("confirmed", False):
            return self._confirm_donation(amount)
        
        # 寄付実行
        return self._execute_donation(amount)
    
    def _confirm_donation(self, amount: int) -> ServiceResult:
        """寄付確認"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        if amount <= 0:
            return ServiceResult(
                success=False,
                message="寄付金額は1G以上を指定してください",
                result_type=ResultType.WARNING
            )
        
        if amount > self.party.gold:
            return ServiceResult(
                success=False,
                message=f"所持金が不足しています（所持金: {self.party.gold} G）",
                result_type=ResultType.WARNING
            )
        
        return ServiceResult(
            success=True,
            message=f"{amount} Gを寄付しますか？",
            result_type=ResultType.CONFIRM,
            data={
                "amount": amount,
                "action": "donation"
            }
        )
    
    def _execute_donation(self, amount: int) -> ServiceResult:
        """寄付を実行"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        if amount > self.party.gold:
            return ServiceResult(False, "所持金が不足しています")
        
        # 寄付実行
        self.party.gold -= amount
        
        # TODO: カルマ値の上昇などの効果を実装
        
        # 寄付額に応じたメッセージ
        if amount >= 10000:
            message = f"多大なる寄付に感謝します！神の加護がありますように（{amount} G）"
        elif amount >= 1000:
            message = f"寛大な寄付をありがとうございます（{amount} G）"
        else:
            message = f"寄付をありがとうございます（{amount} G）"
        
        return ServiceResult(
            success=True,
            message=message,
            result_type=ResultType.SUCCESS,
            data={
                "donated_amount": amount,
                "remaining_gold": self.party.gold,
                "karma_bonus": True
            }
        )
    
    # ヘルパーメソッド
    
    def _has_injured_members(self) -> bool:
        """負傷したメンバーがいるかチェック"""
        if not self.party:
            return False
        
        for member in self.party.members:
            # 新しい統計システムを使用
            if hasattr(member, 'derived_stats') and member.derived_stats:
                if member.derived_stats.current_hp < member.derived_stats.max_hp:
                    return True
        
        return False
    
    def _has_dead_members(self) -> bool:
        """死亡したメンバーがいるかチェック"""
        if not self.party:
            return False
        
        for member in self.party.members:
            # CharacterStatus列挙型に対応
            if hasattr(member, 'status'):
                status_value = member.status.value if hasattr(member.status, 'value') else str(member.status)
                if status_value in ["dead", "ashes"]:
                    return True
        
        return False
    
    def _has_status_ailments(self) -> bool:
        """状態異常のメンバーがいるかチェック"""
        if not self.party:
            return False
        
        for member in self.party.members:
            if hasattr(member, 'status'):
                status_value = member.status.value if hasattr(member.status, 'value') else str(member.status)
                if status_value not in ["good", "normal"]:
                    return True
        
        return False
    
    def _get_character_by_id(self, character_id: str) -> Optional[Character]:
        """IDでキャラクターを取得"""
        if not self.party:
            return None
        
        for member in self.party.members:
            if member.id == character_id:
                return member
        
        return None
    
    def _get_status_name(self, status: str) -> str:
        """状態異常名を取得"""
        status_names = {
            "normal": "正常",
            "poison": "毒",
            "paralysis": "麻痺",
            "petrification": "石化",
            "dead": "死亡",
            "ashes": "灰",
            "curse": "呪い",
            "sleep": "睡眠",
            "silence": "沈黙"
        }
        return status_names.get(status, status)