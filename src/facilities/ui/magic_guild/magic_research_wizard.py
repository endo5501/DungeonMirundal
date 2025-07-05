"""魔法研究ウィザード"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ResearchStep(Enum):
    """研究ステップ"""
    SELECT_RESEARCHER = 1
    SELECT_TYPE = 2
    CONFIGURE = 3
    CONFIRM = 4


class MagicResearchWizard:
    """魔法研究ウィザード
    
    高度な魔法研究をウィザード形式で行うパネル。
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
        self.step_indicator: Optional[pygame_gui.UIPanel] = None
        self.content_panel: Optional[pygame_gui.UIPanel] = None
        self.next_button: Optional[pygame_gui.elements.UIButton] = None
        self.back_button: Optional[pygame_gui.elements.UIButton] = None
        self.cancel_button: Optional[pygame_gui.elements.UIButton] = None
        
        # ステップごとのUI要素
        self.step_uis: Dict[ResearchStep, Dict[str, Any]] = {}
        
        # 状態
        self.current_step = ResearchStep.SELECT_RESEARCHER
        self.research_data: Dict[str, Any] = {}
        
        self._create_ui()
        self._show_current_step()
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        self.container = pygame_gui.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager,
            container=self.parent
        )
        
        # ステップインジケーター
        self._create_step_indicator()
        
        # コンテンツエリア
        self.content_panel = pygame_gui.UIPanel(
            relative_rect=pygame.Rect(10, 80, 410, 280),
            manager=self.ui_manager,
            container=self.container
        )
        
        # ナビゲーションボタン
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 370, 80, 30),
            text="戻る",
            manager=self.ui_manager,
            container=self.container
        )
        self.back_button.disable()
        
        self.next_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(100, 370, 80, 30),
            text="次へ",
            manager=self.ui_manager,
            container=self.container
        )
        
        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(340, 370, 80, 30),
            text="キャンセル",
            manager=self.ui_manager,
            container=self.container
        )
        
        # 各ステップのUI要素を作成
        self._create_step_uis()
    
    def _create_step_indicator(self) -> None:
        """ステップインジケーターを作成"""
        self.step_indicator = pygame_gui.UIPanel(
            relative_rect=pygame.Rect(10, 10, 410, 60),
            manager=self.ui_manager,
            container=self.container
        )
        
        steps = [
            ("研究者選択", ResearchStep.SELECT_RESEARCHER),
            ("研究種別", ResearchStep.SELECT_TYPE),
            ("詳細設定", ResearchStep.CONFIGURE),
            ("確認", ResearchStep.CONFIRM)
        ]
        
        step_width = 410 // len(steps)
        for i, (name, step) in enumerate(steps):
            # ステップ状態に応じた表示
            if step.value < self.current_step.value:
                text = f"✓ {name}"
                color = "#28a745"  # 完了済み - 緑
            elif step == self.current_step:
                text = f"▶ {name}"
                color = "#007bff"  # 現在 - 青
            else:
                text = f"○ {name}"
                color = "#6c757d"  # 未完了 - グレー
            
            label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(i * step_width, 20, step_width, 20),
                text=text,
                manager=self.ui_manager,
                container=self.step_indicator
            )
    
    def _create_step_uis(self) -> None:
        """各ステップのUI要素を作成"""
        # 研究者選択
        self._create_researcher_selection_ui()
        
        # 研究種別選択
        self._create_research_type_ui()
        
        # 詳細設定
        self._create_configure_ui()
        
        # 確認
        self._create_confirm_ui()
    
    def _create_researcher_selection_ui(self) -> None:
        """研究者選択UIを作成"""
        ui_elements = {}
        
        # タイトル
        ui_elements['title'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 390, 30),
            text="魔法研究を行う研究者を選択してください",
            manager=self.ui_manager,
            container=self.content_panel
        )
        
        # 研究者リスト
        ui_elements['researcher_list'] = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(10, 50, 390, 220),
            item_list=[],
            manager=self.ui_manager,
            container=self.content_panel
        )
        
        self.step_uis[ResearchStep.SELECT_RESEARCHER] = ui_elements
    
    def _create_research_type_ui(self) -> None:
        """研究種別選択UIを作成"""
        ui_elements = {}
        
        # タイトル
        ui_elements['title'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 390, 30),
            text="研究の種類を選択してください",
            manager=self.ui_manager,
            container=self.content_panel
        )
        
        # 研究種別リスト
        ui_elements['type_list'] = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(10, 50, 390, 180),
            item_list=[],
            manager=self.ui_manager,
            container=self.content_panel
        )
        
        # 説明表示
        ui_elements['description'] = pygame_gui.elements.UITextBox(
            html_text="",
            relative_rect=pygame.Rect(10, 240, 390, 30),
            manager=self.ui_manager,
            container=self.content_panel
        )
        
        self.step_uis[ResearchStep.SELECT_TYPE] = ui_elements
    
    def _create_configure_ui(self) -> None:
        """詳細設定UIを作成"""
        ui_elements = {}
        
        # タイトル
        ui_elements['title'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 390, 30),
            text="研究の詳細を設定してください",
            manager=self.ui_manager,
            container=self.content_panel
        )
        
        # 設定項目（仮）
        ui_elements['config_box'] = pygame_gui.elements.UITextBox(
            html_text="",
            relative_rect=pygame.Rect(10, 50, 390, 220),
            manager=self.ui_manager,
            container=self.content_panel
        )
        
        self.step_uis[ResearchStep.CONFIGURE] = ui_elements
    
    def _create_confirm_ui(self) -> None:
        """確認UIを作成"""
        ui_elements = {}
        
        # タイトル
        ui_elements['title'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 390, 30),
            text="研究内容の確認",
            manager=self.ui_manager,
            container=self.content_panel
        )
        
        # 確認内容表示
        ui_elements['summary'] = pygame_gui.elements.UITextBox(
            html_text="",
            relative_rect=pygame.Rect(10, 50, 390, 220),
            manager=self.ui_manager,
            container=self.content_panel
        )
        
        self.step_uis[ResearchStep.CONFIRM] = ui_elements
    
    def _show_current_step(self) -> None:
        """現在のステップを表示"""
        # すべてのステップUIを非表示
        for step_ui in self.step_uis.values():
            for element in step_ui.values():
                if hasattr(element, 'hide'):
                    element.hide()
        
        # 現在のステップUIを表示
        current_ui = self.step_uis.get(self.current_step, {})
        for element in current_ui.values():
            if hasattr(element, 'show'):
                element.show()
        
        # ステップごとのデータ読み込み
        if self.current_step == ResearchStep.SELECT_RESEARCHER:
            self._load_researchers()
        elif self.current_step == ResearchStep.SELECT_TYPE:
            self._load_research_types()
        elif self.current_step == ResearchStep.CONFIGURE:
            self._load_configuration()
        elif self.current_step == ResearchStep.CONFIRM:
            self._load_summary()
        
        # ボタンの有効/無効を更新
        self._update_navigation_buttons()
    
    def _load_researchers(self) -> None:
        """研究者リストを読み込み"""
        result = self.service.execute_action("magic_research", {
            "step": "select_researcher"
        })
        
        if result.success and result.data:
            researchers = result.data.get("researchers", [])
            
            # リスト項目を作成
            items = []
            for researcher in researchers:
                item_text = f"{researcher['name']} ({researcher['class']}) Lv.{researcher['level']} INT:{researcher['intelligence']}"
                items.append(item_text)
            
            # UIを更新
            ui = self.step_uis[ResearchStep.SELECT_RESEARCHER]
            ui['researcher_list'].set_item_list(items)
            
            # データを保存
            self.research_data['researchers'] = researchers
    
    def _load_research_types(self) -> None:
        """研究種別を読み込み"""
        result = self.service.execute_action("magic_research", {
            "step": "select_research_type",
            "researcher_id": self.research_data.get("selected_researcher_id")
        })
        
        if result.success and result.data:
            types = result.data.get("research_types", [])
            
            # リスト項目を作成
            items = []
            for rtype in types:
                item_text = f"{rtype['name']} - {rtype['cost']}G ({rtype['duration']}日)"
                items.append(item_text)
            
            # UIを更新
            ui = self.step_uis[ResearchStep.SELECT_TYPE]
            ui['type_list'].set_item_list(items)
            
            # データを保存
            self.research_data['research_types'] = types
    
    def _load_configuration(self) -> None:
        """設定内容を読み込み"""
        # 研究種別に応じた設定画面を表示（仮実装）
        ui = self.step_uis[ResearchStep.CONFIGURE]
        config_text = """
        <b>研究設定</b><br>
        <br>
        研究期間: 30日<br>
        必要資金: 5000 G<br>
        成功率: 75%<br>
        <br>
        オプション:<br>
        ・資金を追加投入 (+1000G で成功率+10%)<br>
        ・研究期間延長 (+10日で成功率+15%)<br>
        """
        ui['config_box'].html_text = config_text.strip()
        ui['config_box'].rebuild()
    
    def _load_summary(self) -> None:
        """確認内容を読み込み"""
        # 研究内容の要約を表示
        ui = self.step_uis[ResearchStep.CONFIRM]
        
        researcher = self.research_data.get("selected_researcher", {})
        research_type = self.research_data.get("selected_type", {})
        
        summary_text = f"""
        <b>魔法研究の確認</b><br>
        <br>
        研究者: {researcher.get('name', '未選択')}<br>
        研究種別: {research_type.get('name', '未選択')}<br>
        研究期間: {research_type.get('duration', 0)}日<br>
        必要資金: {research_type.get('cost', 0)} G<br>
        <br>
        この内容で研究を開始しますか？
        """
        
        ui['summary'].html_text = summary_text.strip()
        ui['summary'].rebuild()
    
    def _update_navigation_buttons(self) -> None:
        """ナビゲーションボタンを更新"""
        # 戻るボタン
        if self.current_step == ResearchStep.SELECT_RESEARCHER:
            self.back_button.disable()
        else:
            self.back_button.enable()
        
        # 次へボタン
        if self.current_step == ResearchStep.CONFIRM:
            self.next_button.set_text("完了")
        else:
            self.next_button.set_text("次へ")
        
        # ステップごとの次へボタンの有効性チェック
        if self.current_step == ResearchStep.SELECT_RESEARCHER:
            # 研究者が選択されているか
            ui = self.step_uis[ResearchStep.SELECT_RESEARCHER]
            selection = ui['researcher_list'].get_single_selection()
            self.next_button.enable() if selection is not None else self.next_button.disable()
        elif self.current_step == ResearchStep.SELECT_TYPE:
            # 研究種別が選択されているか
            ui = self.step_uis[ResearchStep.SELECT_TYPE]
            selection = ui['type_list'].get_single_selection()
            self.next_button.enable() if selection is not None else self.next_button.disable()
        else:
            self.next_button.enable()
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """イベントを処理"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.next_button:
                self._handle_next()
            elif event.ui_element == self.back_button:
                self._handle_back()
            elif event.ui_element == self.cancel_button:
                self._handle_cancel()
        
        elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            # 選択が変更された時の処理
            if self.current_step == ResearchStep.SELECT_RESEARCHER:
                ui = self.step_uis[ResearchStep.SELECT_RESEARCHER]
                if event.ui_element == ui['researcher_list']:
                    selection = ui['researcher_list'].get_single_selection()
                    if selection is not None:
                        researcher = self.research_data['researchers'][selection]
                        self.research_data['selected_researcher'] = researcher
                        self.research_data['selected_researcher_id'] = researcher['id']
                        self._update_navigation_buttons()
            
            elif self.current_step == ResearchStep.SELECT_TYPE:
                ui = self.step_uis[ResearchStep.SELECT_TYPE]
                if event.ui_element == ui['type_list']:
                    selection = ui['type_list'].get_single_selection()
                    if selection is not None:
                        rtype = self.research_data['research_types'][selection]
                        self.research_data['selected_type'] = rtype
                        # 説明を更新
                        ui['description'].html_text = rtype['description']
                        ui['description'].rebuild()
                        self._update_navigation_buttons()
    
    def _handle_next(self) -> None:
        """次へボタンの処理"""
        if self.current_step == ResearchStep.CONFIRM:
            # 研究開始
            self._complete_research()
        else:
            # 次のステップへ
            self.current_step = ResearchStep(self.current_step.value + 1)
            self._update_step_indicator()
            self._show_current_step()
    
    def _handle_back(self) -> None:
        """戻るボタンの処理"""
        if self.current_step.value > 1:
            self.current_step = ResearchStep(self.current_step.value - 1)
            self._update_step_indicator()
            self._show_current_step()
    
    def _handle_cancel(self) -> None:
        """キャンセルボタンの処理"""
        # ウィザードを閉じる
        # 実際の実装では、親コンポーネントに通知
        logger.info("Magic research wizard cancelled")
    
    def _complete_research(self) -> None:
        """研究を完了"""
        result = self.service.execute_action("magic_research", {
            "step": "complete",
            **self.research_data
        })
        
        if result.success:
            # 成功メッセージを表示して閉じる
            logger.info("Magic research completed successfully")
        else:
            logger.error(f"Magic research failed: {result.message}")
    
    def _update_step_indicator(self) -> None:
        """ステップインジケーターを更新"""
        # インジケーターを再作成
        if self.step_indicator:
            self.step_indicator.kill()
        self._create_step_indicator()
    
    def refresh(self) -> None:
        """ウィザードをリフレッシュ"""
        self.current_step = ResearchStep.SELECT_RESEARCHER
        self.research_data = {}
        self._update_step_indicator()
        self._show_current_step()
    
    def show(self) -> None:
        """ウィザードを表示"""
        if self.container:
            self.container.show()
    
    def hide(self) -> None:
        """ウィザードを非表示"""
        if self.container:
            self.container.hide()
    
    def destroy(self) -> None:
        """ウィザードを破棄"""
        if self.container:
            self.container.kill()