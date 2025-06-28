"""
MenuLayout クラス

メニューのレイアウト計算を担当
"""

import pygame
from typing import Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class LayoutConfig:
    """レイアウト設定"""
    screen_width: int = 1024
    screen_height: int = 768
    menu_width: int = 400
    button_height: int = 40
    button_spacing: int = 10
    padding: int = 20
    title_height: int = 30


class MenuLayout:
    """
    メニューレイアウト計算クラス
    
    メニューのサイズ、位置、ボタン配置を計算する
    """
    
    def __init__(self, config: LayoutConfig = None):
        """
        レイアウト計算器を初期化
        
        Args:
            config: レイアウト設定
        """
        self.config = config or LayoutConfig()
    
    def calculate_menu_rect(self, button_count: int, has_title: bool = False) -> pygame.Rect:
        """
        メニュー全体の矩形を計算
        
        Args:
            button_count: ボタンの数
            has_title: タイトルがあるかどうか
            
        Returns:
            pygame.Rect: メニューの矩形
        """
        menu_height = self._calculate_menu_height(button_count, has_title)
        menu_x = (self.config.screen_width - self.config.menu_width) // 2
        menu_y = (self.config.screen_height - menu_height) // 2
        
        return pygame.Rect(menu_x, menu_y, self.config.menu_width, menu_height)
    
    def _calculate_menu_height(self, button_count: int, has_title: bool) -> int:
        """メニューの高さを計算"""
        title_height = self.config.title_height + self.config.padding if has_title else 0
        buttons_height = button_count * (self.config.button_height + self.config.button_spacing)
        padding_height = self.config.padding * 2
        
        return title_height + buttons_height + padding_height
    
    def calculate_title_rect(self, menu_rect: pygame.Rect) -> pygame.Rect:
        """
        タイトルの矩形を計算
        
        Args:
            menu_rect: メニュー全体の矩形
            
        Returns:
            pygame.Rect: タイトルの矩形
        """
        return pygame.Rect(
            self.config.padding,
            self.config.padding,
            menu_rect.width - (self.config.padding * 2),
            self.config.title_height
        )
    
    def calculate_button_rects(self, menu_rect: pygame.Rect, button_count: int, 
                              has_title: bool = False) -> list[pygame.Rect]:
        """
        ボタンの矩形リストを計算
        
        Args:
            menu_rect: メニュー全体の矩形
            button_count: ボタンの数
            has_title: タイトルがあるかどうか
            
        Returns:
            List[pygame.Rect]: ボタンの矩形リスト
        """
        button_rects = []
        
        # 開始Y位置を計算
        button_start_y = self.config.padding
        if has_title:
            button_start_y += self.config.title_height + self.config.padding
        
        # 各ボタンの矩形を計算
        for i in range(button_count):
            button_y = button_start_y + i * (self.config.button_height + self.config.button_spacing)
            button_rect = pygame.Rect(
                self.config.padding,
                button_y,
                menu_rect.width - (self.config.padding * 2),
                self.config.button_height
            )
            button_rects.append(button_rect)
        
        return button_rects
    
    def calculate_centered_position(self, content_width: int, content_height: int) -> Tuple[int, int]:
        """
        画面中央の位置を計算
        
        Args:
            content_width: コンテンツの幅
            content_height: コンテンツの高さ
            
        Returns:
            Tuple[int, int]: (x, y) 位置
        """
        x = (self.config.screen_width - content_width) // 2
        y = (self.config.screen_height - content_height) // 2
        return x, y
    
    def update_config(self, **kwargs) -> None:
        """
        レイアウト設定を更新
        
        Args:
            **kwargs: 更新する設定項目
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def get_layout_info(self, button_count: int, has_title: bool = False) -> Dict[str, Any]:
        """
        レイアウト情報を辞書で取得
        
        Args:
            button_count: ボタンの数
            has_title: タイトルがあるかどうか
            
        Returns:
            Dict[str, Any]: レイアウト情報
        """
        menu_rect = self.calculate_menu_rect(button_count, has_title)
        button_rects = self.calculate_button_rects(menu_rect, button_count, has_title)
        
        result = {
            'menu_rect': menu_rect,
            'button_rects': button_rects,
            'config': self.config
        }
        
        if has_title:
            result['title_rect'] = self.calculate_title_rect(menu_rect)
        
        return result