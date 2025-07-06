"""冒険者ギルドサービス"""

import logging
from typing import List, Dict, Any, Optional
from ..core.facility_service import FacilityService, MenuItem
from ..core.service_result import ServiceResult, ResultType
from .service_utils import (
    ServiceResultFactory,
    PartyMemberUtility,
    ConfirmationFlowUtility,
    ActionExecutorMixin
)
# 正しいインポートパスに修正
try:
    from src.core.game_manager import GameManager as Game
except ImportError:
    # テスト時のフォールバック
    Game = None

from src.character.character import Character
from src.character.party import Party

# モデルクラスは必要に応じて後で実装
CharacterModel = None
PartyModel = None

logger = logging.getLogger(__name__)


class GuildService(FacilityService, ActionExecutorMixin):
    """冒険者ギルドサービス
    
    キャラクター作成、パーティ編成、クラス変更などの
    冒険者管理機能を提供する。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__("guild")
        # GameManagerはシングルトンではないため、必要時に別途設定
        self.game = None
        self.character_model = CharacterModel() if CharacterModel else None
        self.party_model = PartyModel() if PartyModel else None
        
        # キャラクター作成の一時データ
        self._creation_data: Dict[str, Any] = {}
        
        # ユーティリティクラス
        self.party_utility = None  # パーティが設定されたときに初期化
        
        logger.info("GuildService initialized")
    
    def get_menu_items(self) -> List[MenuItem]:
        """メニュー項目を取得"""
        items = []
        
        # キャラクター作成
        items.append(MenuItem(
            id="character_creation",
            label="キャラクター作成",
            description="新しいキャラクターを作成します",
            enabled=self._can_create_character(),
            service_type="wizard"
        ))
        
        # パーティ編成
        items.append(MenuItem(
            id="party_formation", 
            label="パーティ編成",
            description="パーティメンバーを編成します",
            enabled=self._has_characters(),
            service_type="panel"
        ))
        
        # クラス変更
        items.append(MenuItem(
            id="class_change",
            label="クラス変更", 
            description="キャラクターのクラスを変更します",
            enabled=self._can_change_class(),
            service_type="action"
        ))
        
        # 冒険者一覧
        items.append(MenuItem(
            id="character_list",
            label="冒険者一覧",
            description="登録されている冒険者の一覧を表示します",
            enabled=True,
            service_type="list"
        ))
        
        # 退出
        items.append(MenuItem(
            id="exit",
            label="退出",
            description="ギルドから退出します",
            enabled=True,
            service_type="action"
        ))
        
        return items
    
    def can_execute(self, action_id: str) -> bool:
        """アクション実行可能かチェック"""
        # 基本的にすべてのアクションが実行可能
        valid_actions = ["character_creation", "character_creation_complete", 
                        "party_formation", "class_change", "character_list", "exit"]
        return action_id in valid_actions
    
    def execute_action(self, action_id: str, params: Dict[str, Any]) -> ServiceResult:
        """アクションを実行"""
        action_map = {
            "character_creation": self._handle_character_creation,
            "character_creation_complete": self._complete_character_creation,
            "party_formation": self._handle_party_formation,
            "class_change": self._handle_class_change,
            "character_list": self._handle_character_list,
            "exit": lambda p: ServiceResultFactory.success("ギルドから退出しました")
        }
        
        return self.execute_with_error_handling(action_map, action_id, params)
    
    # キャラクター作成関連
    
    def _handle_character_creation(self, params: Dict[str, Any]) -> ServiceResult:
        """キャラクター作成を開始"""
        # ウィザードの初期化
        self._creation_data = {}
        
        return ServiceResultFactory.info(
            "キャラクター作成を開始します",
            data={"wizard_started": True}
        )
    
    def _complete_character_creation(self, params: Dict[str, Any]) -> ServiceResult:
        """キャラクター作成を完了"""
        try:
            # 必須パラメータの確認
            required = ["name", "race", "class", "stats"]
            for field in required:
                if field not in params:
                    return ServiceResultFactory.error(f"必須項目が不足しています: {field}")
            
            # キャラクターを作成
            character = self._create_character_from_params(params)
            if not character:
                return ServiceResultFactory.error("キャラクターの作成に失敗しました")
            
            # データベースに保存
            if self.character_model:
                self.character_model.create(character)
            
            # キャラクターをゲームに登録
            if self.game:
                self.game.add_character(character)
            
            return ServiceResultFactory.success(
                f"キャラクター「{character.name}」を作成しました！",
                data={"character_id": character.id}
            )
            
        except Exception as e:
            logger.error(f"Character creation failed: {e}")
            return ServiceResultFactory.error("キャラクター作成中にエラーが発生しました")
    
    def _create_character_from_params(self, params: Dict[str, Any]) -> Optional[Character]:
        """パラメータからキャラクターを作成"""
        try:
            # 基本情報
            name = params["name"]
            race = params["race"]
            char_class = params["class"]
            stats = params["stats"]
            
            # キャラクターインスタンスを作成
            character = Character(
                name=name,
                race=race,
                char_class=char_class,
                strength=stats.get("strength", 10),
                intelligence=stats.get("intelligence", 10),
                piety=stats.get("piety", 10),
                vitality=stats.get("vitality", 10),
                agility=stats.get("agility", 10),
                luck=stats.get("luck", 10)
            )
            
            return character
            
        except Exception as e:
            logger.error(f"Failed to create character from params: {e}")
            return None
    
    # パーティ編成関連
    
    def _handle_party_formation(self, params: Dict[str, Any]) -> ServiceResult:
        """パーティ編成を処理"""
        action = params.get("action")
        
        if action == "add_member":
            return self._add_party_member(params)
        elif action == "remove_member":
            return self._remove_party_member(params)
        elif action == "reorder":
            return self._reorder_party(params)
        elif action == "get_info":
            return self._get_party_info()
        else:
            return ServiceResultFactory.success(
                "パーティ編成画面を表示します",
                data={"panel_type": "party_formation"}
            )
    
    def _add_party_member(self, params: Dict[str, Any]) -> ServiceResult:
        """パーティにメンバーを追加"""
        character_id = params.get("character_id")
        if not character_id:
            return ServiceResultFactory.error("キャラクターIDが指定されていません")
        
        # キャラクターを取得
        if not self.character_model:
            return ServiceResultFactory.error("キャラクターモデルが利用できません")
        
        character = self.character_model.get(character_id)
        if not character:
            return ServiceResultFactory.error("キャラクターが見つかりません")
        
        # パーティに追加
        if self.party and len(self.party.members) >= 6:
            return ServiceResultFactory.error("パーティは満員です（最大6人）")
        
        if not self.party:
            # 新しいパーティを作成
            self.party = Party()
            self.game.set_party(self.party)
        
        if self.party.add_member(character):
            return ServiceResultFactory.success(
                f"{character.name}をパーティに追加しました",
                data={"party_size": len(self.party.members)}
            )
        else:
            return ServiceResultFactory.error("パーティへの追加に失敗しました")
    
    def _remove_party_member(self, params: Dict[str, Any]) -> ServiceResult:
        """パーティからメンバーを削除"""
        character_id = params.get("character_id")
        if not character_id:
            return ServiceResultFactory.error("キャラクターIDが指定されていません")
        
        if not self.party:
            return ServiceResultFactory.error("パーティが存在しません")
        
        # メンバーを削除
        for i, member in enumerate(self.party.members):
            if member.id == character_id:
                removed = self.party.remove_member(i)
                if removed:
                    return ServiceResultFactory.success(
                        f"{removed.name}をパーティから外しました",
                        data={"party_size": len(self.party.members)}
                    )
        
        return ServiceResultFactory.error("指定されたキャラクターはパーティにいません")
    
    def _reorder_party(self, params: Dict[str, Any]) -> ServiceResult:
        """パーティの並び順を変更"""
        new_order = params.get("order", [])
        
        if not self.party:
            return ServiceResultFactory.error("パーティが存在しません")
        
        # 並び替えを実行
        if self.party.reorder_members(new_order):
            return ServiceResultFactory.success("パーティの並び順を変更しました")
        else:
            return ServiceResultFactory.error("並び順の変更に失敗しました")
    
    def _get_party_info(self) -> ServiceResult:
        """パーティ情報を取得"""
        if not self.party:
            return ServiceResultFactory.info(
                "パーティが編成されていません",
                data={"party": None, "members": []}
            )
        
        # パーティ情報を構築
        members_info = []
        for member in self.party.members:
            members_info.append({
                "id": member.id,
                "name": member.name,
                "level": member.level,
                "class": member.char_class,
                "hp": f"{member.hp}/{member.max_hp}",
                "status": member.status
            })
        
        return ServiceResultFactory.success(
            "パーティ情報",
            data={
                "party_name": self.party.name,
                "members": members_info,
                "size": len(self.party.members)
            }
        )
    
    # クラス変更関連
    
    def _handle_class_change(self, params: Dict[str, Any]) -> ServiceResult:
        """クラス変更を処理"""
        character_id = params.get("character_id")
        new_class = params.get("new_class")
        
        if not character_id or not new_class:
            return ServiceResultFactory.success(
                "クラス変更画面を表示します",
                data={"available_classes": self._get_available_classes()}
            )
        
        # キャラクターを取得
        if not self.character_model:
            return ServiceResultFactory.error("キャラクターモデルが利用できません")
        
        character = self.character_model.get(character_id)
        if not character:
            return ServiceResultFactory.error("キャラクターが見つかりません")
        
        # クラス変更の条件をチェック
        if character.level < 5:
            return ServiceResultFactory.error(
                "クラス変更にはレベル5以上が必要です",
                result_type=ResultType.WARNING
            )
        
        # クラス変更を実行
        old_class = character.char_class
        if character.change_class(new_class):
            if self.character_model:
                self.character_model.update(character)
            return ServiceResultFactory.success(
                f"{character.name}のクラスを{old_class}から{new_class}に変更しました"
            )
        else:
            return ServiceResultFactory.error("クラス変更に失敗しました")
    
    # キャラクター一覧関連
    
    def _handle_character_list(self, params: Dict[str, Any]) -> ServiceResult:
        """キャラクター一覧を処理"""
        self._ensure_party_utility()
        
        # フィルタオプション
        filter_by = params.get("filter", "all")
        sort_by = params.get("sort", "name")
        
        # 全キャラクターを取得
        if self.character_model:
            all_characters = self.character_model.get_all()
        else:
            # モデルがない場合は空リスト
            all_characters = []
        
        # フィルタリング
        if filter_by == "available":
            # パーティに入っていないキャラクターのみ
            if self.party_utility.has_party():
                party_ids = [m.id for m in self.party.members]
                characters = [c for c in all_characters if c.id not in party_ids]
            else:
                characters = all_characters
        elif filter_by == "in_party":
            # パーティメンバーのみ
            characters = self.party.members if self.party_utility.has_party() else []
        else:
            characters = all_characters
        
        # ソート
        self._sort_characters(characters, sort_by)
        
        # PartyMemberUtilityを使用してキャラクター情報辞書を作成
        character_list = []
        for char in characters:
            char_info = self.party_utility.create_member_info_dict(
                char,
                additional_fields={
                    "race": char.race,
                    "class": char.char_class,
                    "in_party": self.party_utility.has_party() and char in self.party.members
                }
            )
            character_list.append(char_info)
        
        return ServiceResultFactory.success(
            f"冒険者一覧（{len(character_list)}人）",
            data={
                "characters": character_list,
                "total": len(character_list)
            }
        )
    
    def _sort_characters(self, characters: List, sort_by: str) -> None:
        """キャラクターリストをソート"""
        if sort_by == "level":
            characters.sort(key=lambda c: c.level, reverse=True)
        elif sort_by == "class":
            characters.sort(key=lambda c: c.char_class)
        else:  # name
            characters.sort(key=lambda c: c.name)
    
    # ヘルパーメソッド
    
    def _ensure_party_utility(self) -> None:
        """PartyMemberUtilityを初期化（必要時）"""
        if self.party_utility is None:
            self.party_utility = PartyMemberUtility(self.party)
    
    def _can_create_character(self) -> bool:
        """キャラクター作成が可能かチェック"""
        # 最大キャラクター数などの制限をチェック
        max_characters = 20  # 仮の値
        
        # モデルが利用できない場合は、パーティから推定
        if self.character_model is None:
            if self.party:
                current_count = len(self.party.get_all_characters())
            else:
                current_count = 0
        else:
            current_count = len(self.character_model.get_all())
        
        return current_count < max_characters
    
    def _has_characters(self) -> bool:
        """キャラクターが存在するかチェック"""
        # モデルが利用できない場合は、パーティから推定
        if self.character_model is None:
            if self.party:
                return len(self.party.get_all_characters()) > 0
            else:
                return False
        else:
            return len(self.character_model.get_all()) > 0
    
    def _can_change_class(self) -> bool:
        """クラス変更が可能なキャラクターがいるかチェック"""
        # レベル5以上のキャラクターがいるかチェック
        
        # モデルが利用できない場合は、パーティから推定
        if self.character_model is None:
            if self.party:
                characters = self.party.get_all_characters()
                return any(c.experience.level >= 5 for c in characters)
            else:
                return False
        else:
            characters = self.character_model.get_all()
            return any(c.level >= 5 for c in characters)
    
    def _get_available_classes(self) -> List[str]:
        """利用可能なクラスのリストを取得"""
        return [
            "fighter", "priest", "thief", "mage",
            "bishop", "samurai", "lord", "ninja"
        ]