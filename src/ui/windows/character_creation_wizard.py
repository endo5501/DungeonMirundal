"""キャラクター作成ウィザード - WindowSystem用キャラクター作成UI"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import pygame
import pygame_gui

from src.ui.window_system.window import Window
from src.ui.window_system.window_manager import WindowManager
from src.character.character import Character
from src.character.stats import BaseStats, StatGenerator, StatValidator
from src.core.config_manager import config_manager
from src.utils.logger import logger


class CreationStep(Enum):
    """作成ステップ"""
    NAME_INPUT = "name_input"
    RACE_SELECTION = "race_selection"
    STATS_GENERATION = "stats_generation"
    CLASS_SELECTION = "class_selection"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"


class CharacterCreationWizard(Window):
    """キャラクター作成ウィザード - WindowSystem準拠"""
    
    def __init__(self, window_id: str, parent: Optional[Window] = None, modal: bool = True, callback: Optional[Callable] = None):
        """
        キャラクター作成ウィザードを初期化
        
        Args:
            window_id: ウィンドウID
            parent: 親ウィンドウ
            modal: モーダル表示
            callback: 作成完了時のコールバック
        """
        super().__init__(window_id, parent, modal)
        
        # コールバック
        self.callback = callback  # 作成完了時のコールバック
        self.cancel_callback: Optional[Callable] = None  # キャンセル時のコールバック
        
        # 現在のステップ
        self.current_step = CreationStep.NAME_INPUT
        
        # 作成中のキャラクターデータ
        self.character_data = {
            "name": "",
            "race": "",
            "class": "",
            "stats": None
        }
        
        # UI要素
        self.ui_elements: Dict[str, pygame_gui.UIElement] = {}
        self.content_panel: Optional[pygame_gui.elements.UIPanel] = None
        
        # 設定データ
        self.char_config = config_manager.load_config("characters")
        self.races_config = self.char_config.get("races", {})
        self.classes_config = self.char_config.get("classes", {})
        
        # ステータス生成器
        self.stat_generator = StatGenerator()
        self.stat_validator = StatValidator()
        
        logger.info(f"CharacterCreationWizard作成: {window_id}")

    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            window_manager = WindowManager.get_instance()
            self.ui_manager = window_manager.ui_manager
            self.surface = window_manager.screen
        
        if not self.surface:
            logger.error("画面サーフェスが設定されていません")
            return
        
        # ウィンドウサイズ設定
        screen_rect = self.surface.get_rect()
        self.rect = pygame.Rect(
            screen_rect.width // 6,
            screen_rect.height // 8,
            screen_rect.width * 2 // 3,
            screen_rect.height * 3 // 4
        )
        
        # メインパネル作成
        self.content_panel = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager,
            element_id="character_creation_wizard_panel"
        )
        self.ui_elements["main_panel"] = self.content_panel
        
        # 現在のステップに応じてコンテンツを作成
        self._create_content_for_current_step()
        
        logger.debug(f"CharacterCreationWizard UI要素を作成: {self.window_id}")

    def _create_content_for_current_step(self) -> None:
        """現在のステップに応じてコンテンツを作成"""
        if self.current_step == CreationStep.NAME_INPUT:
            self.create_name_input_step()
        elif self.current_step == CreationStep.RACE_SELECTION:
            self.create_race_selection_step()
        elif self.current_step == CreationStep.STATS_GENERATION:
            self.create_stats_generation_step()
        elif self.current_step == CreationStep.CLASS_SELECTION:
            self.create_class_selection_step()
        elif self.current_step == CreationStep.CONFIRMATION:
            self.create_confirmation_step()
        elif self.current_step == CreationStep.COMPLETED:
            self.create_completed_step()

    def start_wizard(self) -> None:
        """ウィザードを開始"""
        self.current_step = CreationStep.NAME_INPUT
        if self.state.value == "shown":
            self._clear_content()
            self.create_name_input_step()

    def create_name_input_step(self) -> None:
        """名前入力ステップのUI要素を作成"""
        if not self.content_panel:
            return
        
        # タイトル
        title_rect = pygame.Rect(20, 20, 400, 40)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=config_manager.get_text("character.creation_title"),
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        # ステップ表示
        step_rect = pygame.Rect(20, 70, 500, 30)
        step_label = pygame_gui.elements.UILabel(
            relative_rect=step_rect,
            text="ステップ 1/5: キャラクター名を入力してください",
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["step_label"] = step_label
        
        # 名前入力フィールド
        name_label_rect = pygame.Rect(20, 120, 150, 30)
        name_label = pygame_gui.elements.UILabel(
            relative_rect=name_label_rect,
            text="キャラクター名:",
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["name_label"] = name_label
        
        name_entry_rect = pygame.Rect(180, 120, 300, 30)
        name_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=name_entry_rect,
            manager=self.ui_manager,
            container=self.content_panel,
            initial_text=self.character_data["name"]
        )
        self.ui_elements["name_entry"] = name_entry
        
        # 注意事項
        note_rect = pygame.Rect(20, 170, 500, 60)
        note_text = "※ 名前は1-50文字で入力してください。\\n※ 特殊文字は使用できません。"
        note_label = pygame_gui.elements.UILabel(
            relative_rect=note_rect,
            text=note_text,
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["note"] = note_label
        
        # ボタン
        self._create_navigation_buttons(first_step=True)

    def create_race_selection_step(self) -> None:
        """種族選択ステップのUI要素を作成"""
        if not self.content_panel:
            return
        
        # タイトル
        title_rect = pygame.Rect(20, 20, 400, 40)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="種族選択",
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        # ステップ表示
        step_rect = pygame.Rect(20, 70, 500, 30)
        step_label = pygame_gui.elements.UILabel(
            relative_rect=step_rect,
            text="ステップ 2/5: 種族を選択してください",
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["step_label"] = step_label
        
        # 種族リスト
        y_offset = 110
        for i, (race_id, race_data) in enumerate(self.races_config.items()):
            race_name = race_data.get("name", race_id)
            race_description = race_data.get("description", "")
            
            # 種族ボタン
            button_rect = pygame.Rect(20, y_offset + i * 60, 400, 35)
            is_selected = self.character_data["race"] == race_id
            button_text = f"● {race_name}" if is_selected else f"○ {race_name}"
            
            race_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=button_text,
                manager=self.ui_manager,
                container=self.content_panel,
                object_id=f"race_button_{race_id}"
            )
            self.ui_elements[f"race_button_{race_id}"] = race_button
            
            # 説明
            desc_rect = pygame.Rect(40, y_offset + i * 60 + 40, 400, 20)
            desc_label = pygame_gui.elements.UILabel(
                relative_rect=desc_rect,
                text=race_description,
                manager=self.ui_manager,
                container=self.content_panel
            )
            self.ui_elements[f"race_desc_{race_id}"] = desc_label
        
        # ボタン
        self._create_navigation_buttons()

    def create_stats_generation_step(self) -> None:
        """ステータス生成ステップのUI要素を作成"""
        if not self.content_panel:
            return
        
        # タイトル
        title_rect = pygame.Rect(20, 20, 400, 40)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="ステータス生成",
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        # ステップ表示
        step_rect = pygame.Rect(20, 70, 500, 30)
        step_label = pygame_gui.elements.UILabel(
            relative_rect=step_rect,
            text="ステップ 3/5: ステータスを生成してください",
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["step_label"] = step_label
        
        # ステータス表示
        if self.character_data["stats"]:
            self._create_stats_display()
        else:
            # 初回生成案内
            info_rect = pygame.Rect(20, 120, 500, 30)
            info_label = pygame_gui.elements.UILabel(
                relative_rect=info_rect,
                text="「ステータス生成」ボタンを押してステータスを生成してください",
                manager=self.ui_manager,
                container=self.content_panel
            )
            self.ui_elements["info"] = info_label
        
        # 生成・再生成ボタン
        generate_rect = pygame.Rect(20, 350, 120, 35)
        generate_text = "再生成" if self.character_data["stats"] else "ステータス生成"
        generate_button = pygame_gui.elements.UIButton(
            relative_rect=generate_rect,
            text=generate_text,
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="generate_stats_button"
        )
        self.ui_elements["generate_stats_button"] = generate_button
        
        # ボタン
        self._create_navigation_buttons()

    def _create_stats_display(self) -> None:
        """ステータス表示を作成"""
        if not self.character_data["stats"]:
            return
        
        stats = self.character_data["stats"]
        
        # ステータス表示エリア
        stats_rect = pygame.Rect(20, 120, 300, 200)
        stats_text = f"""生成されたステータス:

