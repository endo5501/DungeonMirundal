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


# 既存のフィクスチャも保持
@pytest.fixture
def api_base_url():
    """デバッグAPIのベースURL（後方互換性）"""
    return "http://localhost:8765"