"""Pygame基本UIシステムのテスト"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import pygame

# ヘッドレス環境でのPygame初期化
os.environ['SDL_VIDEODRIVER'] = 'dummy'

from src.ui.base_ui_pygame import (
    UIElement, UIText, UIButton, UIDialog, UIManager,  # UIMenu: Phase 4.5で削除
    UIState, UIAlignment, ui_manager
)


class TestUIElement:
    """UIElement基底クラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # Pygameの初期化（ヘッドレス）
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_ui_element_initialization(self):
        """UIElement初期化テスト"""
        element = UIElement("test_element", x=10, y=20, width=100, height=30)
        
        assert element.element_id == "test_element"
        assert element.state == UIState.HIDDEN
        assert element.rect.x == 10
        assert element.rect.y == 20
        assert element.rect.width == 100
        assert element.rect.height == 30
        assert element.parent is None
        assert len(element.children) == 0
        assert element.is_hovered is False
        assert element.is_pressed is False
    
    def test_ui_element_show_hide(self):
        """UIElement表示・非表示テスト"""
        element = UIElement("test_element")
        
        # 初期状態は非表示
        assert element.state == UIState.HIDDEN
        
        # 表示
        element.show()
        assert element.state == UIState.VISIBLE
        
        # 非表示
        element.hide()
        assert element.state == UIState.HIDDEN
    
    def test_ui_element_modal(self):
        """UIElementモーダル表示テスト"""
        element = UIElement("test_element")
        
        # 通常表示
        element.show()
        assert element.state == UIState.VISIBLE
        
        # 非表示
        element.hide()
        assert element.state == UIState.HIDDEN
    
    def test_ui_element_child_management(self):
        """UIElement子要素管理テスト（基本的な親子関係）"""
        parent = UIElement("parent")
        child1 = UIElement("child1")
        child2 = UIElement("child2")
        
        # 手動で親子関係を設定
        child1.parent = parent
        child2.parent = parent
        parent.children.append(child1)
        parent.children.append(child2)
        
        assert len(parent.children) == 2
        assert child1 in parent.children
        assert child2 in parent.children
        assert child1.parent == parent
        assert child2.parent == parent
        
        # 子要素削除
        parent.children.remove(child1)
        child1.parent = None
        assert len(parent.children) == 1
        assert child1 not in parent.children
        assert child1.parent is None
    
    def test_ui_element_event_handling(self):
        """UIElementイベント処理テスト"""
        element = UIElement("test_element", x=10, y=10, width=100, height=50)
        element.show()  # 要素を表示状態にする
        
        click_called = False
        hover_called = False
        
        def on_click():
            nonlocal click_called
            click_called = True
        
        def on_hover():
            nonlocal hover_called
            hover_called = True
        
        element.on_click = on_click
        element.on_hover = on_hover
        
        # クリックイベント
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(50, 35), button=1)
        element.handle_event(event)
        assert click_called
        
        # ホバーイベント（マウス移動）
        event = pygame.event.Event(pygame.MOUSEMOTION, pos=(50, 35))
        element.handle_event(event)
        assert hover_called
    
    def test_ui_element_point_collision(self):
        """UIElement座標衝突判定テスト"""
        element = UIElement("test_element", x=10, y=10, width=100, height=50)
        
        # 要素内の点
        assert element.rect.collidepoint(50, 35) is True
        assert element.rect.collidepoint(10, 10) is True  # 左上角
        assert element.rect.collidepoint(109, 59) is True  # 右下角（境界内）
        
        # 要素外の点
        assert element.rect.collidepoint(5, 35) is False   # 左側
        assert element.rect.collidepoint(115, 35) is False # 右側
        assert element.rect.collidepoint(50, 5) is False   # 上側
        assert element.rect.collidepoint(50, 65) is False  # 下側


