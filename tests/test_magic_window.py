"""MagicWindow テストケース

t-wada式TDD：
1. Red: 失敗するテストを書く
2. Green: テストを通すための最小限の実装
3. Refactor: Fowlerリファクタリングパターンでコードを改善
"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock

from src.ui.window_system.magic_window import MagicWindow
from src.ui.window_system.window import Window
from src.ui.window_system.menu_window import MenuWindow
from src.ui.window_system.dialog_window import DialogWindow
from src.character.party import Party
from src.character.character import Character
from src.magic.spells import SpellBook


class TestMagicWindow:
    """MagicWindow テストクラス
    
    テスト戦略：
    - Window System 基本機能のテスト
    - 魔法システム特有の機能のテスト
    - パーティと魔法書の管理機能のテスト
    - エラーハンドリングのテスト
    """
    
    def setup_method(self):
        """テスト前セットアップ"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
        # モックオブジェクトの作成
        self.mock_window_manager = Mock()
        self.mock_party = Mock(spec=Party)
        self.mock_character = Mock(spec=Character)
        self.mock_spellbook = Mock(spec=SpellBook)
        
        # キャラクターのモック設定
        self.mock_character.name = "テストキャラクター"
        self.mock_character.get_spellbook.return_value = self.mock_spellbook
        self.mock_party.get_all_characters.return_value = [self.mock_character]
        
        # 魔法書のモック設定
        self.mock_spellbook.get_spell_summary.return_value = {
            'learned_count': 5,
            'equipped_slots': 3,
            'total_slots': 6,
            'available_uses': 2,
            'slots_by_level': {
                1: {'equipped': 2, 'total': 3, 'available': 1},
                2: {'equipped': 1, 'total': 3, 'available': 1}
            }
        }
    
    def test_magic_window_creation_success(self):
        """MagicWindowクラスが正常に作成できることを確認（Green段階）"""
        # MagicWindowが正常に作成できることを確認
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        
        # Windowクラスを継承していることを確認
        assert isinstance(magic_window, Window)
        assert magic_window.window_manager == self.mock_window_manager
    
    def test_magic_window_inherits_from_window(self):
        """MagicWindowがWindowクラスを継承することを確認"""
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        assert isinstance(magic_window, Window)
    
    def test_magic_window_has_party_property(self):
        """MagicWindowがpartyプロパティを持つことを確認"""
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        
        # パーティプロパティの存在確認
        assert hasattr(magic_window, 'party')
        assert magic_window.party is None
    
    def test_magic_window_set_party_method(self):
        """set_party メソッドの動作を確認"""
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        
        # パーティ設定
        magic_window.set_party(self.mock_party)
        assert magic_window.party == self.mock_party
    
    def test_magic_window_show_party_magic_menu(self):
        """show_party_magic_menu メソッドの動作を確認"""
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        
        # パーティ魔法メニューの表示
        magic_window.show_party_magic_menu(self.mock_party)
        
        # パーティが設定されていることを確認
        assert magic_window.party == self.mock_party
        
        # ウィンドウマネージャーの呼び出し確認
        self.mock_window_manager.show_window.assert_called_once()
    
    def test_magic_window_show_character_magic(self):
        """show_character_magic メソッドの動作を確認"""
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        
        # キャラクター魔法表示
        magic_window.show_character_magic(self.mock_character)
        
        # キャラクターが設定されていることを確認
        assert hasattr(magic_window, 'current_character')
        assert magic_window.current_character == self.mock_character
    
    def test_magic_window_spell_slot_management(self):
        """魔法スロット管理機能のテスト"""
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        
        # 魔法スロット表示
        magic_window.show_spell_slots(self.mock_character)
        
        # 魔法書の取得が呼ばれることを確認
        self.mock_character.get_spellbook.assert_called_once()
    
    def test_magic_window_error_handling(self):
        """エラーハンドリングのテスト"""
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        
        # Noneパーティでのエラーハンドリング
        magic_window.show_party_magic_menu(None)
        # エラーが発生せずに適切に処理されることを確認
        
        # 無効なキャラクターでのエラーハンドリング
        magic_window.show_character_magic(None)
        # エラーが発生せずに適切に処理されることを確認
    
    def teardown_method(self):
        """テスト後クリーンアップ"""
        pygame.quit()


