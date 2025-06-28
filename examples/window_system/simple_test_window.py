"""
テスト用ウィンドウクラス

Window Systemの基本動作確認用
"""

import pygame
import pygame_gui
from typing import Optional

import sys
import os
# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.ui.window_system.window import Window


class SimpleTestWindow(Window):
    """
    テスト用の簡単なウィンドウ
    
    基本的なUI要素とイベント処理を実装し、
    Window Systemの動作確認に使用する
    """
    
    def __init__(self, window_id: str, title: str = "Test Window", 
                 parent: Optional[Window] = None, modal: bool = False):
        super().__init__(window_id, parent, modal)
        self.title = title
        self.button = None
        self.label = None
        
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            # 画面サイズを取得（デフォルト値を使用）
            screen_width = 1024
            screen_height = 768
            
            # UIManagerを作成
            self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
            
            # ウィンドウのサイズと位置を設定
            window_width = 400
            window_height = 300
            window_x = (screen_width - window_width) // 2
            window_y = (screen_height - window_height) // 2
            
            self.rect = pygame.Rect(window_x, window_y, window_width, window_height)
            
            # パネル（背景）を作成
            self.panel = pygame_gui.elements.UIPanel(
                relative_rect=self.rect,
                manager=self.ui_manager
            )
            
            # ラベルを作成
            label_rect = pygame.Rect(20, 20, window_width - 40, 30)
            self.label = pygame_gui.elements.UILabel(
                relative_rect=label_rect,
                text=self.title,
                manager=self.ui_manager,
                container=self.panel
            )
            
            # ボタンを作成
            button_rect = pygame.Rect(20, 60, 100, 30)
            self.button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text='Close',
                manager=self.ui_manager,
                container=self.panel
            )
            
            # モーダルダイアログの場合は背景を半透明にする
            if self.modal:
                self.panel.background_colour = pygame.Color(0, 0, 0, 128)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if not self.ui_manager:
            return False
        
        # pygame-guiにイベントを渡す
        self.ui_manager.process_events(event)
        
        # ボタンクリックを処理
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.button:
                self.send_message("close_requested")
                return True
        
        return False
    
    def handle_escape(self) -> bool:
        """ESCキーの処理"""
        self.send_message("close_requested")
        return True