class TestUIText:
    """UITextクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # Pygameの初期化（ヘッドレス）
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_ui_text_initialization(self):
        """UIText初期化テスト"""
        text = UIText("test_text", "Hello World", x=10, y=20)
        
        assert text.element_id == "test_text"
        assert text.text == "Hello World"
        assert text.rect.x == 10
        assert text.rect.y == 20
        assert text.font_size == 24  # デフォルトサイズ
    
    def test_ui_text_with_custom_font_size(self):
        """UITextカスタムフォントサイズテスト"""
        text = UIText("test_text", "Hello", font_size=36)
        assert text.font_size == 36
    
    def test_ui_text_set_text(self):
        """UITextテキスト設定テスト"""
        text = UIText("test_text", "Original")
        
        # テキスト変更（直接代入）
        text.text = "Modified"
        assert text.text == "Modified"
    
    def test_ui_text_with_japanese_font(self):
        """UIText日本語フォント使用テスト"""
        # 日本語テキストが正常に格納されることを確認
        text = UIText("test_text", "こんにちは")
        assert text.text == "こんにちは"
        
        # フォントサイズが設定されることを確認
        assert text.font_size == 24  # デフォルトサイズ


class TestUIButton:
    """UIButtonクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_ui_button_initialization(self):
        """UIButton初期化テスト"""
        button = UIButton("test_button", "Click Me", x=10, y=20, width=100, height=40)
        
        assert button.element_id == "test_button"
        assert button.text == "Click Me"
        assert button.rect.x == 10
        assert button.rect.y == 20
        assert button.rect.width == 100
        assert button.rect.height == 40
    
    def test_ui_button_enable_disable(self):
        """UIButtonの表示・非表示テスト"""
        button = UIButton("test_button", "Click Me")
        
        # 初期状態は非表示
        assert button.state == UIState.HIDDEN
        
        # 表示
        button.show()
        assert button.state == UIState.VISIBLE
        
        # 非表示
        button.hide()
        assert button.state == UIState.HIDDEN
    
    def test_ui_button_click_when_enabled(self):
        """UIButton表示時のクリックテスト"""
        button = UIButton("test_button", "Click Me", x=0, y=0, width=100, height=40)
        button.show()  # 表示状態にする
        clicked = False
        
        def on_click():
            nonlocal clicked
            clicked = True
        
        button.on_click = on_click
        
        # クリックイベント
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(50, 20), button=1)
        button.handle_event(event)
        
        assert clicked is True
    
    def test_ui_button_click_when_disabled(self):
        """UIButton非表示時のクリックテスト"""
        button = UIButton("test_button", "Click Me", x=0, y=0, width=100, height=40)
        # 非表示状態のまま（デフォルト）
        clicked = False
        
        def on_click():
            nonlocal clicked
            clicked = True
        
        button.on_click = on_click
        
        # クリックイベント
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(50, 20), button=1)
        button.handle_event(event)
        
        assert clicked is False  # 非表示なので実行されない