class TestMagicWindowIntegration:
    """MagicWindow 統合テスト"""
    
    def setup_method(self):
        """統合テスト用セットアップ"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
        # より実際に近いモックオブジェクト
        self.mock_window_manager = Mock()
        self.mock_party = Mock(spec=Party)
        
    def test_magic_window_with_menu_window_integration(self):
        """MenuWindowとの統合テスト"""
        pytest.skip("MagicWindow未実装のためスキップ")
        
        # MenuWindowからMagicWindowへの遷移をテスト
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        
        # メニューからの遷移を模擬
        magic_window.show_party_magic_menu(self.mock_party)
        
        # 適切にウィンドウが表示されることを確認
        self.mock_window_manager.show_window.assert_called()
    
    def test_magic_window_with_dialog_window_integration(self):
        """DialogWindowとの統合テスト"""
        pytest.skip("MagicWindow未実装のためスキップ")
        
        # DialogWindowとの連携をテスト
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        
        # 確認ダイアログの表示を模擬
        magic_window.show_confirmation_dialog("魔法を使用しますか？")
        
        # ダイアログウィンドウが作成されることを確認
        # （実際の実装で検証）
    
    def teardown_method(self):
        """統合テスト後クリーンアップ"""
        pygame.quit()


class TestMagicWindowRefactoring:
    """MagicWindow リファクタリングテスト（Fowlerパターン）"""
    
    def setup_method(self):
        """リファクタリングテスト用セットアップ"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
        # モックオブジェクトの作成
        self.mock_window_manager = Mock()
        self.mock_party = Mock(spec=Party)
        self.mock_character = Mock(spec=Character)
        self.mock_spellbook = Mock(spec=SpellBook)
        
        # キャラクターのモック設定
        self.mock_character.name = "テストキャラクター"
        self.mock_character.get_spellbook.return_value = self.mock_spellbook
        self.mock_party.get_all_characters.return_value = [self.mock_character]
        
        # 魔法書のモック設定
        self.mock_spellbook.get_spell_summary.return_value = {
            'learned_count': 5,
            'equipped_slots': 3,
            'total_slots': 6,
            'available_uses': 2,
            'slots_by_level': {
                1: {'equipped': 2, 'total': 3, 'available': 1},
                2: {'equipped': 1, 'total': 3, 'available': 1}
            }
        }
    
    def teardown_method(self):
        """リファクタリングテスト後クリーンアップ"""
        pygame.quit()
    
    def test_extract_spell_display_class(self):
        """Extract Class: 魔法表示クラスの抽出"""
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        
        # MagicDisplayManagerが抽出されていることを確認
        assert hasattr(magic_window, 'display_manager')
        assert magic_window.display_manager is not None
        
        # パーティサマリー取得機能
        magic_window.set_party(self.mock_party)
        summary = magic_window.get_party_magic_summary()
        assert isinstance(summary, list)
    
    def test_extract_slot_management_class(self):
        """Extract Class: スロット管理クラスの抽出"""
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        
        # SpellSlotManagerが抽出されていることを確認
        assert hasattr(magic_window, 'slot_manager')
        assert magic_window.slot_manager is not None
        
        # スロット操作機能
        from src.ui.window_system.spell_slot_manager import SlotOperationResult
        result = magic_window.equip_spell_to_slot(self.mock_character, "spell_1", 1, 0)
        assert isinstance(result, SlotOperationResult)
        assert result.success is True
    
    def test_refactored_method_delegation(self):
        """リファクタリング後のメソッド委譲テスト"""
        magic_window = MagicWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 400)
        )
        
        # パーティ統計取得（MagicDisplayManagerに委譲）
        magic_window.set_party(self.mock_party)
        stats = magic_window.get_party_magic_statistics()
        assert isinstance(stats, dict)
        assert 'total_learned' in stats
        
        # キャラクタースロット取得（MagicDisplayManagerに委譲）
        slots = magic_window.get_character_spell_slots(self.mock_character)
        assert isinstance(slots, dict)
        
        # スロット操作（SpellSlotManagerに委譲）
        result = magic_window.unequip_spell_from_slot(self.mock_character, 1, 0)
        assert result.success is True