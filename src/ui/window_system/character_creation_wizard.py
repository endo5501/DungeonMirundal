"""
CharacterCreationWizard クラス

キャラクター作成ウィザード用のウィンドウ
"""

import pygame
import pygame_gui
import random
from typing import Dict, List, Any, Optional
from pathlib import Path

from .window import Window
from .character_creation_types import (
    WizardStep, CharacterData, CharacterStats, WizardConfig, StepValidationResult
)
from .character_creation_step_manager import CharacterCreationStepManager
from .character_creation_stats_generator import CharacterCreationStatsGenerator
from .character_creation_ui_factory import CharacterCreationUIFactory
from src.utils.logger import logger


class CharacterCreationWizard(Window):
    """
    キャラクター作成ウィザードクラス
    
    5段階のステップでキャラクター作成を行う
    """
    
    def __init__(self, window_id: str, wizard_config: Dict[str, Any], 
                 parent: Optional[Window] = None, modal: bool = True):
        """
        キャラクター作成ウィザードを初期化
        
        Args:
            window_id: ウィンドウID
            wizard_config: ウィザード設定辞書
            parent: 親ウィンドウ
            modal: モーダルウィンドウかどうか
        """
        super().__init__(window_id, parent, modal)
        
        # 設定の検証と変換
        self.wizard_config = self._validate_and_convert_config(wizard_config)
        
        # Extract Classパターン適用 - 専門クラス
        self.step_manager = CharacterCreationStepManager()
        self.stats_generator = CharacterCreationStatsGenerator(self.wizard_config)
        self.ui_factory: Optional[CharacterCreationUIFactory] = None
        
        # キャラクターデータ
        self.character_data = self._initialize_character_data()
        
        # UI要素
        self.main_container: Optional[pygame_gui.core.UIElement] = None
        self.step_title: Optional[pygame_gui.elements.UILabel] = None
        self.content_container: Optional[pygame_gui.core.UIElement] = None
        self.button_container: Optional[pygame_gui.core.UIElement] = None
        
        # ステップ別UI要素
        self.current_ui_elements: Dict[str, Any] = {}
        
        logger.debug(f"CharacterCreationWizardを初期化: {window_id}")
    
    @property
    def current_step(self) -> WizardStep:
        """現在のステップを取得（リファクタリング用プロパティ）"""
        return self.step_manager.current_step
    
    @property
    def current_step_index(self) -> int:
        """現在のステップインデックスを取得（リファクタリング用プロパティ）"""
        return self.step_manager.current_step_index
    
    @property
    def steps(self) -> List[WizardStep]:
        """全ステップリストを取得（リファクタリング用プロパティ）"""
        return self.step_manager.steps
    
    def _validate_and_convert_config(self, config: Dict[str, Any]) -> WizardConfig:
        """設定を検証してWizardConfigに変換"""
        if 'character_classes' not in config:
            raise ValueError("Wizard config must contain 'character_classes'")
        if 'races' not in config:
            raise ValueError("Wizard config must contain 'races'")
        
        wizard_config = WizardConfig(
            character_classes=config['character_classes'],
            races=config['races'],
            title=config.get('title', 'キャラクター作成'),
            allow_stats_reroll=config.get('allow_stats_reroll', True),
            min_name_length=config.get('min_name_length', 1),
            max_name_length=config.get('max_name_length', 20)
        )
        
        wizard_config.validate()
        return wizard_config
    
    def _initialize_character_data(self) -> Dict[str, Any]:
        """キャラクターデータを初期化"""
        return {
            'name': '',
            'race': '',
            'character_class': '',
            'level': 1
        }
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            self._initialize_ui_manager()
            self._calculate_layout()
            self._create_main_container()
            self._create_step_title()
            self._create_content_container()
            self._create_button_container()
            self._create_current_step_ui()
        
        logger.debug(f"CharacterCreationWizard UI要素を作成: {self.window_id}")
    
    def _initialize_ui_manager(self) -> None:
        """UIManagerを初期化"""
        screen_width = 1024
        screen_height = 768
        self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
    
    def _calculate_layout(self) -> None:
        """ウィザード画面のレイアウトを計算"""
        wizard_width = 600
        wizard_height = 500
        
        # 画面中央に配置
        screen_width = 1024
        screen_height = 768
        wizard_x = (screen_width - wizard_width) // 2
        wizard_y = (screen_height - wizard_height) // 2
        
        self.rect = pygame.Rect(wizard_x, wizard_y, wizard_width, wizard_height)
    
    def _create_main_container(self) -> None:
        """メインコンテナを作成"""
        self.main_container = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager
        )
    
    def _create_step_title(self) -> None:
        """ステップタイトルを作成"""
        title_rect = pygame.Rect(20, 20, self.rect.width - 40, 40)
        self.step_title = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=self._get_step_title(),
            manager=self.ui_manager,
            container=self.main_container
        )
    
    def _create_content_container(self) -> None:
        """コンテンツコンテナを作成"""
        content_rect = pygame.Rect(20, 80, self.rect.width - 40, 350)
        self.content_container = pygame_gui.elements.UIPanel(
            relative_rect=content_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
    
    def _create_button_container(self) -> None:
        """ボタンコンテナを作成"""
        button_rect = pygame.Rect(20, 450, self.rect.width - 40, 40)
        self.button_container = pygame_gui.elements.UIPanel(
            relative_rect=button_rect,
            manager=self.ui_manager,
            container=self.main_container
        )
        
        # ナビゲーションボタンを作成
        self._create_navigation_buttons()
    
    def _create_navigation_buttons(self) -> None:
        """ナビゲーションボタンを作成"""
        button_width = 80
        button_height = 30
        button_spacing = 10
        
        # キャンセルボタン（左端）
        cancel_rect = pygame.Rect(0, 5, button_width, button_height)
        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=cancel_rect,
            text='キャンセル',
            manager=self.ui_manager,
            container=self.button_container
        )
        
        # 次へボタン（右端）
        next_x = self.button_container.relative_rect.width - button_width
        next_rect = pygame.Rect(next_x, 5, button_width, button_height)
        self.next_button = pygame_gui.elements.UIButton(
            relative_rect=next_rect,
            text='次へ',
            manager=self.ui_manager,
            container=self.button_container
        )
        
        # 戻るボタン（次へボタンの左）
        back_x = next_x - button_width - button_spacing
        back_rect = pygame.Rect(back_x, 5, button_width, button_height)
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=back_rect,
            text='戻る',
            manager=self.ui_manager,
            container=self.button_container
        )
        
        self._update_button_states()
    
    def _update_button_states(self) -> None:
        """ボタンの状態を更新"""
        # 戻るボタンは最初のステップでは無効
        if hasattr(self, 'back_button'):
            self.back_button.visible = self.current_step_index > 0
        
        # 次へボタンの文字を更新
        if hasattr(self, 'next_button'):
            if self.current_step == WizardStep.CONFIRMATION:
                self.next_button.set_text('完了')
            else:
                self.next_button.set_text('次へ')
    
    def _create_current_step_ui(self) -> None:
        """現在のステップのUI要素を作成"""
        # 既存のUI要素をクリア
        self._clear_current_step_ui()
        
        if self.current_step == WizardStep.NAME_INPUT:
            self._create_name_input_ui()
        elif self.current_step == WizardStep.RACE_SELECTION:
            self._create_race_selection_ui()
        elif self.current_step == WizardStep.STATS_GENERATION:
            self._create_stats_generation_ui()
        elif self.current_step == WizardStep.CLASS_SELECTION:
            self._create_class_selection_ui()
        elif self.current_step == WizardStep.CONFIRMATION:
            self._create_confirmation_ui()
        
        # ステップタイトルを更新
        if self.step_title:
            self.step_title.set_text(self._get_step_title())
        
        # ボタン状態を更新
        self._update_button_states()
    
    def _clear_current_step_ui(self) -> None:
        """現在のステップのUI要素をクリア"""
        for element in self.current_ui_elements.values():
            if hasattr(element, 'kill'):
                element.kill()
        self.current_ui_elements.clear()
    
    def _create_name_input_ui(self) -> None:
        """名前入力UIを作成"""
        # 説明ラベル
        desc_rect = pygame.Rect(20, 20, 400, 30)
        desc_label = pygame_gui.elements.UILabel(
            relative_rect=desc_rect,
            text='キャラクターの名前を入力してください：',
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 名前入力フィールド
        name_rect = pygame.Rect(20, 60, 400, 30)
        name_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=name_rect,
            manager=self.ui_manager,
            container=self.content_container
        )
        name_input.set_text(self.character_data.get('name', ''))
        
        self.current_ui_elements = {
            'desc_label': desc_label,
            'name_input': name_input
        }
    
    def _create_race_selection_ui(self) -> None:
        """種族選択UIを作成"""
        # 説明ラベル
        desc_rect = pygame.Rect(20, 20, 400, 30)
        desc_label = pygame_gui.elements.UILabel(
            relative_rect=desc_rect,
            text='種族を選択してください：',
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 種族リスト
        race_rect = pygame.Rect(20, 60, 400, 200)
        race_list = pygame_gui.elements.UISelectionList(
            relative_rect=race_rect,
            item_list=self.wizard_config.races,
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 現在の選択を設定
        current_race = self.character_data.get('race', '')
        if current_race and current_race in self.wizard_config.races:
            race_list.set_item_list(self.wizard_config.races, current_race)
        
        self.current_ui_elements = {
            'desc_label': desc_label,
            'race_list': race_list
        }
    
    def _create_stats_generation_ui(self) -> None:
        """ステータス生成UIを作成"""
        # 説明ラベル
        desc_rect = pygame.Rect(20, 20, 400, 30)
        desc_label = pygame_gui.elements.UILabel(
            relative_rect=desc_rect,
            text='ステータスを生成してください：',
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # ステータス表示エリア
        stats_rect = pygame.Rect(20, 60, 400, 180)
        stats_panel = pygame_gui.elements.UIPanel(
            relative_rect=stats_rect,
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 生成ボタン
        generate_rect = pygame.Rect(20, 260, 100, 30)
        generate_button = pygame_gui.elements.UIButton(
            relative_rect=generate_rect,
            text='生成',
            manager=self.ui_manager,
            container=self.content_container
        )
        
        self.current_ui_elements = {
            'desc_label': desc_label,
            'stats_panel': stats_panel,
            'generate_button': generate_button
        }
        
        # 既にステータスが生成されている場合は表示
        if 'strength' in self.character_data:
            self._update_stats_display()
    
    def _create_class_selection_ui(self) -> None:
        """職業選択UIを作成"""
        # 説明ラベル
        desc_rect = pygame.Rect(20, 20, 400, 30)
        desc_label = pygame_gui.elements.UILabel(
            relative_rect=desc_rect,
            text='職業を選択してください：',
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 職業リスト
        class_rect = pygame.Rect(20, 60, 400, 200)
        class_list = pygame_gui.elements.UISelectionList(
            relative_rect=class_rect,
            item_list=self.wizard_config.character_classes,
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 現在の選択を設定
        current_class = self.character_data.get('character_class', '')
        if current_class and current_class in self.wizard_config.character_classes:
            class_list.set_item_list(self.wizard_config.character_classes, current_class)
        
        self.current_ui_elements = {
            'desc_label': desc_label,
            'class_list': class_list
        }
    
    def _create_confirmation_ui(self) -> None:
        """確認UIを作成"""
        # 説明ラベル
        desc_rect = pygame.Rect(20, 20, 400, 30)
        desc_label = pygame_gui.elements.UILabel(
            relative_rect=desc_rect,
            text='以下の内容で作成します：',
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # キャラクター情報表示
        info_rect = pygame.Rect(20, 60, 400, 250)
        info_text = self._format_character_info()
        info_label = pygame_gui.elements.UITextBox(
            relative_rect=info_rect,
            html_text=info_text,
            manager=self.ui_manager,
            container=self.content_container
        )
        
        self.current_ui_elements = {
            'desc_label': desc_label,
            'info_label': info_label
        }
    
    def _get_step_title(self) -> str:
        """現在のステップのタイトルを取得"""
        step_titles = {
            WizardStep.NAME_INPUT: "ステップ 1/5: 名前入力",
            WizardStep.RACE_SELECTION: "ステップ 2/5: 種族選択",
            WizardStep.STATS_GENERATION: "ステップ 3/5: ステータス生成",
            WizardStep.CLASS_SELECTION: "ステップ 4/5: 職業選択",
            WizardStep.CONFIRMATION: "ステップ 5/5: 確認"
        }
        return step_titles.get(self.current_step, "キャラクター作成")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if not self.ui_manager:
            return False
        
        # pygame-guiにイベントを渡す
        self.ui_manager.process_events(event)
        
        # キーボードイベント
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB and event.mod == 0:
                # Tabキーで次のステップ
                return self.next_step()
            elif event.key == pygame.K_TAB and event.mod & pygame.KMOD_SHIFT:
                # Shift+Tabキーで前のステップ
                return self.previous_step()
            elif event.key == pygame.K_RETURN:
                # Enterキーで次のステップまたは完了
                if self.current_step == WizardStep.CONFIRMATION:
                    return self.complete_wizard()
                else:
                    return self.next_step()
        
        # ボタンクリック処理
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            return self._handle_button_click(event)
        
        # ステップ固有のイベント処理
        return self._handle_step_specific_event(event)
    
    def _handle_button_click(self, event) -> bool:
        """ボタンクリックを処理"""
        if hasattr(self, 'next_button') and event.ui_element == self.next_button:
            if self.current_step == WizardStep.CONFIRMATION:
                return self.complete_wizard()
            else:
                return self.next_step()
        elif hasattr(self, 'back_button') and event.ui_element == self.back_button:
            return self.previous_step()
        elif hasattr(self, 'cancel_button') and event.ui_element == self.cancel_button:
            return self.cancel_wizard()
        elif 'generate_button' in self.current_ui_elements and event.ui_element == self.current_ui_elements['generate_button']:
            return self.generate_stats()
        
        return False
    
    def _handle_step_specific_event(self, event) -> bool:
        """ステップ固有のイベントを処理"""
        if self.current_step == WizardStep.NAME_INPUT:
            return self._handle_name_input_event(event)
        elif self.current_step == WizardStep.RACE_SELECTION:
            return self._handle_race_selection_event(event)
        elif self.current_step == WizardStep.CLASS_SELECTION:
            return self._handle_class_selection_event(event)
        
        return False
    
    def _handle_name_input_event(self, event) -> bool:
        """名前入力イベントを処理"""
        if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            if 'name_input' in self.current_ui_elements and event.ui_element == self.current_ui_elements['name_input']:
                new_name = event.text
                self.character_data['name'] = new_name
                return True
        return False
    
    def _handle_race_selection_event(self, event) -> bool:
        """種族選択イベントを処理"""
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if 'race_list' in self.current_ui_elements and event.ui_element == self.current_ui_elements['race_list']:
                selected_race = event.text
                self.character_data['race'] = selected_race
                return True
        return False
    
    def _handle_class_selection_event(self, event) -> bool:
        """職業選択イベントを処理"""
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if 'class_list' in self.current_ui_elements and event.ui_element == self.current_ui_elements['class_list']:
                selected_class = event.text
                self.character_data['character_class'] = selected_class
                return True
        return False
    
    def set_character_name(self, name: str) -> bool:
        """キャラクター名を設定"""
        if not name.strip():
            return False
        
        if len(name) < self.wizard_config.min_name_length or len(name) > self.wizard_config.max_name_length:
            return False
        
        self.character_data['name'] = name.strip()
        
        # UI要素を更新
        if 'name_input' in self.current_ui_elements:
            self.current_ui_elements['name_input'].set_text(name)
        
        return True
    
    def set_character_race(self, race: str) -> bool:
        """キャラクター種族を設定"""
        if race not in self.wizard_config.races:
            return False
        
        self.character_data['race'] = race
        return True
    
    def set_character_class(self, character_class: str) -> bool:
        """キャラクター職業を設定"""
        if character_class not in self.wizard_config.character_classes:
            return False
        
        self.character_data['character_class'] = character_class
        return True
    
    def generate_stats(self) -> bool:
        """ステータスを生成"""
        # Extract Classパターン適用 - ステータス生成を専門クラスに委譲
        race = self.character_data.get('race', '')
        stats = self.stats_generator.generate_stats(race)
        
        # キャラクターデータに追加
        self.character_data.update(stats.to_dict())
        
        # UI表示を更新
        self._update_stats_display()
        
        logger.debug(f"ステータスを生成: {stats}")
        return True
    
    def _roll_3d6(self) -> int:
        """3d6でダイスロール"""
        return sum(random.randint(1, 6) for _ in range(3))
    
    def _update_stats_display(self) -> None:
        """ステータス表示を更新"""
        if 'stats_panel' not in self.current_ui_elements:
            return
        
        stats_panel = self.current_ui_elements['stats_panel']
        
        # 既存のステータスラベルを削除
        for key in list(self.current_ui_elements.keys()):
            if key.startswith('stat_'):
                element = self.current_ui_elements.pop(key)
                if hasattr(element, 'kill'):
                    element.kill()
        
        # ステータスラベルを作成
        stat_names = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        stat_labels = ['筋力', '敏捷', '体力', '知力', '精神', '魅力']
        
        for i, (stat_name, stat_label) in enumerate(zip(stat_names, stat_labels)):
            if stat_name in self.character_data:
                y_pos = 10 + i * 25
                label_rect = pygame.Rect(10, y_pos, 80, 20)
                value_rect = pygame.Rect(100, y_pos, 50, 20)
                
                # ラベル
                label = pygame_gui.elements.UILabel(
                    relative_rect=label_rect,
                    text=f"{stat_label}:",
                    manager=self.ui_manager,
                    container=stats_panel
                )
                
                # 値
                value = pygame_gui.elements.UILabel(
                    relative_rect=value_rect,
                    text=str(self.character_data[stat_name]),
                    manager=self.ui_manager,
                    container=stats_panel
                )
                
                self.current_ui_elements[f'stat_{stat_name}_label'] = label
                self.current_ui_elements[f'stat_{stat_name}_value'] = value
    
    def _format_character_info(self) -> str:
        """キャラクター情報をフォーマット"""
        lines = [
            f"<b>名前:</b> {self.character_data.get('name', '')}",
            f"<b>種族:</b> {self.character_data.get('race', '')}",
            f"<b>職業:</b> {self.character_data.get('character_class', '')}",
            f"<b>レベル:</b> {self.character_data.get('level', 1)}",
            "",
            "<b>ステータス:</b>"
        ]
        
        stat_names = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        stat_labels = ['筋力', '敏捷', '体力', '知力', '精神', '魅力']
        
        for stat_name, stat_label in zip(stat_names, stat_labels):
            if stat_name in self.character_data:
                lines.append(f"  {stat_label}: {self.character_data[stat_name]}")
        
        return "<br>".join(lines)
    
    def next_step(self) -> bool:
        """次のステップに進む"""
        # Extract Classパターン適用 - ステップ管理を専門クラスに委譲
        validation_result = self.step_manager.can_advance(self.character_data)
        if not validation_result.is_valid:
            return False
        
        # 最後のステップの場合は完了
        if self.step_manager.is_last_step():
            return self.complete_wizard()
        
        # 次のステップに進む
        if self.step_manager.advance_step():
            # UIを更新
            self._create_current_step_ui()
            logger.debug(f"次のステップに進みました: {self.current_step}")
            return True
        
        return False
    
    def previous_step(self) -> bool:
        """前のステップに戻る"""
        # Extract Classパターン適用 - ステップ管理を専門クラスに委譲
        if self.step_manager.go_back():
            # UIを更新
            self._create_current_step_ui()
            logger.debug(f"前のステップに戻りました: {self.current_step}")
            return True
        
        return False
    
    def _validate_current_step(self) -> bool:
        """現在のステップを検証"""
        if self.current_step == WizardStep.NAME_INPUT:
            return bool(self.character_data.get('name', '').strip())
        elif self.current_step == WizardStep.RACE_SELECTION:
            return bool(self.character_data.get('race', ''))
        elif self.current_step == WizardStep.STATS_GENERATION:
            return 'strength' in self.character_data
        elif self.current_step == WizardStep.CLASS_SELECTION:
            return bool(self.character_data.get('character_class', ''))
        elif self.current_step == WizardStep.CONFIRMATION:
            return True  # 確認ステップは常に有効
        
        return False
    
    def complete_wizard(self) -> bool:
        """ウィザードを完了"""
        # 最終検証
        if not self._validate_all_steps():
            return False
        
        # 完了メッセージを送信
        self.send_message('character_created', {
            'character_data': self.character_data
        })
        
        logger.info(f"キャラクター作成完了: {self.character_data}")
        return True
    
    def cancel_wizard(self) -> bool:
        """ウィザードをキャンセル"""
        # キャンセルメッセージを送信
        self.send_message('character_creation_cancelled')
        
        logger.debug("キャラクター作成がキャンセルされました")
        return True
    
    def _validate_all_steps(self) -> bool:
        """全ステップを検証"""
        required_fields = ['name', 'race', 'character_class', 'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        
        for field in required_fields:
            if field not in self.character_data or not self.character_data[field]:
                logger.warning(f"必須フィールドが不足: {field}")
                return False
        
        return True
    
    def handle_escape(self) -> bool:
        """ESCキーの処理"""
        return self.cancel_wizard()
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # ステップUIをクリア
        self._clear_current_step_ui()
        
        # ステップリストをクリア
        self.steps.clear()
        
        # キャラクターデータをクリア
        self.character_data.clear()
        
        # pygame-guiの要素を削除
        if self.ui_manager:
            for element in list(self.ui_manager.get_root_container().elements):
                element.kill()
            self.ui_manager = None
        
        logger.debug(f"CharacterCreationWizard UI要素をクリーンアップ: {self.window_id}")