筋力: {stats.strength}
敏捷性: {stats.agility}
知力: {stats.intelligence}
信仰: {stats.faith}
運: {stats.luck}

合計: {stats.strength + stats.agility + stats.intelligence + stats.faith + stats.luck}"""
        
        stats_label = pygame_gui.elements.UILabel(
            relative_rect=stats_rect,
            text=stats_text,
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["stats_display"] = stats_label

    def create_class_selection_step(self) -> None:
        """職業選択ステップのUI要素を作成"""
        if not self.content_panel:
            return
        
        # タイトル
        title_rect = pygame.Rect(20, 20, 400, 40)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="職業選択",
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        # ステップ表示
        step_rect = pygame.Rect(20, 70, 500, 30)
        step_label = pygame_gui.elements.UILabel(
            relative_rect=step_rect,
            text="ステップ 4/5: 職業を選択してください",
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["step_label"] = step_label
        
        # 職業リスト
        y_offset = 110
        for i, (class_id, class_data) in enumerate(self.classes_config.items()):
            class_name = class_data.get("name", class_id)
            class_description = class_data.get("description", "")
            
            # 職業選択可能性チェック
            can_select = self._can_select_class(class_id)
            
            # 職業ボタン
            button_rect = pygame.Rect(20, y_offset + i * 60, 400, 35)
            is_selected = self.character_data["class"] == class_id
            
            if can_select:
                button_text = f"● {class_name}" if is_selected else f"○ {class_name}"
            else:
                button_text = f"× {class_name} (要件不足)"
            
            class_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=button_text,
                manager=self.ui_manager,
                container=self.content_panel,
                object_id=f"class_button_{class_id}",
                tool_tip_text=None if can_select else "ステータス要件を満たしていません"
            )
            if not can_select:
                class_button.disable()
            
            self.ui_elements[f"class_button_{class_id}"] = class_button
            
            # 説明
            desc_rect = pygame.Rect(40, y_offset + i * 60 + 40, 400, 20)
            desc_label = pygame_gui.elements.UILabel(
                relative_rect=desc_rect,
                text=class_description,
                manager=self.ui_manager,
                container=self.content_panel
            )
            self.ui_elements[f"class_desc_{class_id}"] = desc_label
        
        # ボタン
        self._create_navigation_buttons()

    def create_confirmation_step(self) -> None:
        """確認ステップのUI要素を作成"""
        if not self.content_panel:
            return
        
        # タイトル
        title_rect = pygame.Rect(20, 20, 400, 40)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="キャラクター確認",
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        # ステップ表示
        step_rect = pygame.Rect(20, 70, 500, 30)
        step_label = pygame_gui.elements.UILabel(
            relative_rect=step_rect,
            text="ステップ 5/5: 作成するキャラクターを確認してください",
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["step_label"] = step_label
        
        # キャラクター概要
        summary_text = self.generate_character_summary()
        summary_rect = pygame.Rect(20, 110, 500, 300)
        summary_label = pygame_gui.elements.UILabel(
            relative_rect=summary_rect,
            text=summary_text,
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["summary"] = summary_label
        
        # 作成ボタン
        create_rect = pygame.Rect(self.rect.width - 250, self.rect.height - 60, 100, 35)
        create_button = pygame_gui.elements.UIButton(
            relative_rect=create_rect,
            text="作成",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="create_character_button"
        )
        self.ui_elements["create_character_button"] = create_button
        
        # 戻る・キャンセルボタン
        back_rect = pygame.Rect(self.rect.width - 370, self.rect.height - 60, 100, 35)
        back_button = pygame_gui.elements.UIButton(
            relative_rect=back_rect,
            text="戻る",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="back_button"
        )
        self.ui_elements["back_button"] = back_button
        
        cancel_rect = pygame.Rect(self.rect.width - 130, self.rect.height - 60, 100, 35)
        cancel_button = pygame_gui.elements.UIButton(
            relative_rect=cancel_rect,
            text="キャンセル",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="cancel_button"
        )
        self.ui_elements["cancel_button"] = cancel_button

    def create_completed_step(self) -> None:
        """完了ステップのUI要素を作成"""
        if not self.content_panel:
            return
        
        # タイトル
        title_rect = pygame.Rect(20, 20, 400, 40)
        title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="キャラクター作成完了",
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["title"] = title
        
        # 完了メッセージ
        message_rect = pygame.Rect(20, 100, 500, 100)
        message_text = f"キャラクター「{self.character_data['name']}」の作成が完了しました！"
        message_label = pygame_gui.elements.UILabel(
            relative_rect=message_rect,
            text=message_text,
            manager=self.ui_manager,
            container=self.content_panel
        )
        self.ui_elements["message"] = message_label
        
        # 閉じるボタン
        close_rect = pygame.Rect(self.rect.width - 120, self.rect.height - 60, 100, 35)
        close_button = pygame_gui.elements.UIButton(
            relative_rect=close_rect,
            text="閉じる",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id="close_button"
        )
        self.ui_elements["close_button"] = close_button

    def _create_navigation_buttons(self, first_step: bool = False) -> None:
        """ナビゲーションボタンを作成"""
        # 次へボタン
        next_rect = pygame.Rect(self.rect.width - 120, self.rect.height - 60, 100, 35)
        next_button = pygame_gui.elements.UIButton(
            relative_rect=next_rect,
            text="次へ",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id=pygame_gui.core.ObjectID(object_id="next_button")
        )
        self.ui_elements["next_button"] = next_button
        
        # 戻るボタン（最初のステップ以外）
        if not first_step:
            back_rect = pygame.Rect(self.rect.width - 240, self.rect.height - 60, 100, 35)
            back_button = pygame_gui.elements.UIButton(
                relative_rect=back_rect,
                text="戻る",
                manager=self.ui_manager,
                container=self.content_panel,
                object_id=pygame_gui.core.ObjectID(object_id="back_button")
            )
            self.ui_elements["back_button"] = back_button
        
        # キャンセルボタン
        cancel_rect = pygame.Rect(20, self.rect.height - 60, 100, 35)
        cancel_button = pygame_gui.elements.UIButton(
            relative_rect=cancel_rect,
            text="キャンセル",
            manager=self.ui_manager,
            container=self.content_panel,
            object_id=pygame_gui.core.ObjectID(object_id="cancel_button")
        )
        self.ui_elements["cancel_button"] = cancel_button

    def set_character_name(self, name: str) -> None:
        """キャラクター名を設定"""
        self.character_data["name"] = name

    def set_character_race(self, race: str) -> None:
        """種族を設定"""
        self.character_data["race"] = race

    def set_character_class(self, char_class: str) -> None:
        """職業を設定"""
        self.character_data["class"] = char_class

    def set_character_stats(self, stats: BaseStats) -> None:
        """ステータスを設定"""
        self.character_data["stats"] = stats

    def generate_character_stats(self) -> None:
        """キャラクターステータスを生成"""
        if self.character_data["race"]:
            stats = self.stat_generator.generate_stats(self.character_data["race"])
            self.set_character_stats(stats)

    def reroll_character_stats(self) -> None:
        """ステータスを再生成"""
        self.generate_character_stats()
        # 現在の表示を更新
        if self.current_step == CreationStep.STATS_GENERATION:
            self._clear_content()
            self.create_stats_generation_step()

    def proceed_to_next_step(self) -> None:
        """次のステップに進む"""
        next_step_map = {
            CreationStep.NAME_INPUT: CreationStep.RACE_SELECTION,
            CreationStep.RACE_SELECTION: CreationStep.STATS_GENERATION,
            CreationStep.STATS_GENERATION: CreationStep.CLASS_SELECTION,
            CreationStep.CLASS_SELECTION: CreationStep.CONFIRMATION,
            CreationStep.CONFIRMATION: CreationStep.COMPLETED
        }
        
        if self.current_step in next_step_map:
            self.next_step(next_step_map[self.current_step])

    def go_to_previous_step(self) -> None:
        """前のステップに戻る"""
        previous_step_map = {
            CreationStep.RACE_SELECTION: CreationStep.NAME_INPUT,
            CreationStep.STATS_GENERATION: CreationStep.RACE_SELECTION,
            CreationStep.CLASS_SELECTION: CreationStep.STATS_GENERATION,
            CreationStep.CONFIRMATION: CreationStep.CLASS_SELECTION
        }
        
        if self.current_step in previous_step_map:
            self.previous_step(previous_step_map[self.current_step])

    def next_step(self, step: CreationStep) -> None:
        """指定ステップに進む"""
        self.current_step = step
        self._clear_content()
        self._create_content_for_current_step()

    def previous_step(self, step: CreationStep) -> None:
        """指定ステップに戻る"""
        self.current_step = step
        self._clear_content()
        self._create_content_for_current_step()

    def validate_step_data(self, step: CreationStep) -> bool:
        """ステップのデータを検証"""
        if step == CreationStep.NAME_INPUT:
            name = self.character_data["name"]
            # 名前が空の場合、デフォルト名を設定
            if not name or len(name.strip()) == 0:
                default_name = "テスト冒険者"
                self.set_character_name(default_name)
                logger.info(f"空の名前にデフォルト名を設定: '{default_name}'")
                return True
            return len(name) <= 50
        elif step == CreationStep.RACE_SELECTION:
            return self.character_data["race"] in self.races_config
        elif step == CreationStep.STATS_GENERATION:
            return self.character_data["stats"] is not None
        elif step == CreationStep.CLASS_SELECTION:
            return self.character_data["class"] in self.classes_config
        elif step == CreationStep.CONFIRMATION:
            return self.validate_character_data()
        
        return False

    def validate_character_data(self) -> bool:
        """キャラクターデータ全体を検証"""
        return (
            self.character_data["name"] and 
            self.character_data["race"] and 
            self.character_data["class"] and 
            self.character_data["stats"] is not None
        )

    def _can_select_class(self, class_id: str) -> bool:
        """職業選択可能性をチェック"""
        if not self.character_data["stats"]:
            return False
        
        # クラス要件をチェック（簡単な実装）
        stats = self.character_data["stats"]
        class_data = self.classes_config.get(class_id, {})
        requirements = class_data.get("requirements", {})
        
        for stat, min_value in requirements.items():
            if hasattr(stats, stat) and getattr(stats, stat) < min_value:
                return False
        
        return True

    def generate_character_summary(self) -> str:
        """キャラクター概要を生成"""
        name = self.character_data["name"]
        race_id = self.character_data["race"]
        class_id = self.character_data["class"]
        stats = self.character_data["stats"]
        
        race_name = self.races_config.get(race_id, {}).get("name", race_id)
        class_name = self.classes_config.get(class_id, {}).get("name", class_id)
        
        summary = f"""作成するキャラクター:

