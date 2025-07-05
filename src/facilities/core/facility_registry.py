"""施設のグローバル登録・管理"""

from typing import Dict, Type, Optional, List, Any
import json
import logging
from pathlib import Path
from src.character.party import Party
from .facility_service import FacilityService
from .facility_controller import FacilityController
from .service_result import ServiceResult

logger = logging.getLogger(__name__)


class FacilityRegistry:
    """施設のグローバル登録・管理
    
    全施設の登録、管理、アクセスを統括するシングルトン。
    施設の入退場を制御し、一度に一つの施設のみアクティブにする。
    """
    
    _instance = None
    
    def __init__(self):
        """初期化（シングルトン）"""
        self.facilities: Dict[str, FacilityController] = {}
        self.service_classes: Dict[str, Type[FacilityService]] = {}
        self.config: Dict[str, Any] = {}
        self.current_facility_id: Optional[str] = None
        self.current_party: Optional[Party] = None
        
        # 設定ファイルを読み込み
        self._load_config()
        
        logger.info("FacilityRegistry initialized")
    
    @classmethod
    def get_instance(cls) -> 'FacilityRegistry':
        """シングルトンインスタンスを取得
        
        Returns:
            FacilityRegistryのインスタンス
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """インスタンスをリセット（テスト用）"""
        if cls._instance:
            cls._instance.cleanup()
        cls._instance = None
    
    def _load_config(self) -> None:
        """施設設定を読み込み"""
        config_path = Path("src/facilities/config/facilities.json")
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                    logger.info(f"Loaded facility config from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load facility config: {e}")
                self.config = {}
        else:
            logger.info(f"Facility config not found at {config_path}, using defaults")
            self.config = {}
    
    def register_service_class(self, facility_id: str, service_class: Type[FacilityService]) -> None:
        """サービスクラスを登録
        
        Args:
            facility_id: 施設ID
            service_class: サービスクラス
        """
        self.service_classes[facility_id] = service_class
        logger.info(f"Registered service class: {facility_id} -> {service_class.__name__}")
    
    def register_all_services(self) -> None:
        """すべてのサービスクラスを自動登録"""
        # 各施設のサービスクラスをインポートして登録
        try:
            from ..services.guild.guild_service import GuildService
            self.register_service_class("guild", GuildService)
        except ImportError:
            logger.info("GuildService not available")
        
        try:
            from ..services.inn.inn_service import InnService
            self.register_service_class("inn", InnService)
        except ImportError:
            logger.info("InnService not available")
        
        try:
            from ..services.shop.shop_service import ShopService
            self.register_service_class("shop", ShopService)
        except ImportError:
            logger.info("ShopService not available")
        
        try:
            from ..services.temple.temple_service import TempleService
            self.register_service_class("temple", TempleService)
        except ImportError:
            logger.info("TempleService not available")
        
        try:
            from ..services.magic_guild.magic_guild_service import MagicGuildService
            self.register_service_class("magic_guild", MagicGuildService)
        except ImportError:
            logger.info("MagicGuildService not available")
    
    def get_facility_controller(self, facility_id: str) -> Optional[FacilityController]:
        """施設コントローラーを取得
        
        Args:
            facility_id: 施設ID
            
        Returns:
            施設コントローラー（存在しない場合None）
        """
        return self.facilities.get(facility_id)
    
    def create_facility_controller(self, facility_id: str) -> Optional[FacilityController]:
        """施設コントローラーを作成
        
        Args:
            facility_id: 施設ID
            
        Returns:
            作成した施設コントローラー（失敗時None）
        """
        # すでに存在する場合はそれを返す
        if facility_id in self.facilities:
            return self.facilities[facility_id]
        
        # サービスクラスを取得
        service_class = self.service_classes.get(facility_id)
        if not service_class:
            logger.error(f"Service class not found for: {facility_id}")
            return None
        
        # コントローラーを作成
        try:
            controller = FacilityController(facility_id, service_class)
            
            # 設定を適用
            facility_config = self.config.get("facilities", {}).get(facility_id, {})
            controller.set_config(facility_config)
            
            self.facilities[facility_id] = controller
            logger.info(f"Created facility controller: {facility_id}")
            return controller
            
        except Exception as e:
            logger.error(f"Failed to create facility controller: {facility_id}", exc_info=True)
            return None
    
    def enter_facility(self, facility_id: str, party: Party) -> ServiceResult:
        """施設に入る
        
        Args:
            facility_id: 施設ID
            party: 現在のパーティ
            
        Returns:
            実行結果
        """
        # 既存の施設から退出
        if self.current_facility_id:
            exit_result = self.exit_current_facility()
            if not exit_result.is_success():
                return exit_result
        
        # 施設コントローラーを取得/作成
        controller = self.get_facility_controller(facility_id)
        if not controller:
            controller = self.create_facility_controller(facility_id)
            if not controller:
                return ServiceResult.error(f"Failed to create facility: {facility_id}")
        
        # 施設に入る
        try:
            if controller.enter(party):
                self.current_facility_id = facility_id
                self.current_party = party
                return ServiceResult.ok(f"Entered {facility_id}")
            else:
                return ServiceResult.error(f"Failed to enter {facility_id}")
                
        except Exception as e:
            logger.error(f"Exception entering facility: {facility_id}", exc_info=True)
            return ServiceResult.error(f"Exception: {str(e)}")
    
    def exit_current_facility(self) -> ServiceResult:
        """現在の施設から退出
        
        Returns:
            実行結果
        """
        if not self.current_facility_id:
            return ServiceResult.ok("No facility to exit")
        
        controller = self.get_facility_controller(self.current_facility_id)
        if not controller:
            # コントローラーがない場合でも状態をクリア
            self.current_facility_id = None
            self.current_party = None
            return ServiceResult.warning("Facility controller not found, cleared state")
        
        # 施設から退出
        try:
            if controller.exit():
                facility_id = self.current_facility_id
                self.current_facility_id = None
                self.current_party = None
                return ServiceResult.ok(f"Exited {facility_id}")
            else:
                return ServiceResult.error("Failed to exit facility")
                
        except Exception as e:
            logger.error("Exception exiting facility", exc_info=True)
            # エラーでも状態はクリア
            self.current_facility_id = None
            self.current_party = None
            return ServiceResult.error(f"Exception: {str(e)}")
    
    def get_current_facility(self) -> Optional[FacilityController]:
        """現在の施設コントローラーを取得
        
        Returns:
            現在の施設コントローラー（ない場合None）
        """
        if self.current_facility_id:
            return self.get_facility_controller(self.current_facility_id)
        return None
    
    def is_in_facility(self) -> bool:
        """施設内にいるかどうか
        
        Returns:
            施設内にいればTrue
        """
        return self.current_facility_id is not None
    
    def get_facility_list(self) -> List[str]:
        """登録されている施設IDのリストを取得
        
        Returns:
            施設IDのリスト
        """
        return list(self.service_classes.keys())
    
    def get_facility_info(self, facility_id: str) -> Dict[str, Any]:
        """施設情報を取得
        
        Args:
            facility_id: 施設ID
            
        Returns:
            施設情報の辞書
        """
        info = {
            'id': facility_id,
            'registered': facility_id in self.service_classes,
            'has_controller': facility_id in self.facilities,
            'is_current': facility_id == self.current_facility_id
        }
        
        # 設定情報を追加
        facility_config = self.config.get("facilities", {}).get(facility_id, {})
        info.update({
            'name': facility_config.get('name', facility_id),
            'icon': facility_config.get('icon'),
            'welcome_message': facility_config.get('welcome_message')
        })
        
        return info
    
    def cleanup(self) -> None:
        """クリーンアップ処理"""
        # すべての施設から退出
        if self.current_facility_id:
            self.exit_current_facility()
        
        # すべてのコントローラーをクリア
        self.facilities.clear()
        self.current_facility_id = None
        self.current_party = None
        
        logger.info("FacilityRegistry cleaned up")


# グローバルインスタンス
facility_registry = FacilityRegistry.get_instance()