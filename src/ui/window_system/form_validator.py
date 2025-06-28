"""
FormValidator クラス

フォーム検証の専門クラス
"""

from typing import Dict, Any, List
from .form_types import FormField, FormFieldType, FormValidationResult


class FormValidator:
    """
    フォーム検証クラス
    
    各種フィールドの検証ロジックを担当
    """
    
    def __init__(self):
        """FormValidatorを初期化"""
        pass
    
    def validate_fields(self, fields: List[FormField], form_data: Dict[str, Any]) -> FormValidationResult:
        """
        全フィールドを検証
        
        Args:
            fields: 検証対象のフィールドリスト
            form_data: フォームデータ
            
        Returns:
            FormValidationResult: 検証結果
        """
        errors = {}
        
        for field in fields:
            field_value = form_data.get(field.field_id)
            field_errors = self._validate_single_field(field, field_value)
            
            if field_errors:
                errors[field.field_id] = field_errors
        
        return FormValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    def _validate_single_field(self, field: FormField, value: Any) -> str:
        """
        単一フィールドを検証
        
        Args:
            field: 検証対象フィールド
            value: フィールドの値
            
        Returns:
            str: エラーメッセージ（エラーがない場合は空文字）
        """
        # 必須フィールドチェック
        if field.required and (not value or value == ''):
            return f"{field.label} is required"
        
        # 値が空の場合は以降の検証をスキップ
        if not value or value == '':
            return ''
        
        # タイプ別検証
        if field.field_type == FormFieldType.NUMBER:
            return self._validate_number_field(field, value)
        elif field.field_type == FormFieldType.TEXT:
            return self._validate_text_field(field, value)
        
        return ''
    
    def _validate_number_field(self, field: FormField, value: Any) -> str:
        """数値フィールドを検証"""
        try:
            num_value = float(value)
            
            if field.validation_rules:
                if 'min' in field.validation_rules and num_value < field.validation_rules['min']:
                    return f"{field.label} is out of range"
                elif 'max' in field.validation_rules and num_value > field.validation_rules['max']:
                    return f"{field.label} is out of range"
                    
            return ''
        except ValueError:
            return f"{field.label} must be a number"
    
    def _validate_text_field(self, field: FormField, value: Any) -> str:
        """テキストフィールドを検証"""
        if field.validation_rules and 'pattern' in field.validation_rules:
            import re
            pattern = field.validation_rules['pattern']
            if not re.match(pattern, str(value)):
                return f"{field.label} format is invalid"
        
        return ''