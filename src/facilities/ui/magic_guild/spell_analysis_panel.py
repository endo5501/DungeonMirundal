"""魔法分析パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class SpellAnalysisPanel:
    """魔法分析パネル
    
    習得済み魔法の詳細分析を行うパネル。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.UIPanel,
                 ui_manager: pygame_gui.UIManager, controller, service):
        """初期化"""
        self.rect = rect
        self.parent = parent
        self.ui_manager = ui_manager
        self.controller = controller
        self.service = service
        
        # UI要素
        self.container: Optional[pygame_gui.UIPanel] = None
        self.title_label: Optional[pygame_gui.elements.UILabel] = None
        self.character_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.spell_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.analyze_button: Optional[pygame_gui.elements.UIButton] = None
        self.cost_label: Optional[pygame_gui.elements.UILabel] = None
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        self.result_box: Optional[pygame_gui.elements.UITextBox] = None
        
        # 状態
        self.selected_character: Optional[str] = None
        self.selected_spell: Optional[str] = None
        self.characters_data: List[Dict[str, Any]] = []
        self.spells_data: List[Dict[str, Any]] = []
        
        self._create_ui()
        self._refresh_characters()
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        self.container = pygame_gui.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager,
            container=self.parent
        )
        
        # タイトル
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 300, 30),
            text="魔法分析 - キャラクターと魔法を選択",
            manager=self.ui_manager,
            container=self.container
        )
        
        # キャラクターリスト（左側）
        char_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 50, 195, 25),
            text="キャラクター:",
            manager=self.ui_manager,
            container=self.container
        )
        
        self.character_list = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(10, 80, 195, 120),
            item_list=[],
            manager=self.ui_manager,
            container=self.container
        )
        
        # 魔法リスト（右側）
        spell_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(215, 50, 195, 25),
            text="習得済み魔法:",
            manager=self.ui_manager,
            container=self.container
        )
        
        self.spell_list = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(215, 80, 195, 120),
            item_list=[],
            manager=self.ui_manager,
            container=self.container
        )
        
        # 分析ボタン
        self.analyze_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 210, 100, 30),
            text="分析",
            manager=self.ui_manager,
            container=self.container
        )
        self.analyze_button.disable()
        
        # コスト表示
        self.cost_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(120, 210, 150, 30),
            text="費用: -",
            manager=self.ui_manager,
            container=self.container
        )
        
        # 所持金表示
        self.gold_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(280, 210, 130, 30),
            text="所持金: 0 G",
            manager=self.ui_manager,
            container=self.container
        )
        
        # 分析結果表示
        self.result_box = pygame_gui.elements.UITextBox(
            html_text="",
            relative_rect=pygame.Rect(10, 250, 400, 150),
            manager=self.ui_manager,
            container=self.container
        )
    
    def _refresh_characters(self) -> None:
        """キャラクターリストを更新"""
        # 魔法を持つキャラクターを取得
        result = self.service.execute_action("analyze_magic", {})
        
        if result.success and result.data:
            self.characters_data = result.data.get("characters", [])
            
            # リスト項目を作成
            char_items = []
            for char in self.characters_data:
                item_text = f"{char['name']} ({char['spell_count']}魔法)"
                char_items.append(item_text)
            
            # UIリストを更新
            self.character_list.set_item_list(char_items)
            
            # 結果メッセージを更新
            if result.message:
                self.result_box.html_text = result.message
                self.result_box.rebuild()
        else:
            self.character_list.set_item_list([])
            message = result.message if result.message else "魔法を持つキャラクターがいません"
            self.result_box.html_text = message
            self.result_box.rebuild()
    
    def _refresh_spells(self, character_id: str) -> None:
        """魔法リストを更新"""
        # キャラクターの魔法を取得
        result = self.service.execute_action("analyze_magic", {
            "character_id": character_id
        })
        
        if result.success and result.data:
            self.spells_data = result.data.get("spells", [])
            party_gold = result.data.get("party_gold", 0)
            
            # リスト項目を作成
            spell_items = []
            for spell in self.spells_data:
                item_text = f"Lv{spell['level']} {spell['name']} - {spell['cost']}G"
                spell_items.append(item_text)
            
            # UIリストを更新
            self.spell_list.set_item_list(spell_items)
            
            # 所持金を更新
            self.gold_label.set_text(f"所持金: {party_gold} G")
            
            # 結果をクリア
            self.result_box.html_text = ""
            self.result_box.rebuild()
        else:
            self.spell_list.set_item_list([])
            self.result_box.html_text = result.message if result.message else ""
            self.result_box.rebuild()
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """イベントを処理"""
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.character_list:
                # キャラクターが選択された
                selection_index = self.character_list.get_single_selection()
                if selection_index is not None and selection_index < len(self.characters_data):
                    selected_char = self.characters_data[selection_index]
                    self.selected_character = selected_char["id"]
                    
                    # 魔法リストを更新
                    self._refresh_spells(self.selected_character)
                    
                    # 魔法選択をリセット
                    self.selected_spell = None
                    self.analyze_button.disable()
                    self.cost_label.set_text("費用: -")
            
            elif event.ui_element == self.spell_list:
                # 魔法が選択された
                selection_index = self.spell_list.get_single_selection()
                if selection_index is not None and selection_index < len(self.spells_data):
                    selected_spell = self.spells_data[selection_index]
                    self.selected_spell = selected_spell["id"]
                    
                    # コスト表示を更新
                    self.cost_label.set_text(f"費用: {selected_spell['cost']} G")
                    
                    # 分析ボタンを有効化
                    self.analyze_button.enable()
                    
                    # 結果をクリア
                    self.result_box.html_text = ""
                    self.result_box.rebuild()
        
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.analyze_button:
                self._perform_analysis()
    
    def _perform_analysis(self) -> None:
        """分析を実行"""
        if not self.selected_character or not self.selected_spell:
            return
        
        # 確認
        result = self.service.execute_action("analyze_magic", {
            "character_id": self.selected_character,
            "spell_id": self.selected_spell
        })
        
        if result.success and result.result_type.name == "CONFIRM":
            # 確認後実行
            result = self.service.execute_action("analyze_magic", {
                "character_id": self.selected_character,
                "spell_id": self.selected_spell,
                "confirmed": True
            })
            
            # 結果を表示
            if result.success:
                result_text = f"""
                <b>魔法分析結果</b><br>
                <br>
                {result.message.replace('\n', '<br>')}<br>
                <br>
                <i>残り所持金: {result.data.get('remaining_gold', 0)} G</i>
                """
                self.result_box.html_text = result_text.strip()
            else:
                self.result_box.html_text = f"<font color='#FF0000'>{result.message}</font>"
            
            self.result_box.rebuild()
            
            if result.success:
                # 成功時は金額を更新
                self.gold_label.set_text(f"所持金: {result.data.get('remaining_gold', 0)} G")
        else:
            # エラーメッセージを表示
            self.result_box.html_text = f"<font color='#FF0000'>{result.message}</font>"
            self.result_box.rebuild()
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        self._refresh_characters()
        self.selected_character = None
        self.selected_spell = None
        self.spell_list.set_item_list([])
        self.analyze_button.disable()
        self.cost_label.set_text("費用: -")
        self.result_box.html_text = ""
        self.result_box.rebuild()
    
    def show(self) -> None:
        """パネルを表示"""
        if self.container:
            self.container.show()
    
    def hide(self) -> None:
        """パネルを非表示"""
        if self.container:
            self.container.hide()
    
    def destroy(self) -> None:
        """パネルを破棄"""
        if self.container:
            self.container.kill()