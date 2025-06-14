"""設定管理システム"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logger import logger


class ConfigManager:
    """ゲーム設定の管理"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._text_data: Dict[str, Dict[str, str]] = {}
        self.current_language = "ja"
        
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """設定ファイルの読み込み"""
        if config_name in self._configs:
            return self._configs[config_name]
            
        config_path = self.config_dir / f"{config_name}.yaml"
        
        if not config_path.exists():
            logger.warning(f"設定ファイルが見つかりません: {config_path}")
            return {}
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
                self._configs[config_name] = config_data
                logger.info(f"設定ファイルを読み込みました: {config_name}")
                return config_data
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗: {config_name}, エラー: {e}")
            return {}
    
    def get_config(self, config_name: str, key: str, default: Any = None) -> Any:
        """設定値の取得"""
        config = self.load_config(config_name)
        return config.get(key, default)
    
    def load_text_data(self, language: str = None) -> Dict[str, str]:
        """テキストデータの読み込み"""
        if language is None:
            language = self.current_language
            
        if language in self._text_data:
            return self._text_data[language]
            
        text_path = self.config_dir / "text" / f"{language}.yaml"
        
        if not text_path.exists():
            logger.warning(f"テキストファイルが見つかりません: {text_path}")
            return {}
            
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                text_data = yaml.safe_load(f) or {}
                self._text_data[language] = text_data
                logger.info(f"テキストデータを読み込みました: {language}")
                return text_data
        except Exception as e:
            logger.error(f"テキストファイルの読み込みに失敗: {language}, エラー: {e}")
            return {}
    
    def get_text(self, key: str, language: str = None) -> str:
        """テキストの取得"""
        if language is None:
            language = self.current_language
            
        text_data = self.load_text_data(language)
        
        # ネストされたキーの処理
        keys = key.split('.')
        current_data = text_data
        
        for k in keys:
            if isinstance(current_data, dict) and k in current_data:
                current_data = current_data[k]
            else:
                return f"[{key}]"
                
        return str(current_data)
    
    def set_language(self, language: str):
        """言語の設定"""
        self.current_language = language
        logger.info(f"言語を設定しました: {language}")
    
    def reload_all(self):
        """全設定の再読み込み"""
        self._configs.clear()
        self._text_data.clear()
        logger.info("全設定を再読み込みしました")


# グローバルインスタンス
config_manager = ConfigManager()