"""
CharacterCreationWizard 型定義

キャラクター作成ウィザードに関する型定義
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass


class WizardStep(Enum):
    """ウィザードステップ"""
    NAME_INPUT = "name_input"
    RACE_SELECTION = "race_selection"
    STATS_GENERATION = "stats_generation"
    CLASS_SELECTION = "class_selection"
    CONFIRMATION = "confirmation"


@dataclass
class CharacterStats:
    """キャラクターステータス"""
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    
    def to_dict(self) -> Dict[str, int]:
        """辞書形式に変換"""
        return {
            'strength': self.strength,
            'dexterity': self.dexterity,
            'constitution': self.constitution,
            'intelligence': self.intelligence,
            'wisdom': self.wisdom,
            'charisma': self.charisma
        }


@dataclass
class CharacterData:
    """キャラクターデータ"""
    name: str = ""
    race: str = ""
    character_class: str = ""
    stats: Optional[CharacterStats] = None
    level: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        result = {
            'name': self.name,
            'race': self.race,
            'character_class': self.character_class,
            'level': self.level
        }
        if self.stats:
            result.update(self.stats.to_dict())
        return result
    
    def is_valid_for_step(self, step: WizardStep) -> bool:
        """指定されたステップに必要なデータが揃っているかチェック"""
        if step == WizardStep.NAME_INPUT:
            return True  # 最初のステップは常に有効
        elif step == WizardStep.RACE_SELECTION:
            return bool(self.name.strip())
        elif step == WizardStep.STATS_GENERATION:
            return bool(self.name.strip() and self.race)
        elif step == WizardStep.CLASS_SELECTION:
            return bool(self.name.strip() and self.race and self.stats)
        elif step == WizardStep.CONFIRMATION:
            return bool(self.name.strip() and self.race and self.character_class and self.stats)
        return False


@dataclass
class WizardConfig:
    """ウィザード設定"""
    character_classes: List[str]
    races: List[str]
    title: str = "キャラクター作成"
    allow_stats_reroll: bool = True
    min_name_length: int = 1
    max_name_length: int = 20
    
    def validate(self) -> None:
        """設定の妥当性をチェック"""
        if not self.character_classes:
            raise ValueError("Wizard config must contain 'character_classes'")
        if not self.races:
            raise ValueError("Wizard config must contain 'races'")
        if self.min_name_length <= 0:
            raise ValueError("min_name_length must be positive")
        if self.max_name_length <= self.min_name_length:
            raise ValueError("max_name_length must be greater than min_name_length")


@dataclass
class StepValidationResult:
    """ステップ検証結果"""
    is_valid: bool
    error_message: str = ""
    
    @classmethod
    def valid(cls) -> 'StepValidationResult':
        """有効な結果を作成"""
        return cls(is_valid=True)
    
    @classmethod
    def invalid(cls, message: str) -> 'StepValidationResult':
        """無効な結果を作成"""
        return cls(is_valid=False, error_message=message)


# コールバック型定義
StatsGeneratorFunc = Callable[[], CharacterStats]
NameValidatorFunc = Callable[[str], StepValidationResult]
RaceValidatorFunc = Callable[[str], StepValidationResult]
ClassValidatorFunc = Callable[[str], StepValidationResult]