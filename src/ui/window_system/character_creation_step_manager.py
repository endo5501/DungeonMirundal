"""
CharacterCreationStepManager クラス

ウィザードのステップ管理専門クラス
"""

from typing import List, Dict, Any, Optional
from .character_creation_types import WizardStep, CharacterData, StepValidationResult
from src.utils.logger import logger


class CharacterCreationStepManager:
    """
    キャラクター作成ステップ管理クラス
    
    ウィザードのステップ遷移と検証を担当
    """
    
    def __init__(self):
        """CharacterCreationStepManagerを初期化"""
        self.steps: List[WizardStep] = [
            WizardStep.NAME_INPUT,
            WizardStep.RACE_SELECTION,
            WizardStep.STATS_GENERATION,
            WizardStep.CLASS_SELECTION,
            WizardStep.CONFIRMATION
        ]
        self.current_step_index = 0
    
    @property
    def current_step(self) -> WizardStep:
        """現在のステップを取得"""
        return self.steps[self.current_step_index]
    
    def can_advance(self, character_data: Dict[str, Any]) -> StepValidationResult:
        """次のステップに進めるかチェック"""
        current_step = self.current_step
        
        if current_step == WizardStep.NAME_INPUT:
            name = character_data.get('name', '').strip()
            if not name:
                return StepValidationResult.invalid("名前を入力してください")
            
        elif current_step == WizardStep.RACE_SELECTION:
            race = character_data.get('race', '')
            if not race:
                return StepValidationResult.invalid("種族を選択してください")
                
        elif current_step == WizardStep.STATS_GENERATION:
            if 'strength' not in character_data:
                return StepValidationResult.invalid("ステータスを生成してください")
                
        elif current_step == WizardStep.CLASS_SELECTION:
            character_class = character_data.get('character_class', '')
            if not character_class:
                return StepValidationResult.invalid("職業を選択してください")
        
        return StepValidationResult.valid()
    
    def advance_step(self) -> bool:
        """次のステップに進む"""
        if self.current_step_index >= len(self.steps) - 1:
            return False
        
        self.current_step_index += 1
        logger.debug(f"ステップを進めました: {self.current_step}")
        return True
    
    def go_back(self) -> bool:
        """前のステップに戻る"""
        if self.current_step_index <= 0:
            return False
        
        self.current_step_index -= 1
        logger.debug(f"ステップを戻しました: {self.current_step}")
        return True
    
    def reset_to_beginning(self) -> None:
        """最初のステップに戻る"""
        self.current_step_index = 0
        logger.debug("ステップを最初に戻しました")
    
    def is_last_step(self) -> bool:
        """最後のステップかどうか"""
        return self.current_step_index >= len(self.steps) - 1
    
    def is_first_step(self) -> bool:
        """最初のステップかどうか"""
        return self.current_step_index <= 0
    
    def get_step_title(self) -> str:
        """現在のステップのタイトルを取得"""
        current_index = self.current_step_index + 1
        total_steps = len(self.steps)
        
        step_titles = {
            WizardStep.NAME_INPUT: "名前入力",
            WizardStep.RACE_SELECTION: "種族選択",
            WizardStep.STATS_GENERATION: "ステータス生成",
            WizardStep.CLASS_SELECTION: "職業選択",
            WizardStep.CONFIRMATION: "確認"
        }
        
        title = step_titles.get(self.current_step, "キャラクター作成")
        return f"ステップ {current_index}/{total_steps}: {title}"
    
    def get_progress_percentage(self) -> float:
        """進捗パーセンテージを取得"""
        return (self.current_step_index / max(len(self.steps) - 1, 1)) * 100.0
    
    def validate_all_steps(self, character_data: Dict[str, Any]) -> StepValidationResult:
        """全ステップのデータを検証"""
        required_fields = {
            'name': "名前",
            'race': "種族", 
            'character_class': "職業",
            'strength': "筋力",
            'dexterity': "敏捷",
            'constitution': "体力",
            'intelligence': "知力",
            'wisdom': "精神",
            'charisma': "魅力"
        }
        
        for field, field_name in required_fields.items():
            if field not in character_data or not character_data[field]:
                return StepValidationResult.invalid(f"{field_name}が設定されていません")
        
        return StepValidationResult.valid()