"""
ListLayoutManager クラス

リストレイアウト計算の専門クラス
"""

import pygame
from typing import Dict, Any, List


class ListLayoutManager:
    """
    リストレイアウト管理クラス
    
    リストのレイアウト計算を担当
    """
    
    def __init__(self, screen_width: int = 1024, screen_height: int = 768):
        """
        ListLayoutManagerを初期化
        
        Args:
            screen_width: 画面幅
            screen_height: 画面高さ
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # レイアウト定数
        self.MIN_WIDTH = 400
        self.MAX_HEIGHT = 500
        self.TITLE_HEIGHT = 40
        self.SEARCH_HEIGHT = 40
        self.ITEM_HEIGHT = 25
        self.BASE_HEIGHT = 300
        self.PADDING = 20
    
    def calculate_list_rect(self, columns: List[Dict[str, Any]], item_count: int, 
                           has_title: bool, has_search: bool) -> pygame.Rect:
        """
        リスト全体のRectを計算
        
        Args:
            columns: カラム定義リスト
            item_count: アイテム数
            has_title: タイトルの有無
            has_search: 検索フィールドの有無
            
        Returns:
            pygame.Rect: リストのRect
        """
        # カラム幅の合計を計算
        total_width = sum(col['width'] for col in columns)
        list_width = max(self.MIN_WIDTH, total_width + 2 * self.PADDING)
        
        # アイテム数に応じて高さを調整
        list_height = self.BASE_HEIGHT + min(item_count * self.ITEM_HEIGHT, 200)
        list_height = min(list_height, self.MAX_HEIGHT)
        
        # タイトル・検索の高さを追加
        if has_title:
            list_height += self.TITLE_HEIGHT
        if has_search:
            list_height += self.SEARCH_HEIGHT
        
        # 画面中央に配置
        list_x = (self.screen_width - list_width) // 2
        list_y = (self.screen_height - list_height) // 2
        
        return pygame.Rect(list_x, list_y, list_width, list_height)
    
    def calculate_title_rect(self, list_rect: pygame.Rect) -> pygame.Rect:
        """
        タイトルのRectを計算
        
        Args:
            list_rect: リスト全体のRect
            
        Returns:
            pygame.Rect: タイトルのRect
        """
        return pygame.Rect(
            self.PADDING,
            self.PADDING,
            list_rect.width - 2 * self.PADDING,
            30
        )
    
    def calculate_search_rect(self, list_rect: pygame.Rect, has_title: bool) -> pygame.Rect:
        """
        検索フィールドのRectを計算
        
        Args:
            list_rect: リスト全体のRect
            has_title: タイトルの有無
            
        Returns:
            pygame.Rect: 検索フィールドのRect
        """
        search_y = 60 if has_title else 20
        return pygame.Rect(
            self.PADDING,
            search_y,
            list_rect.width - 2 * self.PADDING,
            30
        )
    
    def calculate_list_ui_rect(self, list_rect: pygame.Rect, has_title: bool, 
                              has_search: bool) -> pygame.Rect:
        """
        リストUI要素のRectを計算
        
        Args:
            list_rect: リスト全体のRect
            has_title: タイトルの有無
            has_search: 検索フィールドの有無
            
        Returns:
            pygame.Rect: リストUI要素のRect
        """
        list_y = 60
        if has_title:
            list_y += self.TITLE_HEIGHT
        if has_search:
            list_y += self.SEARCH_HEIGHT
        
        return pygame.Rect(
            self.PADDING,
            list_y,
            list_rect.width - 2 * self.PADDING,
            list_rect.height - list_y - self.PADDING
        )
    
    def calculate_column_widths(self, columns: List[Dict[str, Any]], 
                               available_width: int) -> List[int]:
        """
        カラム幅を計算
        
        Args:
            columns: カラム定義リスト
            available_width: 利用可能幅
            
        Returns:
            List[int]: 計算されたカラム幅のリスト
        """
        # 指定された幅の合計を計算
        total_specified_width = sum(col.get('width', 100) for col in columns)
        
        # 利用可能幅に対する倍率を計算
        if total_specified_width > available_width:
            scale_factor = available_width / total_specified_width
        else:
            scale_factor = 1.0
        
        # 各カラム幅を調整
        adjusted_widths = []
        for col in columns:
            specified_width = col.get('width', 100)
            adjusted_width = int(specified_width * scale_factor)
            adjusted_widths.append(max(50, adjusted_width))  # 最小幅50px
        
        return adjusted_widths
    
    def calculate_header_positions(self, columns: List[Dict[str, Any]], 
                                  column_widths: List[int]) -> List[pygame.Rect]:
        """
        ヘッダー位置を計算
        
        Args:
            columns: カラム定義リスト
            column_widths: カラム幅リスト
            
        Returns:
            List[pygame.Rect]: ヘッダー位置のリスト
        """
        header_rects = []
        current_x = 0
        
        for i, width in enumerate(column_widths):
            header_rect = pygame.Rect(current_x, 0, width, 30)
            header_rects.append(header_rect)
            current_x += width
        
        return header_rects