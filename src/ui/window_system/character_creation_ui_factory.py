"""
CharacterCreationUIFactory クラス

ウィザードUI要素作成専門クラス
"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
from .character_creation_types import WizardStep, WizardConfig
from src.utils.logger import logger


class CharacterCreationUIFactory:
    """
    キャラクター作成UI要素ファクトリクラス
    
    ステップ別UI要素の作成を担当
    """
    
    def __init__(self, ui_manager: pygame_gui.UIManager, 
                 content_container: pygame_gui.core.UIElement,
                 config: WizardConfig):
        """
        CharacterCreationUIFactoryを初期化
        
        Args:
            ui_manager: UIManager
            content_container: コンテンツコンテナ
            config: ウィザード設定
        """
        self.ui_manager = ui_manager
        self.content_container = content_container
        self.config = config
    
    def create_step_ui(self, step: WizardStep, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ステップ別のUI要素を作成
        
        Args:
            step: 作成するステップ
            character_data: 現在のキャラクターデータ
            
        Returns:
            Dict[str, Any]: 作成されたUI要素の辞書
        """
        if step == WizardStep.NAME_INPUT:
            return self._create_name_input_ui(character_data)
        elif step == WizardStep.RACE_SELECTION:
            return self._create_race_selection_ui(character_data)
        elif step == WizardStep.STATS_GENERATION:
            return self._create_stats_generation_ui(character_data)
        elif step == WizardStep.CLASS_SELECTION:
            return self._create_class_selection_ui(character_data)
        elif step == WizardStep.CONFIRMATION:
            return self._create_confirmation_ui(character_data)
        
        return {}
    
    def _create_name_input_ui(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """名前入力UIを作成"""
        ui_elements = {}
        
        # 説明ラベル
        desc_rect = pygame.Rect(20, 20, 400, 30)
        ui_elements['desc_label'] = pygame_gui.elements.UILabel(
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
        name_input.set_text(character_data.get('name', ''))
        ui_elements['name_input'] = name_input
        
        # 制限表示
        limit_rect = pygame.Rect(20, 100, 400, 20)
        ui_elements['limit_label'] = pygame_gui.elements.UILabel(
            relative_rect=limit_rect,
            text=f'（{self.config.min_name_length}〜{self.config.max_name_length}文字）',
            manager=self.ui_manager,
            container=self.content_container
        )
        
        return ui_elements
    
    def _create_race_selection_ui(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """種族選択UIを作成"""
        ui_elements = {}
        
        # 説明ラベル
        desc_rect = pygame.Rect(20, 20, 400, 30)
        ui_elements['desc_label'] = pygame_gui.elements.UILabel(
            relative_rect=desc_rect,
            text='種族を選択してください：',
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 種族リスト
        race_rect = pygame.Rect(20, 60, 300, 200)
        race_list = pygame_gui.elements.UISelectionList(
            relative_rect=race_rect,
            item_list=self.config.races,
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 現在の選択を設定
        current_race = character_data.get('race', '')
        if current_race and current_race in self.config.races:
            race_list.set_item_list(self.config.races, current_race)
        
        ui_elements['race_list'] = race_list
        
        # 種族説明エリア
        desc_rect = pygame.Rect(340, 60, 200, 200)
        ui_elements['race_description'] = pygame_gui.elements.UITextBox(
            relative_rect=desc_rect,
            html_text="種族を選択すると説明が表示されます",
            manager=self.ui_manager,
            container=self.content_container
        )
        
        return ui_elements
    
    def _create_stats_generation_ui(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """ステータス生成UIを作成"""
        ui_elements = {}
        
        # 説明ラベル
        desc_rect = pygame.Rect(20, 20, 400, 30)
        ui_elements['desc_label'] = pygame_gui.elements.UILabel(
            relative_rect=desc_rect,
            text='ステータスを生成してください：',
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # ステータス表示パネル
        stats_rect = pygame.Rect(20, 60, 300, 180)
        ui_elements['stats_panel'] = pygame_gui.elements.UIPanel(
            relative_rect=stats_rect,
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 生成ボタン
        generate_rect = pygame.Rect(20, 260, 100, 30)
        ui_elements['generate_button'] = pygame_gui.elements.UIButton(
            relative_rect=generate_rect,
            text='生成',
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 再生成ボタン（設定で許可されている場合）
        if self.config.allow_stats_reroll:
            reroll_rect = pygame.Rect(130, 260, 100, 30)
            ui_elements['reroll_button'] = pygame_gui.elements.UIButton(
                relative_rect=reroll_rect,
                text='再生成',
                manager=self.ui_manager,
                container=self.content_container
            )
        
        # 合計表示エリア
        total_rect = pygame.Rect(340, 60, 200, 100)
        ui_elements['stats_summary'] = pygame_gui.elements.UITextBox(
            relative_rect=total_rect,
            html_text="ステータスを生成してください",
            manager=self.ui_manager,
            container=self.content_container
        )
        
        return ui_elements
    
    def _create_class_selection_ui(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """職業選択UIを作成"""
        ui_elements = {}
        
        # 説明ラベル
        desc_rect = pygame.Rect(20, 20, 400, 30)
        ui_elements['desc_label'] = pygame_gui.elements.UILabel(
            relative_rect=desc_rect,
            text='職業を選択してください：',
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 職業リスト
        class_rect = pygame.Rect(20, 60, 300, 200)
        class_list = pygame_gui.elements.UISelectionList(
            relative_rect=class_rect,
            item_list=self.config.character_classes,
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 現在の選択を設定
        current_class = character_data.get('character_class', '')
        if current_class and current_class in self.config.character_classes:
            class_list.set_item_list(self.config.character_classes, current_class)
        
        ui_elements['class_list'] = class_list
        
        # 職業説明エリア
        desc_rect = pygame.Rect(340, 60, 200, 200)
        ui_elements['class_description'] = pygame_gui.elements.UITextBox(
            relative_rect=desc_rect,
            html_text="職業を選択すると説明が表示されます",
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 推奨表示（ステータスが設定されている場合）
        if 'strength' in character_data:
            recommend_rect = pygame.Rect(20, 280, 520, 30)
            ui_elements['recommendation_label'] = pygame_gui.elements.UILabel(
                relative_rect=recommend_rect,
                text="推奨職業: （計算中...）",
                manager=self.ui_manager,
                container=self.content_container
            )
        
        return ui_elements
    
    def _create_confirmation_ui(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """確認UIを作成"""
        ui_elements = {}
        
        # 説明ラベル
        desc_rect = pygame.Rect(20, 20, 400, 30)
        ui_elements['desc_label'] = pygame_gui.elements.UILabel(
            relative_rect=desc_rect,
            text='以下の内容で作成します：',
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # キャラクター情報表示
        info_rect = pygame.Rect(20, 60, 520, 250)
        info_text = self._format_character_info(character_data)
        ui_elements['info_display'] = pygame_gui.elements.UITextBox(
            relative_rect=info_rect,
            html_text=info_text,
            manager=self.ui_manager,
            container=self.content_container
        )
        
        return ui_elements
    
    def update_stats_display(self, ui_elements: Dict[str, Any], character_data: Dict[str, Any]) -> None:
        """ステータス表示を更新"""
        if 'stats_panel' not in ui_elements:
            return
        
        stats_panel = ui_elements['stats_panel']
        
        # 既存のステータスラベルを削除
        existing_labels = [key for key in ui_elements.keys() if key.startswith('stat_')]
        for key in existing_labels:
            element = ui_elements.pop(key)
            if hasattr(element, 'kill'):
                element.kill()
        
        # ステータスラベルを作成
        stat_names = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        stat_labels = ['筋力', '敏捷', '体力', '知力', '精神', '魅力']
        
        for i, (stat_name, stat_label) in enumerate(zip(stat_names, stat_labels)):
            if stat_name in character_data:
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
                    text=str(character_data[stat_name]),
                    manager=self.ui_manager,
                    container=stats_panel
                )
                
                ui_elements[f'stat_{stat_name}_label'] = label
                ui_elements[f'stat_{stat_name}_value'] = value
    
    def _format_character_info(self, character_data: Dict[str, Any]) -> str:
        """キャラクター情報をフォーマット"""
        lines = [
            f"<b>名前:</b> {character_data.get('name', '')}",
            f"<b>種族:</b> {character_data.get('race', '')}",
            f"<b>職業:</b> {character_data.get('character_class', '')}",
            f"<b>レベル:</b> {character_data.get('level', 1)}",
            "",
            "<b>ステータス:</b>"
        ]
        
        stat_names = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        stat_labels = ['筋力', '敏捷', '体力', '知力', '精神', '魅力']
        
        for stat_name, stat_label in zip(stat_names, stat_labels):
            if stat_name in character_data:
                lines.append(f"  {stat_label}: {character_data[stat_name]}")
        
        return "<br>".join(lines)
    
    def destroy_ui_elements(self, ui_elements: Dict[str, Any]) -> None:
        """UI要素を破棄"""
        for element in ui_elements.values():
            if hasattr(element, 'kill'):
                element.kill()
        ui_elements.clear()