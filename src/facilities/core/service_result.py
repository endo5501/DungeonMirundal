"""サービス実行結果の統一型"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class ResultType(Enum):
    """結果タイプ"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    CONFIRM = "confirm"  # 確認が必要な結果


@dataclass
class ServiceResult:
    """サービス実行結果
    
    すべてのサービス実行結果を統一的に表現するクラス。
    成功/失敗の状態、メッセージ、付加データを含む。
    """
    
    success: bool
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    result_type: ResultType = ResultType.SUCCESS
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def ok(cls, message: str = "", data: Optional[Dict[str, Any]] = None, **kwargs) -> 'ServiceResult':
        """成功結果を作成
        
        Args:
            message: 成功メッセージ
            data: 結果データ
            **kwargs: 追加のメタデータ
            
        Returns:
            成功結果
        """
        return cls(
            success=True,
            message=message,
            data=data,
            result_type=ResultType.SUCCESS,
            metadata=kwargs
        )
    
    @classmethod
    def error(cls, message: str, errors: Optional[List[str]] = None, **kwargs) -> 'ServiceResult':
        """エラー結果を作成
        
        Args:
            message: エラーメッセージ
            errors: 詳細エラーリスト
            **kwargs: 追加のメタデータ
            
        Returns:
            エラー結果
        """
        return cls(
            success=False,
            message=message,
            result_type=ResultType.ERROR,
            errors=errors or [],
            metadata=kwargs
        )
    
    @classmethod
    def warning(cls, message: str, data: Optional[Dict[str, Any]] = None, 
                warnings: Optional[List[str]] = None, **kwargs) -> 'ServiceResult':
        """警告付き結果を作成
        
        Args:
            message: 警告メッセージ
            data: 結果データ
            warnings: 詳細警告リスト
            **kwargs: 追加のメタデータ
            
        Returns:
            警告付き結果
        """
        return cls(
            success=True,
            message=message,
            data=data,
            result_type=ResultType.WARNING,
            warnings=warnings or [],
            metadata=kwargs
        )
    
    @classmethod
    def info(cls, message: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> 'ServiceResult':
        """情報結果を作成
        
        Args:
            message: 情報メッセージ
            data: 結果データ
            **kwargs: 追加のメタデータ
            
        Returns:
            情報結果
        """
        return cls(
            success=True,
            message=message,
            data=data,
            result_type=ResultType.INFO,
            metadata=kwargs
        )
    
    @classmethod
    def confirm(cls, message: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> 'ServiceResult':
        """確認が必要な結果を作成
        
        Args:
            message: 確認メッセージ
            data: 確認データ
            **kwargs: 追加のメタデータ
            
        Returns:
            確認結果
        """
        return cls(
            success=False,  # 確認が完了するまでは未成功
            message=message,
            data=data,
            result_type=ResultType.CONFIRM,
            metadata=kwargs
        )
    
    def is_success(self) -> bool:
        """成功かどうか"""
        return self.success and self.result_type != ResultType.ERROR
    
    def is_error(self) -> bool:
        """エラーかどうか"""
        return not self.success or self.result_type == ResultType.ERROR
    
    def is_warning(self) -> bool:
        """警告があるかどうか"""
        return self.result_type == ResultType.WARNING or len(self.warnings) > 0
    
    def needs_confirmation(self) -> bool:
        """確認が必要かどうか"""
        return self.result_type == ResultType.CONFIRM
    
    def has_data(self) -> bool:
        """データを持っているかどうか"""
        return self.data is not None and len(self.data) > 0
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """データを取得
        
        Args:
            key: データキー
            default: デフォルト値
            
        Returns:
            データ値
        """
        if self.data is None:
            return default
        return self.data.get(key, default)
    
    def add_error(self, error: str) -> None:
        """エラーを追加
        
        Args:
            error: エラーメッセージ
        """
        self.errors.append(error)
        self.success = False
        if self.result_type == ResultType.SUCCESS:
            self.result_type = ResultType.ERROR
    
    def add_warning(self, warning: str) -> None:
        """警告を追加
        
        Args:
            warning: 警告メッセージ
        """
        self.warnings.append(warning)
        if self.result_type == ResultType.SUCCESS:
            self.result_type = ResultType.WARNING
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換
        
        Returns:
            結果の辞書表現
        """
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'result_type': self.result_type.value,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        """文字列表現"""
        status = "OK" if self.success else "ERROR"
        return f"ServiceResult({status}: {self.message})"