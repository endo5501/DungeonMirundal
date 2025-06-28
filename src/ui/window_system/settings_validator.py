"""
SettingsValidator クラス

設定値検証の専門クラス
"""

from typing import Dict, Any, List, Optional
from .settings_types import SettingsField, SettingsFieldType, SettingsValidationResult


class SettingsValidator:
    """
    設定検証クラス
    
    設定値の検証処理を担当
    """
    
    def __init__(self):
        """SettingsValidatorを初期化"""
        pass
    
    def validate_field_value(self, field: SettingsField, value: Any) -> bool:
        """
        フィールド値を検証
        
        Args:
            field: 検証対象フィールド
            value: 検証する値
            
        Returns:
            bool: 検証成功の場合True
        """
        # 基本的な型チェック
        if not self._validate_field_type(field, value):
            return False
        
        # 範囲チェック
        if not self._validate_field_range(field, value):
            return False
        
        # カスタム検証
        if field.validation_func:
            return field.validation_func(value)
        
        return True
    
    def _validate_field_type(self, field: SettingsField, value: Any) -> bool:
        """フィールドタイプ検証"""
        if field.field_type == SettingsFieldType.SLIDER:
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        elif field.field_type == SettingsFieldType.DROPDOWN:
            if field.options and value not in field.options:
                return False
        elif field.field_type == SettingsFieldType.CHECKBOX:
            if not isinstance(value, bool):
                return False
        elif field.field_type == SettingsFieldType.TEXT_INPUT:
            # テキスト入力は基本的に何でも受け入れる
            pass
        
        return True
    
    def _validate_field_range(self, field: SettingsField, value: Any) -> bool:
        """フィールド範囲検証"""
        if field.field_type == SettingsFieldType.SLIDER:
            try:
                numeric_value = float(value)
                
                if field.min_value is not None and numeric_value < field.min_value:
                    return False
                if field.max_value is not None and numeric_value > field.max_value:
                    return False
            except (ValueError, TypeError):
                return False
        
        return True
    
    def validate_all_fields(self, fields: List[SettingsField], 
                          settings_data: Dict[str, Any]) -> SettingsValidationResult:
        """
        全フィールドを検証
        
        Args:
            fields: 検証対象フィールドリスト
            settings_data: 設定データ
            
        Returns:
            SettingsValidationResult: 検証結果
        """
        errors = {}
        warnings = {}
        
        for field in fields:
            field_value = settings_data.get(field.field_id, field.default_value)
            
            if not self.validate_field_value(field, field_value):
                errors[field.field_id] = f"{field.label} has invalid value"
            
            # 再起動が必要な設定の警告
            if (field.requires_restart and 
                field_value != field.current_value):
                warnings[field.field_id] = f"{field.label} requires restart to take effect"
        
        return SettingsValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def get_validation_error_message(self, field: SettingsField, value: Any) -> str:
        """
        検証エラーメッセージを取得
        
        Args:
            field: フィールド
            value: 値
            
        Returns:
            str: エラーメッセージ
        """
        if field.field_type == SettingsFieldType.SLIDER:
            if field.min_value is not None and field.max_value is not None:
                return f"{field.label} must be between {field.min_value} and {field.max_value}"
            elif field.min_value is not None:
                return f"{field.label} must be at least {field.min_value}"
            elif field.max_value is not None:
                return f"{field.label} must be at most {field.max_value}"
        elif field.field_type == SettingsFieldType.DROPDOWN:
            if field.options:
                return f"{field.label} must be one of: {', '.join(field.options)}"
        
        return f"{field.label} has invalid value"