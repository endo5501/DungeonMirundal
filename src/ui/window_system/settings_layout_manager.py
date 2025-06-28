"""
SettingsLayoutManager クラス

設定画面レイアウト計算の専門クラス
"""

import pygame
from typing import Dict, Any, List, Tuple


class SettingsLayoutManager:
    """
    設定レイアウト管理クラス
    
    設定画面のレイアウト計算を担当
    """
    
    def __init__(self, screen_width: int = 1024, screen_height: int = 768):
        """
        SettingsLayoutManagerを初期化
        
        Args:
            screen_width: 画面幅
            screen_height: 画面高さ
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # レイアウト定数
        self.DEFAULT_WIDTH = 800
        self.DEFAULT_HEIGHT = 600
        self.TITLE_HEIGHT = 40
        self.TAB_HEIGHT = 40
        self.BUTTON_HEIGHT = 40
        self.FIELD_HEIGHT = 60
        self.PADDING = 20
        self.BUTTON_WIDTH = 100
        self.BUTTON_SPACING = 10
    
    def calculate_settings_rect(self, has_title: bool = True) -> pygame.Rect:
        """
        設定画面全体のRectを計算
        
        Args:
            has_title: タイトルの有無
            
        Returns:
            pygame.Rect: 設定画面のRect
        """
        settings_width = self.DEFAULT_WIDTH
        settings_height = self.DEFAULT_HEIGHT
        
        # 画面中央に配置
        settings_x = (self.screen_width - settings_width) // 2
        settings_y = (self.screen_height - settings_height) // 2
        
        return pygame.Rect(settings_x, settings_y, settings_width, settings_height)
    
    def calculate_title_rect(self, settings_rect: pygame.Rect) -> pygame.Rect:
        """
        タイトルのRectを計算
        
        Args:
            settings_rect: 設定画面全体のRect
            
        Returns:
            pygame.Rect: タイトルのRect
        """
        return pygame.Rect(
            self.PADDING,
            self.PADDING,
            settings_rect.width - 2 * self.PADDING,
            30
        )
    
    def calculate_tab_container_rect(self, settings_rect: pygame.Rect, 
                                   has_title: bool) -> pygame.Rect:
        """
        タブコンテナのRectを計算
        
        Args:
            settings_rect: 設定画面全体のRect
            has_title: タイトルの有無
            
        Returns:
            pygame.Rect: タブコンテナのRect
        """
        tab_y = 60 if has_title else 20
        return pygame.Rect(
            self.PADDING,
            tab_y,
            settings_rect.width - 2 * self.PADDING,
            self.TAB_HEIGHT
        )
    
    def calculate_content_container_rect(self, settings_rect: pygame.Rect, 
                                       has_title: bool) -> pygame.Rect:
        """
        コンテンツコンテナのRectを計算
        
        Args:
            settings_rect: 設定画面全体のRect
            has_title: タイトルの有無
            
        Returns:
            pygame.Rect: コンテンツコンテナのRect
        """
        content_y = 120 if has_title else 80
        content_height = settings_rect.height - content_y - 80  # ボタン分を除く
        
        return pygame.Rect(
            self.PADDING,
            content_y,
            settings_rect.width - 2 * self.PADDING,
            content_height
        )
    
    def calculate_button_container_rect(self, settings_rect: pygame.Rect) -> pygame.Rect:
        """
        ボタンコンテナのRectを計算
        
        Args:
            settings_rect: 設定画面全体のRect
            
        Returns:
            pygame.Rect: ボタンコンテナのRect
        """
        button_y = settings_rect.height - 60
        return pygame.Rect(
            self.PADDING,
            button_y,
            settings_rect.width - 2 * self.PADDING,
            self.BUTTON_HEIGHT
        )
    
    def calculate_tab_positions(self, tab_container_rect: pygame.Rect, 
                              tab_count: int) -> List[pygame.Rect]:
        """
        タブ位置を計算
        
        Args:
            tab_container_rect: タブコンテナのRect
            tab_count: タブ数
            
        Returns:
            List[pygame.Rect]: タブ位置のリスト
        """
        if tab_count == 0:
            return []
        
        tab_width = (tab_container_rect.width - 2 * self.PADDING) // tab_count
        tab_positions = []
        
        for i in range(tab_count):
            tab_x = i * tab_width
            tab_rect = pygame.Rect(tab_x, 0, tab_width, self.TAB_HEIGHT)
            tab_positions.append(tab_rect)
        
        return tab_positions
    
    def calculate_field_positions(self, content_rect: pygame.Rect, 
                                field_count: int) -> List[Dict[str, pygame.Rect]]:
        """
        フィールド位置を計算
        
        Args:
            content_rect: コンテンツエリアのRect
            field_count: フィールド数
            
        Returns:
            List[Dict[str, pygame.Rect]]: フィールド位置のリスト
        """
        field_positions = []
        
        for i in range(field_count):
            y_position = 20 + i * self.FIELD_HEIGHT
            
            label_rect = pygame.Rect(20, y_position, 200, 25)
            input_rect = pygame.Rect(240, y_position, 300, 25)
            
            field_positions.append({
                'label': label_rect,
                'input': input_rect
            })
        
        return field_positions
    
    def calculate_action_button_positions(self, button_container_rect: pygame.Rect) -> Dict[str, pygame.Rect]:
        """
        アクションボタン位置を計算
        
        Args:
            button_container_rect: ボタンコンテナのRect
            
        Returns:
            Dict[str, pygame.Rect]: ボタン位置の辞書
        """
        # 右から左に配置
        button_y = 5
        
        # Resetボタン（一番右）
        reset_x = button_container_rect.width - self.BUTTON_WIDTH + 10
        reset_rect = pygame.Rect(reset_x, button_y, self.BUTTON_WIDTH - 10, 30)
        
        # Cancelボタン（中央）
        cancel_x = reset_x - self.BUTTON_WIDTH - self.BUTTON_SPACING
        cancel_rect = pygame.Rect(cancel_x, button_y, self.BUTTON_WIDTH, 30)
        
        # Applyボタン（左）
        apply_x = cancel_x - self.BUTTON_WIDTH - self.BUTTON_SPACING
        apply_rect = pygame.Rect(apply_x, button_y, self.BUTTON_WIDTH, 30)
        
        return {
            'apply': apply_rect,
            'cancel': cancel_rect,
            'reset': reset_rect
        }
    
    def calculate_responsive_layout(self, window_width: int, window_height: int) -> Dict[str, Any]:
        """
        レスポンシブレイアウトを計算
        
        Args:
            window_width: ウィンドウ幅
            window_height: ウィンドウ高さ
            
        Returns:
            Dict[str, Any]: レイアウト設定
        """
        # 画面サイズに応じて調整
        scale_factor = min(window_width / 1024, window_height / 768)
        scale_factor = max(0.7, min(scale_factor, 1.5))  # 0.7～1.5倍の範囲
        
        scaled_width = int(self.DEFAULT_WIDTH * scale_factor)
        scaled_height = int(self.DEFAULT_HEIGHT * scale_factor)
        
        return {
            'width': scaled_width,
            'height': scaled_height,
            'scale_factor': scale_factor,
            'padding': int(self.PADDING * scale_factor),
            'field_height': int(self.FIELD_HEIGHT * scale_factor)
        }