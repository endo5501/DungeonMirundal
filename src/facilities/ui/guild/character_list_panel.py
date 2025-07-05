"""キャラクター一覧パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
import logging
from ..service_panel import ServicePanel
from ...core.service_result import ServiceResult

logger = logging.getLogger(__name__)


class CharacterListPanel(ServicePanel):
    """キャラクター一覧パネル
    
    登録されているキャラクターの一覧表示と詳細情報を提供するパネル。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        super().__init__(rect, parent, controller, "character_list", ui_manager)
        
        # UI要素
        self.filter_dropdown: Optional[pygame_gui.elements.UIDropDownMenu] = None
        self.sort_dropdown: Optional[pygame_gui.elements.UIDropDownMenu] = None
        self.character_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.detail_box: Optional[pygame_gui.elements.UITextBox] = None
        self.action_button: Optional[pygame_gui.elements.UIButton] = None
        
        # データ
        self.characters: List[Dict[str, Any]] = []
        self.selected_character: Optional[Dict[str, Any]] = None
        self.selected_index: Optional[int] = None
        self.current_filter = "all"
        self.current_sort = "name"
        
        logger.info("CharacterListPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        # レイアウト定数
        filter_width = 150
        dropdown_height = 30
        list_width = (self.rect.width - 30) // 2
        list_height = 300
        
        # フィルターラベル
        filter_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 60, dropdown_height),
            text="表示:",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(filter_label)
        
        # フィルタードロップダウン
        filter_rect = pygame.Rect(75, 10, filter_width, dropdown_height)
        filter_options = ["全員", "パーティ外", "パーティ内"]
        self.filter_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=filter_options,
            starting_option="全員",
            relative_rect=filter_rect,
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.filter_dropdown)
        
        # ソートラベル
        sort_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(240, 10, 60, dropdown_height),
            text="並び順:",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(sort_label)
        
        # ソートドロップダウン
        sort_rect = pygame.Rect(305, 10, filter_width, dropdown_height)
        sort_options = ["名前順", "レベル順", "職業順"]
        self.sort_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=sort_options,
            starting_option="名前順",
            relative_rect=sort_rect,
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.sort_dropdown)
        
        # キャラクターリスト
        list_rect = pygame.Rect(10, 50, list_width, list_height)
        self.character_list = pygame_gui.elements.UISelectionList(
            relative_rect=list_rect,
            item_list=[],
            manager=self.ui_manager,
            container=self.container,
            allow_multi_select=False
        )
        self.ui_elements.append(self.character_list)
        
        # 詳細表示ボックス
        detail_rect = pygame.Rect(
            list_width + 20, 50,
            self.rect.width - list_width - 30, list_height
        )
        self.detail_box = pygame_gui.elements.UITextBox(
            html_text="<b>キャラクター詳細</b><br>キャラクターを選択してください",
            relative_rect=detail_rect,
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.detail_box)
        
        # アクションボタン（クラス変更など）
        button_rect = pygame.Rect(
            self.rect.width - 140, 360,
            130, 35
        )
        self.action_button = self._create_button(
            "クラス変更",
            button_rect,
            container=self.container,
            object_id="#action_button"
        )
        self.action_button.disable()  # 初期状態は無効
        
        # 初期データを読み込み
        self._load_character_data()
    
    def _load_character_data(self) -> None:
        """キャラクターデータを読み込み"""
        # フィルターとソート設定を適用してデータを取得
        params = {
            "filter": self.current_filter,
            "sort": self.current_sort
        }
        
        result = self._execute_service_action("character_list", params)
        
        if result.is_success() and result.data:
            self.characters = result.data.get("characters", [])
            self._update_character_list()
            
            # 選択をクリア
            self.selected_character = None
            self.selected_index = None
            self._update_detail_view()
            self._update_action_button()
    
    def _update_character_list(self) -> None:
        """キャラクターリストを更新"""
        if not self.character_list:
            return
        
        # リストアイテムを構築
        items = []
        for char in self.characters:
            # パーティ内マーク
            party_mark = "●" if char.get("in_party", False) else "  "
            
            # ステータス表示
            status_mark = ""
            if char.get("status") != "normal":
                status_mark = f" [{char['status']}]"
            
            text = f"{party_mark} {char['name']} Lv{char['level']} {char['class']}{status_mark}"
            items.append(text)
        
        self.character_list.set_item_list(items)
    
    def _update_detail_view(self) -> None:
        """詳細ビューを更新"""
        if not self.detail_box:
            return
        
        if not self.selected_character:
            self.detail_box.html_text = "<b>キャラクター詳細</b><br>キャラクターを選択してください"
            self.detail_box.rebuild()
            return
        
        char = self.selected_character
        
        # 種族名の日本語化
        race_names = {
            "human": "人間", "elf": "エルフ", "dwarf": "ドワーフ",
            "gnome": "ノーム", "hobbit": "ホビット"
        }
        
        # 職業名の日本語化
        class_names = {
            "fighter": "戦士", "priest": "僧侶", "thief": "盗賊",
            "mage": "魔法使い", "bishop": "司教", "samurai": "侍",
            "lord": "君主", "ninja": "忍者"
        }
        
        # ステータスの日本語化
        status_names = {
            "normal": "正常", "poison": "毒", "paralysis": "麻痺",
            "petrification": "石化", "dead": "死亡", "ashes": "灰"
        }
        
        # 詳細テキストを構築
        detail_text = f"<b>{char['name']}</b><br>"
        detail_text += f"<b>基本情報</b><br>"
        detail_text += f"レベル: {char['level']}<br>"
        detail_text += f"種族: {race_names.get(char['race'], char['race'])}<br>"
        detail_text += f"職業: {class_names.get(char['class'], char['class'])}<br>"
        detail_text += f"<br>"
        detail_text += f"<b>ステータス</b><br>"
        detail_text += f"HP: {char['hp']}<br>"
        detail_text += f"MP: {char['mp']}<br>"
        detail_text += f"状態: {status_names.get(char['status'], char['status'])}<br>"
        
        if char.get("in_party", False):
            detail_text += f"<br><font color='#00aa00'>パーティメンバー</font>"
        
        # TODO: 能力値、装備、スキルなどの詳細情報を追加
        
        self.detail_box.html_text = detail_text
        self.detail_box.rebuild()
    
    def _update_action_button(self) -> None:
        """アクションボタンを更新"""
        if not self.action_button or not self.selected_character:
            if self.action_button:
                self.action_button.disable()
            return
        
        char = self.selected_character
        
        # クラス変更可能かチェック（レベル5以上）
        if char.get("level", 1) >= 5:
            self.action_button.enable()
            self.action_button.set_text("クラス変更")
        else:
            self.action_button.disable()
            self.action_button.set_text("クラス変更（Lv5必要）")
    
    def _handle_filter_change(self, selected_option: str) -> None:
        """フィルター変更を処理"""
        # フィルター値をマッピング
        filter_map = {
            "全員": "all",
            "パーティ外": "available",
            "パーティ内": "in_party"
        }
        
        new_filter = filter_map.get(selected_option, "all")
        if new_filter != self.current_filter:
            self.current_filter = new_filter
            self._load_character_data()
    
    def _handle_sort_change(self, selected_option: str) -> None:
        """ソート変更を処理"""
        # ソート値をマッピング
        sort_map = {
            "名前順": "name",
            "レベル順": "level",
            "職業順": "class"
        }
        
        new_sort = sort_map.get(selected_option, "name")
        if new_sort != self.current_sort:
            self.current_sort = new_sort
            self._load_character_data()
    
    def _handle_character_selection(self, selection: Optional[str]) -> None:
        """キャラクター選択を処理"""
        if not selection:
            self.selected_character = None
            self.selected_index = None
        else:
            # 選択されたインデックスを取得
            index = self.character_list.item_list.index(selection)
            if 0 <= index < len(self.characters):
                self.selected_index = index
                self.selected_character = self.characters[index]
            else:
                self.selected_character = None
                self.selected_index = None
        
        # UIを更新
        self._update_detail_view()
        self._update_action_button()
    
    def _handle_class_change(self) -> None:
        """クラス変更を処理"""
        if not self.selected_character:
            return
        
        # TODO: クラス変更ダイアログを表示
        # 現時点では単純にクラス変更画面への遷移をリクエスト
        character_id = self.selected_character["id"]
        result = self._execute_service_action(
            "class_change",
            {"character_id": character_id}
        )
        
        if result.is_success():
            self._show_message("クラス変更画面を表示します", "info")
            # TODO: クラス変更UIの実装
        else:
            self._show_message(result.message, "error")
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        if button == self.action_button:
            self._handle_class_change()
            return True
        
        return False
    
    def handle_dropdown_changed(self, event: pygame.event.Event) -> bool:
        """ドロップダウン変更イベントを処理"""
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.filter_dropdown:
                self._handle_filter_change(event.text)
                return True
            elif event.ui_element == self.sort_dropdown:
                self._handle_sort_change(event.text)
                return True
        
        return False
    
    def handle_selection_list_changed(self, event: pygame.event.Event) -> bool:
        """選択リスト変更イベントを処理"""
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.character_list:
                selection = self.character_list.get_single_selection()
                self._handle_character_selection(selection)
                return True
        
        return False
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        self._load_character_data()
    
    def get_selected_character(self) -> Optional[Dict[str, Any]]:
        """選択されているキャラクターを取得"""
        return self.selected_character