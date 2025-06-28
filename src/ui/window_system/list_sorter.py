"""
ListSorter クラス

リストソートの専門クラス
"""

from typing import List, Any, Callable
from .list_types import ListItem, ListColumn, SortOrder, ListSortState


class ListSorter:
    """
    リストソートクラス
    
    リストアイテムのソート処理を担当
    """
    
    def __init__(self):
        """ListSorterを初期化"""
        pass
    
    def sort_items(self, items: List[ListItem], columns: List[ListColumn], 
                   sort_state: ListSortState) -> List[ListItem]:
        """
        アイテムをソート
        
        Args:
            items: ソート対象のアイテムリスト
            columns: カラム定義リスト
            sort_state: ソート状態
            
        Returns:
            List[ListItem]: ソート済みアイテムリスト
        """
        if not sort_state.column_id:
            return items
        
        # ソート対象カラムが存在するか確認
        target_column = self._find_column_by_id(columns, sort_state.column_id)
        if not target_column or not target_column.sortable:
            return items
        
        # ソートを実行
        sorted_items = sorted(
            items,
            key=lambda item: self._get_sort_key(item, sort_state.column_id),
            reverse=(sort_state.order == SortOrder.DESCENDING)
        )
        
        return sorted_items
    
    def _find_column_by_id(self, columns: List[ListColumn], column_id: str) -> ListColumn:
        """IDでカラムを検索"""
        for column in columns:
            if column.column_id == column_id:
                return column
        return None
    
    def _get_sort_key(self, item: ListItem, column_id: str) -> Any:
        """ソートキーを取得"""
        value = item.data.get(column_id, '')
        
        # 数値として解釈可能な場合は数値でソート
        if isinstance(value, (int, float)):
            return value
        
        try:
            return float(str(value))
        except (ValueError, TypeError):
            # 文字列として小文字でソート
            return str(value).lower()
    
    def is_column_sortable(self, columns: List[ListColumn], column_id: str) -> bool:
        """カラムがソート可能かチェック"""
        target_column = self._find_column_by_id(columns, column_id)
        return target_column is not None and target_column.sortable
    
    def get_next_sort_order(self, current_order: SortOrder) -> SortOrder:
        """次のソート順を取得"""
        if current_order == SortOrder.ASCENDING:
            return SortOrder.DESCENDING
        else:
            return SortOrder.ASCENDING