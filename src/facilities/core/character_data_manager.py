"""キャラクター設定データ管理"""

from typing import Dict, Any, List, Optional, NamedTuple
import logging
from dataclasses import dataclass
from src.core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class RaceData:
    """種族データ"""
    id: str
    name: str
    description: str
    base_stats: Dict[str, int]
    stat_modifiers: Dict[str, float]


@dataclass
class ClassData:
    """職業データ"""
    id: str
    name: str
    description: str
    base_stats: Dict[str, int]
    hp_multiplier: float
    mp_multiplier: float
    requirements: Dict[str, int]
    weapon_types: List[str]
    armor_types: List[str]
    spell_schools: Optional[List[str]] = None
    special_abilities: Optional[List[str]] = None


class CharacterDataManager:
    """キャラクター設定データ管理クラス
    
    config/characters.yamlとconfig/text/ja.yamlから
    種族・職業データを読み込み、統一的にアクセスできるAPIを提供
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """初期化
        
        Args:
            config_manager: 設定管理インスタンス（Noneの場合はグローバルインスタンスを使用）
        """
        if config_manager is None:
            from src.core.config_manager import config_manager as global_config_manager
            self.config_manager = global_config_manager
        else:
            self.config_manager = config_manager
        
        self._character_config: Optional[Dict[str, Any]] = None
        self._races_cache: Optional[List[RaceData]] = None
        self._classes_cache: Optional[List[ClassData]] = None
        
        logger.info("CharacterDataManager初期化完了")
    
    def _load_character_config(self) -> Dict[str, Any]:
        """キャラクター設定を読み込み（キャッシュ機能付き）"""
        if self._character_config is None:
            self._character_config = self.config_manager.load_config("characters")
            logger.info("キャラクター設定を読み込み完了")
        return self._character_config
    
    def get_races(self) -> List[RaceData]:
        """利用可能な種族データのリストを取得
        
        Returns:
            種族データのリスト
        """
        if self._races_cache is None:
            self._races_cache = self._build_races_data()
        
        return self._races_cache.copy()
    
    def get_classes(self) -> List[ClassData]:
        """利用可能な職業データのリストを取得
        
        Returns:
            職業データのリスト
        """
        if self._classes_cache is None:
            self._classes_cache = self._build_classes_data()
        
        return self._classes_cache.copy()
    
    def get_race_by_id(self, race_id: str) -> Optional[RaceData]:
        """IDによる種族データ取得
        
        Args:
            race_id: 種族ID
            
        Returns:
            種族データ（見つからない場合はNone）
        """
        races = self.get_races()
        for race in races:
            if race.id == race_id:
                return race
        return None
    
    def get_class_by_id(self, class_id: str) -> Optional[ClassData]:
        """IDによる職業データ取得
        
        Args:
            class_id: 職業ID
            
        Returns:
            職業データ（見つからない場合はNone）
        """
        classes = self.get_classes()
        for cls in classes:
            if cls.id == class_id:
                return cls
        return None
    
    def check_class_requirements(self, stats: Dict[str, int], class_id: str) -> bool:
        """職業要件チェック
        
        Args:
            stats: キャラクターの能力値辞書
            class_id: 職業ID
            
        Returns:
            要件を満たしている場合True
        """
        class_data = self.get_class_by_id(class_id)
        if not class_data:
            logger.warning(f"職業データが見つかりません: {class_id}")
            return False
        
        # 要件チェック
        for stat_name, required_value in class_data.requirements.items():
            if stats.get(stat_name, 0) < required_value:
                logger.debug(f"職業要件未満: {class_id} - {stat_name} {stats.get(stat_name, 0)} < {required_value}")
                return False
        
        return True
    
    def get_available_classes(self, stats: Dict[str, int]) -> List[ClassData]:
        """能力値に基づいて選択可能な職業を取得
        
        Args:
            stats: キャラクターの能力値辞書
            
        Returns:
            選択可能な職業データのリスト
        """
        all_classes = self.get_classes()
        available = []
        
        for class_data in all_classes:
            if self.check_class_requirements(stats, class_data.id):
                available.append(class_data)
        
        return available
    
    def get_display_name(self, category: str, key: str) -> str:
        """表示名取得（多言語対応）
        
        Args:
            category: カテゴリ（"race" または "class"）
            key: キー（種族IDまたは職業ID）
            
        Returns:
            表示名（見つからない場合はキーをそのまま返す）
        """
        text_key = f"{category}.{key}"
        display_name = self.config_manager.get_text(text_key, default=key)
        return display_name
    
    def get_description(self, category: str, key: str) -> str:
        """説明文取得（多言語対応）
        
        Args:
            category: カテゴリ（"race" または "class"）
            key: キー（種族IDまたは職業ID）
            
        Returns:
            説明文（見つからない場合は空文字列）
        """
        text_key = f"{category}.{key}_desc"
        description = self.config_manager.get_text(text_key, default="")
        return description
    
    def _build_races_data(self) -> List[RaceData]:
        """種族データを構築"""
        config = self._load_character_config()
        races_config = config.get("races", {})
        
        races = []
        for race_id, race_config in races_config.items():
            race_data = RaceData(
                id=race_id,
                name=self.get_display_name("race", race_id),
                description=self.get_description("race", race_id),
                base_stats=race_config.get("base_stats", {}),
                stat_modifiers=race_config.get("stat_modifiers", {})
            )
            races.append(race_data)
        
        logger.info(f"種族データ構築完了: {len(races)}種族")
        return races
    
    def _build_classes_data(self) -> List[ClassData]:
        """職業データを構築"""
        config = self._load_character_config()
        classes_config = config.get("classes", {})
        
        classes = []
        for class_id, class_config in classes_config.items():
            class_data = ClassData(
                id=class_id,
                name=self.get_display_name("class", class_id),
                description=self.get_description("class", class_id),
                base_stats=class_config.get("base_stats", {}),
                hp_multiplier=class_config.get("hp_multiplier", 1.0),
                mp_multiplier=class_config.get("mp_multiplier", 1.0),
                requirements=class_config.get("requirements", {}),
                weapon_types=class_config.get("weapon_types", []),
                armor_types=class_config.get("armor_types", []),
                spell_schools=class_config.get("spell_schools"),
                special_abilities=class_config.get("special_abilities")
            )
            classes.append(class_data)
        
        logger.info(f"職業データ構築完了: {len(classes)}職業")
        return classes
    
    def invalidate_cache(self) -> None:
        """キャッシュを無効化（設定変更時用）"""
        self._character_config = None
        self._races_cache = None
        self._classes_cache = None
        logger.info("CharacterDataManagerキャッシュを無効化")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """デバッグ情報取得
        
        Returns:
            デバッグ情報辞書
        """
        return {
            "config_loaded": self._character_config is not None,
            "races_cached": self._races_cache is not None,
            "classes_cached": self._classes_cache is not None,
            "races_count": len(self._races_cache) if self._races_cache else 0,
            "classes_count": len(self._classes_cache) if self._classes_cache else 0,
            "config_manager_available": self.config_manager is not None
        }


# グローバルインスタンス（必要に応じて使用）
character_data_manager = CharacterDataManager()