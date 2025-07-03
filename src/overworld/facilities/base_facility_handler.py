"""
BaseFacilityHandler - 施設操作の統一ハンドラー

Inn施設クラスの90-99%重複を統合するため、共通パターンを抽象化
Template Method + Strategy + Command パターンの組み合わせによる統合
"""

from abc import abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.party import Party
from src.ui.window_system import WindowManager
from src.utils.logger import logger


class OperationType(Enum):
    """操作タイプ"""
    SHOW_SERVICE = "show_service"
    SHOW_DIALOG = "show_dialog"
    VALIDATE_PARTY = "validate_party"
    CLEANUP_UI = "cleanup_ui"


@dataclass
class FacilityOperationResult:
    """施設操作結果"""
    success: bool
    message: str = ""
    error_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class FacilityCommand:
    """施設操作コマンド（Command Pattern）"""
    
    def __init__(self, operation: str, params: Dict[str, Any], handler: 'BaseFacilityHandler'):
        self.operation = operation
        self.params = params
        self.handler = handler
    
    def execute(self) -> FacilityOperationResult:
        """コマンドを実行"""
        return self.handler.execute_facility_operation(self.operation, **self.params)
    
    def undo(self) -> FacilityOperationResult:
        """コマンドを元に戻す（将来的な拡張用）"""
        # TODO: 元に戻す操作の実装
        return FacilityOperationResult(success=True, message="Undo not implemented")


