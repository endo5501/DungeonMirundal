"""キャラクター作成ウィザード（WindowSystem統合版）"""

from typing import Optional, Dict, Any, Callable
from enum import Enum

from src.ui.window_system import WindowManager
from src.ui.window_system.character_creation_wizard import CharacterCreationWizard
from src.character.character import Character
from src.character.stats import BaseStats, StatGenerator, StatValidator
from src.core.config_manager import config_manager
from src.utils.logger import logger

# キャラクター作成UI定数
CREATION_TITLE_X = 400
CREATION_TITLE_Y = 50
CREATION_DIALOG_WIDTH = 600
CREATION_DIALOG_HEIGHT = 400
STATS_DIALOG_WIDTH = 500
STATS_DIALOG_HEIGHT = 350
CONFIRM_DIALOG_WIDTH = 500
CONFIRM_DIALOG_HEIGHT = 300

# キャラクターデータキー定数
CHAR_DATA_NAME = 'name'
CHAR_DATA_RACE = 'race'
CHAR_DATA_CLASS = 'character_class'
CHAR_DATA_STATS = 'base_stats'

# 設定ファイルキー定数
CONFIG_CHARACTERS = "characters"
CONFIG_RACES = "races"
CONFIG_CLASSES = "classes"


class CreationStep(Enum):
    """作成ステップ"""
    NAME_INPUT = "name_input"
    RACE_SELECTION = "race_selection"
    STATS_GENERATION = "stats_generation"
    CLASS_SELECTION = "class_selection"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"


