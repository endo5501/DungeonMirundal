"""pygame-gui UISelectionListを使用したリスト表示コンポーネント"""

from typing import List, Dict, Any, Callable, Optional, Tuple
import pygame
import pygame_gui
from pygame_gui.elements import UISelectionList, UIButton, UIPanel
from pygame_gui.core import ObjectID

from src.utils.logger import logger


class SelectionListData:
    """選択リストのデータ項目"""
    
    def __init__(self, display_text: str, data: Any = None, callback: Optional[Callable] = None):
        self.display_text = display_text
        self.data = data  # アイテムオブジェクトなど
        self.callback = callback  # 選択時のコールバック


class CustomSelectionList:
    """pygame-gui UISelectionListをラップしたカスタムコンポーネント"""
    
    def __init__(self, 
                 relative_rect: pygame.Rect,
                 manager: pygame_gui.UIManager,
                 items: List[SelectionListData] = None,
                 title: str = "",
                 allow_multi_select: bool = False,
                 container: pygame_gui.core.UIContainer = None):
        """
        Args:
            relative_rect: リストの位置とサイズ
            manager: pygame_gui UIManager
            items: 表示項目のリスト
            title: リストのタイトル
            allow_multi_select: 複数選択を許可するか
            container: 親コンテナ
        """
        self.manager = manager
        self.relative_rect = relative_rect
        self.title = title
        self.allow_multi_select = allow_multi_select
        self.container = container
        
        # データ管理
        self.items: List[SelectionListData] = items or []
        self.selected_items: List[SelectionListData] = []
        self.current_selected_index: Optional[int] = None
        
        # UI要素
        self.panel: Optional[UIPanel] = None
        self.title_label: Optional[pygame_gui.elements.UILabel] = None
        self.selection_list: Optional[UISelectionList] = None
        self.action_buttons: List[UIButton] = []
        
        # コールバック
        self.on_selection_changed: Optional[Callable[[List[SelectionListData]], None]] = None
        self.on_double_click: Optional[Callable[[SelectionListData], None]] = None
        
        self._create_ui()
    
    def _create_ui(self):
        """UI要素を作成"""
        try:
            # メインパネル作成
            self.panel = UIPanel(
                relative_rect=self.relative_rect,
                manager=self.manager,
                container=self.container
            )
            
            # タイトルラベル作成（タイトルがある場合）
            title_height = 0
            if self.title:
                title_height = 40
                title_rect = pygame.Rect(10, 10, self.relative_rect.width - 20, 30)
                self.title_label = pygame_gui.elements.UILabel(
                    relative_rect=title_rect,
                    text=self.title,
                    manager=self.manager,
                    container=self.panel
                )
            
            # セレクションリスト作成
            list_rect = pygame.Rect(
                10, 
                title_height + 10,
                self.relative_rect.width - 20,
                self.relative_rect.height - title_height - 70  # ボタン用スペースを確保
            )
            
            # 表示用テキストリストを作成
            display_texts = [item.display_text for item in self.items]
            
            self.selection_list = UISelectionList(
                relative_rect=list_rect,
                item_list=display_texts,
                manager=self.manager,
                container=self.panel,
                allow_multi_select=self.allow_multi_select
            )
            
            # アクションボタンエリア
            self._create_action_buttons()
            
            logger.debug(f"CustomSelectionList作成完了: {len(self.items)}項目")
            
        except Exception as e:
            logger.error(f"CustomSelectionList作成エラー: {e}")
            raise
    
    def _create_action_buttons(self):
        """アクションボタンを作成"""
        button_y = self.relative_rect.height - 50
        button_width = 100
        button_height = 30
        button_spacing = 110
        
        # 選択ボタン
        select_rect = pygame.Rect(10, button_y, button_width, button_height)
        select_button = UIButton(
            relative_rect=select_rect,
            text="選択",
            manager=self.manager,
            container=self.panel
        )
        self.action_buttons.append(select_button)
        
        # 戻るボタン
        back_rect = pygame.Rect(10 + button_spacing, button_y, button_width, button_height)
        back_button = UIButton(
            relative_rect=back_rect,
            text="戻る",
            manager=self.manager,
            container=self.panel
        )
        self.action_buttons.append(back_button)
    
    def add_item(self, item: SelectionListData):
        """項目を追加"""
        self.items.append(item)
        logger.debug(f"UISelectionListに項目追加: {item.display_text}, callback={item.callback}")
        self._refresh_list()
    
    def remove_item(self, item: SelectionListData):
        """項目を削除"""
        if item in self.items:
            self.items.remove(item)
            self._refresh_list()
    
    def clear_items(self):
        """全項目をクリア"""
        self.items.clear()
        self._refresh_list()
    
    def _refresh_list(self):
        """リスト表示を更新"""
        if self.selection_list:
            display_texts = [item.display_text for item in self.items]
            logger.debug(f"UISelectionListを更新: {len(display_texts)}項目")
            self.selection_list.set_item_list(display_texts)
        else:
            logger.warning("selection_listがNoneのため更新できません")
    
    def get_selected_items(self) -> List[SelectionListData]:
        """選択された項目を取得"""
        if not self.selection_list:
            return []
        
        selected_items = []
        
        if self.allow_multi_select:
            selected_indices = self.selection_list.get_multi_selection()
        else:
            single_index = self.selection_list.get_single_selection()
            logger.debug(f"get_single_selection結果: {single_index}")
            selected_indices = [single_index] if single_index is not None else []
        
        for index in selected_indices:
            if index is not None and isinstance(index, int) and 0 <= index < len(self.items):
                selected_items.append(self.items[index])
        
        return selected_items
    
    def get_selected_item(self) -> Optional[SelectionListData]:
        """選択された単一項目を取得"""
        if self.current_selected_index is not None and 0 <= self.current_selected_index < len(self.items):
            selected_item = self.items[self.current_selected_index]
            logger.debug(f"選択されたアイテム: {selected_item.display_text}")
            return selected_item
        else:
            logger.debug("選択されたアイテムなし")
            return None
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理"""
        if not self.panel or not self.selection_list:
            return False
        
        # UIイベント処理
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.selection_list:
                # pygame_guiの選択インデックスを直接取得
                selected_index = self.selection_list.get_single_selection()
                logger.debug(f"選択イベント - インデックス: {selected_index}")
                
                if selected_index is not None:
                    # pygame_guiは選択されたテキストを返すので、インデックスを逆引き
                    if isinstance(selected_index, str):
                        # テキストからインデックスを検索
                        for i, item in enumerate(self.items):
                            if item.display_text == selected_index:
                                self.current_selected_index = i
                                self.selected_items = [item]
                                logger.debug(f"選択されたアイテム: {item.display_text} (インデックス: {i})")
                                break
                        else:
                            logger.warning(f"選択されたテキストに対応するアイテムが見つかりません: {selected_index}")
                            self.current_selected_index = None
                            self.selected_items = []
                    else:
                        # 整数インデックスの場合
                        try:
                            index = int(selected_index)
                            if 0 <= index < len(self.items):
                                self.current_selected_index = index
                                self.selected_items = [self.items[index]]
                                logger.debug(f"選択されたアイテム: {self.items[index].display_text}")
                            else:
                                self.current_selected_index = None
                                self.selected_items = []
                        except (ValueError, TypeError):
                            logger.warning(f"無効な選択インデックス: {selected_index}")
                            self.current_selected_index = None
                            self.selected_items = []
                else:
                    self.current_selected_index = None
                    self.selected_items = []
                
                if self.on_selection_changed:
                    self.on_selection_changed(self.selected_items)
                return True
        
        elif event.type == pygame_gui.UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION:
            if event.ui_element == self.selection_list:
                selected_item = self.get_selected_item()
                logger.debug(f"ダブルクリック選択: {selected_item}")
                if selected_item and self.on_double_click:
                    self.on_double_click(selected_item)
                elif selected_item and selected_item.callback:
                    # ダブルクリックでもコールバックを実行
                    logger.info(f"ダブルクリックでコールバックを実行: {selected_item.display_text}")
                    selected_item.callback()
                return True
        
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            # アクションボタンの処理
            if event.ui_element in self.action_buttons:
                button_text = event.ui_element.text
                if button_text == "選択":
                    selected_item = self.get_selected_item()
                    logger.debug(f"選択ボタンが押されました。選択アイテム: {selected_item}")
                    if selected_item:
                        logger.debug(f"選択アイテムのコールバック: {selected_item.callback}")
                        if selected_item.callback:
                            logger.info(f"コールバックを実行します: {selected_item.display_text}")
                            selected_item.callback()
                        else:
                            logger.warning(f"選択アイテムにコールバックがありません: {selected_item.display_text}")
                    else:
                        logger.warning("選択されたアイテムがありません")
                    return True
                elif button_text == "戻る":
                    self.kill()  # hideではなくkillで完全に破棄
                    return True
        
        return False
    
    def show(self):
        """リストを表示"""
        if self.panel:
            self.panel.show()
    
    def hide(self):
        """リストを非表示"""
        if self.panel:
            self.panel.hide()
    
    def kill(self):
        """リストを破棄"""
        if self.panel:
            self.panel.kill()
            self.panel = None
            self.selection_list = None
            self.action_buttons.clear()
    
    def update(self, time_delta: float):
        """更新処理"""
        # pygame_guiが自動的に更新を処理するため、特別な処理は不要
        pass


class ItemSelectionList(CustomSelectionList):
    """アイテム選択用の特化リスト"""
    
    def __init__(self, 
                 relative_rect: pygame.Rect,
                 manager: pygame_gui.UIManager,
                 title: str = "アイテム選択",
                 container: pygame_gui.core.UIContainer = None):
        super().__init__(relative_rect, manager, [], title, False, container)
        
        # アイテム特化のコールバック
        self.on_item_selected: Optional[Callable[[Any], None]] = None  # アイテムオブジェクトを渡す
        self.on_item_details: Optional[Callable[[Any], None]] = None   # アイテム詳細表示
    
    def add_item_data(self, item_obj: Any, display_text: str = None):
        """アイテムオブジェクトを追加"""
        if not display_text:
            # アイテムオブジェクトから表示名を取得（get_name()メソッドがあると仮定）
            display_text = getattr(item_obj, 'get_name', lambda: str(item_obj))()
        
        item_data = SelectionListData(
            display_text=display_text,
            data=item_obj,
            callback=lambda: self._on_item_callback(item_obj)
        )
        self.add_item(item_data)
    
    def _on_item_callback(self, item_obj: Any):
        """アイテム選択時のコールバック"""
        if self.on_item_selected:
            self.on_item_selected(item_obj)
    
    def _create_action_buttons(self):
        """アイテム用のアクションボタンを作成"""
        button_y = self.relative_rect.height - 50
        button_width = 80
        button_height = 30
        button_spacing = 90
        
        # 選択ボタン
        select_rect = pygame.Rect(10, button_y, button_width, button_height)
        select_button = UIButton(
            relative_rect=select_rect,
            text="選択",
            manager=self.manager,
            container=self.panel
        )
        self.action_buttons.append(select_button)
        
        # 詳細ボタン
        details_rect = pygame.Rect(10 + button_spacing, button_y, button_width, button_height)
        details_button = UIButton(
            relative_rect=details_rect,
            text="詳細",
            manager=self.manager,
            container=self.panel
        )
        self.action_buttons.append(details_button)
        
        # 戻るボタン
        back_rect = pygame.Rect(10 + button_spacing * 2, button_y, button_width, button_height)
        back_button = UIButton(
            relative_rect=back_rect,
            text="戻る",
            manager=self.manager,
            container=self.panel
        )
        self.action_buttons.append(back_button)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """アイテム用のイベント処理"""
        # 親クラスのイベント処理を先に実行
        if super().handle_event(event):
            return True
        
        # アイテム特化のイベント処理
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element in self.action_buttons:
                button_text = event.ui_element.text
                if button_text == "詳細":
                    selected_item = self.get_selected_item()
                    if selected_item and selected_item.data and self.on_item_details:
                        self.on_item_details(selected_item.data)
                    return True
        
        return False