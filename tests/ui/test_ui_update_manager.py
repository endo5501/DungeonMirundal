"""UIUpdateManager のテスト"""

import unittest
from unittest.mock import Mock, MagicMock
from src.ui.ui_update_manager import UIUpdateManager, get_ui_update_manager
from src.ui.ui_component_base import DummyPartyUIComponent
from src.character.party import Party
from src.character.character import Character


class TestUIUpdateManager(unittest.TestCase):
    """UIUpdateManagerのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.manager = UIUpdateManager()
        
        # テスト用のパーティとキャラクターを作成
        self.test_character = Character("TestHero", "human", "fighter")
        self.test_party = Party()
        self.test_party.name = "TestParty"  # 明示的に名前を設定
        self.test_party.add_character(self.test_character)
    
    def test_component_registration(self):
        """コンポーネント登録のテスト"""
        component = DummyPartyUIComponent()
        
        # 登録
        self.manager.register_component("test_component", component)
        self.assertIn("test_component", self.manager._registered_components)
        
        # 登録解除
        self.manager.unregister_component("test_component")
        self.assertNotIn("test_component", self.manager._registered_components)
    
    def test_party_update_across_ui(self):
        """UI横断的なパーティ更新のテスト"""
        # テスト用コンポーネントを複数登録
        components = {}
        for i in range(3):
            comp = DummyPartyUIComponent()
            name = f"test_component_{i}"
            components[name] = comp
            self.manager.register_component(name, comp)
        
        # パーティ更新を実行
        result = self.manager.update_party_across_ui(self.test_party)
        
        # 結果確認
        self.assertTrue(result)
        
        # 各コンポーネントが正しく更新されているか確認
        for comp in components.values():
            self.assertEqual(comp.last_party_name, "TestParty")
            # update_displayを明示的に呼び出してrefresh_countを確認
            comp.update_display()
            self.assertEqual(comp.refresh_count, 1)
    
    def test_window_manager_integration(self):
        """WindowManager統合のテスト"""
        # MockのWindowManagerを作成
        mock_window_manager = Mock()
        mock_window = Mock()
        mock_character_status_bar = Mock()
        
        # WindowManagerとウィンドウの設定
        mock_window_manager.get_active_window.return_value = mock_window
        mock_window.character_status_bar = mock_character_status_bar
        mock_window.update_party_status = Mock()
        
        # 自動検出を無効化して二重呼び出しを防ぐ
        mock_windows = Mock()
        mock_windows.items.return_value = []
        mock_window_manager.windows = mock_windows
        
        # UIUpdateManagerに設定
        self.manager.set_window_manager(mock_window_manager)
        self.manager._auto_discovery_enabled = False  # 自動検出を無効化
        
        # パーティ更新を実行
        result = self.manager.update_party_across_ui(self.test_party)
        
        # 結果確認
        self.assertTrue(result)
        
        # メソッドが呼び出されているか確認
        mock_character_status_bar.set_party.assert_called_once_with(self.test_party)
        mock_window.update_party_status.assert_called_once()
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        # エラーを発生させるコンポーネント
        error_component = Mock()
        error_component.set_party.side_effect = Exception("Test error")
        
        # 正常なコンポーネント
        normal_component = DummyPartyUIComponent()
        
        # 両方を登録
        self.manager.register_component("error_component", error_component)
        self.manager.register_component("normal_component", normal_component)
        
        # パーティ更新を実行（エラーがあっても処理は継続される）
        result = self.manager.update_party_across_ui(self.test_party)
        
        # エラーがあっても一部成功すればFalseが返される
        self.assertFalse(result)
        
        # 正常なコンポーネントは更新されている
        self.assertEqual(normal_component.last_party_name, "TestParty")
    
    def test_auto_discovery(self):
        """自動検出機能のテスト"""
        # MockのWindowManagerとウィンドウを作成
        mock_window_manager = Mock()
        mock_window = Mock()
        
        # UI要素を持つウィンドウを設定
        mock_character_status_bar = Mock()
        mock_character_status_bar.set_party = Mock()
        mock_window.character_status_bar = mock_character_status_bar
        
        mock_magic_ui = Mock()
        mock_magic_ui.set_party = Mock()
        mock_window.magic_ui = mock_magic_ui
        
        # WindowManagerの設定
        mock_window_manager.get_active_window.return_value = mock_window
        # Mock用のitemsメソッドを設定
        mock_windows = Mock()
        mock_windows.items.return_value = [("main", mock_window)]
        mock_window_manager.windows = mock_windows
        
        self.manager.set_window_manager(mock_window_manager)
        
        # 自動検出を実行
        discovered_count = self.manager.auto_discover_components()
        
        # 結果確認
        self.assertGreater(discovered_count, 0)
        self.assertGreater(len(self.manager._registered_components), 0)
    
    def test_singleton_instance(self):
        """シングルトンインスタンスのテスト"""
        instance1 = get_ui_update_manager()
        instance2 = get_ui_update_manager()
        
        # 同じインスタンスが返されることを確認
        self.assertIs(instance1, instance2)
    
    def test_ui_updateable_interface(self):
        """UIUpdateableインターフェースのテスト"""
        component = DummyPartyUIComponent()
        
        # 初期状態
        self.assertIsNone(component.party)
        self.assertEqual(component.refresh_count, 0)
        
        # パーティ設定
        component.set_party(self.test_party)
        self.assertEqual(component.party, self.test_party)
        
        # 更新実行
        component.update_display()
        self.assertEqual(component.refresh_count, 1)
        
        # 統計情報確認
        stats = component.get_stats()
        self.assertEqual(stats['last_party_name'], "TestParty")
        self.assertEqual(stats['refresh_count'], 1)
        self.assertTrue(stats['has_party'])


if __name__ == '__main__':
    unittest.main()