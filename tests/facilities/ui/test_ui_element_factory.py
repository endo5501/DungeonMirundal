"""UIElementFactoryのテスト"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import pygame

from src.facilities.ui.ui_element_factory import (
    UIElementFactory, ModernUICreationStrategy, LegacyUICreationStrategy
)


class TestUIElementFactory(unittest.TestCase):
    """UIElementFactoryのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # Mock objects to avoid pygame_gui initialization issues
        self.ui_manager = Mock()
        self.container = Mock()
        
        # UIElementManager（現代的な戦略用）
        self.ui_element_manager = Mock()
        self.ui_element_manager.is_destroyed = False
        
        # UI要素リスト（レガシー戦略用）
        self.ui_elements_list = []
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # Mock objects なのでクリーンアップは不要
        pass
    
    def test_modern_strategy_initialization(self):
        """現代的戦略での初期化テスト"""
        factory = UIElementFactory(
            self.ui_manager, self.container, self.ui_element_manager, self.ui_elements_list
        )
        
        # 現代的戦略が選択されていることを確認
        self.assertIsInstance(factory.strategy, ModernUICreationStrategy)
        self.assertEqual(factory.get_strategy_type(), "ModernUICreationStrategy")
    
    def test_legacy_strategy_initialization(self):
        """レガシー戦略での初期化テスト"""
        # UIElementManagerを無効化
        self.ui_element_manager.is_destroyed = True
        
        factory = UIElementFactory(
            self.ui_manager, self.container, self.ui_element_manager, self.ui_elements_list
        )
        
        # レガシー戦略が選択されていることを確認
        self.assertIsInstance(factory.strategy, LegacyUICreationStrategy)
        self.assertEqual(factory.get_strategy_type(), "LegacyUICreationStrategy")
    
    def test_create_label(self):
        """ラベル作成テスト"""
        factory = UIElementFactory(
            self.ui_manager, self.container, self.ui_element_manager, self.ui_elements_list
        )
        
        # UIElementManagerのcreate_labelメソッドのMockを設定
        mock_label = Mock()
        self.ui_element_manager.create_label.return_value = mock_label
        
        rect = Mock()
        label = factory.create_label("test_label", "テストラベル", rect)
        
        # UIElementManagerのcreate_labelが呼ばれていることを確認
        self.ui_element_manager.create_label.assert_called_once_with(
            "test_label", "テストラベル", rect, self.container
        )
        self.assertEqual(label, mock_label)
    
    def test_create_button_with_shortcut(self):
        """ショートカット付きボタン作成テスト"""
        factory = UIElementFactory(
            self.ui_manager, self.container, self.ui_element_manager, self.ui_elements_list
        )
        
        # UIElementManagerのcreate_buttonメソッドのMockを設定
        mock_button = Mock()
        self.ui_element_manager.create_button.return_value = mock_button
        
        rect = Mock()
        button = factory.create_button("test_button", "テストボタン", rect)
        
        # UIElementManagerのcreate_buttonが呼ばれていることを確認
        self.ui_element_manager.create_button.assert_called_once_with(
            "test_button", "テストボタン", rect, self.container, None, object_id=None
        )
        
        # ショートカットキーが割り当てられていることを確認
        self.assertEqual(mock_button.button_index, 0)
        self.assertEqual(mock_button.shortcut_key, "1")
        self.assertEqual(button, mock_button)
    
    def test_multiple_buttons_shortcut_assignment(self):
        """複数ボタンのショートカット割り当てテスト"""
        factory = UIElementFactory(
            self.ui_manager, self.container, self.ui_element_manager, self.ui_elements_list
        )
        
        # 複数のMockボタンを作成
        mock_buttons = [Mock() for _ in range(3)]
        self.ui_element_manager.create_button.side_effect = mock_buttons
        
        buttons = []
        for i in range(3):
            rect = Mock()
            button = factory.create_button(f"button_{i}", f"ボタン{i+1}", rect)
            buttons.append(button)
        
        # 各ボタンのショートカットキーが順番に割り当てられていることを確認
        for i, button in enumerate(buttons):
            self.assertEqual(button.button_index, i)
            self.assertEqual(button.shortcut_key, str(i + 1))
    
    def test_create_text_box(self):
        """テキストボックス作成テスト"""
        factory = UIElementFactory(
            self.ui_manager, self.container, self.ui_element_manager, self.ui_elements_list
        )
        
        # UIElementManagerのcreate_text_boxメソッドのMockを設定
        mock_text_box = Mock()
        self.ui_element_manager.create_text_box.return_value = mock_text_box
        
        rect = Mock()
        text_box = factory.create_text_box("test_textbox", "初期テキスト", rect)
        
        # UIElementManagerのcreate_text_boxが呼ばれていることを確認
        self.ui_element_manager.create_text_box.assert_called_once_with(
            "test_textbox", "初期テキスト", rect, self.container
        )
        self.assertEqual(text_box, mock_text_box)
    
    def test_create_selection_list(self):
        """選択リスト作成テスト"""
        factory = UIElementFactory(
            self.ui_manager, self.container, self.ui_element_manager, self.ui_elements_list
        )
        
        # UIElementManagerのcreate_selection_listメソッドのMockを設定
        mock_selection_list = Mock()
        self.ui_element_manager.create_selection_list.return_value = mock_selection_list
        
        rect = Mock()
        items = ["アイテム1", "アイテム2", "アイテム3"]
        selection_list = factory.create_selection_list("test_list", rect, items)
        
        # UIElementManagerのcreate_selection_listが呼ばれていることを確認
        self.ui_element_manager.create_selection_list.assert_called_once_with(
            "test_list", rect, items, self.container
        )
        self.assertEqual(selection_list, mock_selection_list)
    
    def test_create_text_entry(self):
        """テキスト入力フィールド作成テスト"""
        factory = UIElementFactory(
            self.ui_manager, self.container, self.ui_element_manager, self.ui_elements_list
        )
        
        # UIElementManagerのcreate_text_entryメソッドのMockを設定
        mock_text_entry = Mock()
        self.ui_element_manager.create_text_entry.return_value = mock_text_entry
        
        rect = Mock()
        text_entry = factory.create_text_entry(
            "test_entry", rect, initial_text="初期値", placeholder_text="プレースホルダー"
        )
        
        # UIElementManagerのcreate_text_entryが呼ばれていることを確認
        self.ui_element_manager.create_text_entry.assert_called_once_with(
            "test_entry", rect, initial_text="初期値", container=self.container, placeholder_text="プレースホルダー"
        )
        self.assertEqual(text_entry, mock_text_entry)
    
    def test_button_counter_reset(self):
        """ボタンカウンターリセットテスト"""
        factory = UIElementFactory(
            self.ui_manager, self.container, self.ui_element_manager, self.ui_elements_list
        )
        
        # 複数のMockボタンを作成
        mock_button1 = Mock()
        mock_button2 = Mock()
        self.ui_element_manager.create_button.side_effect = [mock_button1, mock_button2]
        
        # 最初のボタンを作成
        rect = Mock()
        button1 = factory.create_button("button1", "ボタン1", rect)
        self.assertEqual(button1.shortcut_key, "1")
        
        # カウンターをリセット
        factory.reset_button_counter()
        
        # 次のボタンが再び1から始まることを確認
        button2 = factory.create_button("button2", "ボタン2", rect)
        self.assertEqual(button2.shortcut_key, "1")
    
    @patch('src.facilities.ui.ui_element_factory.pygame_gui.elements.UILabel')
    def test_legacy_fallback(self, mock_label_class):
        """レガシーフォールバックテスト"""
        # UIElementManagerを無効化
        self.ui_element_manager.is_destroyed = True
        
        factory = UIElementFactory(
            self.ui_manager, self.container, self.ui_element_manager, self.ui_elements_list
        )
        
        # レガシー戦略が使用されることを確認
        self.assertIsInstance(factory.strategy, LegacyUICreationStrategy)
        
        # Mockラベルインスタンス
        mock_label_instance = Mock()
        mock_label_class.return_value = mock_label_instance
        
        # UI要素を作成
        rect = Mock()
        label = factory.create_label("legacy_label", "レガシーラベル", rect)
        
        # レガシー戦略でラベルが作成されていることを確認
        mock_label_class.assert_called_once()
        self.assertEqual(label, mock_label_instance)
        self.assertIn(mock_label_instance, self.ui_elements_list)
    
    def test_error_handling(self):
        """エラーハンドリングテスト"""
        factory = UIElementFactory(
            self.ui_manager, self.container, self.ui_element_manager, self.ui_elements_list
        )
        
        # 無効な要素タイプでエラーが発生することを確認
        rect = Mock()
        with self.assertRaises(ValueError):
            factory._create_element("invalid_type", "test", rect, self.container)


if __name__ == '__main__':
    unittest.main()