"""パーティ編成パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
import logging
from ..service_panel import ServicePanel
from ...core.service_result import ServiceResult

logger = logging.getLogger(__name__)


class PartyFormationPanel(ServicePanel):
    """パーティ編成パネル
    
    パーティメンバーの追加、削除、並び替えを行うパネル。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        super().__init__(rect, parent, controller, "party_formation", ui_manager)
        
        # UI要素
        self.party_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.available_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.add_button: Optional[pygame_gui.elements.UIButton] = None
        self.remove_button: Optional[pygame_gui.elements.UIButton] = None
        self.up_button: Optional[pygame_gui.elements.UIButton] = None
        self.down_button: Optional[pygame_gui.elements.UIButton] = None
        self.party_info_box: Optional[pygame_gui.elements.UITextBox] = None
        
        # データ
        self.party_members: List[Dict[str, Any]] = []
        self.available_characters: List[Dict[str, Any]] = []
        self.selected_party_index: Optional[int] = None
        self.selected_available_index: Optional[int] = None
        
        logger.info("PartyFormationPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        # レイアウト定数
        list_width = (self.rect.width - 30) // 2 - 40
        list_height = 250
        button_size = 35
        
        # パーティリストラベル
        party_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, list_width, 30),
            text="パーティメンバー（最大6人）",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(party_label)
        
        # パーティメンバーリスト
        party_rect = pygame.Rect(10, 45, list_width, list_height)
        self.party_list = pygame_gui.elements.UISelectionList(
            relative_rect=party_rect,
            item_list=[],
            manager=self.ui_manager,
            container=self.container,
            allow_multi_select=False
        )
        self.ui_elements.append(self.party_list)
        
        # 中央のボタン群
        center_x = self.rect.width // 2 - button_size // 2
        
        # 追加ボタン
        add_rect = pygame.Rect(center_x - 25, 100, 50, button_size)
        self.add_button = self._create_button(
            "→",
            add_rect,
            container=self.container,
            object_id="#add_member_button"
        )
        
        # 削除ボタン
        remove_rect = pygame.Rect(center_x - 25, 150, 50, button_size)
        self.remove_button = self._create_button(
            "←",
            remove_rect,
            container=self.container,
            object_id="#remove_member_button"
        )
        
        # 利用可能リストラベル
        available_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(self.rect.width - list_width - 10, 10, list_width, 30),
            text="登録済み冒険者",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(available_label)
        
        # 利用可能キャラクターリスト
        available_rect = pygame.Rect(
            self.rect.width - list_width - 10, 45,
            list_width, list_height
        )
        self.available_list = pygame_gui.elements.UISelectionList(
            relative_rect=available_rect,
            item_list=[],
            manager=self.ui_manager,
            container=self.container,
            allow_multi_select=False
        )
        self.ui_elements.append(self.available_list)
        
        # 並び替えボタン
        order_x = 10 + list_width + 10
        
        # 上へボタン
        up_rect = pygame.Rect(order_x, 100, 40, button_size)
        self.up_button = self._create_button(
            "↑",
            up_rect,
            container=self.container,
            object_id="#move_up_button"
        )
        
        # 下へボタン
        down_rect = pygame.Rect(order_x, 150, 40, button_size)
        self.down_button = self._create_button(
            "↓",
            down_rect,
            container=self.container,
            object_id="#move_down_button"
        )
        
        # パーティ情報ボックス
        info_rect = pygame.Rect(10, 305, self.rect.width - 20, 80)
        self.party_info_box = pygame_gui.elements.UITextBox(
            html_text="<b>パーティ情報</b><br>メンバー: 0/6",
            relative_rect=info_rect,
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.party_info_box)
        
        # 初期データを読み込み
        self._load_party_data()
    
    def _load_party_data(self) -> None:
        """パーティデータを読み込み"""
        # パーティ情報を取得
        result = self._execute_service_action("party_formation", {"action": "get_info"})
        
        if result.is_success() and result.data:
            self.party_members = result.data.get("members", [])
            self._update_party_list()
        
        # 利用可能なキャラクターを取得
        result = self._execute_service_action("character_list", {"filter": "available"})
        
        if result.is_success() and result.data:
            self.available_characters = result.data.get("characters", [])
            self._update_available_list()
        
        self._update_buttons()
        self._update_party_info()
    
    def _update_party_list(self) -> None:
        """パーティリストを更新"""
        if not self.party_list:
            return
        
        # リストアイテムを構築
        items = []
        for i, member in enumerate(self.party_members):
            text = f"{i+1}. {member['name']} Lv{member['level']} {member['class']}"
            items.append(text)
        
        self.party_list.set_item_list(items)
    
    def _update_available_list(self) -> None:
        """利用可能リストを更新"""
        if not self.available_list:
            return
        
        # リストアイテムを構築
        items = []
        for char in self.available_characters:
            text = f"{char['name']} Lv{char['level']} {char['class']}"
            items.append(text)
        
        self.available_list.set_item_list(items)
    
    def _update_buttons(self) -> None:
        """ボタンの有効/無効を更新"""
        # 追加ボタン
        if self.add_button:
            can_add = (len(self.party_members) < 6 and 
                      self.selected_available_index is not None)
            if can_add:
                self.add_button.enable()
            else:
                self.add_button.disable()
        
        # 削除ボタン
        if self.remove_button:
            can_remove = self.selected_party_index is not None
            if can_remove:
                self.remove_button.enable()
            else:
                self.remove_button.disable()
        
        # 上へボタン
        if self.up_button:
            can_move_up = (self.selected_party_index is not None and 
                          self.selected_party_index > 0)
            if can_move_up:
                self.up_button.enable()
            else:
                self.up_button.disable()
        
        # 下へボタン
        if self.down_button:
            can_move_down = (self.selected_party_index is not None and 
                           self.selected_party_index < len(self.party_members) - 1)
            if can_move_down:
                self.down_button.enable()
            else:
                self.down_button.disable()
    
    def _update_party_info(self) -> None:
        """パーティ情報を更新"""
        if not self.party_info_box:
            return
        
        member_count = len(self.party_members)
        
        # パーティ名を取得（あれば）
        party_name = "未編成"
        if member_count > 0:
            # TODO: パーティ名を取得する処理
            party_name = "冒険者パーティ"
        
        # 情報テキストを構築
        info_text = f"<b>パーティ情報</b><br>"
        info_text += f"パーティ名: {party_name}<br>"
        info_text += f"メンバー: {member_count}/6<br>"
        
        if member_count > 0:
            # 前衛/後衛の情報
            front_count = min(3, member_count)
            back_count = max(0, member_count - 3)
            info_text += f"編成: 前衛{front_count}人 / 後衛{back_count}人"
        
        self.party_info_box.html_text = info_text
        self.party_info_box.rebuild()
    
    def _add_member(self) -> None:
        """メンバーを追加"""
        if self.selected_available_index is None:
            return
        
        if self.selected_available_index >= len(self.available_characters):
            return
        
        # 選択されたキャラクターを取得
        character = self.available_characters[self.selected_available_index]
        
        # パーティに追加
        result = self._execute_service_action(
            "party_formation",
            {
                "action": "add_member",
                "character_id": character["id"]
            }
        )
        
        if result.is_success():
            # リストから削除して移動
            self.available_characters.pop(self.selected_available_index)
            self.party_members.append(character)
            
            # UIを更新
            self._update_party_list()
            self._update_available_list()
            self._update_party_info()
            
            # 選択をクリア
            self.selected_available_index = None
            self._update_buttons()
            
            self._show_message(result.message, "info")
        else:
            self._show_message(result.message, "error")
    
    def _remove_member(self) -> None:
        """メンバーを削除"""
        if self.selected_party_index is None:
            return
        
        if self.selected_party_index >= len(self.party_members):
            return
        
        # 選択されたメンバーを取得
        member = self.party_members[self.selected_party_index]
        
        # パーティから削除
        result = self._execute_service_action(
            "party_formation",
            {
                "action": "remove_member",
                "character_id": member["id"]
            }
        )
        
        if result.is_success():
            # リストから削除して移動
            self.party_members.pop(self.selected_party_index)
            self.available_characters.append(member)
            
            # UIを更新
            self._update_party_list()
            self._update_available_list()
            self._update_party_info()
            
            # 選択をクリア
            self.selected_party_index = None
            self._update_buttons()
            
            self._show_message(result.message, "info")
        else:
            self._show_message(result.message, "error")
    
    def _move_member_up(self) -> None:
        """メンバーを上に移動"""
        if self.selected_party_index is None or self.selected_party_index == 0:
            return
        
        # 順序を入れ替え
        index = self.selected_party_index
        self.party_members[index], self.party_members[index-1] = \
            self.party_members[index-1], self.party_members[index]
        
        # 新しい順序を送信
        new_order = [m["id"] for m in self.party_members]
        result = self._execute_service_action(
            "party_formation",
            {
                "action": "reorder",
                "order": new_order
            }
        )
        
        if result.is_success():
            # 選択位置を更新
            self.selected_party_index -= 1
            
            # UIを更新
            self._update_party_list()
            self.party_list.set_selected_index(self.selected_party_index)
            self._update_buttons()
        else:
            # 失敗したら元に戻す
            self.party_members[index], self.party_members[index-1] = \
                self.party_members[index-1], self.party_members[index]
            self._show_message(result.message, "error")
    
    def _move_member_down(self) -> None:
        """メンバーを下に移動"""
        if (self.selected_party_index is None or 
            self.selected_party_index >= len(self.party_members) - 1):
            return
        
        # 順序を入れ替え
        index = self.selected_party_index
        self.party_members[index], self.party_members[index+1] = \
            self.party_members[index+1], self.party_members[index]
        
        # 新しい順序を送信
        new_order = [m["id"] for m in self.party_members]
        result = self._execute_service_action(
            "party_formation",
            {
                "action": "reorder",
                "order": new_order
            }
        )
        
        if result.is_success():
            # 選択位置を更新
            self.selected_party_index += 1
            
            # UIを更新
            self._update_party_list()
            self.party_list.set_selected_index(self.selected_party_index)
            self._update_buttons()
        else:
            # 失敗したら元に戻す
            self.party_members[index], self.party_members[index+1] = \
                self.party_members[index+1], self.party_members[index]
            self._show_message(result.message, "error")
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        if button == self.add_button:
            self._add_member()
            return True
        elif button == self.remove_button:
            self._remove_member()
            return True
        elif button == self.up_button:
            self._move_member_up()
            return True
        elif button == self.down_button:
            self._move_member_down()
            return True
        
        return False
    
    def handle_selection_list_changed(self, event: pygame.event.Event) -> bool:
        """選択リスト変更イベントを処理"""
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.party_list:
                # パーティリストの選択が変更された
                selection = self.party_list.get_single_selection()
                if selection is not None:
                    self.selected_party_index = self.party_list.item_list.index(selection)
                    # 利用可能リストの選択をクリア
                    self.selected_available_index = None
                    if self.available_list:
                        self.available_list.set_selected_index(None)
                else:
                    self.selected_party_index = None
                
                self._update_buttons()
                return True
                
            elif event.ui_element == self.available_list:
                # 利用可能リストの選択が変更された
                selection = self.available_list.get_single_selection()
                if selection is not None:
                    self.selected_available_index = self.available_list.item_list.index(selection)
                    # パーティリストの選択をクリア
                    self.selected_party_index = None
                    if self.party_list:
                        self.party_list.set_selected_index(None)
                else:
                    self.selected_available_index = None
                
                self._update_buttons()
                return True
        
        return False
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        self._load_party_data()