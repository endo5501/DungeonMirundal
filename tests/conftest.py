"""pytest共通設定とフィクスチャ"""

import pytest
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.debug.game_debug_client import GameDebugClient
from src.debug.debug_helper import DebugSession


@pytest.fixture(scope="session")
def game_debug_session():
    """
    ゲームデバッグセッション（セッション全体で1回のみ起動）
    
    integrationテストで使用。ゲームを自動起動し、
    終了時に自動的にクリーンアップする。
    """
    with DebugSession(auto_start=True) as session:
        yield session


@pytest.fixture
def game_api_client(game_debug_session):
    """
    ゲームAPIクライアント
    
    各テストで使用するAPIクライアント。
    game_debug_sessionに依存するため、ゲームが起動している状態で使用可能。
    """
    return game_debug_session.client


@pytest.fixture
def debug_helper(game_api_client):
    """
    デバッグヘルパー
    
    高レベルなデバッグ機能を提供。
    """
    from src.debug.debug_helper import DebugHelper
    return DebugHelper(game_api_client)


# pytest marks の定義
def pytest_configure(config):
    """pytest設定の初期化"""
    config.addinivalue_line("markers", "integration: 統合テスト（ゲーム起動が必要）")
    config.addinivalue_line("markers", "slow: 実行時間が長いテスト")
    config.addinivalue_line("markers", "manual: 手動で確認が必要なテスト") 
    config.addinivalue_line("markers", "unit: 単体テスト（依存関係なし）")
    config.addinivalue_line("markers", "ui: UIコンポーネントのテスト")
    config.addinivalue_line("markers", "facility: 施設システムのテスト")


# 既存のフィクスチャも保持  
@pytest.fixture
def api_base_url():
    """デバッグAPIのベースURL（後方互換性）"""
    return "http://localhost:8765"


# モックフィクスチャ
@pytest.fixture
def mock_character():
    """テスト用キャラクターのモック"""
    from unittest.mock import Mock
    char = Mock()
    char.name = "テストキャラクター"
    char.race = "human"
    char.character_class = "fighter" 
    char.level = 1
    char.hp = 50
    char.max_hp = 50
    return char


@pytest.fixture  
def mock_party():
    """テスト用パーティのモック"""
    from unittest.mock import Mock
    party = Mock()
    party.name = "テストパーティ"
    party.gold = 1000
    party.members = []
    return party


@pytest.fixture
def temp_config_file(tmp_path):
    """一時的な設定ファイル"""
    config_file = tmp_path / "test_config.yaml"
    config_data = {
        'character_races': {
            'human': {'name': '人間', 'stat_modifiers': {}},
            'elf': {'name': 'エルフ', 'stat_modifiers': {'agility': 1.1}}
        },
        'character_classes': {
            'fighter': {'name': '戦士', 'requirements': {'strength': 11}},
            'mage': {'name': '魔術師', 'requirements': {'intelligence': 11}}
        }
    }
    import yaml
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    return config_file