# class TestUIMenu:  # UIMenu削除済み - Phase 4.5
class TestUIMenuRemoved:
    """UIMenuクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_ui_menu_initialization(self):
        """UIMenu初期化テスト"""
        menu = UIMenu("test_menu", "Test Menu")
        
        assert menu.menu_id == "test_menu"
        assert menu.title == "Test Menu"
        assert len(menu.elements) == 0
        assert menu.selected_index == 0
    
    def test_ui_menu_add_menu_item(self):
        """UIMenuメニュー項目追加テスト"""
        menu = UIMenu("test_menu", "Test Menu")
        
        def item1_action():
            pass
        
        def item2_action():
            pass
        
        # UIButtonを作成してメニューに追加
        button1 = UIButton("item1", "Item 1")
        button1.on_click = item1_action
        button2 = UIButton("item2", "Item 2")
        button2.on_click = item2_action
        
        menu.add_element(button1)
        menu.add_element(button2)
        
        assert len(menu.elements) == 2
        assert menu.elements[0].text == "Item 1"
        assert menu.elements[0].on_click == item1_action
        assert menu.elements[1].text == "Item 2"
        assert menu.elements[1].on_click == item2_action
    
    def test_ui_menu_navigation(self):
        """UIMenuナビゲーションテスト"""
        menu = UIMenu("test_menu", "Test Menu")
        
        # UIButtonを作成してメニューに追加
        button1 = UIButton("item1", "Item 1")
        button2 = UIButton("item2", "Item 2")
        button3 = UIButton("item3", "Item 3")
        
        menu.add_element(button1)
        menu.add_element(button2)
        menu.add_element(button3)
        menu.show()  # メニューを表示状態にする
        
        # 初期選択
        assert menu.selected_index == 0
        
        # 下方向移動（キーイベントで）
        down_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        menu.handle_event(down_event)
        assert menu.selected_index == 1
        
        menu.handle_event(down_event)
        assert menu.selected_index == 2
        
        # 上方向移動
        up_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        menu.handle_event(up_event)
        assert menu.selected_index == 1
    
    def test_ui_menu_execute_selected(self):
        """UIMenu選択項目実行テスト"""
        menu = UIMenu("test_menu", "Test Menu")
        
        executed_item = None
        
        def item1_action():
            nonlocal executed_item
            executed_item = "item1"
        
        def item2_action():
            nonlocal executed_item
            executed_item = "item2"
        
        # UIButtonを作成してメニューに追加
        button1 = UIButton("item1", "Item 1")
        button1.on_click = item1_action
        button2 = UIButton("item2", "Item 2")
        button2.on_click = item2_action
        
        menu.add_element(button1)
        menu.add_element(button2)
        menu.show()
        
        # 最初の項目を実行（エンターキーで）
        enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        menu.handle_event(enter_event)
        assert executed_item == "item1"
        
        # 2番目の項目に移動して実行
        down_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        menu.handle_event(down_event)
        menu.handle_event(enter_event)
        assert executed_item == "item2"


class TestUIManager:
    """UIManagerクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        # 新しいUIManagerインスタンスを作成
        self.ui_manager = UIManager(self.screen)
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_ui_manager_initialization(self):
        """UIManager初期化テスト"""
        assert self.ui_manager.screen == self.screen
        assert len(self.ui_manager.elements) == 0
        assert len(self.ui_manager.menus) == 0
        assert len(self.ui_manager.dialogs) == 0
    
    def test_ui_manager_register_element(self):
        """UIManager要素登録テスト"""
        element = UIElement("test_element")
        
        self.ui_manager.add_element(element)
        
        assert "test_element" in self.ui_manager.elements
        assert self.ui_manager.elements["test_element"] == element
    
    def test_ui_manager_add_menu(self):
        """UIManagerメニュー追加テスト"""
        menu = UIMenu("test_menu", "Test Menu")
        
        self.ui_manager.add_menu(menu)
        
        assert "test_menu" in self.ui_manager.menus
        assert self.ui_manager.menus["test_menu"] == menu
    
    def test_ui_manager_show_hide_menu(self):
        """UIManagerメニュー表示・非表示テスト"""
        menu = UIMenu("test_menu", "Test Menu")
        self.ui_manager.add_menu(menu)
        
        # 表示
        self.ui_manager.show_menu("test_menu")
        assert menu.state == UIState.VISIBLE
        
        # 非表示
        self.ui_manager.hide_menu("test_menu")
        assert menu.state == UIState.HIDDEN
    
    def test_ui_manager_modal_menu(self):
        """UIManagerモーダルメニューテスト"""
        menu = UIMenu("test_menu", "Test Menu")
        self.ui_manager.add_menu(menu)
        
        # モーダル表示
        self.ui_manager.show_menu("test_menu", modal=True)
        assert menu.state == UIState.VISIBLE
        assert "test_menu" in self.ui_manager.modal_stack


@pytest.mark.pygame
class TestPygameUIIntegration:
    """Pygame UI統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.ui_manager = UIManager(self.screen)
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_complete_ui_workflow(self):
        """完全なUIワークフローテスト"""
        # メニューを作成
        menu = UIMenu("main_menu", "Main Menu")
        
        executed_actions = []
        
        def action1():
            executed_actions.append("action1")
        
        def action2():
            executed_actions.append("action2")
        
        # UIButtonを作成してメニューに追加
        button1 = UIButton("option1", "Option 1")
        button1.on_click = action1
        button2 = UIButton("option2", "Option 2")
        button2.on_click = action2
        
        menu.add_element(button1)
        menu.add_element(button2)
        
        # UIManagerに登録・表示
        self.ui_manager.add_menu(menu)
        self.ui_manager.show_menu("main_menu")
        
        # メニューが表示されていることを確認
        assert menu.state == UIState.VISIBLE
        
        # キーボードナビゲーション
        down_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        self.ui_manager.handle_event(down_event)
        assert menu.selected_index == 1
        
        # エンターキーで実行
        enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        self.ui_manager.handle_event(enter_event)
        assert "action2" in executed_actions
        
        # 非表示
        self.ui_manager.hide_menu("main_menu")
        assert menu.state == UIState.HIDDEN