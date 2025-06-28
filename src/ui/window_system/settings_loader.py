"""
SettingsLoader クラス

設定読み込み・保存の専門クラス
"""

import yaml
from pathlib import Path
from typing import Dict, Any
from src.utils.logger import logger


class SettingsLoader:
    """
    設定読み込み・保存クラス
    
    設定ファイルの読み込み・保存処理を担当
    """
    
    def __init__(self, settings_file_path: Path):
        """
        SettingsLoaderを初期化
        
        Args:
            settings_file_path: 設定ファイルパス
        """
        self.settings_file_path = settings_file_path
        self.default_settings = self._get_default_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """
        設定を読み込み
        
        Returns:
            Dict[str, Any]: 読み込まれた設定
        """
        try:
            if self.settings_file_path.exists():
                return self._load_from_file()
            else:
                logger.info(f"設定ファイルが存在しません: {self.settings_file_path}")
                return self.default_settings.copy()
        except Exception as e:
            logger.warning(f"設定読み込みエラー: {e}")
            return self.default_settings.copy()
    
    def _load_from_file(self) -> Dict[str, Any]:
        """ファイルから設定を読み込み"""
        with open(self.settings_file_path, 'r', encoding='utf-8') as f:
            user_settings = yaml.safe_load(f) or {}
        
        # デフォルト設定と統合
        settings = self.default_settings.copy()
        settings.update(user_settings)
        
        logger.debug(f"設定を読み込みました: {self.settings_file_path}")
        return settings
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        設定をファイルに保存
        
        Args:
            settings: 保存する設定
            
        Returns:
            bool: 保存成功の場合True
        """
        try:
            # ディレクトリを作成
            self.settings_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # ファイルに書き込み
            with open(self.settings_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(settings, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=True)
            
            logger.debug(f"設定を保存しました: {self.settings_file_path}")
            return True
        except Exception as e:
            logger.error(f"設定保存エラー: {e}")
            return False
    
    def backup_settings(self) -> bool:
        """
        設定をバックアップ
        
        Returns:
            bool: バックアップ成功の場合True
        """
        if not self.settings_file_path.exists():
            return False
        
        try:
            backup_path = self.settings_file_path.with_suffix('.yaml.backup')
            backup_path.write_bytes(self.settings_file_path.read_bytes())
            
            logger.debug(f"設定をバックアップしました: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"設定バックアップエラー: {e}")
            return False
    
    def restore_from_backup(self) -> bool:
        """
        バックアップから設定を復元
        
        Returns:
            bool: 復元成功の場合True
        """
        backup_path = self.settings_file_path.with_suffix('.yaml.backup')
        if not backup_path.exists():
            return False
        
        try:
            self.settings_file_path.write_bytes(backup_path.read_bytes())
            logger.debug(f"設定をバックアップから復元しました: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"設定復元エラー: {e}")
            return False
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            # オーディオ設定
            "master_volume": 1.0,
            "music_volume": 0.8,
            "sfx_volume": 0.9,
            "voice_volume": 1.0,
            
            # ゲームプレイ設定
            "language": "ja",
            "difficulty": "normal",
            "battle_speed": "normal",
            "message_speed": "normal",
            "auto_save": True,
            
            # 表示設定
            "resolution": "1024x768",
            "ui_scale": 1.0,
            "fullscreen": False,
            
            # 操作設定
            "analog_deadzone": 0.3,
            "analog_sensitivity": 1.0,
            
            # アクセシビリティ
            "feedback_level": "normal",
            "high_contrast": False
        }
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """
        デフォルト設定にリセット
        
        Returns:
            Dict[str, Any]: デフォルト設定
        """
        default_settings = self.default_settings.copy()
        self.save_settings(default_settings)
        logger.info("設定をデフォルト値にリセットしました")
        return default_settings
    
    def get_setting_value(self, key: str, default: Any = None) -> Any:
        """
        個別設定値を取得
        
        Args:
            key: 設定キー
            default: デフォルト値
            
        Returns:
            Any: 設定値
        """
        settings = self.load_settings()
        return settings.get(key, default)
    
    def set_setting_value(self, key: str, value: Any) -> bool:
        """
        個別設定値を保存
        
        Args:
            key: 設定キー
            value: 設定値
            
        Returns:
            bool: 保存成功の場合True
        """
        settings = self.load_settings()
        settings[key] = value
        return self.save_settings(settings)