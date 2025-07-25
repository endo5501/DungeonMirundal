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
        
        # サービスにコントローラーの参照を設定（GuildServiceの場合）
        if hasattr(self.service, 'set_controller'):
            self.service.set_controller(self)
        
        self.window = None  # FacilityWindowは後で設定
        self.is_active = False
        self._party: Optional[Party] = None
        self._config: Dict[str, Any] = {}
        self._game_manager = None  # GameManagerの参照
        
        logger.info(f"FacilityController created: {facility_id}")
    
    def get_party(self) -> Optional[Party]:
        """現在のパーティを取得
        
        Returns:
            現在のパーティ、または None
        """
        return self._party
    
    def set_game_manager(self, game_manager):
        """GameManagerの参照を設定"""
        self._game_manager = game_manager
        
        # サービスにGameManagerの参照を設定
        if hasattr(self.service, 'set_game_manager'):
            self.service.set_game_manager(game_manager)
            logger.debug(f"[DEBUG] FacilityController: GameManager set to service: {self.facility_id}")
    
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
        except Exception:
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
            logger.info(f"Facility already inactive, clearing state: {self.facility_id}")
            # 既に非アクティブでも、状態をクリアして成功とみなす
            self._party = None
            if self.window:
                self._close_window()
            return True
        
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
            logger.debug(f"[DEBUG] FacilityController: Calling service.execute_action({action_id}, {params})")
            logger.debug(f"[DEBUG] FacilityController: Service instance: {self.service}")
            logger.debug(f"[DEBUG] FacilityController: Service type: {type(self.service)}")
            
            result = self.service.execute_action(action_id, params)
            
            logger.debug(f"[DEBUG] FacilityController: Service returned: {result}")
            
            # 成功時はUIを更新（ただし情報取得系のアクションは除く）
            if result.is_success() and self.window and not self._is_info_action(action_id, params):
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
        logger.debug(f"[DEBUG] get_menu_items called: is_active={self.is_active}, facility_id={self.facility_id}")
        if not self.is_active:
            logger.warning(f"[DEBUG] get_menu_items: facility not active, returning empty list")
            return []
        
        try:
            menu_items = self.service.get_menu_items()
            logger.debug(f"[DEBUG] get_menu_items: service returned {len(menu_items)} items")
            return menu_items
        except Exception:
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
                window_id = f"facility_{self.facility_id}_window"
                
                # 既存のウィンドウをチェック
                existing_window = window_manager.get_window(window_id)
                if existing_window and self.window is None:
                    # 既存のウィンドウを再利用
                    self.window = existing_window
                    logger.info(f"Reusing existing FacilityWindow: {window_id}")
                elif self.window is None:
                    # 新しいウィンドウを作成
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
                if self.window is None:
                    self.window = FacilityWindow(self)
                self.window.show()
                logger.warning("WindowManager not available, creating window directly")
            
            return True
            
        except ImportError:
            logger.info("FacilityWindow not available, running without UI")
            return False
        except Exception:
            logger.error(f"Failed to create window: {self.facility_id}", exc_info=True)
            return False
    
    def _close_window(self) -> None:
        """ウィンドウを閉じる"""
        if self.window:
            try:
                # WindowManagerを通してウィンドウを適切に削除
                from src.ui.window_system.window_manager import WindowManager
                window_manager = WindowManager.get_instance()
                if window_manager:
                    # close_window()は破棄とウィンドウスタック管理を含む
                    window_manager.close_window(self.window)
                    logger.info(f"FacilityWindow closed via WindowManager: {self.window.window_id}")
                else:
                    # フォールバック: 直接削除
                    self.window.close()
                    logger.warning("WindowManager not available, closing window directly")
                
                # ウィンドウインスタンスを削除
                self.window = None
                
            except Exception:
                logger.error(f"Failed to close window: {self.facility_id}", exc_info=True)
                # エラーが発生した場合でもウィンドウインスタンスを削除
                self.window = None
    
    def _is_info_action(self, action_id: str, params: Dict[str, Any]) -> bool:
        """情報取得系のアクションかどうかを判定
        
        Args:
            action_id: アクションID
            params: パラメータ
            
        Returns:
            情報取得系のアクションならTrue
        """
        # パラメータにactionがある場合、情報取得系の操作をチェック
        if params and params.get("action") in ["get_info", "get_list", "get_data"]:
            return True
        
        # アクションIDが情報取得系の場合
        info_actions = ["character_list", "party_info", "get_info"]
        return action_id in info_actions
    
    def _update_window(self) -> None:
        """ウィンドウを更新"""
        if self.window:
            try:
                self.window.refresh_content()
            except Exception:
                logger.error(f"Failed to update window: {self.facility_id}", exc_info=True)
    
    def _return_to_overworld(self) -> None:
        """地上画面に戻る"""
        try:
            # WindowManagerで施設ウィンドウが閉じられると、
            # 自動的に前のウィンドウ（地上画面）に戻る
            logger.info("Facility exit completed, returned to overworld")
        except Exception:
            logger.error("Failed to return to overworld", exc_info=True)