"""施設の統一制御クラス"""

from typing import Dict, Optional, Type, Any
import logging
from src.character.party import Party
from .facility_service import FacilityService
from .service_result import ServiceResult

logger = logging.getLogger(__name__)


class FacilityController:
    """施設の統一制御クラス
    
    施設の入退場、サービス実行、UI管理を統括する。
    シンプルで直接的な制御フローを提供。
    """
    
    def __init__(self, facility_id: str, service_class: Type[FacilityService]):
        """初期化
        
        Args:
            facility_id: 施設ID
            service_class: サービスクラス
        """
        self.facility_id = facility_id
        self.service = service_class()  # サービスクラスは引数なしで初期化
        self.window = None  # FacilityWindowは後で設定
        self.is_active = False
        self._party: Optional[Party] = None
        self._config: Dict[str, Any] = {}
        
        logger.info(f"FacilityController created: {facility_id}")
    
    def enter(self, party: Party) -> bool:
        """施設に入る
        
        Args:
            party: 現在のパーティ
            
        Returns:
            成功したらTrue
        """
        if self.is_active:
            logger.warning(f"Already in facility: {self.facility_id}")
            return False
        
        # パーティを設定
        self._party = party
        self.service.set_party(party)
        
        # 施設をアクティブ状態に設定（ウィンドウ作成前に必要）
        self.is_active = True
        
        # ウィンドウを作成・表示（UIモジュールがある場合）
        try:
            if self._create_and_show_window():
                logger.info(f"Entered facility: {self.facility_id}")
                return True
            else:
                # UIなしでも施設は利用可能（テスト用など）
                logger.info(f"Entered facility (no UI): {self.facility_id}")
                return True
        except Exception as e:
            # ウィンドウ作成に失敗した場合、状態をリセット
            logger.error(f"Failed to create facility window: {self.facility_id}", exc_info=True)
            self.is_active = False
            self._party = None
            return False
    
    def exit(self) -> bool:
        """施設から出る - シンプルな直接処理
        
        Returns:
            成功したらTrue
        """
        if not self.is_active:
            logger.warning(f"Not in facility: {self.facility_id}")
            return False
        
        # ウィンドウを閉じる
        if self.window:
            self._close_window()
        
        # 状態をクリア
        self.is_active = False
        self._party = None
        self.service.clear_service_data()
        
        logger.info(f"Exited facility: {self.facility_id}")
        
        # 地上画面に直接戻る（シンプルな処理）
        self._return_to_overworld()
        
        return True
    
    def execute_service(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> ServiceResult:
        """サービスを実行
        
        Args:
            action_id: アクションID
            params: アクションパラメータ
            
        Returns:
            実行結果
        """
        if not self.is_active:
            return ServiceResult.error("Facility not active")
        
        # パラメータのデフォルト値
        if params is None:
            params = {}
        
        # 実行可能性チェック
        if not self.service.can_execute(action_id):
            return ServiceResult.error(f"Cannot execute action: {action_id}")
        
        # パラメータ検証
        if not self.service.validate_action_params(action_id, params):
            return ServiceResult.error("Invalid action parameters")
        
        # サービス実行
        try:
            result = self.service.execute_action(action_id, params)
            
            # 成功時はUIを更新
            if result.is_success() and self.window:
                self._update_window()
            
            return result
            
        except Exception as e:
            logger.error(f"Service execution failed: {action_id}", exc_info=True)
            return ServiceResult.error(f"Service execution failed: {str(e)}")
    
    def get_menu_items(self) -> list:
        """現在利用可能なメニュー項目を取得
        
        Returns:
            メニュー項目のリスト
        """
        logger.info(f"[DEBUG] get_menu_items called: is_active={self.is_active}, facility_id={self.facility_id}")
        if not self.is_active:
            logger.warning(f"[DEBUG] get_menu_items: facility not active, returning empty list")
            return []
        
        try:
            menu_items = self.service.get_menu_items()
            logger.info(f"[DEBUG] get_menu_items: service returned {len(menu_items)} items")
            return menu_items
        except Exception as e:
            logger.error(f"Failed to get menu items: {self.facility_id}", exc_info=True)
            return []
    
    def get_service_info(self) -> Dict[str, Any]:
        """サービス情報を取得
        
        Returns:
            サービス情報の辞書
        """
        return {
            'facility_id': self.facility_id,
            'is_active': self.is_active,
            'has_window': self.window is not None,
            'service_type': self.service.__class__.__name__,
            'party_name': self._party.name if self._party else None
        }
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """設定を設定
        
        Args:
            config: 施設設定
        """
        self._config = config
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """設定を取得
        
        Args:
            key: 設定キー
            default: デフォルト値
            
        Returns:
            設定値
        """
        return self._config.get(key, default)
    
    # プライベートメソッド
    
    def _create_and_show_window(self) -> bool:
        """ウィンドウを作成して表示
        
        Returns:
            成功したらTrue
        """
        try:
            # UI モジュールを遅延インポート（循環参照回避）
            from ..ui.facility_window import FacilityWindow
            from src.ui.window_system.window_manager import WindowManager
            
            # WindowManagerを通してウィンドウを作成・表示
            window_manager = WindowManager.get_instance()
            if window_manager:
                # WindowManagerでウィンドウを作成（自動的に登録される）
                window_id = f"facility_{self.facility_id}_window"
                self.window = window_manager.create_window(
                    FacilityWindow, 
                    window_id=window_id,
                    facility_controller=self
                )
                logger.info(f"FacilityWindow created via WindowManager: {self.window.window_id}")
                
                # ウィンドウを表示
                window_manager.show_window(self.window)
                logger.info(f"FacilityWindow shown via WindowManager: {self.window.window_id}")
            else:
                # フォールバック: 直接作成・表示
                self.window = FacilityWindow(self)
                self.window.show()
                logger.warning("WindowManager not available, creating window directly")
            
            return True
            
        except ImportError:
            logger.info("FacilityWindow not available, running without UI")
            return False
        except Exception as e:
            logger.error(f"Failed to create window: {self.facility_id}", exc_info=True)
            return False
    
    def _close_window(self) -> None:
        """ウィンドウを閉じる"""
        if self.window:
            try:
                # WindowManagerを通してウィンドウを閉じる
                from src.ui.window_system.window_manager import WindowManager
                window_manager = WindowManager.get_instance()
                if window_manager:
                    window_manager.hide_window(self.window, remove_from_stack=True)
                    logger.info(f"FacilityWindow removed from WindowManager: {self.window.window_id}")
                else:
                    # フォールバック: 直接閉じる
                    self.window.close()
                    logger.warning("WindowManager not available, closing window directly")
            except Exception as e:
                logger.error(f"Failed to close window: {self.facility_id}", exc_info=True)
            finally:
                self.window = None
    
    def _update_window(self) -> None:
        """ウィンドウを更新"""
        if self.window:
            try:
                self.window.refresh_content()
            except Exception as e:
                logger.error(f"Failed to update window: {self.facility_id}", exc_info=True)
    
    def _return_to_overworld(self) -> None:
        """地上画面に戻る"""
        try:
            # WindowManagerで施設ウィンドウが閉じられると、
            # 自動的に前のウィンドウ（地上画面）に戻る
            logger.info("Facility exit completed, returned to overworld")
        except Exception as e:
            logger.error("Failed to return to overworld", exc_info=True)