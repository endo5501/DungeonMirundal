"""魔法分析パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
import logging
from ..service_panel import ServicePanel

logger = logging.getLogger(__name__)


class SpellAnalysisPanel(ServicePanel):
    """魔法分析パネル
    
    習得済み魔法の詳細分析を行うパネル。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        # SpellAnalysisPanel固有のUI要素（ServicePanel初期化前に定義）
        self.title_label: Optional[pygame_gui.elements.UILabel] = None
        self.character_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.spell_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.analyze_button: Optional[pygame_gui.elements.UIButton] = None
        self.cost_label: Optional[pygame_gui.elements.UILabel] = None
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        self.result_box: Optional[pygame_gui.elements.UITextBox] = None
        
        # 状態（ServicePanel初期化前に定義）
        self.selected_character: Optional[str] = None
        self.selected_spell: Optional[str] = None
        self.characters_data: List[Dict[str, Any]] = []
        self.spells_data: List[Dict[str, Any]] = []
        
        # ServicePanel初期化
        super().__init__(rect, parent, controller, "spell_analysis", ui_manager)
        
        # 初期データを読み込み
        self._refresh_characters()
        
        logger.info("SpellAnalysisPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        self._create_header()
        self._create_selection_area()
        self._create_action_controls()
        self._create_result_area()
    
    def _create_header(self) -> None:
        """ヘッダー部分を作成"""
        title_rect = pygame.Rect(10, 10, 300, 30)
        
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.title_label = self.ui_element_manager.create_label(
                "title_label", "魔法分析 - キャラクターと魔法を選択", title_rect
            )
        else:
            # フォールバック
            self.title_label = pygame_gui.elements.UILabel(
                relative_rect=title_rect,
                text="魔法分析 - キャラクターと魔法を選択",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.title_label)
    
    def _create_selection_area(self) -> None:
        """選択エリア（キャラクター・魔法リスト）を作成"""
        # キャラクターリスト（左側）
        char_label_rect = pygame.Rect(10, 50, 195, 25)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            char_label = self.ui_element_manager.create_label(
                "char_label", "キャラクター:", char_label_rect
            )
        else:
            # フォールバック
            char_label = pygame_gui.elements.UILabel(
                relative_rect=char_label_rect,
                text="キャラクター:",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(char_label)
        
        char_list_rect = pygame.Rect(10, 80, 195, 120)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.character_list = self.ui_element_manager.create_selection_list(
                "character_list", [], char_list_rect, allow_multi_select=False
            )
        else:
            # フォールバック
            self.character_list = pygame_gui.elements.UISelectionList(
                relative_rect=char_list_rect,
                item_list=[],
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.character_list)
        
        # 魔法リスト（右側）
        spell_label_rect = pygame.Rect(215, 50, 195, 25)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            spell_label = self.ui_element_manager.create_label(
                "spell_label", "習得済み魔法:", spell_label_rect
            )
        else:
            # フォールバック
            spell_label = pygame_gui.elements.UILabel(
                relative_rect=spell_label_rect,
                text="習得済み魔法:",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(spell_label)
        
        spell_list_rect = pygame.Rect(215, 80, 195, 120)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.spell_list = self.ui_element_manager.create_selection_list(
                "spell_list", [], spell_list_rect, allow_multi_select=False
            )
        else:
            # フォールバック
            self.spell_list = pygame_gui.elements.UISelectionList(
                relative_rect=spell_list_rect,
                item_list=[],
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.spell_list)
    
    def _create_action_controls(self) -> None:
        """アクションコントロール（ボタン・ラベル）を作成"""
        # 分析ボタン
        analyze_button_rect = pygame.Rect(10, 210, 100, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.analyze_button = self.ui_element_manager.create_button(
                "analyze_button", "分析", analyze_button_rect
            )
        else:
            # フォールバック
            self.analyze_button = pygame_gui.elements.UIButton(
                relative_rect=analyze_button_rect,
                text="分析",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.analyze_button)
        
        # 初期状態は無効化
        if self.analyze_button:
            self.analyze_button.disable()
        
        # コスト表示
        cost_label_rect = pygame.Rect(120, 210, 150, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.cost_label = self.ui_element_manager.create_label(
                "cost_label", "費用: -", cost_label_rect
            )
        else:
            # フォールバック
            self.cost_label = pygame_gui.elements.UILabel(
                relative_rect=cost_label_rect,
                text="費用: -",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.cost_label)
        
        # 所持金表示
        gold_label_rect = pygame.Rect(280, 210, 130, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.gold_label = self.ui_element_manager.create_label(
                "gold_label", "所持金: 0 G", gold_label_rect
            )
        else:
            # フォールバック
            self.gold_label = pygame_gui.elements.UILabel(
                relative_rect=gold_label_rect,
                text="所持金: 0 G",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.gold_label)
    
    def _create_result_area(self) -> None:
        """結果表示エリアを作成"""
        result_rect = pygame.Rect(10, 250, 400, 150)
        
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.result_box = self.ui_element_manager.create_text_box(
                "result_box", "", result_rect
            )
        else:
            # フォールバック
            self.result_box = pygame_gui.elements.UITextBox(
                html_text="",
                relative_rect=result_rect,
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.result_box)
    
    def _refresh_characters(self) -> None:
        """キャラクターリストを更新"""
        # 魔法を持つキャラクターを取得
        result = self._execute_service_action("analyze_magic", {})
        
        if result.is_success() and result.data:
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
        result = self._execute_service_action("analyze_magic", {
            "character_id": character_id
        })
        
        if result.is_success() and result.data:
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
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理（後方互換性のため）"""
        # ボタンイベント処理
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.analyze_button:
                return self.handle_button_click(event.ui_element)
        
        # 選択リストイベント処理
        elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            return self.handle_selection_list_changed(event)
        
        return False
    
    def _perform_analysis(self) -> None:
        """分析を実行"""
        if not self.selected_character or not self.selected_spell:
            return
        
        # 確認
        result = self._execute_service_action("analyze_magic", {
            "character_id": self.selected_character,
            "spell_id": self.selected_spell
        })
        
        if result.is_success() and result.result_type.name == "CONFIRM":
            # 確認後実行
            result = self._execute_service_action("analyze_magic", {
                "character_id": self.selected_character,
                "spell_id": self.selected_spell,
                "confirmed": True
            })
            
            # 結果を表示
            if result.is_success():
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
            
            if result.is_success():
                # 成功時は金額を更新
                self.gold_label.set_text(f"所持金: {result.data.get('remaining_gold', 0)} G")
        else:
            # エラーメッセージを表示
            self.result_box.html_text = f"<font color='#FF0000'>{result.message}</font>"
            self.result_box.rebuild()
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理（ServicePanelパターン）"""
        if button == self.analyze_button:
            self._perform_analysis()
            return True
        
        return False
    
    def handle_selection_list_changed(self, event: pygame.event.Event) -> bool:
        """選択リスト変更イベントを処理"""
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
                    if self.analyze_button:
                        self.analyze_button.disable()
                    if self.cost_label:
                        self.cost_label.set_text("費用: -")
                return True
            
            elif event.ui_element == self.spell_list:
                # 魔法が選択された
                selection_index = self.spell_list.get_single_selection()
                if selection_index is not None and selection_index < len(self.spells_data):
                    selected_spell = self.spells_data[selection_index]
                    self.selected_spell = selected_spell["id"]
                    
                    # コスト表示を更新
                    if self.cost_label:
                        self.cost_label.set_text(f"費用: {selected_spell['cost']} G")
                    
                    # 分析ボタンを有効化
                    if self.analyze_button:
                        self.analyze_button.enable()
                    
                    # 結果をクリア
                    if self.result_box:
                        self.result_box.html_text = ""
                        self.result_box.rebuild()
                return True
        
        return False
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        self._refresh_characters()
        self.selected_character = None
        self.selected_spell = None
        if self.spell_list:
            self.spell_list.set_item_list([])
        if self.analyze_button:
            self.analyze_button.disable()
        if self.cost_label:
            self.cost_label.set_text("費用: -")
        if self.result_box:
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
        # SpellAnalysisPanel固有のクリーンアップ
        self.title_label = None
        self.character_list = None
        self.spell_list = None
        self.analyze_button = None
        self.cost_label = None
        self.gold_label = None
        self.result_box = None
        
        # 状態をクリア
        self.selected_character = None
        self.selected_spell = None
        self.characters_data = []
        self.spells_data = []
        
        # ServicePanelの基本破棄処理を呼び出し
        super().destroy()
        
        logger.info("SpellAnalysisPanel destroyed")