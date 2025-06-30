"""0044 Phase 1: テストコードのUIMenu使用除去テスト"""

import pytest
import os
import glob
from pathlib import Path


class TestUIMenuCleanupInTests:
    """テストコード内のUIMenu使用除去確認テスト"""
    
    def setup_method(self):
        """テストのセットアップ"""
        self.test_dir = Path(__file__).parent.parent  # tests/ディレクトリ
        self.exclude_files = {
            'test_0044_phase1_test_code_cleanup.py',  # このファイル自身
            'test_0044_phase1_base_facility_cleanup.py',  # Phase 1テスト
            # Phase 3で削除予定の核心UIテスト
            'test_settings_menu_return_bug.py',
            'test_comprehensive_menu_navigation.py', 
            'test_settings_menu_navigation.py',
            'test_menu_architecture_integration.py'
        }
    
    def test_no_uimenu_imports_in_test_files(self):
        """テストファイルにUIMenuのインポートがないことを確認"""
        uimenu_imports = []
        
        # すべてのPythonテストファイルを検索
        for test_file in self.test_dir.rglob("test_*.py"):
            if test_file.name in self.exclude_files:
                continue
                
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # UIMenuのインポートをチェック
            if 'from src.ui.base_ui_pygame import UIMenu' in content:
                uimenu_imports.append(str(test_file.relative_to(self.test_dir)))
            elif 'import UIMenu' in content and 'import' not in test_file.name:
                uimenu_imports.append(str(test_file.relative_to(self.test_dir)))
        
        assert len(uimenu_imports) == 0, \
            f"Following test files still import UIMenu: {uimenu_imports}"
    
    def test_no_uimenu_mock_usage(self):
        """テストファイルでUIMenuのモックが使用されていないことを確認"""
        uimenu_mocks = []
        
        # すべてのPythonテストファイルを検索
        for test_file in self.test_dir.rglob("test_*.py"):
            if test_file.name in self.exclude_files:
                continue
                
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # UIMenuのモック使用をチェック
            if 'Mock(spec=UIMenu)' in content or 'MagicMock(spec=UIMenu)' in content:
                uimenu_mocks.append(str(test_file.relative_to(self.test_dir)))
            elif 'mock_uimenu' in content.lower() and 'migration' not in test_file.name:
                uimenu_mocks.append(str(test_file.relative_to(self.test_dir)))
        
        assert len(uimenu_mocks) == 0, \
            f"Following test files still use UIMenu mocks: {uimenu_mocks}"
    
    def test_migration_tests_check_no_uimenu(self):
        """移行テストがUIMenuの不使用を確認していることを検証"""
        migration_tests = list(self.test_dir.rglob("*migration*.py"))
        
        # 移行テストが存在することを確認
        assert len(migration_tests) > 0, "Migration tests should exist"
        
        # 各移行テストがUIMenuの不使用を確認していることを検証
        for test_file in migration_tests:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # WindowSystemへの移行を確認するテストが含まれていることを確認
            if 'window' in test_file.name.lower():
                assert 'WindowManager' in content or 'Window' in content, \
                    f"{test_file.name} should test WindowSystem migration"
    
    def test_no_commented_uimenu_code(self):
        """コメントアウトされたUIMenuコードがないことを確認"""
        commented_uimenu = []
        
        # すべてのPythonテストファイルを検索
        for test_file in self.test_dir.rglob("test_*.py"):
            if test_file.name in self.exclude_files:
                continue
            
            # Phase 1テストファイル自身を除外
            if 'test_0044_phase1' in test_file.name:
                continue
                
            with open(test_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # コメントアウトされたUIMenuコードをチェック
            for i, line in enumerate(lines):
                if '#' in line and 'UIMenu' in line and 'migration' not in test_file.name:
                    # 説明的なコメントは除外
                    if not any(keyword in line for keyword in ['should', 'must', 'not', 'test']):
                        commented_uimenu.append(
                            f"{test_file.relative_to(self.test_dir)}:{i+1}"
                        )
        
        assert len(commented_uimenu) == 0, \
            f"Following locations have commented UIMenu code: {commented_uimenu}"