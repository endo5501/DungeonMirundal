"""
ServiceResultクラスのテスト

統一結果型であるServiceResultクラスの全機能をテストする
"""

import pytest
from src.facilities.core.service_result import ServiceResult, ResultType


class TestServiceResult:
    """ServiceResultクラスのテスト"""
    
    def test_ok_result_creation(self):
        """成功結果の作成テスト"""
        result = ServiceResult.ok("成功しました", {"data": "test"})
        
        assert result.success is True
        assert result.message == "成功しました"
        assert result.data == {"data": "test"}
        assert result.result_type == ResultType.SUCCESS
        assert result.is_success() is True
        assert result.is_error() is False
        assert result.is_warning() is False
        assert result.needs_confirmation() is False
    
    def test_error_result_creation(self):
        """エラー結果の作成テスト"""
        errors = ["エラー1", "エラー2"]
        result = ServiceResult.error("エラーが発生しました", errors)
        
        assert result.success is False
        assert result.message == "エラーが発生しました"
        assert result.result_type == ResultType.ERROR
        assert result.errors == errors
        assert result.is_success() is False
        assert result.is_error() is True
        assert result.is_warning() is False
        assert result.needs_confirmation() is False
    
    def test_warning_result_creation(self):
        """警告結果の作成テスト"""
        warnings = ["警告1", "警告2"]
        result = ServiceResult.warning(
            "警告があります", 
            {"data": "warning_data"}, 
            warnings
        )
        
        assert result.success is True
        assert result.message == "警告があります"
        assert result.data == {"data": "warning_data"}
        assert result.result_type == ResultType.WARNING
        assert result.warnings == warnings
        assert result.is_success() is True
        assert result.is_error() is False
        assert result.is_warning() is True
        assert result.needs_confirmation() is False
    
    def test_info_result_creation(self):
        """情報結果の作成テスト"""
        result = ServiceResult.info("情報です", {"info": "data"})
        
        assert result.success is True
        assert result.message == "情報です"
        assert result.data == {"info": "data"}
        assert result.result_type == ResultType.INFO
        assert result.is_success() is True
        assert result.is_error() is False
        assert result.is_warning() is False
        assert result.needs_confirmation() is False
    
    def test_confirm_result_creation(self):
        """確認結果の作成テスト"""
        result = ServiceResult.confirm("確認してください", {"confirm": "data"})
        
        assert result.success is False  # 確認完了まで未成功
        assert result.message == "確認してください"
        assert result.data == {"confirm": "data"}
        assert result.result_type == ResultType.CONFIRM
        assert result.is_success() is False
        # is_error()の実装では success=False の場合 True を返す
        assert result.is_error() is True
        assert result.is_warning() is False
        assert result.needs_confirmation() is True
    
    def test_has_data(self):
        """データ保有チェックテスト"""
        result_with_data = ServiceResult.ok("テスト", {"key": "value"})
        result_without_data = ServiceResult.ok("テスト")
        result_empty_data = ServiceResult.ok("テスト", {})
        
        assert result_with_data.has_data() is True
        assert result_without_data.has_data() is False
        assert result_empty_data.has_data() is False
    
    def test_get_data(self):
        """データ取得テスト"""
        data = {"key1": "value1", "key2": "value2"}
        result = ServiceResult.ok("テスト", data)
        
        assert result.get_data("key1") == "value1"
        assert result.get_data("key2") == "value2"
        assert result.get_data("nonexistent") is None
        assert result.get_data("nonexistent", "default") == "default"
        
        # データがない場合
        result_no_data = ServiceResult.ok("テスト")
        assert result_no_data.get_data("key") is None
        assert result_no_data.get_data("key", "default") == "default"
    
    def test_add_error(self):
        """エラー追加テスト"""
        result = ServiceResult.ok("成功")
        
        # エラー追加
        result.add_error("エラー1")
        assert result.errors == ["エラー1"]
        assert result.success is False
        assert result.result_type == ResultType.ERROR
        
        # 複数エラー追加
        result.add_error("エラー2")
        assert result.errors == ["エラー1", "エラー2"]
    
    def test_add_warning(self):
        """警告追加テスト"""
        result = ServiceResult.ok("成功")
        
        # 警告追加
        result.add_warning("警告1")
        assert result.warnings == ["警告1"]
        assert result.success is True  # successは変わらない
        assert result.result_type == ResultType.WARNING
        
        # 複数警告追加
        result.add_warning("警告2")
        assert result.warnings == ["警告1", "警告2"]
    
    def test_to_dict(self):
        """辞書変換テスト"""
        result = ServiceResult.ok(
            "成功しました", 
            {"data": "test"}, 
            meta="value"
        )
        result.add_warning("警告")
        
        expected = {
            'success': True,
            'message': "成功しました",
            'data': {"data": "test"},
            'result_type': 'warning',  # 警告追加により変更される
            'errors': [],
            'warnings': ["警告"],
            'metadata': {"meta": "value"}
        }
        
        assert result.to_dict() == expected
    
    def test_str_representation(self):
        """文字列表現テスト"""
        success_result = ServiceResult.ok("成功")
        error_result = ServiceResult.error("失敗")
        
        assert str(success_result) == "ServiceResult(OK: 成功)"
        assert str(error_result) == "ServiceResult(ERROR: 失敗)"
    
    def test_metadata_handling(self):
        """メタデータ処理テスト"""
        result = ServiceResult.ok(
            "成功", 
            key1="value1", 
            key2="value2"
        )
        
        assert result.metadata == {"key1": "value1", "key2": "value2"}
        
        # メタデータ付きエラー
        error_result = ServiceResult.error(
            "エラー", 
            error_code=500
        )
        
        assert error_result.metadata == {"error_code": 500}


class TestResultType:
    """ResultType enumのテスト"""
    
    def test_enum_values(self):
        """Enum値のテスト"""
        assert ResultType.SUCCESS.value == "success"
        assert ResultType.ERROR.value == "error"
        assert ResultType.WARNING.value == "warning"
        assert ResultType.INFO.value == "info"
        assert ResultType.CONFIRM.value == "confirm"
    
    def test_enum_membership(self):
        """Enum要素の確認"""
        assert ResultType.SUCCESS in ResultType
        assert ResultType.ERROR in ResultType
        assert ResultType.WARNING in ResultType
        assert ResultType.INFO in ResultType
        assert ResultType.CONFIRM in ResultType