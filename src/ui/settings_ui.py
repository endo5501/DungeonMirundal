"""設定画面UIシステム（WindowSystem統合版）"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import pygame

from src.ui.window_system import WindowManager
from src.ui.window_system.settings_window import SettingsWindow
from src.core.config_manager import config_manager
from src.utils.logger import logger

# 設定UI定数
SETTINGS_CONFIG_DIR = "config"
SETTINGS_FILE_NAME = "user_settings.yaml"
GAME_SETTINGS_CONFIG = "game_settings"
USER_SETTINGS_KEY = "user_settings"

# デフォルト設定値
DEFAULT_LANGUAGE = "ja"
DEFAULT_DIFFICULTY = "normal"
DEFAULT_BATTLE_SPEED = "normal"
DEFAULT_MESSAGE_SPEED = "normal"
DEFAULT_ANALOG_DEADZONE = 0.3
DEFAULT_ANALOG_SENSITIVITY = 1.0
DEFAULT_MASTER_VOLUME = 1.0
DEFAULT_MUSIC_VOLUME = 0.8
DEFAULT_SFX_VOLUME = 0.9
DEFAULT_VOICE_VOLUME = 1.0
DEFAULT_RESOLUTION = "1024x768"
DEFAULT_UI_SCALE = 1.0
DEFAULT_FEEDBACK_LEVEL = "normal"


class SettingsCategory(Enum):
    """設定カテゴリ"""
    GAMEPLAY = "gameplay"       # ゲームプレイ
    CONTROLS = "controls"       # 操作設定
    AUDIO = "audio"            # 音声設定
    GRAPHICS = "graphics"      # 表示設定
    ACCESSIBILITY = "accessibility"  # アクセシビリティ


class SettingsUI:
    """設定画面UI管理クラス（WindowSystem統合版）"""
    
    def __init__(self):
        # UI状態
        self.is_open = False
        self.current_category: Optional[SettingsCategory] = None
        self.callback_on_close: Optional[Callable] = None
        
        # WindowSystem統合
        self.window_manager = WindowManager.get_instance()
        self.settings_window: Optional[SettingsWindow] = None
        
        # 設定値の初期化
        self.current_settings = self._load_default_settings()
        
        logger.info("SettingsUI（WindowSystem版）を初期化しました")
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """デフォルト設定値を読み込み"""
        return {
            'gameplay': {
                'language': DEFAULT_LANGUAGE,
                'difficulty': DEFAULT_DIFFICULTY,
                'battle_speed': DEFAULT_BATTLE_SPEED,
                'message_speed': DEFAULT_MESSAGE_SPEED,
            },
            'controls': {
                'analog_deadzone': DEFAULT_ANALOG_DEADZONE,
                'analog_sensitivity': DEFAULT_ANALOG_SENSITIVITY,
            },
            'audio': {
                'master_volume': DEFAULT_MASTER_VOLUME,
                'music_volume': DEFAULT_MUSIC_VOLUME,
                'sfx_volume': DEFAULT_SFX_VOLUME,
                'voice_volume': DEFAULT_VOICE_VOLUME,
            },
            'graphics': {
                'resolution': DEFAULT_RESOLUTION,
                'ui_scale': DEFAULT_UI_SCALE,
            },
            'accessibility': {
                'feedback_level': DEFAULT_FEEDBACK_LEVEL,
            }
        }
    
    def _get_settings_window(self) -> SettingsWindow:
        """SettingsWindowインスタンスを取得または作成"""
        if self.settings_window is None:
            # SettingsWindowの初期化
            self.settings_window = SettingsWindow(
                window_id="settings_main",
                settings_config=self._create_settings_config()
            )
        return self.settings_window
    
    def _create_settings_config(self) -> Dict[str, Any]:
        """設定ウィンドウ用設定を作成"""
        return {
            'title': '設定',
            'categories': [
                {
                    'id': 'gameplay',
                    'label': 'ゲームプレイ',
                    'fields': [
                        {
                            'id': 'language',
                            'label': '言語',
                            'type': 'dropdown',
                            'value': self.current_settings['gameplay']['language'],
                            'options': ['ja', 'en']
                        },
                        {
                            'id': 'difficulty',
                            'label': '難易度',
                            'type': 'dropdown',
                            'value': self.current_settings['gameplay']['difficulty'],
                            'options': ['easy', 'normal', 'hard']
                        }
                    ]
                },
                {
                    'id': 'audio',
                    'label': '音声設定',
                    'fields': [
                        {
                            'id': 'master_volume',
                            'label': 'マスター音量',
                            'type': 'slider',
                            'value': self.current_settings['audio']['master_volume'],
                            'min': 0.0,
                            'max': 1.0
                        },
                        {
                            'id': 'music_volume',
                            'label': 'BGM音量',
                            'type': 'slider',
                            'value': self.current_settings['audio']['music_volume'],
                            'min': 0.0,
                            'max': 1.0
                        }
                    ]
                }
            ]
        }
    
    def show_settings_menu(self):
        """設定メニューを表示（WindowSystem版）"""
        try:
            settings_window = self._get_settings_window()
            settings_window.show()
            self.is_open = True
            logger.info("設定メニューを表示（WindowSystem版）")
        except Exception as e:
            logger.error(f"設定メニュー表示エラー: {e}")
    
    def show_category_settings(self, category: str):
        """カテゴリ別設定を表示（WindowSystem版）"""
        try:
            settings_window = self._get_settings_window()
            settings_window.show_category(category)
            self.current_category = SettingsCategory(category)
            logger.info(f"カテゴリ設定を表示: {category}")
        except Exception as e:
            logger.error(f"カテゴリ設定表示エラー: {e}")
    
    def apply_settings(self, settings: Dict[str, Any]):
        """設定を適用（WindowSystem版）"""
        try:
            self.current_settings.update(settings)
            # 設定をconfig_managerに保存
            config_manager.save_user_settings(self.current_settings)
            logger.info("設定を適用しました")
        except Exception as e:
            logger.error(f"設定適用エラー: {e}")
    
    def reset_to_defaults(self):
        """設定をデフォルトにリセット"""
        try:
            self.current_settings = self._load_default_settings()
            if self.settings_window:
                self.settings_window.update_settings(self.current_settings)
            logger.info("設定をデフォルトにリセット")
        except Exception as e:
            logger.error(f"設定リセットエラー: {e}")
    
    def hide(self):
        """設定UIを非表示（WindowSystem版）"""
        try:
            if self.settings_window:
                self.settings_window.close()
            self.is_open = False
            logger.info("設定UIを非表示")
        except Exception as e:
            logger.error(f"設定UI非表示エラー: {e}")
    
    def show(self):
        """設定UIを表示"""
        self.show_settings_menu()
    
    def set_callback_on_close(self, callback: Callable):
        """クローズ時コールバックを設定"""
        self.callback_on_close = callback
    
    def cleanup(self):
        """リソースクリーンアップ"""
        if self.settings_window:
            self.settings_window.cleanup()
            self.settings_window = None
        self.is_open = False
        logger.info("SettingsUIリソースをクリーンアップしました")


# グローバルインスタンス（互換性のため）
settings_ui = SettingsUI()