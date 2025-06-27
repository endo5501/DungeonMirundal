"""
テスト用のモックウィンドウクラス

pygame-guiに依存しないテスト専用のWindow実装
"""

from src.ui.window_system import Window
import pygame


class MockWindow(Window):
    """
    テスト用のモックウィンドウ
    
    pygame-guiに依存せず、テストで必要な基本機能のみを実装
    """
    
    def __init__(self, window_id: str, parent=None, modal=False, **kwargs):
        super().__init__(window_id, parent, modal)
        self.create_called = False
        self.show_called = False
        self.hide_called = False
        self.destroy_called = False
        self.handle_event_calls = []
        self.handle_escape_calls = []
        
        # テスト用の追加属性
        self.test_data = kwargs
    
    def create(self):
        """UI要素を作成（モック）"""
        self.create_called = True
        # 実際のUI作成は行わず、フラグのみ設定
        
    def handle_event(self, event):
        """イベントを処理（モック）"""
        self.handle_event_calls.append(event)
        return False  # デフォルトでは処理しない
    
    def handle_escape(self):
        """ESCキーの処理（モック）"""
        self.handle_escape_calls.append(True)
        return True  # デフォルトでは処理する
    
    def on_show(self):
        """表示時のイベントハンドラー（モック）"""
        self.show_called = True
    
    def on_hide(self):
        """非表示時のイベントハンドラー（モック）"""
        self.hide_called = True
    
    def on_destroy(self):
        """破棄時のイベントハンドラー（モック）"""
        self.destroy_called = True
    
    def cleanup_ui(self):
        """UI要素のクリーンアップ（モック）"""
        # 実際のクリーンアップは不要
        pass
    
    def update(self, time_delta: float):
        """ウィンドウの更新（モック）"""
        # 実際の更新処理は不要
        pass
    
    def draw(self, surface):
        """ウィンドウの描画（モック）"""
        # 実際の描画処理は不要
        pass