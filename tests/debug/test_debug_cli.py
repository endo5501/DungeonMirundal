"""
デバッグCLIのテスト

コマンドライン インターフェースの動作をテストする。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from click.testing import CliRunner
from io import StringIO

from src.debug.debug_cli import debug_cli, ui_dump, ui_find, ui_tree


class TestDebugCLI:
    """デバッグCLIのテストクラス"""
    
    @pytest.fixture
    def runner(self):
        """Click CLIテストランナー"""
        return CliRunner()
    
    @pytest.fixture
    def mock_game_client(self):
        """モックのGameDebugClientを作成"""
        with patch('src.debug.debug_cli.GameDebugClient') as mock_class:
            mock_instance = Mock()
            mock_instance.wait_for_api.return_value = True
            mock_instance.is_api_available.return_value = True
            # get_ui_hierarchyは辞書を返す
            mock_instance.get_ui_hierarchy.return_value = {
                'windows': [
                    {
                        'id': 'main_window',
                        'type': 'MainWindow',
                        'visible': True,
                        'position': {'x': 0, 'y': 0},
                        'size': {'width': 800, 'height': 600}
                    }
                ],
                'ui_elements': [
                    {
                        'object_id': 'test_button',
                        'type': 'UIButton',
                        'visible': True,
                        'position': {'x': 100, 'y': 100},
                        'size': {'width': 100, 'height': 30}
                    }
                ],
                'window_stack': ['main_window']
            }
            mock_class.return_value = mock_instance
            yield mock_instance
    
    
    def test_ui_dump_command_basic(self, runner, mock_game_client):
        """ui-dumpコマンドの基本テスト"""
        # コマンドを実行
        result = runner.invoke(ui_dump)
        
        # 結果を検証
        assert result.exit_code == 0
        assert 'main_window' in result.output
        assert 'test_button' in result.output
        assert 'MainWindow' in result.output
        assert 'UIButton' in result.output
    
    def test_ui_dump_command_with_save(self, runner, mock_game_client, tmp_path):
        """ui-dumpコマンドの保存オプションテスト"""
        # mock_game_clientは既にmock_ui_dataを持っている
        
        # 一時ファイルパス
        save_path = tmp_path / "ui_state.json"
        
        # コマンドを実行
        result = runner.invoke(ui_dump, ['--save', str(save_path)])
        
        # 結果を検証
        assert result.exit_code == 0
        assert save_path.exists()
        assert f"UI hierarchy saved to {save_path}" in result.output
        
        # 保存されたファイルの内容を確認
        with open(save_path, 'r') as f:
            saved_data = json.load(f)
        
        # mock_game_clientで設定されたデータと一致することを確認
        expected_data = mock_game_client.get_ui_hierarchy.return_value
        assert saved_data == expected_data
    
    def test_ui_dump_command_tree_format(self, runner, mock_game_client):
        """ui-dumpコマンドのツリー形式テスト"""
        # コマンドを実行
        result = runner.invoke(ui_dump, ['--format', 'tree'])
        
        # 結果を検証
        assert result.exit_code == 0
        assert "UI Hierarchy Tree:" in result.output
        assert "MainWindow" in result.output
        assert "UIButton" in result.output
    
    def test_ui_dump_command_api_not_available(self, runner, mock_game_client):
        """APIが利用不可の場合のテスト"""
        mock_game_client.wait_for_api.return_value = False
        
        # コマンドを実行
        result = runner.invoke(ui_dump)
        
        # エラーメッセージを検証
        assert result.exit_code == 1
        assert "Game API is not available" in result.output
    
    def test_ui_find_command(self, runner, mock_game_client):
        """ui-findコマンドのテスト"""
        # コマンドを実行（test_buttonを検索）
        result = runner.invoke(ui_find, ['test_button'])
        
        # 結果を検証
        assert result.exit_code == 0
        assert 'test_button' in result.output
        assert 'UIButton' in result.output
        assert 'position' in result.output
        assert '100' in result.output
    
    def test_ui_find_command_not_found(self, runner, mock_game_client):
        """ui-findコマンドで要素が見つからない場合のテスト"""
        # コマンドを実行
        result = runner.invoke(ui_find, ['non_existent'])
        
        # 結果を検証
        assert result.exit_code == 0
        assert "UI element 'non_existent' not found" in result.output
    
    def test_ui_tree_command(self, runner, mock_game_client):
        """ui-treeコマンドのテスト"""
        # コマンドを実行
        result = runner.invoke(ui_tree)
        
        # 結果を検証
        assert result.exit_code == 0
        assert "UI Hierarchy Tree:" in result.output
        assert 'MainWindow' in result.output
        assert 'UIButton' in result.output
    
    def test_ui_dump_with_filter(self, runner, mock_game_client):
        """ui-dumpコマンドのフィルタオプションテスト"""
        # ボタンのみフィルタ
        result = runner.invoke(ui_dump, ['--filter', 'UIButton'])
        
        assert result.exit_code == 0
        assert 'test_button' in result.output
        # フィルタされた結果でwindowsは空になる
        assert '"windows": []' in result.output
    
    def test_ui_dump_verbose_mode(self, runner, mock_game_client):
        """ui-dumpコマンドの詳細モードテスト"""
        # 詳細モードで実行
        result = runner.invoke(ui_dump, ['--verbose'])
        
        assert result.exit_code == 0
        assert 'test_button' in result.output
        assert 'UIButton' in result.output