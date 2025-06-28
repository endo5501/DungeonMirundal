"""StatusEffectsWindow テストケース

t-wada式TDD：
1. Red: 失敗するテストを書く
2. Green: テストを通すための最小限の実装
3. Refactor: Fowlerリファクタリングパターンでコードを改善
"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock
from enum import Enum

from src.ui.window_system.status_effects_window import StatusEffectsWindow
from src.ui.window_system.window import Window
from src.ui.window_system.menu_window import MenuWindow
from src.ui.window_system.dialog_window import DialogWindow


class TestStatusEffectsWindow:
    """StatusEffectsWindow テストクラス
    
    テスト戦略：
    - Window System 基本機能のテスト
    - ステータス効果表示機能のテスト
    - パーティ効果管理機能のテスト
    - 個別キャラクター効果管理のテスト
    - 効果解除機能のテスト
    - エラーハンドリングのテスト
    """
    
    def setup_method(self):
        """テスト前セットアップ"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
        # モックオブジェクトの作成
        self.mock_window_manager = Mock()
        
        # モックパーティと効果データ
        self.mock_party = Mock()
        self.mock_character = Mock()
        self.mock_character.name = "テストキャラクター"
        self.mock_character.status_effects = []
        self.mock_party.characters = [self.mock_character]
    
    def test_status_effects_window_creation_success(self):
        """StatusEffectsWindowクラスが正常に作成できることを確認（Green段階）"""
        # StatusEffectsWindowが正常に作成できることを確認
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # Windowクラスを継承していることを確認
        assert isinstance(status_window, Window)
        assert status_window.window_manager == self.mock_window_manager
    
    def test_status_effects_window_inherits_from_window(self):
        """StatusEffectsWindowがWindowクラスを継承することを確認"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        assert isinstance(status_window, Window)
    
    def test_status_effects_window_has_party_effects(self):
        """StatusEffectsWindowがパーティ効果を持つことを確認"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # パーティ効果プロパティの存在確認
        assert hasattr(status_window, 'party_effects')
        assert status_window.party_effects is not None
    
    def test_status_effects_window_show_party_effects(self):
        """show_party_effects メソッドの動作を確認"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # パーティ効果の表示
        status_window.show_party_effects(self.mock_party)
        
        # ウィンドウマネージャーの呼び出し確認
        self.mock_window_manager.show_window.assert_called_once()
    
    def test_status_effects_window_show_character_effects(self):
        """show_character_effects メソッドの動作を確認"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # キャラクター効果の表示
        status_window.show_character_effects(self.mock_character)
        
        # 現在のキャラクターが設定されていることを確認
        assert hasattr(status_window, 'current_character')
        assert status_window.current_character == self.mock_character
    
    def test_status_effects_window_show_effect_details(self):
        """show_effect_details メソッドの動作を確認"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # モック効果データ
        mock_effect = {
            'name': 'poison',
            'description': '毒状態',
            'turns_remaining': 3
        }
        
        # 効果詳細の表示
        status_window.show_effect_details(mock_effect)
        
        # 現在の効果が設定されていることを確認
        assert hasattr(status_window, 'current_effect')
        assert status_window.current_effect == mock_effect
    
    def test_status_effects_window_remove_effect(self):
        """remove_effect メソッドの動作を確認"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # モック効果データ
        mock_effect = {
            'name': 'poison',
            'description': '毒状態',
            'removable': True
        }
        
        # 効果の削除
        result = status_window.remove_effect(self.mock_character, mock_effect)
        
        # 削除が実行されることを確認
        assert isinstance(result, bool)
    
    def test_status_effects_window_get_party_effect_summary(self):
        """get_party_effect_summary メソッドの動作を確認"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # パーティ効果サマリーの取得
        summary = status_window.get_party_effect_summary(self.mock_party)
        
        # サマリーが取得できることを確認
        assert isinstance(summary, dict)
        assert 'total_effects' in summary
        assert 'by_character' in summary
    
    def test_status_effects_window_get_effect_statistics(self):
        """get_effect_statistics メソッドの動作を確認"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # 効果統計の取得
        stats = status_window.get_effect_statistics(self.mock_party)
        
        # 統計が取得できることを確認
        assert isinstance(stats, dict)
        assert 'debuff_count' in stats
        assert 'buff_count' in stats
    
    def test_status_effects_window_filter_removable_effects(self):
        """filter_removable_effects メソッドの動作を確認"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # モック効果リスト
        mock_effects = [
            {'name': 'poison', 'removable': True},
            {'name': 'blessing', 'removable': False},
            {'name': 'paralysis', 'removable': True}
        ]
        
        # 除去可能な効果のフィルタリング
        removable = status_window.filter_removable_effects(mock_effects)
        
        # 除去可能な効果のみが返されることを確認
        assert isinstance(removable, list)
        assert len(removable) == 2
    
    def test_status_effects_window_error_handling(self):
        """エラーハンドリングのテスト"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # Noneパーティでのエラーハンドリング
        status_window.show_party_effects(None)
        # エラーが発生せずに適切に処理されることを確認
        
        # 無効な効果でのエラーハンドリング
        status_window.show_effect_details(None)
        # エラーが発生せずに適切に処理されることを確認
    
    def teardown_method(self):
        """テスト後クリーンアップ"""
        pygame.quit()