名前: {name}
種族: {race_name}
職業: {class_name}

ステータス:"""
        
        if stats:
            summary += f"""
筋力: {stats.strength}
敏捷性: {stats.agility}
知力: {stats.intelligence}
信仰: {stats.faith}
運: {stats.luck}
合計: {stats.strength + stats.agility + stats.intelligence + stats.faith + stats.luck}"""
        
        return summary

    def create_character(self) -> None:
        """キャラクターを作成"""
        if not self.validate_character_data():
            logger.error("キャラクターデータが不完全です")
            return
        
        try:
            character = Character(
                name=self.character_data["name"],
                race=self.character_data["race"],
                character_class=self.character_data["class"],
                base_stats=self.character_data["stats"]
            )
            
            self.current_step = CreationStep.COMPLETED
            self._clear_content()
            self.create_completed_step()
            
            if self.callback:
                self.callback(character)
                
            logger.info(f"キャラクター作成完了: {character.name}")
            
        except Exception as e:
            logger.error(f"キャラクター作成エラー: {e}")

    def cancel_wizard(self) -> None:
        """ウィザードをキャンセル"""
        if self.cancel_callback:
            self.cancel_callback()
        else:
            self.hide()

    def set_cancel_callback(self, callback: Callable) -> None:
        """キャンセルコールバックを設定"""
        self.cancel_callback = callback

    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            return self._handle_button_press(event)
        elif event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            return self._handle_text_entry(event)
        return False

    def _handle_button_press(self, event: pygame.event.Event) -> bool:
        """ボタン押下イベントを処理"""
        element_id = ''
        
        # pygame-guiのイベント構造に対応した確実な取得方法
        if hasattr(event, 'ui_object_id') and hasattr(event.ui_object_id, 'object_id'):
            element_id = event.ui_object_id.object_id
            logger.info(f"ui_object_id.object_idから取得: '{element_id}'")
        elif hasattr(event, 'ui_element'):
            # UI要素からobject_idを検索
            for key, element in self.ui_elements.items():
                if element == event.ui_element:
                    element_id = key
                    logger.info(f"UI要素の照合から取得: '{element_id}'")
                    break
        
        logger.info(f"ボタン押下イベント処理: element_id='{element_id}', step={self.current_step.value}")
        
        # 共通ボタン
        if element_id == "next_button":
            logger.info(f"次へボタンが押されました - 現在のステップ: {self.current_step.value}")
            if self._validate_current_step():
                logger.info("バリデーション成功 - 次のステップに進みます")
                self.proceed_to_next_step()
            else:
                logger.warning("バリデーション失敗 - 次のステップに進めません")
            return True
        elif element_id == "back_button":
            self.go_to_previous_step()
            return True
        elif element_id == "cancel_button":
            self.cancel_wizard()
            return True
        
        # ステップ固有のボタン
        if self.current_step == CreationStep.RACE_SELECTION:
            if element_id.startswith("race_button_"):
                race_id = element_id.split("_")[-1]
                self.set_character_race(race_id)
                self._clear_content()
                self.create_race_selection_step()
                return True
        
        elif self.current_step == CreationStep.STATS_GENERATION:
            if element_id == "generate_stats_button":
                if self.character_data["stats"]:
                    self.reroll_character_stats()
                else:
                    self.generate_character_stats()
                    self._clear_content()
                    self.create_stats_generation_step()
                return True
        
        elif self.current_step == CreationStep.CLASS_SELECTION:
            if element_id.startswith("class_button_"):
                class_id = element_id.split("_")[-1]
                if self._can_select_class(class_id):
                    self.set_character_class(class_id)
                    self._clear_content()
                    self.create_class_selection_step()
                return True
        
        elif self.current_step == CreationStep.CONFIRMATION:
            if element_id == "create_character_button":
                self.create_character()
                return True
        
        elif self.current_step == CreationStep.COMPLETED:
            if element_id == "close_button":
                self.hide()
                return True
        
        return False

    def _handle_text_entry(self, event: pygame.event.Event) -> bool:
        """テキスト入力イベントを処理"""
        if self.current_step == CreationStep.NAME_INPUT:
            name_entry = self.ui_elements.get("name_entry")
            if name_entry and event.ui_element == name_entry:
                self.set_character_name(name_entry.get_text())
                return True
        return False

    def _validate_current_step(self) -> bool:
        """現在のステップのデータを検証"""
        logger.info(f"ステップバリデーション開始: {self.current_step.value}")
        
        # 名前入力の場合、テキストエントリから最新の値を取得
        if self.current_step == CreationStep.NAME_INPUT:
            name_entry = self.ui_elements.get("name_entry")
            if name_entry:
                current_name = name_entry.get_text()
                logger.info(f"名前入力から取得: '{current_name}'")
                self.set_character_name(current_name)
            else:
                logger.warning("name_entryが見つかりません")
        
        result = self.validate_step_data(self.current_step)
        logger.info(f"バリデーション結果: {result}, データ: {self.character_data}")
        return result

    def _clear_content(self) -> None:
        """コンテンツをクリア"""
        for element_id, element in list(self.ui_elements.items()):
            if element_id != "main_panel":
                element.kill()
                del self.ui_elements[element_id]

    def destroy(self) -> None:
        """ウィンドウを破棄"""
        self._clear_content()
        
        if self.content_panel:
            self.content_panel.kill()
            self.content_panel = None
        
        # キャラクターデータをリセット
        self.character_data = {
            "name": "",
            "race": "",
            "class": "",
            "stats": None
        }
        
        super().destroy()
        logger.debug(f"CharacterCreationWizardを破棄: {self.window_id}")

    def on_show(self) -> None:
        """表示時の処理"""
        logger.debug(f"CharacterCreationWizardを表示: {self.window_id}")

    def on_hide(self) -> None:
        """非表示時の処理"""
        logger.debug(f"CharacterCreationWizardを非表示: {self.window_id}")

    def on_update(self, time_delta: float) -> None:
        """更新処理"""
        pass