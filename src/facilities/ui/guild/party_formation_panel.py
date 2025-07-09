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
        # UI要素（super().__init__の前に定義）
        self.party_list_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.available_list_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.party_buttons: List[pygame_gui.elements.UIButton] = []
        self.available_buttons: List[pygame_gui.elements.UIButton] = []
        self.add_button: Optional[pygame_gui.elements.UIButton] = None
        self.remove_button: Optional[pygame_gui.elements.UIButton] = None
        self.up_button: Optional[pygame_gui.elements.UIButton] = None
        self.down_button: Optional[pygame_gui.elements.UIButton] = None
        self.party_info_box: Optional[pygame_gui.elements.UITextBox] = None
        
        # データ（super().__init__の前に定義）
        self.party_members: List[Dict[str, Any]] = []
        self.available_characters: List[Dict[str, Any]] = []
        self.selected_party_index: Optional[int] = None
        self.selected_available_index: Optional[int] = None
        
        super().__init__(rect, parent, controller, "party_formation", ui_manager)
        
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
        
        # パーティメンバーリスト（パネルとして実装）
        party_rect = pygame.Rect(10, 45, list_width, list_height)
        self.party_list_panel = pygame_gui.elements.UIPanel(
            relative_rect=party_rect,
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.party_list_panel)
        
        # パーティメンバーボタンリスト
        self.party_buttons: List[pygame_gui.elements.UIButton] = []
        
        # 中央のボタン群（パーティ⇔利用可能の移動ボタン）
        # パネル幅を考慮して真ん中に配置
        transfer_button_x = (self.rect.width - 100) // 2
        
        # 追加ボタン（→）
        add_rect = pygame.Rect(transfer_button_x, 120, 100, button_size)
        self.add_button = self._create_button(
            "追加 → (A)",
            add_rect,
            container=self.container,
            object_id="#add_member_button"
        )
        
        # 削除ボタン（←）
        remove_rect = pygame.Rect(transfer_button_x, 170, 100, button_size)
        self.remove_button = self._create_button(
            "← 削除 (R)",
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
        
        # 利用可能キャラクターリスト（パネルとして実装）
        available_rect = pygame.Rect(
            self.rect.width - list_width - 10, 45,
            list_width, list_height
        )
        self.available_list_panel = pygame_gui.elements.UIPanel(
            relative_rect=available_rect,
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.available_list_panel)
        
        # 利用可能キャラクターボタンリスト
        self.available_buttons: List[pygame_gui.elements.UIButton] = []
        
        # 並び替えボタン（パーティリストの右側に配置）
        # パーティリストの右端 + 少し間隔を開ける
        order_x = 10 + list_width + 10
        
        # 上へボタン（↑） - 中央の移動ボタンと同じ高さに配置
        up_rect = pygame.Rect(order_x, 100, 80, button_size)
        self.up_button = self._create_button(
            "↑ 上へ (U)",
            up_rect,
            container=self.container,
            object_id="#move_up_button"
        )
        
        # 下へボタン（↓） - 適切な間隔で配置
        down_rect = pygame.Rect(order_x, 150, 80, button_size)
        self.down_button = self._create_button(
            "↓ 下へ (D)",
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
        
        # ボタンの初期状態を設定
        logger.info(f"[DEBUG] Initial button state: add_button={self.add_button}, remove_button={self.remove_button}")
    
    def _load_party_data(self) -> None:
        """パーティデータを読み込み"""
        logger.info("[DEBUG] _load_party_data called")
        
        # パーティ情報を取得
        result = self._execute_service_action("party_formation", {"action": "get_info"})
        logger.info(f"[DEBUG] Party info result: {result}")
        
        if result.is_success() and result.data:
            self.party_members = result.data.get("members", [])
            logger.info(f"[DEBUG] Loaded party members: {len(self.party_members)}")
            self._update_party_list()
        
        # 利用可能なキャラクターを取得
        result = self._execute_service_action("character_list", {"filter": "available"})
        logger.info(f"[DEBUG] Available characters result: {result}")
        
        if result.is_success() and result.data:
            self.available_characters = result.data.get("characters", [])
            logger.info(f"[DEBUG] Loaded available characters: {len(self.available_characters)}")
            for i, char in enumerate(self.available_characters):
                logger.info(f"[DEBUG] Character {i}: {char}")
            self._update_available_list()
        
        self._update_buttons()
        self._update_party_info()
    
    def _update_party_list(self) -> None:
        """パーティリストを更新"""
        if not self.party_list_panel:
            return
        
        # 既存のボタンを削除
        for button in self.party_buttons:
            button.kill()
        self.party_buttons.clear()
        
        # パーティメンバーのボタンを作成
        button_height = 35
        button_spacing = 5
        for i, member in enumerate(self.party_members):
            text = f"{i+1}. {member['name']} Lv{member['level']} {member['class']}"
            button_rect = pygame.Rect(5, 5 + i * (button_height + button_spacing), 
                                    self.party_list_panel.relative_rect.width - 10, button_height)
            
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=text,
                manager=self.ui_manager,
                container=self.party_list_panel,
                object_id=f"#party_member_{i}"
            )
            
            self.party_buttons.append(button)
            self.ui_elements.append(button)
    
    def _update_available_list(self) -> None:
        """利用可能リストを更新"""
        if not self.available_list_panel:
            return
        
        # 既存のボタンを削除
        for button in self.available_buttons:
            button.kill()
        self.available_buttons.clear()
        
        # 利用可能キャラクターのボタンを作成
        button_height = 35
        button_spacing = 5
        for i, char in enumerate(self.available_characters):
            text = f"{char['name']} Lv{char['level']} {char['class']}"
            button_rect = pygame.Rect(5, 5 + i * (button_height + button_spacing), 
                                    self.available_list_panel.relative_rect.width - 10, button_height)
            
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=text,
                manager=self.ui_manager,
                container=self.available_list_panel,
                object_id=f"#available_character_{i}"
            )
            
            self.available_buttons.append(button)
            self.ui_elements.append(button)
    
    def _update_buttons(self) -> None:
        """ボタンの有効/無効を更新"""
        logger.info(f"[DEBUG] _update_buttons called: selected_available_index={self.selected_available_index}, selected_party_index={self.selected_party_index}")
        logger.info(f"[DEBUG] Party members: {len(self.party_members)}, Available: {len(self.available_characters)}")
        
        # 追加ボタン
        if self.add_button:
            can_add = (len(self.party_members) < 6 and 
                      self.selected_available_index is not None)
            logger.info(f"[DEBUG] Add button: can_add={can_add}")
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
        logger.info(f"[DEBUG] _add_member called: selected_available_index={self.selected_available_index}")
        
        if self.selected_available_index is None:
            logger.warning("[DEBUG] _add_member: selected_available_index is None")
            return
        
        if self.selected_available_index >= len(self.available_characters):
            logger.warning(f"[DEBUG] _add_member: invalid index {self.selected_available_index} >= {len(self.available_characters)}")
            return
        
        # 選択されたキャラクターを取得
        character = self.available_characters[self.selected_available_index]
        logger.info(f"[DEBUG] _add_member: adding character {character}")
        
        # パーティに追加
        result = self._execute_service_action(
            "party_formation",
            {
                "action": "add_member",
                "character_id": character["id"]
            }
        )
        
        logger.info(f"[DEBUG] _add_member: service result = {result}")
        
        if result.is_success():
            # サービスが追加処理を行った後、データを再読み込み
            self._load_party_data()
            
            # 選択をクリア
            self.selected_available_index = None
            self._update_buttons()
            
            self._show_message(result.message, "info")
        else:
            logger.error(f"[DEBUG] _add_member: failed with message: {result.message}")
            self._show_message(result.message, "error")
    
    def _remove_member(self) -> None:
        """メンバーを削除"""
        if self.selected_party_index is None:
            return
        
        # パーティが空の場合は何もしない
        if len(self.party_members) == 0:
            self.selected_party_index = None
            self._update_buttons()
            return
        
        if self.selected_party_index >= len(self.party_members):
            self.selected_party_index = None
            self._update_buttons()
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
            # サービスが削除処理を行った後、データを再読み込み
            self._load_party_data()
            
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
            self._highlight_selected_buttons()
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
            self._highlight_selected_buttons()
            self._update_buttons()
        else:
            # 失敗したら元に戻す
            self.party_members[index], self.party_members[index+1] = \
                self.party_members[index+1], self.party_members[index]
            self._show_message(result.message, "error")
    
    def handle_key_event(self, event: pygame.event.Event) -> bool:
        """キーボードショートカットを処理"""
        if event.type != pygame.KEYDOWN:
            return False
        
        key = event.key
        if key == pygame.K_a:
            # 追加ボタン（→）
            if self.add_button and self.add_button.is_enabled:
                self._add_member()
                return True
        elif key == pygame.K_r:
            # 削除ボタン（←）
            if self.remove_button and self.remove_button.is_enabled:
                self._remove_member()
                return True
        elif key == pygame.K_u:
            # 上へボタン（↑）
            if self.up_button and self.up_button.is_enabled:
                self._move_member_up()
                return True
        elif key == pygame.K_d:
            # 下へボタン（↓）
            if self.down_button and self.down_button.is_enabled:
                self._move_member_down()
                return True
        
        return False
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        logger.info(f"[DEBUG] PartyFormationPanel: handle_button_click called with button: {button}")
        
        if button == self.add_button:
            logger.info("[DEBUG] Add button clicked")
            self._add_member()
            return True
        elif button == self.remove_button:
            logger.info("[DEBUG] Remove button clicked")
            self._remove_member()
            return True
        elif button == self.up_button:
            logger.info("[DEBUG] Up button clicked")
            self._move_member_up()
            return True
        elif button == self.down_button:
            logger.info("[DEBUG] Down button clicked")
            self._move_member_down()
            return True
        
        # パーティメンバーボタンのクリック
        for i, party_button in enumerate(self.party_buttons):
            if button == party_button:
                logger.info(f"[DEBUG] Party member button {i} clicked")
                self.selected_party_index = i
                self.selected_available_index = None
                self._highlight_selected_buttons()
                self._update_buttons()
                return True
        
        # 利用可能キャラクターボタンのクリック
        for i, available_button in enumerate(self.available_buttons):
            if button == available_button:
                logger.info(f"[DEBUG] Available character button {i} clicked")
                self.selected_available_index = i
                self.selected_party_index = None
                self._highlight_selected_buttons()
                self._update_buttons()
                return True
        
        logger.info(f"[DEBUG] Button not handled: {button}")
        return False
    
    def _highlight_selected_buttons(self) -> None:
        """選択されたボタンをハイライト"""
        logger.info(f"[DEBUG] _highlight_selected_buttons called")
        
        # すべてのボタンの通常色に戻す
        for button in self.party_buttons:
            button.colours['normal_bg'] = pygame.Color('#25292e')
            button.rebuild()
            
        for button in self.available_buttons:
            button.colours['normal_bg'] = pygame.Color('#25292e')
            button.rebuild()
        
        # 選択されたパーティメンバーボタンをハイライト
        if self.selected_party_index is not None and self.selected_party_index < len(self.party_buttons):
            button = self.party_buttons[self.selected_party_index]
            button.colours['normal_bg'] = pygame.Color('#4a5a6a')  # 選択色
            button.rebuild()
            logger.info(f"[DEBUG] Highlighted party button at index {self.selected_party_index}")
        
        # 選択された利用可能キャラクターボタンをハイライト
        if self.selected_available_index is not None and self.selected_available_index < len(self.available_buttons):
            button = self.available_buttons[self.selected_available_index]
            button.colours['normal_bg'] = pygame.Color('#4a5a6a')  # 選択色
            button.rebuild()
            logger.info(f"[DEBUG] Highlighted available button at index {self.selected_available_index}")
    
    def handle_selection_list_changed(self, event: pygame.event.Event) -> bool:
        """選択リスト変更イベントを処理（UISelectionListが削除されたため不要）"""
        # UISelectionListを使わないため、このメソッドは不要
        return False
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        self._load_party_data()