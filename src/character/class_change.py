"""クラスチェンジシステム"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from src.character.character import Character
from src.character.stats import BaseStats
from src.core.config_manager import config_manager
from src.utils.logger import logger


@dataclass
class ClassChangeRequirements:
    """クラスチェンジの要求条件"""
    min_level: int = 1
    required_stats: Dict[str, int] = None
    required_gold: int = 0
    
    def __post_init__(self):
        if self.required_stats is None:
            self.required_stats = {}


class ClassChangeValidator:
    """クラスチェンジの検証クラス"""
    
    @staticmethod
    def can_change_class(character: Character, target_class: str) -> Tuple[bool, List[str]]:
        """クラスチェンジが可能かチェック
        
        Returns:
            (可能か, エラーメッセージのリスト)
        """
        errors = []
        
        # 設定を読み込み
        char_config = config_manager.load_config("characters")
        classes_config = char_config.get("classes", {})
        
        if target_class not in classes_config:
            errors.append(f"存在しないクラス: {target_class}")
            return False, errors
        
        # 同じクラスへの変更は不可
        if character.character_class == target_class:
            errors.append("同じクラスへの変更はできません")
            return False, errors
        
        target_class_config = classes_config[target_class]
        requirements = target_class_config.get("requirements", {})
        
        # レベル要求（一般的にレベル10以上）
        if character.experience.level < 10:
            errors.append(f"レベルが不足しています（必要: 10、現在: {character.experience.level}）")
        
        # 能力値要求
        for stat_name, required_value in requirements.items():
            current_value = getattr(character.base_stats, stat_name, 0)
            if current_value < required_value:
                errors.append(f"{stat_name}が不足しています（必要: {required_value}、現在: {current_value}）")
        
        # 上級職への制限
        advanced_classes = ["bishop", "samurai", "lord", "ninja"]
        basic_classes = ["fighter", "mage", "priest", "thief"]
        
        if target_class in advanced_classes:
            # 基本職での経験が必要
            if character.character_class not in basic_classes:
                errors.append("上級職へは基本職からのみ転職可能です")
        
        # 基本職同士の転職は制限なし（fighterからmageなど）
        
        return len(errors) == 0, errors
    
    @staticmethod
    def get_available_classes(character: Character) -> List[str]:
        """転職可能なクラスのリストを取得"""
        char_config = config_manager.load_config("characters")
        classes_config = char_config.get("classes", {})
        
        available = []
        for class_name in classes_config.keys():
            can_change, _ = ClassChangeValidator.can_change_class(character, class_name)
            if can_change:
                available.append(class_name)
        
        return available


class ClassChangeManager:
    """クラスチェンジ管理クラス"""
    
    @staticmethod
    def change_class(character: Character, target_class: str, gold_cost: int = 1000) -> Tuple[bool, str]:
        """クラスチェンジを実行
        
        Args:
            character: 対象キャラクター
            target_class: 変更先のクラス
            gold_cost: 必要なゴールド（デフォルト1000G）
            
        Returns:
            (成功か, メッセージ)
        """
        # 検証
        can_change, errors = ClassChangeValidator.can_change_class(character, target_class)
        if not can_change:
            return False, "クラスチェンジできません: " + ", ".join(errors)
        
        # 設定を読み込み
        char_config = config_manager.load_config("characters")
        classes_config = char_config.get("classes", {})
        target_class_config = classes_config[target_class]
        
        # 古いクラス情報を保存
        old_class = character.character_class
        old_hp = character.derived_stats.max_hp
        old_mp = character.derived_stats.max_mp
        
        # クラスを変更
        character.character_class = target_class
        
        # 能力値ボーナスを適用
        class_stats = target_class_config.get("base_stats", {})
        for stat_name, bonus in class_stats.items():
            # 基本能力値は変更しない（クラスボーナスは派生ステータスで反映）
            pass
        
        # 派生ステータスを再計算
        from src.character.stats import StatGenerator
        races_config = char_config.get("races", {})
        race_config = races_config.get(character.race, {})
        
        character.derived_stats = StatGenerator.calculate_derived_stats(
            character.base_stats,
            character.experience.level,
            target_class_config,
            race_config
        )
        
        # HP/MPの調整（減少させない）
        if character.derived_stats.max_hp < old_hp:
            # 新しい最大値の比率で現在値を調整
            hp_ratio = character.derived_stats.max_hp / old_hp
            character.derived_stats.current_hp = max(1, int(character.derived_stats.current_hp * hp_ratio))
        else:
            # 増加分は現在値に加算
            hp_increase = character.derived_stats.max_hp - old_hp
            character.derived_stats.current_hp += hp_increase
        
        if character.derived_stats.max_mp < old_mp:
            # 新しい最大値の比率で現在値を調整
            mp_ratio = character.derived_stats.max_mp / old_mp if old_mp > 0 else 1
            character.derived_stats.current_mp = max(0, int(character.derived_stats.current_mp * mp_ratio))
        else:
            # 増加分は現在値に加算
            mp_increase = character.derived_stats.max_mp - old_mp
            character.derived_stats.current_mp += mp_increase
        
        # レベルをリセット（伝統的なWizardryスタイル）
        character.experience.level = 1
        character.experience.current_xp = 0
        
        logger.info(f"{character.name}が{old_class}から{target_class}にクラスチェンジしました")
        
        return True, f"{character.name}は{target_class}になりました！"
    
    @staticmethod
    def get_class_change_info(character: Character, target_class: str) -> Dict[str, any]:
        """クラスチェンジ情報を取得"""
        char_config = config_manager.load_config("characters")
        classes_config = char_config.get("classes", {})
        
        if target_class not in classes_config:
            return {}
        
        target_config = classes_config[target_class]
        current_config = classes_config.get(character.character_class, {})
        
        info = {
            "target_class": target_class,
            "target_name": config_manager.get_text(target_config.get("name_key", f"class.{target_class}")),
            "current_class": character.character_class,
            "current_name": config_manager.get_text(current_config.get("name_key", f"class.{character.character_class}")),
            "requirements": target_config.get("requirements", {}),
            "hp_multiplier": target_config.get("hp_multiplier", 1.0),
            "mp_multiplier": target_config.get("mp_multiplier", 1.0),
            "weapon_types": target_config.get("weapon_types", []),
            "armor_types": target_config.get("armor_types", []),
            "spell_schools": target_config.get("spell_schools", []),
            "special_abilities": target_config.get("special_abilities", []),
        }
        
        return info