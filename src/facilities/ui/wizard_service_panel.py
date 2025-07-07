"""ウィザード型サービスパネル"""

import pygame
import pygame_gui
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
from .service_panel import ServicePanel
from ..core.facility_controller import FacilityController
from ..core.service_result import ServiceResult

logger = logging.getLogger(__name__)


@dataclass
class WizardStep:
    """ウィザードステップ"""
    id: str
    name: str
    description: Optional[str] = None
    validator: Optional[Callable[[Dict[str, Any]], bool]] = None
    required_fields: List[str] = None
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = []


class StepIndicatorStyle(Enum):
    """ステップインジケーターのスタイル"""
    COMPLETED = "completed"   # 完了済み
    CURRENT = "current"       # 現在
    PENDING = "pending"       # 未完了
    ERROR = "error"          # エラー


class WizardServicePanel(ServicePanel):
    """ウィザード型サービスパネル
    
    複数のステップを持つウィザード形式のサービス用パネル。
    キャラクター作成などの複雑なプロセスに対応。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller: FacilityController, service_id: str,
                 ui_manager: pygame_gui.UIManager):
        """初期化"""
        # ウィザード固有の属性を先に初期化
        self.wizard_data: Dict[str, Any] = {}
        self.steps: List[WizardStep] = []
        self.current_step_index = 0
        self.step_panels: Dict[str, pygame_gui.elements.UIPanel] = {}
        self.step_validators: Dict[str, Callable] = {}
        
        # UI要素
        self.indicator_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.content_area: Optional[pygame_gui.elements.UIPanel] = None
        self.nav_button_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.back_button: Optional[pygame_gui.elements.UIButton] = None
        self.next_button: Optional[pygame_gui.elements.UIButton] = None
        self.cancel_button: Optional[pygame_gui.elements.UIButton] = None
        
        # 親クラスの初期化
        super().__init__(rect, parent, controller, service_id, ui_manager)
        
        logger.info(f"WizardServicePanel created: {service_id}")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        # ウィザードステップを取得
        self._load_wizard_steps()
        
        # レイアウト定数
        indicator_height = 60
        nav_height = 50
        content_height = self.rect.height - indicator_height - nav_height - 20
        
        # ステップインジケーター
        self._create_step_indicator(indicator_height)
        
        # コンテンツエリア
        content_rect = pygame.Rect(
            10, indicator_height + 10,
            self.rect.width - 20, content_height
        )
        self.content_area = pygame_gui.elements.UIPanel(
            relative_rect=content_rect,
            manager=self.ui_manager,
            container=self.container
        )
        
        # ナビゲーションボタン
        self._create_navigation_buttons(nav_height)
        
        # 最初のステップを表示
        self._show_step(0)
    
    def _load_wizard_steps(self) -> None:
        """ウィザードステップを読み込み"""
        # サービスIDに基づいてステップを定義
        # TODO: 設定ファイルから読み込むように変更
        
        if self.service_id == "character_creation":
            self.steps = [
                WizardStep("name", "名前入力", "キャラクターの名前を入力してください", 
                          required_fields=["name"]),
                WizardStep("race", "種族選択", "キャラクターの種族を選択してください",
                          required_fields=["race"]),
                WizardStep("stats", "能力値決定", "キャラクターの能力値を決定します",
                          required_fields=["stats"]),
                WizardStep("class", "職業選択", "キャラクターの職業を選択してください",
                          required_fields=["class"]),
                WizardStep("confirm", "確認", "入力内容を確認してください")
            ]
        else:
            # デフォルトのシンプルなステップ
            self.steps = [
                WizardStep("input", "入力", "必要な情報を入力してください"),
                WizardStep("confirm", "確認", "入力内容を確認してください")
            ]
    
    def _create_step_indicator(self, height: int) -> None:
        """ステップインジケーターを作成"""
        indicator_rect = pygame.Rect(10, 10, self.rect.width - 20, height)
        self.indicator_panel = pygame_gui.elements.UIPanel(
            relative_rect=indicator_rect,
            manager=self.ui_manager,
            container=self.container
        )
        
        # 各ステップのインジケーターを作成
        step_count = len(self.steps)
        if step_count == 0:
            return
        
        step_width = (self.rect.width - 40) // step_count
        
        for i, step in enumerate(self.steps):
            x = 10 + i * step_width
            
            # ステップ状態を判定
            if i < self.current_step_index:
                style = StepIndicatorStyle.COMPLETED
                symbol = "✓"
                color = "#28a745"
            elif i == self.current_step_index:
                style = StepIndicatorStyle.CURRENT
                symbol = "▶"
                color = "#007bff"
            else:
                style = StepIndicatorStyle.PENDING
                symbol = "○"
                color = "#6c757d"
            
            # ステップラベル
            step_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(x, 10, step_width - 10, 40),
                text=f"{symbol} {step.name}",
                manager=self.ui_manager,
                container=self.indicator_panel
            )
            self.ui_elements.append(step_label)
    
    def _create_navigation_buttons(self, height: int) -> None:
        """ナビゲーションボタンを作成"""
        nav_rect = pygame.Rect(
            10, self.rect.height - height - 10,
            self.rect.width - 20, height
        )
        self.nav_button_panel = pygame_gui.elements.UIPanel(
            relative_rect=nav_rect,
            manager=self.ui_manager,
            container=self.container
        )
        
        button_width = 100
        button_height = 35
        button_spacing = 10
        
        # キャンセルボタン（左端）
        self.cancel_button = self._create_button(
            "キャンセル",
            pygame.Rect(0, 5, button_width, button_height),
            container=self.nav_button_panel,
            object_id="#cancel_button"
        )
        
        # 戻るボタン（右側）
        back_x = self.rect.width - 2 * button_width - button_spacing - 20
        self.back_button = self._create_button(
            "戻る",
            pygame.Rect(back_x, 5, button_width, button_height),
            container=self.nav_button_panel,
            object_id="#back_button"
        )
        
        # 次へ/完了ボタン（右端）
        next_x = self.rect.width - button_width - 20
        self.next_button = self._create_button(
            "次へ",
            pygame.Rect(next_x, 5, button_width, button_height),
            container=self.nav_button_panel,
            object_id="#next_button"
        )
        
        # 初期状態を更新
        self._update_navigation_buttons()
    
    def _update_navigation_buttons(self) -> None:
        """ナビゲーションボタンの状態を更新"""
        # 戻るボタン
        if self.back_button:
            if self.current_step_index > 0:
                self.back_button.enable()
            else:
                self.back_button.disable()
        
        # 次へ/完了ボタン
        if self.next_button:
            if self.current_step_index >= len(self.steps) - 1:
                self.next_button.set_text("完了")
            else:
                self.next_button.set_text("次へ")
    
    def _show_step(self, step_index: int) -> None:
        """指定されたステップを表示"""
        if step_index < 0 or step_index >= len(self.steps):
            logger.error(f"Invalid step index: {step_index}")
            return
        
        # 現在のステップコンテンツを隠す
        current_step_id = self.steps[self.current_step_index].id if self.current_step_index < len(self.steps) else None
        if current_step_id and current_step_id in self.step_panels:
            self.step_panels[current_step_id].hide()
        
        # 新しいステップを設定
        self.current_step_index = step_index
        step = self.steps[step_index]
        
        # ステップパネルを作成/表示
        if step.id not in self.step_panels:
            self._create_step_panel(step)
        
        if step.id in self.step_panels:
            self.step_panels[step.id].show()
        
        # インジケーターとボタンを更新
        self._update_step_indicator()
        self._update_navigation_buttons()
    
    def _create_step_panel(self, step: WizardStep) -> None:
        """ステップパネルを作成"""
        panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(0, 0, self.content_area.relative_rect.width,
                                    self.content_area.relative_rect.height),
            manager=self.ui_manager,
            container=self.content_area
        )
        
        # ステップ説明
        if step.description:
            desc_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(10, 10, panel.relative_rect.width - 20, 40),
                text=step.description,
                manager=self.ui_manager,
                container=panel
            )
            self.ui_elements.append(desc_label)
        
        # ステップ固有のコンテンツを作成
        self._create_step_content(step, panel)
        
        self.step_panels[step.id] = panel
    
    def _create_step_content(self, step: WizardStep, panel: pygame_gui.elements.UIPanel) -> None:
        """ステップ固有のコンテンツを作成（サブクラスでオーバーライド）"""
        # ステップIDに応じたコンテンツ作成
        if step.id == "name":
            self._create_name_input_content(panel)
        elif step.id == "race":
            self._create_race_selection_content(panel)
        elif step.id == "stats":
            self._create_stats_roll_content(panel)
        elif step.id == "class":
            self._create_class_selection_content(panel)
        elif step.id == "confirm":
            self._create_confirmation_content(panel)
        else:
            # プレースホルダー
            placeholder = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(10, 60, panel.relative_rect.width - 20, 30),
                text=f"ステップ '{step.name}' のコンテンツ",
                manager=self.ui_manager,
                container=panel
            )
            self.ui_elements.append(placeholder)
    
    def _create_name_input_content(self, panel: pygame_gui.elements.UIPanel) -> None:
        """名前入力コンテンツを作成"""
        # 名前入力フィールド
        input_rect = pygame.Rect(10, 60, 300, 40)
        self.name_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=input_rect,
            manager=self.ui_manager,
            container=panel,
            placeholder_text="キャラクター名を入力"
        )
        self.ui_elements.append(self.name_input)
        
        # 既存の値を設定
        if "name" in self.wizard_data:
            self.name_input.set_text(self.wizard_data["name"])
    
    def _update_step_indicator(self) -> None:
        """ステップインジケーターを更新"""
        # 既存のインジケーターを破棄して再作成
        if self.indicator_panel:
            # 子要素をクリア
            for element in list(self.indicator_panel.element_ids):
                if hasattr(element, 'kill'):
                    element.kill()
            
            # インジケーターを再作成
            self._create_step_indicator(60)
    
    def _validate_current_step(self) -> bool:
        """現在のステップを検証"""
        if self.current_step_index >= len(self.steps):
            return False
        
        step = self.steps[self.current_step_index]
        
        # カスタムバリデーター
        if step.validator:
            return step.validator(self.wizard_data)
        
        # 必須フィールドチェック
        for field in step.required_fields:
            if field not in self.wizard_data or not self.wizard_data[field]:
                self._show_message(f"'{field}'を入力してください", "warning")
                return False
        
        return True
    
    def _collect_step_data(self) -> None:
        """現在のステップのデータを収集"""
        if self.current_step_index >= len(self.steps):
            return
        
        step = self.steps[self.current_step_index]
        
        # ステップ固有のデータ収集
        if step.id == "name" and hasattr(self, 'name_input'):
            self.wizard_data["name"] = self.name_input.get_text()
        elif step.id == "race" and hasattr(self, 'race_selection'):
            # 種族選択のデータを収集
            selection = self.race_selection.get_single_selection()
            if selection is not None and hasattr(self, 'race_data'):
                self.wizard_data["race"] = self.race_data[selection]
        elif step.id == "stats" and hasattr(self, 'stats_data'):
            # ステータスのデータを収集
            self.wizard_data["stats"] = getattr(self, 'stats_data', {})
        elif step.id == "class" and hasattr(self, 'class_selection'):
            # クラス選択のデータを収集
            selection = self.class_selection.get_single_selection()
            if selection is not None and hasattr(self, 'class_data'):
                self.wizard_data["class"] = self.class_data[selection]
    
    def next_step(self) -> None:
        """次のステップへ進む"""
        # 現在のステップのデータを収集
        self._collect_step_data()
        
        # 検証
        if not self._validate_current_step():
            return
        
        if self.current_step_index < len(self.steps) - 1:
            # 次のステップへ
            self._show_step(self.current_step_index + 1)
        else:
            # 最後のステップの場合は完了処理
            self._complete_wizard()
    
    def previous_step(self) -> None:
        """前のステップへ戻る"""
        if self.current_step_index > 0:
            # 現在のステップのデータを保存
            self._collect_step_data()
            # 前のステップへ
            self._show_step(self.current_step_index - 1)
    
    def _complete_wizard(self) -> None:
        """ウィザード完了処理"""
        # 最終検証
        if not self._validate_all_steps():
            return
        
        # サービスを実行
        result = self._execute_service_action(
            f"{self.service_id}_complete",
            self.wizard_data
        )
        
        if result.is_success():
            self._show_message(result.message, "info")
            # TODO: ウィザードを閉じて元の画面に戻る
        else:
            self._show_message(result.message, "error")
    
    def _validate_all_steps(self) -> bool:
        """すべてのステップを検証"""
        for step in self.steps:
            # 必須フィールドチェック
            for field in step.required_fields:
                if field not in self.wizard_data or not self.wizard_data[field]:
                    self._show_message(f"必須項目 '{field}' が未入力です", "error")
                    return False
        return True
    
    def _cancel_wizard(self) -> None:
        """ウィザードをキャンセル"""
        # TODO: 確認ダイアログを表示
        self._show_message("ウィザードをキャンセルしました", "info")
        # TODO: 元の画面に戻る処理
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        if button == self.next_button:
            self.next_step()
            return True
        elif button == self.back_button:
            self.previous_step()
            return True
        elif button == self.cancel_button:
            self._cancel_wizard()
            return True
        
        return False
    
    def _highlight_button(self, button: pygame_gui.elements.UIButton) -> None:
        """ボタンをハイライト"""
        if button and hasattr(button, 'selected'):
            button.selected = True
        # pygame_guiのボタンは標準的にハイライト機能を持たないため、
        # 代替実装として色やスタイルの変更を行う場合はここに実装
    
    def _unhighlight_button(self, button: pygame_gui.elements.UIButton) -> None:
        """ボタンのハイライトを解除"""
        if button and hasattr(button, 'selected'):
            button.selected = False
        # pygame_guiのボタンは標準的にハイライト機能を持たないため、
        # 代替実装として色やスタイルの変更を行う場合はここに実装
    
    def _create_race_selection_content(self, panel: pygame_gui.elements.UIPanel) -> None:
        """種族選択コンテンツを作成"""
        # 種族選択リスト
        self.race_selection = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(10, 60, 300, 200),
            item_list=[],
            manager=self.ui_manager,
            container=panel
        )
        self.ui_elements.append(self.race_selection)
    
    def _create_stats_roll_content(self, panel: pygame_gui.elements.UIPanel) -> None:
        """ステータスロールコンテンツを作成"""
        # ステータス表示用のラベル
        self.stats_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 60, 300, 100),
            text="ステータスを決定してください",
            manager=self.ui_manager,
            container=panel
        )
        self.ui_elements.append(self.stats_label)
    
    def _create_class_selection_content(self, panel: pygame_gui.elements.UIPanel) -> None:
        """クラス選択コンテンツを作成"""
        # クラス選択リスト
        self.class_selection = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(10, 60, 300, 200),
            item_list=[],
            manager=self.ui_manager,
            container=panel
        )
        self.ui_elements.append(self.class_selection)
    
    def _create_confirmation_content(self, panel: pygame_gui.elements.UIPanel) -> None:
        """確認コンテンツを作成"""
        # 確認用のテキストボックス
        self.confirmation_box = pygame_gui.elements.UITextBox(
            html_text="設定を確認してください",
            relative_rect=pygame.Rect(10, 60, 300, 200),
            manager=self.ui_manager,
            container=panel
        )
        self.ui_elements.append(self.confirmation_box)