"""
ListWindow クラス

リスト表示用のウィンドウ
"""

import pygame
import pygame_gui
from typing import Dict, List, Any, Optional, Callable

from .window import Window
from .list_types import ListItem, ListColumn, SelectionMode, SortOrder, ListSortState, ListFilterState
from .list_sorter import ListSorter
from .list_filter import ListFilter
from .list_layout_manager import ListLayoutManager
from src.utils.logger import logger


class ListWindow(Window):
    """
    リストウィンドウクラス
    
    データのリスト表示と操作を行う
    """
    
    def __init__(self, window_id: str, list_config: Dict[str, Any], 
                 parent: Optional[Window] = None, modal: bool = False):
        """
        リストウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            list_config: リスト設定辞書
            parent: 親ウィンドウ
            modal: モーダルウィンドウかどうか
        """
        super().__init__(window_id, parent, modal)
        
        # 設定の検証
        self._validate_config(list_config)
        
        self.list_config = list_config
        self.columns: List[ListColumn] = []
        self.items: List[ListItem] = []
        self.selected_index = 0
        
        # 選択設定
        self.selection_mode = SelectionMode(list_config.get('selection_mode', 'single'))
        
        # ソート・フィルタ状態
        self.sort_state = ListSortState()
        self.filter_state = ListFilterState()
        
        # UI要素
        self.list_ui_element: Optional[pygame_gui.elements.UISelectionList] = None
        self.search_ui_element: Optional[pygame_gui.elements.UITextEntryLine] = None
        
        # 機能フラグ
        self.searchable = list_config.get('searchable', False)
        
        # Extract Classによる専門クラス
        self.sorter = ListSorter()
        self.filter = ListFilter()
        self.layout_manager = ListLayoutManager()
        
        logger.debug(f"ListWindowを初期化: {window_id}")
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """リスト設定を検証"""
        if 'columns' not in config:
            raise ValueError("List config must contain 'columns'")
        
        if not isinstance(config['columns'], list):
            raise ValueError("List config 'columns' must be a list")
        
        if len(config['columns']) == 0:
            raise ValueError("List config 'columns' cannot be empty")
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            self._initialize_ui_manager()
            self._calculate_layout()
            self._create_panel()
            self._create_title_if_needed()
            self._create_search_if_needed()
            self._create_columns()
            self._create_list_ui()
            self._populate_items()
        
        logger.debug(f"ListWindow UI要素を作成: {self.window_id}")
    
    def _initialize_ui_manager(self) -> None:
        """UIManagerを初期化"""
        screen_width = 1024
        screen_height = 768
        self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
    
    def _calculate_layout(self) -> None:
        """リストのレイアウトを計算"""
        columns = self.list_config['columns']
        item_count = len(self.list_config.get('items', []))
        has_title = 'title' in self.list_config
        has_search = self.searchable
        
        # Extract Methodパターン適用
        self.rect = self.layout_manager.calculate_list_rect(columns, item_count, has_title, has_search)
    
    def _create_panel(self) -> None:
        """リストパネルを作成"""
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager
        )
    
    def _create_title_if_needed(self) -> None:
        """タイトルラベルを作成（必要な場合）"""
        if 'title' in self.list_config:
            title_rect = self.layout_manager.calculate_title_rect(self.rect)
            self.title_label = pygame_gui.elements.UILabel(
                relative_rect=title_rect,
                text=self.list_config['title'],
                manager=self.ui_manager,
                container=self.panel
            )
    
    def _create_search_if_needed(self) -> None:
        """検索フィールドを作成（必要な場合）"""
        if self.searchable:
            has_title = 'title' in self.list_config
            search_rect = self.layout_manager.calculate_search_rect(self.rect, has_title)
            self.search_ui_element = pygame_gui.elements.UITextEntryLine(
                relative_rect=search_rect,
                manager=self.ui_manager,
                container=self.panel
            )
            self.search_ui_element.set_text("Search...")
    
    def _create_columns(self) -> None:
        """カラムを作成"""
        for col_config in self.list_config['columns']:
            column = ListColumn(
                column_id=col_config['id'],
                label=col_config['label'],
                width=col_config['width'],
                sortable=col_config.get('sortable', True),
                resizable=col_config.get('resizable', True),
                align=col_config.get('align', 'left')
            )
            self.columns.append(column)
    
    def _create_list_ui(self) -> None:
        """リストUI要素を作成"""
        has_title = 'title' in self.list_config
        has_search = self.searchable
        list_rect = self.layout_manager.calculate_list_ui_rect(self.rect, has_title, has_search)
        
        # pygame-guiのUISelectionListを使用
        self.list_ui_element = pygame_gui.elements.UISelectionList(
            relative_rect=list_rect,
            item_list=[],
            manager=self.ui_manager,
            container=self.panel,
            allow_multi_select=(self.selection_mode == SelectionMode.MULTIPLE)
        )
    
    def _populate_items(self) -> None:
        """設定からアイテムを作成"""
        for i, item_data in enumerate(self.list_config.get('items', [])):
            list_item = ListItem(
                item_id=f"item_{i}",
                data=item_data,
                selected=False,
                visible=True
            )
            self.items.append(list_item)
        
        self._update_list_display()
    
    def _update_list_display(self) -> None:
        """リスト表示を更新"""
        if not self.list_ui_element:
            return
        
        # フィルタリングされたアイテムを取得
        visible_items = self.get_visible_items()
        
        # 表示テキストを生成
        item_texts = []
        for item in visible_items:
            # 各カラムのデータを連結して表示テキストを作成
            text_parts = []
            for column in self.columns:
                value = str(item.data.get(column.column_id, ''))
                text_parts.append(value.ljust(column.width // 8))  # 簡易的な幅調整
            item_texts.append(' | '.join(text_parts))
        
        # UISelectionListを更新
        self.list_ui_element.set_item_list(item_texts)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if not self.ui_manager:
            return False
        
        # pygame-guiにイベントを渡す
        self.ui_manager.process_events(event)
        
        # キーボードナビゲーション
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self._navigate_down()
                return True
            elif event.key == pygame.K_UP:
                self._navigate_up()
                return True
            elif event.key == pygame.K_SPACE:
                self._toggle_selection()
                return True
            elif event.key == pygame.K_RETURN:
                return self._activate_current_item()
        
        # リスト選択イベント
        if hasattr(event, 'ui_element') and event.ui_element == self.list_ui_element:
            if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
                return self._handle_item_selection(event)
            elif event.type == pygame_gui.UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION:
                return self._handle_item_activation(event)
        
        # 検索フィールドイベント
        if (hasattr(event, 'ui_element') and 
            event.ui_element == self.search_ui_element and
            event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED):
            self._handle_search_changed(event)
            return True
        
        return False
    
    def _navigate_down(self) -> None:
        """下方向のナビゲーション"""
        if len(self.items) > 0:
            self.selected_index = min(self.selected_index + 1, len(self.items) - 1)
    
    def _navigate_up(self) -> None:
        """上方向のナビゲーション"""
        if len(self.items) > 0:
            self.selected_index = max(self.selected_index - 1, 0)
    
    def _toggle_selection(self) -> None:
        """現在のアイテムの選択状態を切り替え"""
        if 0 <= self.selected_index < len(self.items):
            current_item = self.items[self.selected_index]
            
            if self.selection_mode == SelectionMode.SINGLE:
                # 単一選択：他の選択を解除してから選択
                self._clear_all_selections()
                current_item.selected = True
            elif self.selection_mode == SelectionMode.MULTIPLE:
                # 複数選択：トグル
                current_item.selected = not current_item.selected
    
    def _activate_current_item(self) -> bool:
        """現在のアイテムを実行"""
        if 0 <= self.selected_index < len(self.items):
            current_item = self.items[self.selected_index]
            self.send_message('item_activated', {
                'list_id': self.window_id,
                'item_index': self.selected_index,
                'item_data': current_item.data
            })
            return True
        return False
    
    def _handle_item_selection(self, event) -> bool:
        """アイテム選択イベントを処理"""
        # 選択されたアイテムのインデックスを取得
        selected_text = event.text
        visible_items = self.get_visible_items()
        
        for i, item in enumerate(visible_items):
            # アイテム名で最初に見つかるものを選択（簡易実装）
            item_name = str(item.data.get('name', ''))
            if item_name == selected_text or selected_text in item_name:
                # 実際のインデックス（self.items内での位置）を見つける
                actual_index = self.items.index(item)
                self.selected_index = actual_index
                self.send_message('item_selected', {
                    'list_id': self.window_id,
                    'item_index': actual_index,
                    'item_data': item.data
                })
                return True
        return False
    
    def _handle_item_activation(self, event) -> bool:
        """アイテム実行イベントを処理"""
        # ダブルクリックされたアイテムのインデックスを取得
        selected_text = event.text
        visible_items = self.get_visible_items()
        
        for i, item in enumerate(visible_items):
            # アイテム名で最初に見つかるものを実行（簡易実装）
            item_name = str(item.data.get('name', ''))
            if item_name == selected_text or selected_text in item_name:
                # 実際のインデックス（self.items内での位置）を見つける
                actual_index = self.items.index(item)
                self.send_message('item_activated', {
                    'list_id': self.window_id,
                    'item_index': actual_index,
                    'item_data': item.data
                })
                return True
        return False
    
    def _handle_search_changed(self, event) -> None:
        """検索テキスト変更イベントを処理"""
        search_text = event.text
        self.set_filter_text(search_text)
    
    def _format_item_text(self, item: ListItem) -> str:
        """アイテムの表示テキストをフォーマット"""
        text_parts = []
        for column in self.columns:
            value = str(item.data.get(column.column_id, ''))
            text_parts.append(value.ljust(column.width // 8))
        return ' | '.join(text_parts)
    
    def select_item(self, index: int) -> bool:
        """アイテムを選択"""
        if 0 <= index < len(self.items):
            if self.selection_mode == SelectionMode.SINGLE:
                # 単一選択：他の選択を解除
                self._clear_all_selections()
            
            self.items[index].selected = True
            self.selected_index = index
            return True
        return False
    
    def _clear_all_selections(self) -> None:
        """全ての選択を解除"""
        for item in self.items:
            item.selected = False
    
    def get_selected_items(self) -> List[ListItem]:
        """選択されたアイテムを取得"""
        return [item for item in self.items if item.selected]
    
    def get_visible_items(self) -> List[ListItem]:
        """表示されているアイテムを取得"""
        # Extract Classパターン適用 - フィルタリングロジックを専門クラスに委譲
        filtered_items = self.filter.filter_items(self.items, self.columns, self.filter_state)
        
        # ソートを適用
        sorted_items = self.sorter.sort_items(filtered_items, self.columns, self.sort_state)
        
        return sorted_items
    
    def set_filter_text(self, search_text: str) -> None:
        """検索テキストを設定"""
        self.filter_state.search_text = search_text
        self._update_list_display()
    
    def sort_by_column(self, column_id: str, order: SortOrder) -> None:
        """カラムでソート"""
        if not self.sorter.is_column_sortable(self.columns, column_id):
            return
        
        self.sort_state.column_id = column_id
        self.sort_state.order = order
        
        # 表示を更新（ソートはget_visible_itemsで適用される）
        self._update_list_display()
    
    def add_item(self, item_data: Dict[str, Any]) -> None:
        """アイテムを追加"""
        new_item = ListItem(
            item_id=f"item_{len(self.items)}",
            data=item_data,
            selected=False,
            visible=True
        )
        self.items.append(new_item)
        self._update_list_display()
    
    def remove_item(self, index: int) -> bool:
        """アイテムを削除"""
        if 0 <= index < len(self.items):
            del self.items[index]
            
            # 選択インデックスを調整
            if self.selected_index >= len(self.items):
                self.selected_index = max(0, len(self.items) - 1)
            
            self._update_list_display()
            return True
        return False
    
    def clear_items(self) -> None:
        """全アイテムをクリア"""
        self.items.clear()
        self.selected_index = -1
        self._update_list_display()
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # アイテムとカラムをクリア
        self.items.clear()
        self.columns.clear()
        
        # pygame-guiの要素を削除
        if self.ui_manager:
            for element in list(self.ui_manager.get_root_container().elements):
                element.kill()
            self.ui_manager = None
        
        logger.debug(f"ListWindow UI要素をクリーンアップ: {self.window_id}")