"""魔法ギルドサービス"""

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
    """魔法ギルドサービス
    
    魔法学習、魔法鑑定、魔法分析などの機能を提供する。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__("magic_guild")
        # GameManagerはシングルトンではないため、必要時に別途設定
        self.game = None
        
        # 料金設定
        self.identify_magic_cost = 200  # 魔法鑑定の基本料金
        self.analyze_cost_per_level = 50  # 魔法分析のレベル毎料金
        
        # 学習可能な魔法のレベル制限
        self.max_learnable_spell_level = 9  # 最大9レベルまで
        
        # 魔法学習コスト（レベル別）
        self.spell_learning_costs = {
            1: 100,
            2: 300,
            3: 600,
            4: 1000,
            5: 1500,
            6: 2100,
            7: 2800,
            8: 3600,
            9: 4500
        }
        
        logger.info("MagicGuildService initialized")
    
    def get_menu_items(self) -> List[MenuItem]:
        """メニュー項目を取得"""
        items = []
        
        # 魔法学習
        items.append(MenuItem(
            id="learn_spells",
            label="魔法学習",
            description="新しい魔法を学びます",
            enabled=self._has_eligible_learners(),
            service_type="panel"
        ))
        
        # 魔法鑑定
        items.append(MenuItem(
            id="identify_magic",
            label="魔法鑑定",
            description="未知の魔法アイテムを鑑定します",
            enabled=self._has_unidentified_magic_items(),
            service_type="action"
        ))
        
        # 魔法分析
        items.append(MenuItem(
            id="analyze_magic",
            label="魔法分析",
            description="魔法の詳細な効果を分析します",
            enabled=self._has_analyzable_spells(),
            service_type="panel"
        ))
        
        # 魔法研究
        items.append(MenuItem(
            id="magic_research",
            label="魔法研究",
            description="高度な魔法の研究を行います",
            enabled=self._has_advanced_casters(),
            service_type="wizard"
        ))
        
        # 退出
        items.append(MenuItem(
            id="exit",
            label="魔法ギルドを出る",
            description="魔法ギルドから退出します",
            enabled=True,
            service_type="action"
        ))
        
        return items
    
    def can_execute(self, action_id: str) -> bool:
        """アクション実行可能かチェック"""
        if action_id == "learn_spells":
            return self._has_eligible_learners()
        elif action_id == "identify_magic":
            return self._has_unidentified_magic_items()
        elif action_id == "analyze_magic":
            return self._has_analyzable_spells()
        elif action_id == "magic_research":
            return self._has_advanced_casters()
        elif action_id == "exit":
            return True
        else:
            return False
    
    def execute_action(self, action_id: str, params: Dict[str, Any]) -> ServiceResult:
        """アクションを実行"""
        logger.info(f"Executing action: {action_id} with params: {params}")
        
        try:
            if action_id == "learn_spells":
                return self._handle_learn_spells(params)
            elif action_id == "identify_magic":
                return self._handle_identify_magic(params)
            elif action_id == "analyze_magic":
                return self._handle_analyze_magic(params)
            elif action_id == "magic_research":
                return self._handle_magic_research(params)
            elif action_id == "exit":
                return ServiceResult(True, "魔法ギルドから退出しました")
            else:
                return ServiceResult(False, f"不明なアクション: {action_id}")
                
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return ServiceResult(False, f"エラーが発生しました: {str(e)}")
    
    # 魔法学習関連
    
    def _handle_learn_spells(self, params: Dict[str, Any]) -> ServiceResult:
        """魔法学習を処理"""
        character_id = params.get("character_id")
        spell_id = params.get("spell_id")
        
        if not character_id:
            # 学習可能なキャラクターの選択画面
            return self._get_eligible_learners()
        
        if not spell_id:
            # 学習可能な魔法の選択画面
            return self._get_learnable_spells(character_id)
        
        # 学習確認
        if not params.get("confirmed", False):
            return self._confirm_spell_learning(character_id, spell_id)
        
        # 学習実行
        return self._execute_spell_learning(character_id, spell_id)
    
    def _get_eligible_learners(self) -> ServiceResult:
        """学習可能なキャラクターを取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        eligible_learners = []
        
        for member in self.party.members:
            if member.is_alive() and self._can_learn_spells(member):
                eligible_learners.append({
                    "id": member.id,
                    "name": member.name,
                    "class": member.character_class,
                    "level": member.level,
                    "max_spell_level": self._get_max_spell_level(member),
                    "known_spells": len(member.known_spells) if hasattr(member, 'known_spells') else 0
                })
        
        if not eligible_learners:
            return ServiceResult(
                success=True,
                message="魔法を学習できるメンバーがいません",
                result_type=ResultType.INFO
            )
        
        return ServiceResult(
            success=True,
            message="魔法を学習するキャラクターを選択してください",
            data={
                "characters": eligible_learners,
                "panel_type": "learn_spells"
            }
        )
    
    def _get_learnable_spells(self, character_id: str) -> ServiceResult:
        """学習可能な魔法を取得"""
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResult(False, "キャラクターが見つかりません")
        
        # キャラクターの最大魔法レベル
        max_level = self._get_max_spell_level(character)
        
        # 学習可能な魔法リスト（ダミーデータ）
        learnable_spells = []
        
        # レベル別に魔法を生成
        for level in range(1, min(max_level + 1, self.max_learnable_spell_level + 1)):
            # このレベルの魔法例
            if level == 1:
                spells = [
                    {"id": "fire_bolt", "name": "ファイアボルト", "type": "attack"},
                    {"id": "heal_light", "name": "ライトヒール", "type": "healing"},
                    {"id": "shield", "name": "シールド", "type": "defense"}
                ]
            elif level == 2:
                spells = [
                    {"id": "ice_spike", "name": "アイススパイク", "type": "attack"},
                    {"id": "cure_poison", "name": "キュアポイズン", "type": "healing"},
                    {"id": "detect_magic", "name": "ディテクトマジック", "type": "utility"}
                ]
            else:
                # 高レベル魔法の例
                spells = [
                    {"id": f"spell_{level}_1", "name": f"レベル{level}魔法A", "type": "attack"},
                    {"id": f"spell_{level}_2", "name": f"レベル{level}魔法B", "type": "utility"}
                ]
            
            for spell in spells:
                # 既に習得済みかチェック（仮実装）
                if not self._has_learned_spell(character, spell["id"]):
                    learnable_spells.append({
                        "id": spell["id"],
                        "name": spell["name"],
                        "level": level,
                        "type": spell["type"],
                        "cost": self.spell_learning_costs[level],
                        "description": f"{spell['name']}の効果説明"
                    })
        
        if not learnable_spells:
            return ServiceResult(
                success=True,
                message="学習可能な魔法がありません",
                result_type=ResultType.INFO
            )
        
        return ServiceResult(
            success=True,
            message="学習する魔法を選択してください",
            data={
                "character_id": character_id,
                "character_name": character.name,
                "spells": learnable_spells,
                "party_gold": self.party.gold if self.party else 0
            }
        )
    
    def _confirm_spell_learning(self, character_id: str, spell_id: str) -> ServiceResult:
        """魔法学習確認"""
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResult(False, "キャラクターが見つかりません")
        
        # 魔法情報を取得（仮実装）
        spell_info = self._get_spell_info(spell_id)
        if not spell_info:
            return ServiceResult(False, "魔法が見つかりません")
        
        cost = self.spell_learning_costs.get(spell_info["level"], 0)
        
        if self.party and self.party.gold < cost:
            return ServiceResult(
                success=False,
                message=f"学習費用が不足しています（必要: {cost} G）",
                result_type=ResultType.WARNING
            )
        
        return ServiceResult(
            success=True,
            message=f"{character.name}が{spell_info['name']}を学習しますか？\n費用: {cost} G",
            result_type=ResultType.CONFIRM,
            data={
                "character_id": character_id,
                "spell_id": spell_id,
                "cost": cost,
                "action": "learn_spells"
            }
        )
    
    def _execute_spell_learning(self, character_id: str, spell_id: str) -> ServiceResult:
        """魔法学習を実行"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResult(False, "キャラクターが見つかりません")
        
        spell_info = self._get_spell_info(spell_id)
        if not spell_info:
            return ServiceResult(False, "魔法が見つかりません")
        
        cost = self.spell_learning_costs.get(spell_info["level"], 0)
        
        if self.party.gold < cost:
            return ServiceResult(False, "学習費用が不足しています")
        
        # 学習実行
        self.party.gold -= cost
        
        # キャラクターに魔法を追加（仮実装）
        if not hasattr(character, 'known_spells'):
            character.known_spells = []
        character.known_spells.append(spell_id)
        
        return ServiceResult(
            success=True,
            message=f"{character.name}は{spell_info['name']}を習得しました！",
            result_type=ResultType.SUCCESS,
            data={
                "spell_name": spell_info['name'],
                "remaining_gold": self.party.gold
            }
        )
    
    # 魔法鑑定関連
    
    def _handle_identify_magic(self, params: Dict[str, Any]) -> ServiceResult:
        """魔法鑑定を処理"""
        item_id = params.get("item_id")
        
        if not item_id:
            # 鑑定対象の選択画面
            return self._get_unidentified_items()
        
        # 鑑定確認
        if not params.get("confirmed", False):
            return self._confirm_identify(item_id)
        
        # 鑑定実行
        return self._execute_identify(item_id)
    
    def _get_unidentified_items(self) -> ServiceResult:
        """未鑑定の魔法アイテムを取得"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        unidentified_items = []
        
        # 各キャラクターのアイテムをチェック（仮実装）
        for member in self.party.members:
            # ダミーデータ
            if member.name == "Hero":  # テスト用
                unidentified_items.append({
                    "id": "unknown_staff",
                    "name": "不明な杖",
                    "holder": member.name,
                    "holder_id": member.id
                })
        
        if not unidentified_items:
            return ServiceResult(
                success=True,
                message="鑑定が必要なアイテムはありません",
                result_type=ResultType.INFO
            )
        
        return ServiceResult(
            success=True,
            message="鑑定するアイテムを選択してください",
            data={
                "items": unidentified_items,
                "party_gold": self.party.gold
            }
        )
    
    def _confirm_identify(self, item_id: str) -> ServiceResult:
        """鑑定確認"""
        if self.party and self.party.gold < self.identify_magic_cost:
            return ServiceResult(
                success=False,
                message=f"鑑定料金が不足しています（必要: {self.identify_magic_cost} G）",
                result_type=ResultType.WARNING
            )
        
        return ServiceResult(
            success=True,
            message=f"魔法鑑定を行いますか？（{self.identify_magic_cost} G）",
            result_type=ResultType.CONFIRM,
            data={
                "item_id": item_id,
                "cost": self.identify_magic_cost,
                "action": "identify_magic"
            }
        )
    
    def _execute_identify(self, item_id: str) -> ServiceResult:
        """鑑定を実行"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        if self.party.gold < self.identify_magic_cost:
            return ServiceResult(False, "鑑定料金が不足しています")
        
        # 鑑定実行
        self.party.gold -= self.identify_magic_cost
        
        # アイテム情報（仮実装）
        identified_name = "炎の杖+2"
        effects = "火属性魔法の威力+20%、MP消費-10%"
        
        return ServiceResult(
            success=True,
            message=f"鑑定完了！\n「不明な杖」は「{identified_name}」でした\n効果: {effects}",
            result_type=ResultType.SUCCESS,
            data={
                "item_name": identified_name,
                "effects": effects,
                "remaining_gold": self.party.gold
            }
        )
    
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
    
    # 魔法研究関連
    
    def _handle_magic_research(self, params: Dict[str, Any]) -> ServiceResult:
        """魔法研究を処理"""
        step = params.get("step", "select_researcher")
        
        if step == "select_researcher":
            return self._select_researcher()
        elif step == "select_research_type":
            return self._select_research_type(params)
        elif step == "configure_research":
            return self._configure_research(params)
        elif step == "confirm_research":
            return self._confirm_research(params)
        elif step == "complete":
            return self._complete_research(params)
        else:
            return ServiceResult(False, f"不明な研究ステップ: {step}")
    
    # ヘルパーメソッド
    
    def _has_eligible_learners(self) -> bool:
        """学習可能なキャラクターがいるかチェック"""
        if not self.party:
            return False
        
        for member in self.party.members:
            if member.is_alive() and self._can_learn_spells(member):
                return True
        
        return False
    
    def _has_unidentified_magic_items(self) -> bool:
        """未鑑定の魔法アイテムがあるかチェック"""
        if not self.party:
            return False
        
        # 仮実装 - 実際にはアイテムシステムと連携
        return True
    
    def _has_analyzable_spells(self) -> bool:
        """分析可能な魔法があるかチェック"""
        if not self.party:
            return False
        
        for member in self.party.members:
            if member.is_alive() and hasattr(member, 'known_spells') and member.known_spells:
                return True
        
        return False
    
    def _has_advanced_casters(self) -> bool:
        """上級魔法使いがいるかチェック"""
        if not self.party:
            return False
        
        for member in self.party.members:
            if member.is_alive() and self._is_advanced_caster(member):
                return True
        
        return False
    
    def _can_learn_spells(self, character: Character) -> bool:
        """キャラクターが魔法を学習できるかチェック"""
        # 職業チェック（仮実装）
        magic_classes = ["wizard", "sorcerer", "cleric", "druid", "bard"]
        return hasattr(character, 'character_class') and character.character_class.lower() in magic_classes
    
    def _is_advanced_caster(self, character: Character) -> bool:
        """上級魔法使いかチェック"""
        return self._can_learn_spells(character) and character.level >= 10
    
    def _get_max_spell_level(self, character: Character) -> int:
        """キャラクターの最大魔法レベルを取得"""
        # レベルに基づく計算（仮実装）
        if character.level < 1:
            return 0
        elif character.level < 3:
            return 1
        elif character.level < 5:
            return 2
        elif character.level < 7:
            return 3
        elif character.level < 9:
            return 4
        elif character.level < 11:
            return 5
        elif character.level < 13:
            return 6
        elif character.level < 15:
            return 7
        elif character.level < 17:
            return 8
        else:
            return 9
    
    def _has_learned_spell(self, character: Character, spell_id: str) -> bool:
        """魔法を習得済みかチェック"""
        if not hasattr(character, 'known_spells'):
            return False
        return spell_id in character.known_spells
    
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
    
    def _select_researcher(self) -> ServiceResult:
        """研究者を選択"""
        if not self.party:
            return ServiceResult(False, "パーティが存在しません")
        
        researchers = []
        
        for member in self.party.members:
            if member.is_alive() and self._is_advanced_caster(member):
                researchers.append({
                    "id": member.id,
                    "name": member.name,
                    "class": member.character_class,
                    "level": member.level,
                    "intelligence": getattr(member, 'intelligence', 10)
                })
        
        if not researchers:
            return ServiceResult(
                success=True,
                message="魔法研究を行える上級魔法使いがいません",
                result_type=ResultType.INFO
            )
        
        return ServiceResult(
            success=True,
            message="魔法研究を行う研究者を選択してください",
            data={
                "researchers": researchers,
                "step": "select_researcher"
            }
        )
    
    def _select_research_type(self, params: Dict[str, Any]) -> ServiceResult:
        """研究タイプを選択"""
        researcher_id = params.get("researcher_id")
        if not researcher_id:
            return ServiceResult(False, "研究者が選択されていません")
        
        research_types = [
            {
                "id": "new_spell",
                "name": "新魔法開発",
                "description": "全く新しい魔法を開発します",
                "cost": 5000,
                "duration": 30  # 日数
            },
            {
                "id": "spell_enhancement",
                "name": "魔法強化",
                "description": "既存の魔法を強化します",
                "cost": 3000,
                "duration": 20
            },
            {
                "id": "spell_fusion",
                "name": "魔法融合",
                "description": "2つの魔法を融合させます",
                "cost": 4000,
                "duration": 25
            }
        ]
        
        return ServiceResult(
            success=True,
            message="研究タイプを選択してください",
            data={
                "researcher_id": researcher_id,
                "research_types": research_types,
                "party_gold": self.party.gold if self.party else 0,
                "step": "select_research_type"
            }
        )
    
    def _configure_research(self, params: Dict[str, Any]) -> ServiceResult:
        """研究設定"""
        # 研究の詳細設定（省略）
        return ServiceResult(
            success=True,
            message="研究設定を行います",
            data={
                "step": "configure_research"
            }
        )
    
    def _confirm_research(self, params: Dict[str, Any]) -> ServiceResult:
        """研究確認"""
        # 研究の最終確認（省略）
        return ServiceResult(
            success=True,
            message="魔法研究を開始しますか？",
            result_type=ResultType.CONFIRM,
            data={
                "step": "confirm_research"
            }
        )
    
    def _complete_research(self, params: Dict[str, Any]) -> ServiceResult:
        """研究完了"""
        return ServiceResult(
            success=True,
            message="魔法研究が完了しました！新たな魔法の知識を得ました。",
            result_type=ResultType.SUCCESS
        )