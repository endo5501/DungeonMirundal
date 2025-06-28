"""
FormLayoutManager クラス

フォームレイアウト計算の専門クラス
"""

import pygame
from typing import Dict, Any, List


class FormLayoutManager:
    """
    フォームレイアウト管理クラス
    
    フォームのレイアウト計算を担当
    """
    
    def __init__(self, screen_width: int = 1024, screen_height: int = 768):
        """
        FormLayoutManagerを初期化
        
        Args:
            screen_width: 画面幅
            screen_height: 画面高さ
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # レイアウト定数
        self.FIELD_HEIGHT = 60
        self.TITLE_HEIGHT = 40
        self.BUTTON_HEIGHT = 50
        self.BASE_HEIGHT = 100
        self.DEFAULT_WIDTH = 400
        self.PADDING = 20
    
    def calculate_form_rect(self, field_count: int, has_title: bool) -> pygame.Rect:
        """
        フォーム全体のRectを計算
        
        Args:
            field_count: フィールド数
            has_title: タイトルの有無
            
        Returns:
            pygame.Rect: フォームのRect
        """
        form_width = self.DEFAULT_WIDTH
        form_height = self.BASE_HEIGHT
        
        # フィールド分の高さを追加
        form_height += field_count * self.FIELD_HEIGHT
        
        # ボタン分の高さを追加  
        form_height += self.BUTTON_HEIGHT
        
        # タイトル分の高さを追加
        if has_title:
            form_height += self.TITLE_HEIGHT
        
        # 画面中央に配置
        form_x = (self.screen_width - form_width) // 2
        form_y = (self.screen_height - form_height) // 2
        
        return pygame.Rect(form_x, form_y, form_width, form_height)
    
    def calculate_title_rect(self, form_rect: pygame.Rect) -> pygame.Rect:
        """
        タイトルのRectを計算
        
        Args:
            form_rect: フォーム全体のRect
            
        Returns:
            pygame.Rect: タイトルのRect
        """
        return pygame.Rect(
            self.PADDING,
            self.PADDING,
            form_rect.width - 2 * self.PADDING,
            30
        )
    
    def calculate_field_positions(self, form_rect: pygame.Rect, field_count: int, 
                                has_title: bool) -> List[Dict[str, pygame.Rect]]:
        """
        フィールド位置を計算
        
        Args:
            form_rect: フォーム全体のRect
            field_count: フィールド数
            has_title: タイトルの有無
            
        Returns:
            List[Dict[str, pygame.Rect]]: フィールド位置のリスト
        """
        start_y = 60 if has_title else 20
        positions = []
        
        for i in range(field_count):
            field_y = start_y + i * self.FIELD_HEIGHT
            
            label_rect = pygame.Rect(
                self.PADDING,
                field_y,
                form_rect.width - 2 * self.PADDING,
                20
            )
            
            input_rect = pygame.Rect(
                self.PADDING,
                field_y + 25,
                form_rect.width - 2 * self.PADDING,
                30
            )
            
            positions.append({
                'label': label_rect,
                'input': input_rect
            })
        
        return positions
    
    def calculate_button_positions(self, form_rect: pygame.Rect) -> Dict[str, pygame.Rect]:
        """
        ボタン位置を計算
        
        Args:
            form_rect: フォーム全体のRect
            
        Returns:
            Dict[str, pygame.Rect]: ボタン位置の辞書
        """
        button_y = form_rect.height - 40
        button_width = 80
        button_spacing = 10
        
        submit_rect = pygame.Rect(
            form_rect.width - 2 * button_width - button_spacing,
            button_y,
            button_width,
            30
        )
        
        cancel_rect = pygame.Rect(
            form_rect.width - button_width,
            button_y,
            button_width,
            30
        )
        
        return {
            'submit': submit_rect,
            'cancel': cancel_rect
        }