"""
ListFilter クラス

リストフィルタリングの専門クラス
"""

import re
from typing import List, Dict, Any
from .list_types import ListItem, ListColumn, ListFilterState


class ListFilter:
    """
    リストフィルタクラス
    
    リストアイテムのフィルタリング処理を担当
    """
    
    def __init__(self):
        """ListFilterを初期化"""
        pass
    
    def filter_items(self, items: List[ListItem], columns: List[ListColumn], 
                    filter_state: ListFilterState) -> List[ListItem]:
        """
        アイテムをフィルタリング
        
        Args:
            items: フィルタリング対象のアイテムリスト
            columns: カラム定義リスト
            filter_state: フィルタ状態
            
        Returns:
            List[ListItem]: フィルタリング済みアイテムリスト
        """
        filtered_items = []
        
        for item in items:
            if not item.visible:
                continue
            
            # テキスト検索フィルタを適用
            if not self._matches_search_text(item, columns, filter_state.search_text):
                continue
            
            # カラムフィルタを適用
            if not self._matches_column_filters(item, filter_state.column_filters):
                continue
            
            filtered_items.append(item)
        
        return filtered_items
    
    def _matches_search_text(self, item: ListItem, columns: List[ListColumn], 
                           search_text: str) -> bool:
        """テキスト検索にマッチするかチェック"""
        if not search_text:
            return True
        
        search_lower = search_text.lower()
        
        # 全カラムのデータから検索
        for column in columns:
            value = str(item.data.get(column.column_id, ''))
            if search_lower in value.lower():
                return True
        
        return False
    
    def _matches_column_filters(self, item: ListItem, column_filters: Dict[str, Any]) -> bool:
        """カラムフィルタにマッチするかチェック"""
        if not column_filters:
            return True
        
        for column_id, filter_value in column_filters.items():
            item_value = item.data.get(column_id)
            
            if not self._matches_filter_value(item_value, filter_value):
                return False
        
        return True
    
    def _matches_filter_value(self, item_value: Any, filter_value: Any) -> bool:
        """個別フィルタ値にマッチするかチェック"""
        if filter_value is None:
            return True
        
        # 文字列の場合は部分一致
        if isinstance(filter_value, str):
            return filter_value.lower() in str(item_value).lower()
        
        # リストの場合は包含チェック
        if isinstance(filter_value, list):
            return item_value in filter_value
        
        # 辞書の場合は範囲チェック（min/max）
        if isinstance(filter_value, dict):
            return self._matches_range_filter(item_value, filter_value)
        
        # デフォルトは完全一致
        return item_value == filter_value
    
    def _matches_range_filter(self, item_value: Any, range_filter: Dict[str, Any]) -> bool:
        """範囲フィルタにマッチするかチェック"""
        try:
            numeric_value = float(str(item_value))
            
            if 'min' in range_filter:
                if numeric_value < range_filter['min']:
                    return False
            
            if 'max' in range_filter:
                if numeric_value > range_filter['max']:
                    return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    def create_regex_filter(self, pattern: str) -> bool:
        """正規表現フィルタを作成"""
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
    
    def apply_regex_filter(self, items: List[ListItem], columns: List[ListColumn], 
                          column_id: str, pattern: str) -> List[ListItem]:
        """正規表現フィルタを適用"""
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            filtered_items = []
            
            for item in items:
                value = str(item.data.get(column_id, ''))
                if regex.search(value):
                    filtered_items.append(item)
            
            return filtered_items
        except re.error:
            return items