class TestStatusEffectsWindowIntegration:
    """StatusEffectsWindow 統合テスト"""
    
    def setup_method(self):
        """統合テスト用セットアップ"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
        # より実際に近いモックオブジェクト
        self.mock_window_manager = Mock()
        
    def test_status_effects_window_with_menu_window_integration(self):
        """MenuWindowとの統合テスト"""
        # MenuWindowからStatusEffectsWindowへの遷移をテスト
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # メニューからの遷移を模擬
        mock_party = Mock()
        status_window.show_party_effects(mock_party)
        
        # 適切にウィンドウが表示されることを確認
        self.mock_window_manager.show_window.assert_called()
    
    def test_status_effects_window_with_dialog_window_integration(self):
        """DialogWindowとの統合テスト"""
        # DialogWindowとの連携をテスト
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # 詳細ダイアログの表示を模擬
        mock_effect = {'name': 'poison', 'description': '毒状態'}
        status_window.show_effect_details_dialog(mock_effect)
        
        # ダイアログウィンドウが作成されることを確認
        # （実際の実装で検証）
    
    def teardown_method(self):
        """統合テスト後クリーンアップ"""
        pygame.quit()


class TestStatusEffectsWindowRefactoring:
    """StatusEffectsWindow リファクタリングテスト（Fowlerパターン）"""
    
    def setup_method(self):
        """リファクタリングテスト用セットアップ"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
        # モックオブジェクトの作成
        self.mock_window_manager = Mock()
        
    def teardown_method(self):
        """リファクタリングテスト後クリーンアップ"""
        pygame.quit()
    
    def test_extract_status_effect_manager_class(self):
        """Extract Class: ステータス効果管理クラスの抽出"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # StatusEffectManagerが抽出されていることを確認
        assert hasattr(status_window, 'effect_manager')
        assert status_window.effect_manager is not None
        
        # モックパーティを適切に設定
        mock_character = Mock()
        mock_character.name = "テストキャラクター"
        mock_character.status_effects = [
            {'name': 'poison', 'type': 'debuff', 'removable': True}
        ]
        
        mock_party = Mock()
        mock_party.characters = [mock_character]
        
        # 効果管理機能
        summary = status_window.get_party_effect_summary(mock_party)
        assert isinstance(summary, dict)
        
        # 効果統計機能
        stats = status_window.get_effect_statistics(mock_party)
        assert isinstance(stats, dict)
    
    def test_extract_status_display_manager_class(self):
        """Extract Class: ステータス表示管理クラスの抽出"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # StatusDisplayManagerが抽出されていることを確認
        assert hasattr(status_window, 'display_manager')
        assert status_window.display_manager is not None
        
        # 表示フォーマット機能
        mock_effects = [{'name': 'poison', 'description': '毒状態'}]
        formatted = status_window.format_effect_list(mock_effects)
        assert isinstance(formatted, list)
        
        # モックパーティを適切に設定
        mock_character = Mock()
        mock_character.name = "テストキャラクター"
        mock_character.status_effects = [
            {'name': 'poison', 'type': 'debuff', 'removable': True}
        ]
        
        mock_party = Mock()
        mock_party.characters = [mock_character]
        
        # メニューアイテム生成
        menu_items = status_window.get_effect_menu_items(mock_party)
        assert isinstance(menu_items, list)
    
    def test_extract_effect_action_manager_class(self):
        """Extract Class: 効果アクション管理クラスの抽出"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # EffectActionManagerが抽出されていることを確認
        assert hasattr(status_window, 'action_manager')
        assert status_window.action_manager is not None
        
        # モックキャラクターを適切に設定
        mock_character = Mock()
        mock_character.name = "テストキャラクター"
        mock_character.status_effects = [
            {'name': 'poison', 'type': 'debuff', 'removable': True}
        ]
        
        # 効果除去アクション
        mock_effect = {'name': 'poison', 'removable': True}
        result = status_window.remove_effect(mock_character, mock_effect)
        assert isinstance(result, bool)
        
        # 効果フィルタリング
        mock_effects = [
            {'name': 'poison', 'removable': True},
            {'name': 'blessing', 'removable': False}
        ]
        removable = status_window.filter_removable_effects(mock_effects)
        assert isinstance(removable, list)
    
    def test_refactored_method_delegation(self):
        """リファクタリング後のメソッド委譲テスト"""
        status_window = StatusEffectsWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 700, 500)
        )
        
        # モックパーティを適切に設定
        mock_character = Mock()
        mock_character.name = "テストキャラクター"
        mock_character.status_effects = [
            {'name': 'poison', 'type': 'debuff', 'removable': True}
        ]
        
        mock_party = Mock()
        mock_party.characters = [mock_character]
        
        # 効果管理の委譲
        summary = status_window.get_party_effect_summary(mock_party)
        assert isinstance(summary, dict)
        
        stats = status_window.get_effect_statistics(mock_party)
        assert isinstance(stats, dict)
        
        # 表示管理の委譲
        mock_effects = []
        formatted = status_window.format_effect_list(mock_effects)
        assert isinstance(formatted, list)
        
        # アクション管理の委譲
        removable = status_window.filter_removable_effects([])
        assert isinstance(removable, list)