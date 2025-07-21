"""教会サービス"""

import logging
from typing import List, Dict, Any, Optional
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

logger = logging.getLogger(__name__)


class TempleService(FacilityService, ActionExecutorMixin):
    """教会サービス
    
    蘇生、祝福などの機能を提供する。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__("temple")
        # GameManagerはシングルトンではないため、必要時に別途設定
        self.game = None
        
        # コントローラーへの参照（後で設定される）
        self._controller = None
        
        # 料金設定
        self.resurrect_cost_per_level = 100  # レベルあたりの蘇生費
        self.blessing_cost = 500  # 祝福の固定料金
        
        logger.info("TempleService initialized")
    
    def set_controller(self, controller):
        """コントローラーを設定"""
        self._controller = controller
    
    def get_menu_items(self) -> List[MenuItem]:
        """メニュー項目を取得"""
        items = []
        
        # 蘇生
        items.append(MenuItem(
            id="resurrect",
            label="蘇生",
            description="死亡したキャラクターを蘇生させます",
            enabled=self._has_dead_members(),
            service_type="action"
        ))
        
        # 祝福
        items.append(MenuItem(
            id="blessing",
            label="祝福",
            description="パーティに祝福を与えます",
            enabled=self.party is not None,
            service_type="action"
        ))
        
        # 祈祷書購入
        items.append(MenuItem(
            id="prayer_shop",
            label="祈祷書購入",
            description="神聖魔法の祈祷書を購入します",
            enabled=self.party is not None,
            service_type="panel"
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
        if action_id == "resurrect":
            return self._has_dead_members()
        elif action_id == "blessing":
            return self.party is not None
        elif action_id == "prayer_shop":
            return self.party is not None
        elif action_id == "exit":
            return True
        else:
            return False
    
    def execute_action(self, action_id: str, params: Dict[str, Any]) -> ServiceResult:
        """アクションを実行"""
        logger.info(f"Executing action: {action_id} with params: {params}")
        
        try:
            if action_id == "resurrect":
                return self._handle_resurrect(params)
            elif action_id == "blessing":
                return self._handle_blessing(params)
            elif action_id == "prayer_shop":
                return self._handle_prayer_shop(params)
            elif action_id == "exit":
                return ServiceResult(True, "教会から退出しました")
            else:
                return ServiceResult(False, f"不明なアクション: {action_id}")
                
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return ServiceResult(False, f"エラーが発生しました: {str(e)}")
    
    
    # 蘇生関連
    
    def _handle_resurrect(self, params: Dict[str, Any]) -> ServiceResult:
        """蘇生を処理"""
        return ConfirmationFlowUtility.handle_character_action_flow(
            params,
            self._get_dead_members,
            self._confirm_resurrect,
            self._execute_resurrect
        )
    
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
    
    # 祈祷書購入関連
    
    def _handle_prayer_shop(self, params: Dict[str, Any]) -> ServiceResult:
        """祈祷書購入を処理"""
        # 祈祷書購入パネルを表示
        return ServiceResult(
            success=True,
            message="神聖魔法の祈祷書をお選びください",
            data={
                "panel_type": "prayer_shop",
                "categories": ["healing", "blessing", "resurrection", "purification"],
                "available_spells": self._get_available_prayer_books(),
                "party_gold": self.party.gold if self.party else 0
            }
        )
    
    def _get_available_prayer_books(self) -> List[Dict[str, Any]]:
        """利用可能な祈祷書を取得"""
        # 基本的な神聖魔法の祈祷書リスト
        prayer_books = [
            {
                "id": "heal_light",
                "name": "軽い傷の治癒",
                "category": "healing",
                "level": 1,
                "cost": 100,
                "description": "軽微なHP回復を行う基本的な治癒魔法"
            },
            {
                "id": "heal_moderate",
                "name": "傷の治癒",
                "category": "healing", 
                "level": 2,
                "cost": 300,
                "description": "中程度のHP回復を行う治癒魔法"
            },
            {
                "id": "heal_serious",
                "name": "重い傷の治癒",
                "category": "healing",
                "level": 3,
                "cost": 800,
                "description": "重大なHP回復を行う強力な治癒魔法"
            },
            {
                "id": "bless",
                "name": "祝福",
                "category": "blessing",
                "level": 2,
                "cost": 400,
                "description": "パーティの能力を一時的に向上させる"
            },
            {
                "id": "resurrection",
                "name": "蘇生",
                "category": "resurrection",
                "level": 5,
                "cost": 2000,
                "description": "死亡した仲間を蘇生させる高位魔法"
            },
            {
                "id": "remove_curse",
                "name": "呪い除去",
                "category": "purification",
                "level": 3,
                "cost": 600,
                "description": "呪いや状態異常を除去する"
            },
            {
                "id": "turn_undead",
                "name": "アンデッド退散",
                "category": "purification",
                "level": 4,
                "cost": 1200,
                "description": "アンデッドモンスターを退散させる"
            }
        ]
        
        return prayer_books
    
    # ヘルパーメソッド
    
    
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
    
    def create_service_panel(self, service_id: str, rect, parent, ui_manager):
        """教会専用のサービスパネルを作成"""
        logger.info(f"[DEBUG] TempleService.create_service_panel called: service_id={service_id}")
        try:
            if service_id == "prayer_shop":
                # 祈祷書購入は専用パネルを使用
                from src.facilities.ui.temple.prayer_shop_panel import PrayerShopPanel
                # 祈祷書データを取得
                prayer_data = {
                    "available_spells": self._get_available_prayer_books(),
                    "categories": ["healing", "blessing", "resurrection", "purification"],
                    "party_gold": self.party.gold if self.party else 0
                }
                return PrayerShopPanel(
                    rect=rect,
                    parent=parent,
                    ui_manager=ui_manager,
                    controller=self._controller,
                    service=self,
                    data=prayer_data
                )
            elif service_id == "resurrect":
                # 蘇生は専用パネルを使用
                from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
                logger.info(f"[DEBUG] Creating ResurrectPanel with rect={rect}, parent={parent}, controller={self._controller}, ui_manager={ui_manager}")
                return ResurrectPanel(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
            elif service_id == "blessing":
                # 祝福は専用パネルを使用
                from src.facilities.ui.temple.blessing_panel import BlessingPanel
                return BlessingPanel(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
            else:
                logger.warning(f"[DEBUG] Unknown service_id for panel creation: {service_id}")
                return None
        except Exception as e:
            logger.error(f"[DEBUG] Error creating service panel: {e}")
            return None