class CharacterCreationWizard:
    """キャラクター作成ウィザード（WindowSystem統合版）"""
    
    def __init__(self, callback: Optional[Callable] = None):
        # WindowSystem統合
        self.window_manager = WindowManager.get_instance()
        self.wizard_window: Optional[Any] = None
        
        # コールバック設定
        self.callback = callback  # 作成完了時のコールバック
        self.on_cancel = self._default_cancel_handler  # キャンセル時のコールバック
        
        # 状態管理
        self.current_step = CreationStep.NAME_INPUT
        
        # 作成中のキャラクターデータ
        self.character_data = {
            CHAR_DATA_NAME: '',
            CHAR_DATA_RACE: '',
            CHAR_DATA_CLASS: '',
            CHAR_DATA_STATS: None
        }
        
        # 設定データ
        self.char_config = config_manager.load_config(CONFIG_CHARACTERS)
        self.races_config = self.char_config.get(CONFIG_RACES, {})
        self.classes_config = self.char_config.get(CONFIG_CLASSES, {})
        
        logger.info(config_manager.get_text("app_log.character_creation_initialized"))
    
    def _get_wizard_window(self):
        """CharacterCreationWizardインスタンスを取得または作成"""
        if self.wizard_window is None:
            from src.ui.window_system.character_creation_wizard import CharacterCreationWizard as WizardWindow
            wizard_config = self._create_wizard_window_config()
            
            self.wizard_window = WizardWindow(
                window_id="character_creation_wizard",
                wizard_config=wizard_config
            )
        return self.wizard_window
    
    def _create_wizard_window_config(self) -> Dict[str, Any]:
        """CharacterCreationWizard用設定を作成"""
        return {
            'races': self.races_config,
            'character_classes': self.classes_config,  # キーを修正
            'wizard_steps': [step.value for step in CreationStep],
            'auto_advance': False,
            'allow_back_navigation': True,
            'validate_steps': True,
            'show_progress': True,
            'step_validation_required': True,
            'character_data_template': {
                CHAR_DATA_NAME: '',
                CHAR_DATA_RACE: '',
                CHAR_DATA_CLASS: '',
                CHAR_DATA_STATS: None
            }
        }
    
    def start(self):
        """ウィザード開始（WindowSystem版）"""
        try:
            self.current_step = CreationStep.NAME_INPUT
            
            wizard_window = self._get_wizard_window()
            wizard_window.create()
            wizard_window.start_wizard()
            
            logger.info("キャラクター作成ウィザードを開始")
            return True
        except Exception as e:
            logger.error(f"ウィザード開始エラー: {e}")
            return False
    
    def next_step(self):
        """次のステップに進む（WindowSystem版）"""
        try:
            if self.wizard_window:
                return self.wizard_window.next_step()
            
            # フォールバック（基本ステップ管理）
            step_order = list(CreationStep)
            current_index = step_order.index(self.current_step)
            
            if current_index < len(step_order) - 1:
                self.current_step = step_order[current_index + 1]
                self._show_step()
                logger.info(f"次のステップに進行: {self.current_step.value}")
                return True
            else:
                logger.info("最終ステップに到達")
                return False
                
        except Exception as e:
            logger.error(f"ステップ進行エラー: {e}")
            return False
    
    def previous_step(self):
        """前のステップに戻る（WindowSystem版）"""
        try:
            if self.wizard_window:
                return self.wizard_window.previous_step()
            
            # フォールバック（基本ステップ管理）
            step_order = list(CreationStep)
            current_index = step_order.index(self.current_step)
            
            if current_index > 0:
                self.current_step = step_order[current_index - 1]
                self._show_step()
                logger.info(f"前のステップに戻行: {self.current_step.value}")
                return True
            else:
                logger.info("最初のステップに到達")
                return False
                
        except Exception as e:
            logger.error(f"ステップ戻行エラー: {e}")
            return False
    
    def get_current_step(self) -> str:
        """現在のステップを取得"""
        try:
            if self.wizard_window:
                return self.wizard_window.get_current_step()
            
            return self.current_step.value
        except Exception as e:
            logger.error(f"現在ステップ取得エラー: {e}")
            return self.current_step.value
    
    def set_character_data(self, data: Dict[str, Any]):
        """キャラクターデータを設定（WindowSystem版）"""
        try:
            if self.wizard_window:
                return self.wizard_window.set_character_data(data)
            
            # フォールバック（直接設定）
            self.character_data.update(data)
            logger.info(f"キャラクターデータを設定: {list(data.keys())}")
            return True
            
        except Exception as e:
            logger.error(f"キャラクターデータ設定エラー: {e}")
            return False
    
    def get_character_data(self) -> Dict[str, Any]:
        """キャラクターデータを取得"""
        try:
            if self.wizard_window:
                return self.wizard_window.get_character_data()
            
            return self.character_data.copy()
        except Exception as e:
            logger.error(f"キャラクターデータ取得エラー: {e}")
            return self.character_data.copy()
    
    def validate_character_data(self, data: Dict[str, Any]):
        """キャラクターデータを検証（WindowSystem版）"""
        try:
            if self.wizard_window:
                return self.wizard_window.validate_character(data)
            
            # フォールバック（基本検証）
            # 名前チェック
            if not data.get(CHAR_DATA_NAME):
                return False, "キャラクター名が入力されていません"
            
            # 種族チェック
            if not data.get(CHAR_DATA_RACE):
                return False, "種族が選択されていません"
            
            # クラスチェック
            if not data.get(CHAR_DATA_CLASS):
                return False, "クラスが選択されていません"
            
            # ステータスチェック
            if not data.get(CHAR_DATA_STATS):
                return False, "ステータスが設定されていません"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"キャラクターデータ検証エラー: {e}")
            return False, str(e)
    
    def generate_stats(self):
        """ステータス生成（WindowSystem版）"""
        try:
            if self.wizard_window:
                return self.wizard_window.generate_stats()
            
            # フォールバック（基本ステータス生成）
            stats = StatGenerator.generate_random_stats()
            self.character_data[CHAR_DATA_STATS] = stats
            
            logger.info("ステータスを生成しました")
            return stats
            
        except Exception as e:
            logger.error(f"ステータス生成エラー: {e}")
            return None
    
    def finish(self):
        """ウィザード完了（WindowSystem版）"""
        try:
            # キャラクターデータの最終検証
            is_valid, error_message = self.validate_character_data(self.character_data)
            if not is_valid:
                logger.warning(f"キャラクター作成完了失敗: {error_message}")
                return False, error_message
            
            # キャラクター作成
            character = self._create_character_from_data()
            if not character:
                logger.error("キャラクターオブジェクトの作成に失敗")
                return False, "キャラクター作成に失敗しました"
            
            # コールバック実行
            if self.callback:
                self.callback(character)
            
            # ウィザードウィンドウを閉じる
            if self.wizard_window:
                self.wizard_window.close()
            
            self.current_step = CreationStep.COMPLETED
            logger.info(f"キャラクター作成完了: {character.name}")
            return True, character
            
        except Exception as e:
            logger.error(f"ウィザード完了エラー: {e}")
            return False, str(e)
    
    def cancel(self):
        """ウィザードキャンセル（WindowSystem版）"""
        try:
            if self.wizard_window:
                self.wizard_window.close()
            
            # データクリア
            self.character_data = {
                CHAR_DATA_NAME: '',
                CHAR_DATA_RACE: '',
                CHAR_DATA_CLASS: '',
                CHAR_DATA_STATS: None
            }
            
            # キャンセルコールバック実行
            if self.on_cancel:
                self.on_cancel()
            
            logger.info("キャラクター作成をキャンセルしました")
            
        except Exception as e:
            logger.error(f"ウィザードキャンセルエラー: {e}")
    
    def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.wizard_window:
                if hasattr(self.wizard_window, 'cleanup'):
                    self.wizard_window.cleanup()
                self.wizard_window = None
            
            # データクリア
            self.character_data = {
                CHAR_DATA_NAME: '',
                CHAR_DATA_RACE: '',
                CHAR_DATA_CLASS: '',
                CHAR_DATA_STATS: None
            }
            
            logger.info("CharacterCreationWizard（WindowSystem版）リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")
    
    # 内部ヘルパーメソッド
    def _create_character_from_data(self) -> Optional[Character]:
        """キャラクターデータからCharacterオブジェクトを作成"""
        try:
            character = Character(
                name=self.character_data[CHAR_DATA_NAME],
                race=self.character_data[CHAR_DATA_RACE],
                character_class=self.character_data[CHAR_DATA_CLASS],
                base_stats=self.character_data[CHAR_DATA_STATS]
            )
            return character
        except Exception as e:
            logger.error(f"キャラクターオブジェクト作成エラー: {e}")
            return None
    
    def _show_step(self):
        """現在のステップを表示（レガシー互換性）"""
        try:
            if self.wizard_window:
                self.wizard_window.show_current_step()
            else:
                logger.info(f"ステップ表示: {self.current_step.value}")
        except Exception as e:
            logger.error(f"ステップ表示エラー: {e}")
    
    def _default_cancel_handler(self):
        """デフォルトキャンセルハンドラー"""
        logger.info("キャラクター作成がキャンセルされました")


# ファクトリ関数（互換性のため）
def create_character_creation_wizard(callback: Optional[Callable] = None) -> CharacterCreationWizard:
    """キャラクター作成ウィザード作成"""
    return CharacterCreationWizard(callback)