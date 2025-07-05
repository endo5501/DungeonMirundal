"""施設設定ローダー"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


class FacilityConfigLoader:
    """施設設定ローダー
    
    JSONファイルから施設設定を読み込み、検証し、
    必要に応じてデフォルト値を補完する。
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """初期化
        
        Args:
            config_dir: 設定ディレクトリのパス
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config"
        
        self.config_dir = config_dir
        self.config_file = self.config_dir / "facilities.json"
        self.schema_file = self.config_dir / "facilities_schema.json"
        
        self._config: Dict[str, Any] = {}
        self._schema: Dict[str, Any] = {}
        self._loaded = False
        
        logger.info(f"FacilityConfigLoader initialized with dir: {self.config_dir}")
    
    def load(self) -> Dict[str, Any]:
        """設定を読み込む
        
        Returns:
            読み込んだ設定
        """
        if self._loaded:
            return self._config
        
        try:
            # スキーマを読み込み
            self._load_schema()
            
            # 設定を読み込み
            self._load_config()
            
            # 検証
            self._validate_config()
            
            # デフォルト値を補完
            self._apply_defaults()
            
            self._loaded = True
            logger.info("Facility configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load facility configuration: {e}")
            # フォールバックとして最小限の設定を返す
            self._config = self._get_fallback_config()
            self._loaded = True
        
        return self._config
    
    def reload(self) -> Dict[str, Any]:
        """設定を再読み込み
        
        Returns:
            再読み込みした設定
        """
        self._loaded = False
        self._config = {}
        return self.load()
    
    def get_facility_config(self, facility_id: str) -> Dict[str, Any]:
        """特定の施設の設定を取得
        
        Args:
            facility_id: 施設ID
            
        Returns:
            施設設定（見つからない場合は空の辞書）
        """
        if not self._loaded:
            self.load()
        
        return self._config.get("facilities", {}).get(facility_id, {})
    
    def get_service_config(self, facility_id: str, service_id: str) -> Dict[str, Any]:
        """特定のサービスの設定を取得
        
        Args:
            facility_id: 施設ID
            service_id: サービスID
            
        Returns:
            サービス設定（見つからない場合は空の辞書）
        """
        facility_config = self.get_facility_config(facility_id)
        return facility_config.get("services", {}).get(service_id, {})
    
    def get_common_settings(self) -> Dict[str, Any]:
        """共通設定を取得
        
        Returns:
            共通設定
        """
        if not self._loaded:
            self.load()
        
        return self._config.get("common_settings", {})
    
    def get_wizard_steps(self, facility_id: str, service_id: str) -> List[Dict[str, Any]]:
        """ウィザードステップを取得
        
        Args:
            facility_id: 施設ID
            service_id: サービスID
            
        Returns:
            ウィザードステップのリスト
        """
        service_config = self.get_service_config(facility_id, service_id)
        return service_config.get("steps", [])
    
    # プライベートメソッド
    
    def _load_schema(self) -> None:
        """JSONスキーマを読み込む"""
        if not self.schema_file.exists():
            logger.warning(f"Schema file not found: {self.schema_file}")
            self._schema = {}
            return
        
        try:
            with open(self.schema_file, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
                logger.info("Schema loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            self._schema = {}
    
    def _load_config(self) -> None:
        """設定ファイルを読み込む"""
        if not self.config_file.exists():
            logger.warning(f"Config file not found: {self.config_file}")
            self._config = self._get_fallback_config()
            return
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self._config = json.load(f)
                logger.info("Config loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = self._get_fallback_config()
    
    def _validate_config(self) -> None:
        """設定を検証"""
        if not self._schema:
            logger.info("No schema available, skipping validation")
            return
        
        try:
            validate(instance=self._config, schema=self._schema)
            logger.info("Config validation passed")
        except ValidationError as e:
            logger.error(f"Config validation failed: {e}")
            # 検証エラーでも続行（デフォルト値で補完）
    
    def _apply_defaults(self) -> None:
        """デフォルト値を適用"""
        # 共通設定のデフォルト
        if "common_settings" not in self._config:
            self._config["common_settings"] = {}
        
        common = self._config["common_settings"]
        if "ui_theme" not in common:
            common["ui_theme"] = "default"
        if "transition_effect" not in common:
            common["transition_effect"] = "fade"
        
        # 各施設のデフォルト
        for facility_id, facility in self._config.get("facilities", {}).items():
            # 必須フィールドの確認
            if "id" not in facility:
                facility["id"] = facility_id
            if "name" not in facility:
                facility["name"] = facility_id.title()
            if "services" not in facility:
                facility["services"] = {}
            
            # 各サービスのデフォルト
            for service_id, service in facility["services"].items():
                if "name" not in service:
                    service["name"] = service_id.replace("_", " ").title()
                if "type" not in service:
                    service["type"] = "action"
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """フォールバック設定を取得"""
        return {
            "version": "1.0.0",
            "facilities": {
                "guild": {
                    "id": "guild",
                    "name": "冒険者ギルド",
                    "service_class": "GuildService",
                    "services": {}
                },
                "inn": {
                    "id": "inn",
                    "name": "宿屋",
                    "service_class": "InnService",
                    "services": {}
                },
                "shop": {
                    "id": "shop",
                    "name": "商店",
                    "service_class": "ShopService",
                    "services": {}
                },
                "temple": {
                    "id": "temple",
                    "name": "教会",
                    "service_class": "TempleService",
                    "services": {}
                },
                "magic_guild": {
                    "id": "magic_guild",
                    "name": "魔法ギルド",
                    "service_class": "MagicGuildService",
                    "services": {}
                }
            },
            "common_settings": {
                "ui_theme": "default",
                "transition_effect": "fade"
            }
        }


# グローバルインスタンス
config_loader = FacilityConfigLoader()