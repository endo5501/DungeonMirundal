"""魔術師ギルドサービス"""

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


class MagicGuildService(FacilityService):
    """魔術師ギルドサービス
    
    魔法学習、魔法鑑定、魔法分析などの機能を提供する。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__("magic_guild")
        # GameManagerはシングルトンではないため、必要時に別途設定
        self.game = None
        
        # コントローラーへの参照（後で設定される）
        self._controller = None
        
        # 料金設定
        self.analyze_cost_per_level = 50  # 魔法分析のレベル毎料金
        
        logger.info("MagicGuildService initialized")
    
    def set_controller(self, controller):
        """コントローラーを設定"""
        self._controller = controller
    
    def get_menu_items(self) -> List[MenuItem]:
        """メニュー項目を取得"""
        items = []
        
        # 魔術書購入
        items.append(MenuItem(
            id="spellbook_shop",
            label="魔術書店",
            description="魔法書を購入します",
            enabled=True,
            service_type="panel"
        ))
        
        # 魔法分析
        items.append(MenuItem(
            id="analyze_magic",
            label="魔法分析",
            description="魔法の詳細な効果を分析します",
            enabled=self._has_analyzable_spells(),
            service_type="panel"
        ))
        
        
        # 退出
        items.append(MenuItem(
            id="exit",
            label="魔術師ギルドを出る",
            description="魔術師ギルドから退出します",
            enabled=True,
            service_type="action"
        ))
        
        return items
    
    def can_execute(self, action_id: str) -> bool:
        """アクション実行可能かチェック"""
        if action_id == "spellbook_shop":
            return True
        elif action_id == "analyze_magic":
            return self._has_analyzable_spells()
        elif action_id == "exit":
            return True
        else:
            return False
    
    def execute_action(self, action_id: str, params: Dict[str, Any]) -> ServiceResult:
        """アクションを実行"""
        logger.info(f"Executing action: {action_id} with params: {params}")
        
        try:
            if action_id == "spellbook_shop":
                return self._handle_spellbook_shop(params)
            elif action_id == "analyze_magic":
                return self._handle_analyze_magic(params)
            elif action_id == "exit":
                return ServiceResult(True, "魔術師ギルドから退出しました")
            else:
                return ServiceResult(False, f"不明なアクション: {action_id}")
                
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return ServiceResult(False, f"エラーが発生しました: {str(e)}")
    
    
    # 魔法分析関連
    
    def _handle_analyze_magic(self, params: Dict[str, Any]) -> ServiceResult:
        """魔法分析を処理"""
        character_id = params.get("character_id")
        spell_id = params.get("spell_id")
        
        if not character_id:
            # 分析対象キャラクターの選択
            return self._get_characters_with_spells()
        
        if not spell_id:
            # 分析対象魔法の選択
            return self._get_analyzable_spells_for_character(character_id)
        
        # 分析確認
        if not params.get("confirmed", False):
            return self._confirm_analyze(character_id, spell_id)
        
        # 分析実行
        return self._execute_analyze(character_id, spell_id)
    
    def _get_characters_with_spells(self) -> ServiceResult:
        """魔法を持つキャラクターを取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        characters = []
        
        for member in self.party.members:
            if member.is_alive() and hasattr(member, 'known_spells') and member.known_spells:
                characters.append({
                    "id": member.id,
                    "name": member.name,
                    "class": member.character_class,
                    "spell_count": len(member.known_spells)
                })
        
        if not characters:
            return ServiceResult(
                success=True,
                message="魔法を持つメンバーがいません",
                result_type=ResultType.INFO
            )
        
        return ServiceResult(
            success=True,
            message="魔法分析を行うキャラクターを選択してください",
            data={
                "characters": characters,
                "panel_type": "analyze_magic"
            }
        )
    
    
    # ヘルパーメソッド
    
    
    
    def _has_analyzable_spells(self) -> bool:
        """分析可能な魔法があるかチェック"""
        if not self.party:
            return False
        
        for member in self.party.members:
            if member.is_alive() and hasattr(member, 'known_spells') and member.known_spells:
                return True
        return False
    
    
    
    
    
    def _get_spell_info(self, spell_id: str) -> Optional[Dict[str, Any]]:
        """魔法情報を取得（仮実装）"""
        # 実際にはデータベースや設定ファイルから取得
        spell_db = {
            "fire_bolt": {"name": "ファイアボルト", "level": 1, "type": "attack"},
            "heal_light": {"name": "ライトヒール", "level": 1, "type": "healing"},
            "shield": {"name": "シールド", "level": 1, "type": "defense"},
            "ice_spike": {"name": "アイススパイク", "level": 2, "type": "attack"},
            "cure_poison": {"name": "キュアポイズン", "level": 2, "type": "healing"},
            "detect_magic": {"name": "ディテクトマジック", "level": 2, "type": "utility"}
        }
        
        return spell_db.get(spell_id)
    
    def _get_character_by_id(self, character_id: str) -> Optional[Character]:
        """IDでキャラクターを取得"""
        if not self.party:
            return None
        
        for member in self.party.members:
            if member.id == character_id:
                return member
        
        return None
    
    def _get_analyzable_spells_for_character(self, character_id: str) -> ServiceResult:
        """キャラクターの分析可能な魔法を取得"""
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResult(False, "キャラクターが見つかりません")
        
        if not hasattr(character, 'known_spells') or not character.known_spells:
            return ServiceResult(
                success=True,
                message="このキャラクターは魔法を習得していません",
                result_type=ResultType.INFO
            )
        
        analyzable_spells = []
        for spell_id in character.known_spells:
            spell_info = self._get_spell_info(spell_id)
            if spell_info:
                cost = self.analyze_cost_per_level * spell_info["level"]
                analyzable_spells.append({
                    "id": spell_id,
                    "name": spell_info["name"],
                    "level": spell_info["level"],
                    "cost": cost
                })
        
        return ServiceResult(
            success=True,
            message="分析する魔法を選択してください",
            data={
                "character_id": character_id,
                "character_name": character.name,
                "spells": analyzable_spells,
                "party_gold": self.party.gold if self.party else 0
            }
        )
    
    def _confirm_analyze(self, character_id: str, spell_id: str) -> ServiceResult:
        """魔法分析確認"""
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResult(False, "キャラクターが見つかりません")
        
        spell_info = self._get_spell_info(spell_id)
        if not spell_info:
            return ServiceResult(False, "魔法が見つかりません")
        
        cost = self.analyze_cost_per_level * spell_info["level"]
        
        if self.party and self.party.gold < cost:
            return ServiceResult(
                success=False,
                message=f"分析費用が不足しています（必要: {cost} G）",
                result_type=ResultType.WARNING
            )
        
        return ServiceResult(
            success=True,
            message=f"{spell_info['name']}を詳細に分析しますか？（{cost} G）",
            result_type=ResultType.CONFIRM,
            data={
                "character_id": character_id,
                "spell_id": spell_id,
                "cost": cost,
                "action": "analyze_magic"
            }
        )
    
    def _execute_analyze(self, character_id: str, spell_id: str) -> ServiceResult:
        """魔法分析を実行"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        spell_info = self._get_spell_info(spell_id)
        if not spell_info:
            return ServiceResult(False, "魔法が見つかりません")
        
        cost = self.analyze_cost_per_level * spell_info["level"]
        
        if self.party.gold < cost:
            return ServiceResult(False, "分析費用が不足しています")
        
        # 分析実行
        self.party.gold -= cost
        
        # 詳細な分析結果（仮実装）
        analysis = f"""
{spell_info['name']}の詳細分析結果:
・威力係数: 1.5x
・詠唱時間: 2秒
・有効範囲: 単体/半径3m
・属性相性: 火に弱い敵に+50%ダメージ
・消費MP: 基本値の90%
・クリティカル率: +10%
        """
        
        return ServiceResult(
            success=True,
            message=analysis.strip(),
            result_type=ResultType.SUCCESS,
            data={
                "spell_name": spell_info['name'],
                "remaining_gold": self.party.gold
            }
        )
    
    def create_service_panel(self, service_id: str, rect, parent, ui_manager):
        """魔術師ギルド専用のサービスパネルを作成"""
        logger.info(f"[DEBUG] MagicGuildService.create_service_panel called: service_id={service_id}")
        try:
            if service_id == "spellbook_shop":
                # 魔術書店は商店システムと連携するため、商店の購入パネルを使用
                from src.facilities.ui.shop.buy_panel import BuyPanel
                return BuyPanel(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
            elif service_id == "analyze_magic":
                # 魔法分析パネル
                from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
                return SpellAnalysisPanel(
                    rect=rect,
                    parent=parent,
                    ui_manager=ui_manager,
                    controller=self._controller,
                    service=self
                )
            else:
                logger.warning(f"[DEBUG] Unknown service_id for panel creation: {service_id}")
                return None
        except Exception as e:
            logger.error(f"[DEBUG] Error creating service panel: {e}")
            return None
    
    # 魔術書購入関連
    
    def _handle_spellbook_shop(self, params: Dict[str, Any]) -> ServiceResult:
        """魔術書購入を処理"""
        # 商店システムと連携して魔術書を購入
        return ServiceResult(
            success=True,
            message="魔術書店",
            data={
                "shop_type": "spellbook",
                "categories": ["offensive", "defensive", "healing", "utility", "special"],
                "level_requirements": True,
                "panel_type": "spellbook_shop"
            }
        )
