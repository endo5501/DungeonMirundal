"""キャラクター作成ウィザード"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
import logging
import random
from ..wizard_service_panel import WizardServicePanel, WizardStep
from ...core.service_result import ServiceResult

logger = logging.getLogger(__name__)


class CharacterCreationWizard(WizardServicePanel):
    """キャラクター作成ウィザード
    
    複数ステップでキャラクターを作成するウィザード形式のUI。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        # ウィザード固有のUI要素
        self.race_buttons: Dict[str, pygame_gui.elements.UIButton] = {}
        self.class_buttons: Dict[str, pygame_gui.elements.UIButton] = {}
        self.stat_labels: Dict[str, pygame_gui.elements.UILabel] = {}
        self.stat_values: Dict[str, int] = {}
        self.roll_button: Optional[pygame_gui.elements.UIButton] = None
        self.confirm_labels: List[pygame_gui.elements.UILabel] = []
        
        super().__init__(rect, parent, controller, "character_creation", ui_manager)
        
        logger.info("CharacterCreationWizard initialized")
    
    def _load_wizard_steps(self) -> None:
        """ウィザードステップを定義"""
        # 親クラスの重複呼び出しを避けるため、stepsが既に初期化されている場合はスキップ
        if self.steps:
            return
            
        self.steps = [
            WizardStep(
                id="name",
                name="名前入力",
                description="キャラクターの名前を入力してください",
                required_fields=["name"],
                validator=self._validate_name
            ),
            WizardStep(
                id="race",
                name="種族選択",
                description="キャラクターの種族を選択してください",
                required_fields=["race"],
                validator=self._validate_race
            ),
            WizardStep(
                id="stats",
                name="能力値決定",
                description="キャラクターの能力値を決定します",
                required_fields=["stats"],
                validator=self._validate_stats
            ),
            WizardStep(
                id="class",
                name="職業選択",
                description="キャラクターの職業を選択してください", 
                required_fields=["class"],
                validator=self._validate_class
            ),
            WizardStep(
                id="confirm",
                name="確認",
                description="入力内容を確認してください"
            )
        ]
    
    def _create_step_content(self, step: WizardStep, panel: pygame_gui.elements.UIPanel) -> None:
        """ステップ固有のコンテンツを作成"""
        if step.id == "name":
            # UIElementManager版を優先的に使用
            if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
                self._create_name_input_content_managed(panel)
            else:
                self._create_name_input_content(panel)
        elif step.id == "race":
            # UIElementManager版を優先的に使用
            if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
                self._create_race_selection_content_managed(panel)
            else:
                self._create_race_selection_content(panel)
        elif step.id == "stats":
            # UIElementManager版を優先的に使用
            if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
                self._create_stats_roll_content_managed(panel)
            else:
                self._create_stats_roll_content(panel)
        elif step.id == "class":
            # UIElementManager版を優先的に使用
            if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
                self._create_class_selection_content_managed(panel)
            else:
                self._create_class_selection_content(panel)
        elif step.id == "confirm":
            # UIElementManager版を優先的に使用
            if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
                self._create_confirmation_content_managed(panel)
            else:
                self._create_confirmation_content(panel)
    
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
        
        # フォーカスを明示的に設定
        self.name_input.focus()
        
        # デバッグ用：テスト名前を設定
        logger.info(f"[DEBUG] name_input created: {self.name_input}")
        logger.info(f"[DEBUG] name_input has focus: {hasattr(self.name_input, 'focused')}")
        logger.info(f"[DEBUG] name_input focused: {getattr(self.name_input, 'is_focused', False)}")
        
        # テスト用のボタンを追加（デバッグ時の名前設定用）
        test_button_rect = pygame.Rect(320, 60, 100, 40)
        self.test_name_button = pygame_gui.elements.UIButton(
            relative_rect=test_button_rect,
            text="テスト名前",
            manager=self.ui_manager,
            container=panel,
        )
        self.ui_elements.append(self.test_name_button)
    
    def _create_name_input_content_managed(self, panel: pygame_gui.elements.UIPanel) -> None:
        """名前入力コンテンツを作成（UIElementManager版）"""
        # 名前入力フィールド（UIElementManager経由）
        input_rect = pygame.Rect(10, 60, 300, 40)
        self.name_input = self._create_text_entry(
            "character_creation_name_input",
            "",
            input_rect,
            panel,
            placeholder_text="キャラクター名を入力"
        )
        
        # 既存の値を設定
        if "name" in self.wizard_data and self.name_input:
            self.name_input.set_text(self.wizard_data["name"])
        
        # フォーカスを明示的に設定
        if self.name_input:
            self.name_input.focus()
            logger.info(f"[DEBUG] name_input created via UIElementManager: {self.name_input}")
        
        # テスト用のボタンを追加（UIElementManager版）
        test_button_rect = pygame.Rect(320, 60, 100, 40)
        self.test_name_button = self._create_button(
            "character_creation_test_name_button",
            "テスト名前",
            test_button_rect,
            panel
        )
    
    def _create_race_selection_content(self, panel: pygame_gui.elements.UIPanel) -> None:
        """種族選択コンテンツを作成"""
        races = [
            ("human", "人間", "バランスの取れた種族"),
            ("elf", "エルフ", "魔法に優れた種族"),
            ("dwarf", "ドワーフ", "頑強な種族"),
            ("gnome", "ノーム", "信仰心の高い種族"),
            ("hobbit", "ホビット", "幸運な種族")
        ]
        
        y_offset = 60
        button_height = 50
        button_spacing = 10
        
        for race_id, race_name, race_desc in races:
            button_rect = pygame.Rect(10, y_offset, 380, button_height)
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=f"{race_name} - {race_desc}",
                manager=self.ui_manager,
                container=panel,
            )
            
            self.race_buttons[race_id] = button
            self.ui_elements.append(button)
            
            # 選択済みの場合はハイライト
            if self.wizard_data.get("race") == race_id:
                self._highlight_button(button)
            
            y_offset += button_height + button_spacing
    
    def _create_race_selection_content_managed(self, panel: pygame_gui.elements.UIPanel) -> None:
        """種族選択コンテンツを作成（UIElementManager版）"""
        races = [
            ("human", "人間", "バランスの取れた種族"),
            ("elf", "エルフ", "魔法に優れた種族"),
            ("dwarf", "ドワーフ", "頑強な種族"),
            ("gnome", "ノーム", "信仰心の高い種族"),
            ("hobbit", "ホビット", "幸運な種族")
        ]
        
        y_offset = 60
        button_height = 50
        button_spacing = 10
        
        for race_id, race_name, race_desc in races:
            button_rect = pygame.Rect(10, y_offset, 380, button_height)
            button = self._create_button(
                f"character_creation_race_{race_id}",
                f"{race_name} - {race_desc}",
                button_rect,
                panel
            )
            
            if button:
                self.race_buttons[race_id] = button
                
                # 選択済みの場合はハイライト
                if self.wizard_data.get("race") == race_id:
                    self._highlight_button(button)
            
            y_offset += button_height + button_spacing
    
    def _create_stats_roll_content(self, panel: pygame_gui.elements.UIPanel) -> None:
        """能力値決定コンテンツを作成"""
        # ロールボタン
        roll_rect = pygame.Rect(150, 60, 100, 40)
        self.roll_button = pygame_gui.elements.UIButton(
            relative_rect=roll_rect,
            text="ダイスを振る",
            manager=self.ui_manager,
            container=panel
        )
        self.ui_elements.append(self.roll_button)
        
        # 能力値表示
        stats = ["strength", "intelligence", "faith", "vitality", "agility", "luck"]
        stat_names = ["筋力", "知力", "信仰心", "生命力", "敏捷性", "幸運"]
        
        y_offset = 120
        for stat, stat_name in zip(stats, stat_names):
            # ラベル
            label_rect = pygame.Rect(10, y_offset, 100, 30)
            label = pygame_gui.elements.UILabel(
                relative_rect=label_rect,
                text=f"{stat_name}:",
                manager=self.ui_manager,
                container=panel
            )
            self.ui_elements.append(label)
            
            # 値表示
            value_rect = pygame.Rect(120, y_offset, 60, 30)
            value_label = pygame_gui.elements.UILabel(
                relative_rect=value_rect,
                text="--",
                manager=self.ui_manager,
                container=panel
            )
            self.stat_labels[stat] = value_label
            self.ui_elements.append(value_label)
            
            y_offset += 35
        
        # 既存の値があれば表示
        if "stats" in self.wizard_data:
            self._display_stats(self.wizard_data["stats"])
    
    def _create_stats_roll_content_managed(self, panel: pygame_gui.elements.UIPanel) -> None:
        """能力値決定コンテンツを作成（UIElementManager版）"""
        # ロールボタン
        roll_rect = pygame.Rect(150, 60, 100, 40)
        self.roll_button = self._create_button(
            "character_creation_roll_button",
            "ダイスを振る",
            roll_rect,
            panel
        )
        
        # 能力値表示
        stats = ["strength", "intelligence", "faith", "vitality", "agility", "luck"]
        stat_names = ["筋力", "知力", "信仰心", "生命力", "敏捷性", "幸運"]
        
        y_offset = 120
        for stat, stat_name in zip(stats, stat_names):
            # ラベル
            label_rect = pygame.Rect(10, y_offset, 100, 30)
            self._create_label(
                f"character_creation_stat_label_{stat}",
                f"{stat_name}:",
                label_rect,
                panel
            )
            
            # 値表示
            value_rect = pygame.Rect(120, y_offset, 60, 30)
            value_label = self._create_label(
                f"character_creation_stat_value_{stat}",
                "--",
                value_rect,
                panel
            )
            if value_label:
                self.stat_labels[stat] = value_label
            
            y_offset += 35
        
        # 既存の値があれば表示
        if "stats" in self.wizard_data:
            self._display_stats(self.wizard_data["stats"])
    
    def _create_class_selection_content(self, panel: pygame_gui.elements.UIPanel) -> None:
        """職業選択コンテンツを作成"""
        # 能力値に基づいて選択可能な職業を判定
        available_classes = self._get_available_classes()
        
        classes = [
            ("fighter", "戦士", "前衛の物理攻撃職"),
            ("priest", "僧侶", "回復と支援の職業"),
            ("thief", "盗賊", "素早い攻撃と探索"),
            ("mage", "魔法使い", "強力な攻撃魔法"),
            ("bishop", "司教", "魔法と僧侶魔法の両立"),
            ("samurai", "侍", "物理と魔法のバランス"),
            ("lord", "君主", "高い防御と支援"),
            ("ninja", "忍者", "高速攻撃と隠密")
        ]
        
        y_offset = 60
        button_height = 45
        button_spacing = 5
        
        for class_id, class_name, class_desc in classes:
            button_rect = pygame.Rect(10, y_offset, 380, button_height)
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=f"{class_name} - {class_desc}",
                manager=self.ui_manager,
                container=panel,
            )
            
            # 選択不可の職業は無効化
            if class_id not in available_classes:
                button.disable()
            
            self.class_buttons[class_id] = button
            self.ui_elements.append(button)
            
            # 選択済みの場合はハイライト
            if self.wizard_data.get("class") == class_id:
                self._highlight_button(button)
            
            y_offset += button_height + button_spacing
    
    def _create_class_selection_content_managed(self, panel: pygame_gui.elements.UIPanel) -> None:
        """職業選択コンテンツを作成（UIElementManager版）"""
        # 選択可能な職業を判定
        available_classes = self._get_available_classes()
        
        classes = [
            ("fighter", "戦士", "前衛の物理攻撃職"),
            ("priest", "僧侶", "回復と支援の職業"),
            ("thief", "盗賊", "素早い攻撃と探索"),
            ("mage", "魔法使い", "強力な攻撃魔法"),
            ("bishop", "司教", "魔法と僧侶魔法の両立"),
            ("samurai", "侍", "物理と魔法のバランス"),
            ("lord", "君主", "高い防御と支援"),
            ("ninja", "忍者", "高速攻撃と隠密")
        ]
        
        y_offset = 60
        button_height = 45
        button_spacing = 5
        
        for class_id, class_name, class_desc in classes:
            button_rect = pygame.Rect(10, y_offset, 380, button_height)
            button = self._create_button(
                f"character_creation_class_{class_id}",
                f"{class_name} - {class_desc}",
                button_rect,
                panel
            )
            
            if button:
                # 選択不可の職業は無効化
                if class_id not in available_classes:
                    button.disable()
                
                self.class_buttons[class_id] = button
                
                # 選択済みの場合はハイライト
                if self.wizard_data.get("class") == class_id:
                    self._highlight_button(button)
            
            y_offset += button_height + button_spacing
    
    def _create_confirmation_content(self, panel: pygame_gui.elements.UIPanel) -> None:
        """確認画面コンテンツを作成"""
        # プレーンテキストでキャラクター情報を構築（HTMLタグを使わない）
        character_info_lines = self._create_character_info_lines()
        
        y_offset = 60
        line_height = 25
        
        self.confirm_labels = []
        for i, line in enumerate(character_info_lines):
            if line.strip():  # 空行をスキップ
                label_rect = pygame.Rect(10, y_offset, 380, line_height)
                label = pygame_gui.elements.UILabel(
                    relative_rect=label_rect,
                    text=line,
                    manager=self.ui_manager,
                    container=panel
                )
                self.confirm_labels.append(label)
                self.ui_elements.append(label)
                y_offset += line_height
    
    def _create_confirmation_content_managed(self, panel: pygame_gui.elements.UIPanel) -> None:
        """確認画面コンテンツを作成（UIElementManager版）"""
        # プレーンテキストでキャラクター情報を構築
        character_info_lines = self._create_character_info_lines()
        
        y_offset = 60
        line_height = 25
        
        self.confirm_labels = []
        for i, line in enumerate(character_info_lines):
            if line.strip():  # 空行をスキップ
                label_rect = pygame.Rect(10, y_offset, 380, line_height)
                label = self._create_label(
                    f"character_creation_confirm_label_{i}",
                    line,
                    label_rect,
                    panel
                )
                if label:
                    self.confirm_labels.append(label)
                y_offset += line_height
    
    def _create_character_info_lines(self) -> List[str]:
        """キャラクター情報を行ごとのリストで作成"""
        name = self.wizard_data.get("name", "未設定")
        race = self.wizard_data.get("race", "未設定")
        char_class = self.wizard_data.get("class", "未設定")
        stats = self.wizard_data.get("stats", {})
        
        race_names = {
            "human": "人間", "elf": "エルフ", "dwarf": "ドワーフ",
            "gnome": "ノーム", "hobbit": "ホビット"
        }
        
        class_names = {
            "fighter": "戦士", "priest": "僧侶", "thief": "盗賊",
            "mage": "魔法使い", "bishop": "司教", "samurai": "侍",
            "lord": "君主", "ninja": "忍者"
        }
        
        lines = [
            "キャラクター情報",
            "",
            f"名前: {name}",
            f"種族: {race_names.get(race, race)}",
            f"職業: {class_names.get(char_class, char_class)}",
            "",
            "能力値:",
            f"  筋力: {stats.get('strength', '--')}",
            f"  知力: {stats.get('intelligence', '--')}",
            f"  信仰心: {stats.get('faith', '--')}",
            f"  生命力: {stats.get('vitality', '--')}",
            f"  敏捷性: {stats.get('agility', '--')}",
            f"  幸運: {stats.get('luck', '--')}"
        ]
        
        return lines
    
    def _convert_html_to_plain_text(self, html_text: str) -> str:
        """HTMLタグをプレーンテキストに変換"""
        import re
        # HTMLタグを削除
        plain_text = re.sub(r'<[^>]+>', '', html_text)
        # HTMLエスケープ文字を変換
        plain_text = plain_text.replace('&lt;', '<')
        plain_text = plain_text.replace('&gt;', '>')
        plain_text = plain_text.replace('&amp;', '&')
        plain_text = plain_text.replace('&nbsp;', ' ')
        return plain_text
    
    def _create_character_summary(self) -> str:
        """キャラクター情報のサマリーを作成"""
        name = self.wizard_data.get("name", "未設定")
        race = self.wizard_data.get("race", "未設定")
        char_class = self.wizard_data.get("class", "未設定")
        stats = self.wizard_data.get("stats", {})
        
        race_names = {
            "human": "人間", "elf": "エルフ", "dwarf": "ドワーフ",
            "gnome": "ノーム", "hobbit": "ホビット"
        }
        
        class_names = {
            "fighter": "戦士", "priest": "僧侶", "thief": "盗賊",
            "mage": "魔法使い", "bishop": "司教", "samurai": "侍",
            "lord": "君主", "ninja": "忍者"
        }
        
        summary = f"<b>キャラクター情報</b><br><br>"
        summary += f"<b>名前:</b> {name}<br>"
        summary += f"<b>種族:</b> {race_names.get(race, race)}<br>"
        summary += f"<b>職業:</b> {class_names.get(char_class, char_class)}<br><br>"
        summary += f"<b>能力値:</b><br>"
        summary += f"筋力: {stats.get('strength', '--')}<br>"
        summary += f"知力: {stats.get('intelligence', '--')}<br>"
        summary += f"信仰心: {stats.get('faith', '--')}<br>"
        summary += f"生命力: {stats.get('vitality', '--')}<br>"
        summary += f"敏捷性: {stats.get('agility', '--')}<br>"
        summary += f"幸運: {stats.get('luck', '--')}<br>"
        
        return summary
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        # 親クラスのハンドラを先に呼ぶ
        if super().handle_button_click(button):
            return True
        
        # ダイスロールボタン
        if button == self.roll_button:
            self._roll_stats()
            return True
        
        # 種族選択ボタン
        for race_id, race_button in self.race_buttons.items():
            if button == race_button:
                self._select_race(race_id)
                return True
        
        # 職業選択ボタン
        for class_id, class_button in self.class_buttons.items():
            if button == class_button:
                self._select_class(class_id)
                return True
        
        # テスト名前設定ボタン
        if hasattr(self, 'test_name_button') and button == self.test_name_button:
            self._set_test_name()
            return True
        
        return False
    
    def _set_test_name(self) -> None:
        """テスト用の名前を設定"""
        test_name = "TestCharacter"
        logger.info(f"[DEBUG] Setting test name: {test_name}")
        
        if hasattr(self, 'name_input'):
            self.name_input.set_text(test_name)
            logger.info(f"[DEBUG] name_input.set_text() called with: {test_name}")
            logger.info(f"[DEBUG] name_input.get_text() after set: '{self.name_input.get_text()}'")
            
            # wizard_dataにも直接設定
            self.wizard_data["name"] = test_name
            logger.info(f"[DEBUG] wizard_data['name'] set to: {self.wizard_data['name']}")
        else:
            logger.warning("[DEBUG] name_input not found")
    
    def _collect_step_data(self) -> None:
        """現在のステップのデータを収集"""
        if self.current_step_index >= len(self.steps):
            return
        
        step = self.steps[self.current_step_index]
        
        # ステップ固有のデータ収集
        if step.id == "name" and hasattr(self, 'name_input'):
            self.wizard_data["name"] = self.name_input.get_text()
        elif step.id == "race":
            # 種族選択はボタンクリックで既に設定済み
            # デバッグ用: 種族が選択されていない場合はhuman（人間）を強制設定
            if not self.wizard_data.get("race"):
                logger.info("[DEBUG] No race selected, forcing human")
                self.wizard_data["race"] = "human"
        elif step.id == "stats":
            # 能力値は_roll_statsで設定済み  
            # デバッグ用: 能力値が設定されていない場合はデフォルト値を設定
            if not self.wizard_data.get("stats"):
                logger.info("[DEBUG] No stats set, setting default stats")
                self.wizard_data["stats"] = {
                    'strength': 12, 'intelligence': 12, 'faith': 12, 
                    'vitality': 12, 'agility': 12, 'luck': 12
                }
        elif step.id == "class":
            # 職業選択はボタンクリックで既に設定済み
            # デバッグ用: 職業が選択されていない場合はfighter（戦士）を強制設定
            if not self.wizard_data.get("class"):
                logger.info("[DEBUG] No class selected, forcing fighter")
                self.wizard_data["class"] = "fighter"
    
    def _roll_stats(self) -> None:
        """能力値をロール"""
        stats = {}
        stat_types = ["strength", "intelligence", "faith", "vitality", "agility", "luck"]
        
        for stat in stat_types:
            # 3d6をロール
            rolls = [random.randint(1, 6) for _ in range(3)]
            value = sum(rolls)
            stats[stat] = value
        
        self.wizard_data["stats"] = stats
        self._display_stats(stats)
    
    def _display_stats(self, stats: Dict[str, int]) -> None:
        """能力値を表示"""
        for stat, value in stats.items():
            if stat in self.stat_labels:
                self.stat_labels[stat].set_text(str(value))
        
        # ボタンのテキストを変更
        if self.roll_button:
            self.roll_button.set_text("振り直す")
    
    def _select_race(self, race_id: str) -> None:
        """種族を選択"""
        # 以前の選択をクリア
        for button in self.race_buttons.values():
            self._unhighlight_button(button)
        
        # 新しい選択をハイライト
        if race_id in self.race_buttons:
            self._highlight_button(self.race_buttons[race_id])
        
        self.wizard_data["race"] = race_id
    
    def _select_class(self, class_id: str) -> None:
        """職業を選択"""
        # 以前の選択をクリア
        for button in self.class_buttons.values():
            self._unhighlight_button(button)
        
        # 新しい選択をハイライト
        if class_id in self.class_buttons:
            self._highlight_button(self.class_buttons[class_id])
        
        self.wizard_data["class"] = class_id
    
    def _get_available_classes(self) -> List[str]:
        """能力値に基づいて選択可能な職業を判定"""
        stats = self.wizard_data.get("stats", {})
        if not stats:
            return ["fighter", "priest", "thief", "mage"]  # 基本職のみ
        
        available = ["fighter", "priest", "thief", "mage"]
        
        # 上級職の条件判定
        if (stats.get("intelligence", 0) >= 15 and 
            stats.get("faith", 0) >= 15):
            available.append("bishop")
        
        if (stats.get("strength", 0) >= 15 and
            stats.get("intelligence", 0) >= 11 and
            stats.get("faith", 0) >= 10 and
            stats.get("vitality", 0) >= 14 and
            stats.get("agility", 0) >= 10):
            available.append("samurai")
        
        if (stats.get("strength", 0) >= 15 and
            stats.get("faith", 0) >= 15 and
            stats.get("vitality", 0) >= 15 and
            stats.get("agility", 0) >= 14):
            available.append("lord")
        
        if (stats.get("strength", 0) >= 17 and
            stats.get("intelligence", 0) >= 17 and
            stats.get("faith", 0) >= 17 and
            stats.get("vitality", 0) >= 17 and
            stats.get("agility", 0) >= 17 and
            stats.get("luck", 0) >= 17):
            available.append("ninja")
        
        return available
    
    def _highlight_button(self, button: pygame_gui.elements.UIButton) -> None:
        """ボタンをハイライト"""
        # TODO: pygame_guiのテーマでハイライトスタイルを定義
        if hasattr(button, 'selected'):
            button.selected = True
    
    def _unhighlight_button(self, button: pygame_gui.elements.UIButton) -> None:
        """ボタンのハイライトを解除"""
        if hasattr(button, 'selected'):
            button.selected = False
    
    
    def _validate_name(self, data: Dict[str, Any]) -> bool:
        """名前を検証"""
        name = data.get("name", "")
        logger.info(f"[DEBUG] _validate_name: name='{name}', wizard_data={self.wizard_data}")
        
        # デバッグ用：名前が空の場合はデフォルト名を設定
        if not name:
            default_name = "TestCharacter"
            logger.info(f"[DEBUG] Setting default name: {default_name}")
            self.wizard_data["name"] = default_name
            if hasattr(self, 'name_input'):
                self.name_input.set_text(default_name)
            return True
        
        if len(name) > 20:
            self._show_message("名前は20文字以内で入力してください", "warning") 
            return False
        
        # TODO: 文字種の検証
        
        return True
    
    def _validate_race(self, data: Dict[str, Any]) -> bool:
        """種族を検証"""
        race = data.get("race")
        if not race:
            # デバッグ用：種族が選択されていない場合は自動的にhumanを設定
            logger.info("[DEBUG] _validate_race: No race selected, auto-setting human")
            self.wizard_data["race"] = "human"
            data["race"] = "human"
            race = "human"
        
        valid_races = ["human", "elf", "dwarf", "gnome", "hobbit"]
        if race not in valid_races:
            self._show_message("無効な種族です", "error")
            return False
        
        return True
    
    def _validate_stats(self, data: Dict[str, Any]) -> bool:
        """能力値を検証"""
        stats = data.get("stats")
        if not stats:
            # デバッグ用：デフォルト能力値を設定
            default_stats = {
                "strength": 12,
                "intelligence": 12,
                "faith": 12,
                "vitality": 12,
                "agility": 12,
                "luck": 12
            }
            logger.info(f"[DEBUG] Setting default stats: {default_stats}")
            self.wizard_data["stats"] = default_stats
            return True
        
        required_stats = ["strength", "intelligence", "faith", "vitality", "agility", "luck"]
        for stat in required_stats:
            if stat not in stats:
                self._show_message(f"能力値が不完全です: {stat}", "error")
                return False
            
            value = stats[stat]
            if not isinstance(value, int) or value < 3 or value > 18:
                self._show_message(f"無効な能力値です: {stat}={value}", "error")
                return False
        
        return True
    
    def _validate_class(self, data: Dict[str, Any]) -> bool:
        """職業を検証"""
        char_class = data.get("class")
        if not char_class:
            # デバッグ用：職業が選択されていない場合は自動的にfighterを設定
            logger.info("[DEBUG] _validate_class: No class selected, auto-setting fighter")
            self.wizard_data["class"] = "fighter"
            data["class"] = "fighter"
            char_class = "fighter"
        
        # 選択可能な職業かチェック
        available = self._get_available_classes()
        if char_class not in available:
            self._show_message("その職業は選択できません", "error")
            return False
        
        return True
    
    def get_debug_info(self) -> Dict[str, Any]:
        """デバッグ情報を取得
        
        Returns:
            デバッグ情報の辞書
        """
        try:
            # 親クラスのデバッグ情報を取得
            debug_info = super().get_debug_info()
        except (TypeError, AttributeError):
            # super()が失敗した場合（テスト時など）は基本情報を作成
            debug_info = {
                "service_id": getattr(self, 'service_id', 'character_creation'),
                "is_visible": getattr(self, 'is_visible', True),
                "container_valid": hasattr(self, 'container') and self.container is not None
            }
        
        # CharacterCreationWizard固有の情報を追加
        debug_info.update({
            "wizard_type": "character_creation",
            "wizard_data": self.wizard_data.copy() if hasattr(self, 'wizard_data') else {},
            "current_step": (self.steps[self.current_step_index].id 
                           if hasattr(self, 'steps') and self.steps 
                           and hasattr(self, 'current_step_index') 
                           and 0 <= self.current_step_index < len(self.steps) 
                           else None),
            "ui_elements": {
                "race_buttons": len(getattr(self, 'race_buttons', {})),
                "class_buttons": len(getattr(self, 'class_buttons', {})),
                "stat_labels": len(getattr(self, 'stat_labels', {})),
                "confirm_labels": len(getattr(self, 'confirm_labels', [])),
                "name_input_exists": hasattr(self, 'name_input') and self.name_input is not None,
                "roll_button_exists": hasattr(self, 'roll_button') and self.roll_button is not None,
                "test_name_button_exists": hasattr(self, 'test_name_button') and self.test_name_button is not None
            },
            "validation_status": self._get_validation_status()
        })
        
        return debug_info
    
    def _get_validation_status(self) -> Dict[str, bool]:
        """検証状態を安全に取得"""
        if not hasattr(self, 'wizard_data'):
            return {"name": False, "race": False, "stats": False, "class": False}
        
        validation_status = {}
        
        # 各検証メソッドを安全に呼び出し
        try:
            validation_status["name"] = (
                self._validate_name(self.wizard_data) if "name" in self.wizard_data else False
            )
        except Exception:
            validation_status["name"] = False
            
        try:
            validation_status["race"] = (
                self._validate_race(self.wizard_data) if "race" in self.wizard_data else False
            )
        except Exception:
            validation_status["race"] = False
            
        try:
            validation_status["stats"] = (
                self._validate_stats(self.wizard_data) if "stats" in self.wizard_data else False
            )
        except Exception:
            validation_status["stats"] = False
            
        try:
            validation_status["class"] = (
                self._validate_class(self.wizard_data) if "class" in self.wizard_data else False
            )
        except Exception:
            validation_status["class"] = False
        
        return validation_status