class BaseFacilityHandler(BaseFacility):
    """
    施設操作の統一ハンドラー
    
    Template Method パターンによる共通アルゴリズムの定義
    Strategy パターンによる操作の切り替え
    Command パターンによる操作のカプセル化
    """
    
    def __init__(self, facility_id: str, facility_type: FacilityType, name_key: str):
        super().__init__(facility_id, facility_type, name_key)
        
        # UI要素管理
        self._active_ui_elements: List[Any] = []
        
        # WindowManager統合
        self.window_manager = WindowManager.get_instance()
        
        logger.info(f"BaseFacilityHandler初期化: {facility_id}")
    
    def execute_facility_operation(self, operation: str, **kwargs) -> FacilityOperationResult:
        """
        施設操作の統一実行メソッド（Template Method Pattern）
        
        Args:
            operation: 操作タイプ
            **kwargs: 操作パラメータ
            
        Returns:
            FacilityOperationResult: 操作結果
        """
        try:
            # 1. 前提条件の検証
            validation_result = self._validate_operation(operation, **kwargs)
            if not validation_result.success:
                return validation_result
            
            # 2. 操作の実行
            execution_result = self._execute_operation(operation, **kwargs)
            
            # 3. 後処理
            self._post_operation_cleanup(operation, execution_result)
            
            return execution_result
            
        except Exception as e:
            logger.error(f"施設操作エラー({operation}): {e}")
            return FacilityOperationResult(
                success=False,
                error_type='execution_error',
                message=f"操作実行中にエラーが発生しました: {str(e)}"
            )
    
    def _validate_operation(self, operation: str, **kwargs) -> FacilityOperationResult:
        """操作の前提条件を検証"""
        # 基本的なパーティ要件チェック
        if operation in ['show_service', 'show_dialog'] and not self.current_party:
            return FacilityOperationResult(
                success=False,
                error_type='prerequisite_error',
                message="Party not set for facility operation"
            )
        
        # 操作固有の検証（サブクラスでオーバーライド可能）
        return self._validate_specific_operation(operation, **kwargs)
    
    def _validate_specific_operation(self, operation: str, **kwargs) -> FacilityOperationResult:
        """操作固有の検証（サブクラスでオーバーライド）"""
        return FacilityOperationResult(success=True)
    
    @abstractmethod
    def _execute_operation(self, operation: str, **kwargs) -> FacilityOperationResult:
        """
        具体的な操作実行（サブクラスで実装）
        
        Args:
            operation: 操作タイプ
            **kwargs: 操作パラメータ
            
        Returns:
            FacilityOperationResult: 実行結果
        """
        pass
    
    def _post_operation_cleanup(self, operation: str, result: FacilityOperationResult) -> None:
        """操作後のクリーンアップ"""
        # 共通的なクリーンアップ処理
        if not result.success:
            logger.warning(f"操作 {operation} が失敗しました: {result.message}")
        
        # 操作固有のクリーンアップ（サブクラスでオーバーライド可能）
        self._cleanup_specific_operation(operation, result)
    
    def _cleanup_specific_operation(self, operation: str, result: FacilityOperationResult) -> None:
        """操作固有のクリーンアップ（サブクラスでオーバーライド）"""
        pass
    
    def show_facility_window(self, window_type: str, config: Dict[str, Any]) -> FacilityOperationResult:
        """
        施設ウィンドウ表示の統一メソッド（WindowManager統合パターン）
        
        Args:
            window_type: ウィンドウタイプ
            config: ウィンドウ設定
            
        Returns:
            FacilityOperationResult: 表示結果
        """
        try:
            # ウィンドウ設定の作成
            window_config = self.create_service_window_config(window_type, config)
            
            # WindowManagerを使用してウィンドウを表示
            from src.ui.window_system.inn_service_window import InnServiceWindow
            
            # ウィンドウタイプに応じたクラスの選択（Strategy Pattern）
            window_classes = {
                'inn_service': InnServiceWindow,
                # 他の施設用ウィンドウクラスを追加
            }
            
            window_class = window_classes.get(window_type, InnServiceWindow)
            
            window = self.window_manager.create_window(
                window_class,
                f'{self.facility_id}_{window_type}_window',
                facility_config=window_config
            )
            
            self.window_manager.show_window(window, push_to_stack=True)
            
            # アクティブなUI要素として記録
            self._active_ui_elements.append(window)
            
            return FacilityOperationResult(
                success=True,
                message=f"ウィンドウ {window_type} を表示しました"
            )
            
        except Exception as e:
            logger.error(f"ウィンドウ表示エラー({window_type}): {e}")
            return FacilityOperationResult(
                success=False,
                error_type='window_display_error',
                message=f"ウィンドウ表示に失敗しました: {str(e)}"
            )
    
    def create_service_window_config(self, service_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        サービスウィンドウ設定作成の統一メソッド
        
        Args:
            service_type: サービスタイプ
            params: サービスパラメータ
            
        Returns:
            Dict[str, Any]: 統一されたウィンドウ設定
        """
        return {
            'window_type': service_type,
            'facility_config': {
                'facility_id': self.facility_id,
                'facility_type': self.facility_type.value,
                'facility_name': self.get_name(),
                'party': self.current_party
            },
            'service_config': params
        }
    
    def handle_error(self, error_type: str, message: str) -> FacilityOperationResult:
        """
        エラーハンドリングの標準化
        
        Args:
            error_type: エラータイプ
            message: エラーメッセージ
            
        Returns:
            FacilityOperationResult: 標準化されたエラー結果
        """
        logger.error(f"施設エラー({self.facility_id}): {error_type} - {message}")
        
        return FacilityOperationResult(
            success=False,
            error_type=error_type,
            message=message
        )
    
    def show_dialog(self, dialog_type: str, title: str, message: str, **kwargs) -> FacilityOperationResult:
        """
        ダイアログ表示の統一インターフェース
        
        Args:
            dialog_type: ダイアログタイプ（information, error, success）
            title: タイトル
            message: メッセージ
            **kwargs: 追加パラメータ
            
        Returns:
            FacilityOperationResult: 表示結果
        """
        try:
            dialog_methods = {
                'information': self.show_information_dialog,
                'error': self.show_error_dialog,
                'success': self.show_success_dialog
            }
            
            if dialog_type not in dialog_methods:
                return self.handle_error(
                    'invalid_dialog_type',
                    f"未知のダイアログタイプ: {dialog_type}"
                )
            
            dialog_methods[dialog_type](title, message)
            
            return FacilityOperationResult(
                success=True,
                message=f"{dialog_type}ダイアログを表示しました"
            )
            
        except Exception as e:
            return self.handle_error(
                'dialog_display_error',
                f"ダイアログ表示エラー: {str(e)}"
            )
    
    def validate_party_requirements(self) -> FacilityOperationResult:
        """
        パーティ検証パターンの統一
        
        Returns:
            FacilityOperationResult: 検証結果
        """
        if not self.current_party:
            return FacilityOperationResult(
                success=False,
                error_type='no_party',
                message="パーティが設定されていません"
            )
        
        return FacilityOperationResult(
            success=True,
            message="パーティ要件を満たしています"
        )
    
    def cleanup_ui(self) -> None:
        """
        UI要素のクリーンアップパターンの統一
        """
        try:
            # アクティブなUI要素をクリーンアップ
            for element in self._active_ui_elements:
                if hasattr(element, 'cleanup') and callable(element.cleanup):
                    element.cleanup()
            
            self._active_ui_elements.clear()
            
            logger.debug(f"施設 {self.facility_id} のUI要素をクリーンアップしました")
            
        except Exception as e:
            logger.error(f"UIクリーンアップエラー({self.facility_id}): {e}")
    
    def set_party(self, party: Party) -> None:
        """パーティを設定"""
        self.current_party = party
        logger.debug(f"施設 {self.facility_id} にパーティを設定: {party.name if party else None}")
    
    def _on_enter(self):
        """施設入場時の処理（BaseFacility抽象メソッド実装）"""
        # 共通的な入場処理
        logger.info(f"施設 {self.facility_id} への入場処理を開始")
        
        # UI要素をクリア
        self.cleanup_ui()
        
        # 施設固有の入場処理（サブクラスでオーバーライド可能）
        self._on_enter_specific()
    
    def _on_exit(self):
        """施設退場時の処理（BaseFacility抽象メソッド実装）"""
        # 共通的な退場処理
        logger.info(f"施設 {self.facility_id} からの退場処理を開始")
        
        # UI要素をクリーンアップ
        self.cleanup_ui()
        
        # 施設固有の退場処理（サブクラスでオーバーライド可能）
        self._on_exit_specific()
    
    def _on_enter_specific(self):
        """施設固有の入場処理（サブクラスでオーバーライド）"""
        pass
    
    def _on_exit_specific(self):
        """施設固有の退場処理（サブクラスでオーバーライド）"""
        pass