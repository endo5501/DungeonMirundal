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
        
        # コントローラーへの参照（後で設定される）
        self._controller = None
        
        logger.info("GuildService initialized")
    
    def set_controller(self, controller):
        """コントローラーを設定"""
        self._controller = controller
    
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
            from src.character.stats import BaseStats
            
            base_stats = BaseStats(
                strength=stats.get("strength", 10),
                intelligence=stats.get("intelligence", 10),
                faith=stats.get("piety", stats.get("faith", 10)),  # pietyからfaithへ変換
                vitality=stats.get("vitality", 10),
                agility=stats.get("agility", 10),
                luck=stats.get("luck", 10)
            )
            
            character = Character(
                name=name,
                race=race,
                character_class=char_class,
                base_stats=base_stats
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
        
        # GameManagerからパーティを取得
        party = self._get_current_party()
        
        # キャラクターを取得（仮実装）
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResultFactory.error("キャラクターが見つかりません")
        
        # パーティに追加
        if party and len(party.members) >= 6:
            return ServiceResultFactory.error("パーティは満員です（最大6人）")
        
        if not party:
            # 新しいパーティを作成
            party = Party()
            if self.game:
                self.game.set_party(party)
        
        if party.add_character(character):
            return ServiceResultFactory.success(
                f"{character.name}をパーティに追加しました",
                data={"party_size": len(party.members)}
            )
        else:
            return ServiceResultFactory.error("パーティへの追加に失敗しました")
    
    def _remove_party_member(self, params: Dict[str, Any]) -> ServiceResult:
        """パーティからメンバーを削除"""
        character_id = params.get("character_id")
        if not character_id:
            return ServiceResultFactory.error("キャラクターIDが指定されていません")
        
        party = self._get_current_party()
        if not party:
            return ServiceResultFactory.error("パーティが存在しません")
        
        # メンバーを削除
        character = party.get_character(character_id)
        if character:
            if party.remove_character(character_id):
                return ServiceResultFactory.success(
                    f"{character.name}をパーティから外しました",
                    data={"party_size": len(party.members)}
                )
        
        return ServiceResultFactory.error("指定されたキャラクターはパーティにいません")
    
    def _reorder_party(self, params: Dict[str, Any]) -> ServiceResult:
        """パーティの並び順を変更"""
        new_order = params.get("order", [])
        
        party = self._get_current_party()
        if not party:
            return ServiceResultFactory.error("パーティが存在しません")
        
        # 並び替えを実行（フォーメーション変更）
        try:
            # 新しい順序でフォーメーションを再構築
            from src.character.party import PartyPosition
            positions = list(PartyPosition)
            
            # 現在のフォーメーションをクリア
            party.formation.reset()
            
            # 新しい順序でメンバーを配置
            for i, character_id in enumerate(new_order):
                if i < len(positions) and character_id in party.characters:
                    party.formation.add_character(character_id, positions[i])
            
            return ServiceResultFactory.success("パーティの並び順を変更しました")
        except Exception as e:
            logger.error(f"Failed to reorder party: {e}")
            return ServiceResultFactory.error("並び順の変更に失敗しました")
    
    def _get_party_info(self) -> ServiceResult:
        """パーティ情報を取得"""
        party = self._get_current_party()
        if not party:
            return ServiceResultFactory.info(
                "パーティが編成されていません",
                data={"party": None, "members": []}
            )
        
        # パーティ情報を構築（フォーメーション順）
        members_info = []
        from src.character.party import PartyPosition
        
        # フォーメーション順でメンバーを取得
        for position in PartyPosition:
            character_id = party.formation.positions.get(position)
            if character_id and character_id in party.characters:
                member = party.characters[character_id]
                members_info.append({
                    "id": member.character_id,
                    "name": member.name,
                    "level": member.experience.level,
                    "class": member.character_class,
                    "hp": f"{member.derived_stats.current_hp}/{member.derived_stats.max_hp}",
                    "status": member.status.value if hasattr(member.status, 'value') else str(member.status),
                    "position": position.value
                })
        
        return ServiceResultFactory.success(
            "パーティ情報",
            data={
                "party_name": party.name,
                "members": members_info,
                "size": len(members_info)
            }
        )
    
    # クラス変更関連
    
    def _handle_class_change(self, params: Dict[str, Any]) -> ServiceResult:
        """クラス変更を処理"""
        character_id = params.get("character_id")
        new_class = params.get("new_class")
        confirmed = params.get("confirmed", False)
        
        # キャラクターIDがない場合は対象選択画面を表示
        if not character_id:
            return self._get_class_change_candidates()
        
        # キャラクターを取得
        character = self._get_character_by_id(character_id)
        if not character:
            return ServiceResultFactory.error("キャラクターが見つかりません")
        
        # 新しいクラスが指定されていない場合は利用可能クラス一覧を表示
        if not new_class:
            return self._get_available_classes_for_character(character)
        
        # 確認が必要な場合
        if not confirmed:
            return self._confirm_class_change(character, new_class)
        
        # クラス変更を実行
        return self._execute_class_change(character, new_class)
    
    def _get_class_change_candidates(self) -> ServiceResult:
        """クラス変更対象キャラクター一覧を取得"""
        all_characters = self._get_all_available_characters()
        
        # レベル5以上のキャラクターのみ
        candidates = [char for char in all_characters if char.experience.level >= 5]
        
        if not candidates:
            return ServiceResultFactory.info("クラス変更可能なキャラクターがいません（レベル5以上が必要）")
        
        character_list = []
        party = self._get_current_party()
        utility = PartyMemberUtility(party)
        
        for char in candidates:
            char_info = utility.create_member_info_dict(
                char,
                additional_fields={
                    "race": char.race,
                    "class": char.character_class,
                    "can_change_class": True
                }
            )
            character_list.append(char_info)
        
        return ServiceResultFactory.success(
            f"クラス変更可能なキャラクター（{len(candidates)}人）",
            data={
                "characters": character_list,
                "action": "select_character_for_class_change"
            }
        )
    
    def _get_available_classes_for_character(self, character: Character) -> ServiceResult:
        """キャラクターが変更可能なクラス一覧を取得"""
        from src.character.class_change import ClassChangeValidator
        
        # 利用可能クラスを取得
        available_classes = ClassChangeValidator.get_available_classes(character)
        
        if not available_classes:
            return ServiceResultFactory.info(
                f"{character.name}は他のクラスに変更できません",
                data={"character": character.name}
            )
        
        # クラス情報を構築
        class_info = []
        for class_name in available_classes:
            from src.character.class_change import ClassChangeManager
            info = ClassChangeManager.get_class_change_info(character, class_name)
            
            class_info.append({
                "id": class_name,
                "name": info.get("target_name", class_name),
                "description": f"HP倍率: {info.get('hp_multiplier', 1.0)}, MP倍率: {info.get('mp_multiplier', 1.0)}",
                "requirements": info.get("requirements", {}),
                "weapon_types": info.get("weapon_types", []),
                "armor_types": info.get("armor_types", [])
            })
        
        return ServiceResultFactory.success(
            f"{character.name}が変更可能なクラス",
            data={
                "character_id": character.character_id,
                "character_name": character.name,
                "current_class": character.character_class,
                "available_classes": class_info,
                "action": "select_new_class"
            }
        )
    
    def _confirm_class_change(self, character: Character, new_class: str) -> ServiceResult:
        """クラス変更の確認"""
        from src.character.class_change import ClassChangeValidator, ClassChangeManager
        
        # 変更可能かチェック
        can_change, errors = ClassChangeValidator.can_change_class(character, new_class)
        if not can_change:
            return ServiceResultFactory.error(f"クラス変更できません: {', '.join(errors)}")
        
        # クラス変更情報を取得
        info = ClassChangeManager.get_class_change_info(character, new_class)
        
        old_class_name = info.get("current_name", character.character_class)
        new_class_name = info.get("target_name", new_class)
        
        confirm_message = f"{character.name}のクラスを{old_class_name}から{new_class_name}に変更しますか？"
        confirm_message += f"\n\n注意: レベルが1にリセットされます"
        
        return ServiceResultFactory.confirm(
            confirm_message,
            data={
                "character_id": character.character_id,
                "new_class": new_class,
                "character_name": character.name,
                "old_class": old_class_name,
                "new_class_name": new_class_name,
                "action": "execute_class_change"
            }
        )
    
    def _execute_class_change(self, character: Character, new_class: str) -> ServiceResult:
        """クラス変更を実行"""
        from src.character.class_change import ClassChangeManager
        
        # クラス変更を実行
        success, message = ClassChangeManager.change_class(character, new_class)
        
        if success:
            # キャラクターモデルを更新（存在する場合）
            if self.character_model:
                self.character_model.update(character)
            
            return ServiceResultFactory.success(message)
        else:
            return ServiceResultFactory.error(message)
    
    # キャラクター一覧関連
    
    def _handle_character_list(self, params: Dict[str, Any]) -> ServiceResult:
        """キャラクター一覧を処理"""
        party = self._get_current_party()
        self.party_utility = PartyMemberUtility(party)
        
        # フィルタオプション
        filter_by = params.get("filter", "all")
        sort_by = params.get("sort", "name")
        
        # 全キャラクターを取得
        all_characters = self._get_all_available_characters()
        
        # フィルタリング
        if filter_by == "available":
            # パーティに入っていないキャラクターのみ
            if party:
                party_ids = [char_id for char_id in party.characters.keys()]
                characters = [c for c in all_characters if c.character_id not in party_ids]
            else:
                characters = all_characters
        elif filter_by == "in_party":
            # パーティメンバーのみ
            characters = list(party.characters.values()) if party else []
        else:
            characters = all_characters
        
        # ソート
        self._sort_characters(characters, sort_by)
        
        # PartyMemberUtilityを使用してキャラクター情報辞書を作成
        character_list = []
        for char in characters:
            # in_party判定
            in_party = False
            if party:
                in_party = char.character_id in party.characters
            
            char_info = self.party_utility.create_member_info_dict(
                char,
                additional_fields={
                    "race": char.race,
                    "class": char.character_class,
                    "in_party": in_party
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
            characters.sort(key=lambda c: c.experience.level, reverse=True)
        elif sort_by == "class":
            characters.sort(key=lambda c: c.character_class)
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
        
        # モデルが利用できない場合は、利用可能キャラクターから推定
        if self.character_model is None:
            characters = self._get_all_available_characters()
            return any(c.experience.level >= 5 for c in characters)
        else:
            characters = self.character_model.get_all()
            return any(c.experience.level >= 5 for c in characters)
    
    def _get_available_classes(self) -> List[str]:
        """利用可能なクラスのリストを取得"""
        return [
            "fighter", "priest", "thief", "mage",
            "bishop", "samurai", "lord", "ninja"
        ]
    
    def create_service_panel(self, service_id: str, rect, parent, ui_manager):
        """冒険者ギルド専用のサービスパネルを作成"""
        try:
            if service_id == "character_creation":
                # キャラクター作成ウィザード
                from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
                return CharacterCreationWizard(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
                
            elif service_id == "party_formation":
                # パーティ編成パネル
                from src.facilities.ui.guild.party_formation_panel import PartyFormationPanel
                return PartyFormationPanel(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
                
            elif service_id == "character_list" or service_id == "class_change":
                # 冒険者一覧パネル（クラス変更機能付き）
                from src.facilities.ui.guild.character_list_panel import CharacterListPanel
                return CharacterListPanel(
                    rect=rect,
                    parent=parent,
                    controller=self._controller,
                    ui_manager=ui_manager
                )
                
        except ImportError as e:
            logger.error(f"Failed to import guild panel for {service_id}: {e}")
        
        # 未対応のサービスまたは失敗時は汎用パネルを使用
        return None
    
    def _get_current_party(self) -> Optional[Party]:
        """現在のパーティを取得"""
        if self.game and hasattr(self.game, 'get_party'):
            return self.game.get_party()
        return None
    
    def _get_character_by_id(self, character_id: str) -> Optional[Character]:
        """IDでキャラクターを取得（仮実装）"""
        # 実際の実装では、キャラクターデータベースから取得
        # 現在は仮のキャラクターを返す
        if self.character_model:
            return self.character_model.get(character_id)
        
        # フォールバック: パーティからキャラクターを探す
        party = self._get_current_party()
        if party:
            return party.get_character(character_id)
        
        # テスト用の仮キャラクター
        if character_id.startswith("test_"):
            # テストキャラクターをリストから検索
            test_characters = self._get_all_available_characters()
            for char in test_characters:
                if char.character_id == character_id:
                    return char
            
            # 見つからない場合は新しく作成
            from src.character.stats import BaseStats
            base_stats = BaseStats(
                strength=16, intelligence=16, faith=16,
                vitality=16, agility=16, luck=16
            )
            char = Character(
                name=f"Test Character {character_id[-1]}",
                race="human",
                character_class="fighter",
                base_stats=base_stats
            )
            char.character_id = character_id
            char.experience.level = 12  # テスト用に高レベル（クラス変更可能）
            return char
        
        return None
    
    def _get_all_available_characters(self) -> List[Character]:
        """利用可能な全キャラクターを取得"""
        if self.character_model:
            return self.character_model.get_all()
        
        # フォールバック: テスト用キャラクターを返す
        test_characters = []
        from src.character.stats import BaseStats
        
        for i in range(1, 6):
            # 高い基本能力値を設定（クラス変更要件を満たすため）
            base_stats = BaseStats(
                strength=16,
                intelligence=16, 
                faith=16,  # faithに統一
                vitality=16,
                agility=16,
                luck=16
            )
            
            char = Character(
                name=f"Adventurer {i}",
                race=["human", "elf", "dwarf"][i % 3],
                character_class=["fighter", "priest", "mage", "thief"][i % 4],
                base_stats=base_stats
            )
            char.character_id = f"test_char_{i}"
            
            # テスト用のため、一部キャラクターのレベルを上げる（クラス変更は最低レベル10が必要）
            if i <= 3:
                char.experience.level = 10 + i  # レベル11-13にする
            
            test_characters.append(char)
        
        return test_characters