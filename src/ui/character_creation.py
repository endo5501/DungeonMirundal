"""キャラクター作成ウィザード"""

from typing import Dict, List, Optional, Any
from enum import Enum

from src.ui.base_ui_pygame import UIElement, UIText, UIButton, UIMenu, UIDialog, ui_manager
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


class CharacterCreationWizard:
    """キャラクター作成ウィザード"""
    
    def __init__(self, callback: Optional[callable] = None):
        self.callback = callback  # 作成完了時のコールバック
        self.on_cancel = self._default_cancel_handler  # キャンセル時のコールバック
        self.current_step = CreationStep.NAME_INPUT
        
        # 作成中のキャラクターデータ
        self.character_data = {
            'name': '',
            'race': '',
            'character_class': '',
            'base_stats': None
        }
        
        # UI要素
        self.main_container = None
        self.step_title = None
        self.current_ui = None
        
        # 設定データ
        self.char_config = config_manager.load_config("characters")
        self.races_config = self.char_config.get("races", {})
        self.classes_config = self.char_config.get("classes", {})
        
        self._initialize_ui()
    
    def _initialize_ui(self):
        """UI初期化"""
        # メインコンテナ
        self.main_container = UIElement("character_creation_main")
        
        # ステップタイトル
        self.step_title = UIText(
            "creation_step_title",
            ui_manager.get_text("character.creation_title"),
            pos=(0, 0.9),
            scale=0.08,
            color=(1, 1, 0, 1)
        )
        
        ui_manager.register_element(self.main_container)
        ui_manager.register_element(self.step_title)
        
        logger.info("キャラクター作成ウィザードを初期化しました")
    
    def start(self):
        """ウィザード開始"""
        self.current_step = CreationStep.NAME_INPUT
        self._show_step()
        
        ui_manager.show_element("character_creation_main", modal=True)
        ui_manager.show_element("creation_step_title")
        
        logger.info("キャラクター作成を開始しました")
    
    def _show_step(self):
        """現在のステップを表示"""
        # 前のUIを隠す
        if self.current_ui:
            ui_manager.hide_element(self.current_ui.element_id)
            ui_manager.unregister_element(self.current_ui.element_id)
        
        # ステップに応じたUIを表示
        if self.current_step == CreationStep.NAME_INPUT:
            self._show_name_input()
        elif self.current_step == CreationStep.RACE_SELECTION:
            self._show_race_selection()
        elif self.current_step == CreationStep.STATS_GENERATION:
            self._show_stats_generation()
        elif self.current_step == CreationStep.CLASS_SELECTION:
            self._show_class_selection()
        elif self.current_step == CreationStep.CONFIRMATION:
            self._show_confirmation()
    
    def _show_name_input(self):
        """名前入力ステップ"""
        # 現在の名前があればそれを初期値とする、なければデフォルト名
        current_name = self.character_data.get('name', config_manager.get_text('character_creation.default_name'))
        
        # メッセージテキストを取得（シンプルなメッセージを使用してラベル重複を回避）
        message = config_manager.get_text("character_creation.enter_name_prompt")
        
        dialog = UIInputDialog(
            "name_input_dialog",
            "",  # タイトルを空にして重複回避（ページ上部に既に表示済み）
            message,  # メッセージのみ表示
            initial_text=current_name,
            placeholder="",  # プレースホルダーは空のまま
            on_confirm=self._on_name_confirmed,
            on_cancel=self._on_name_cancelled
        )
        
        self.current_ui = dialog
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id)
    
    def _on_name_confirmed(self, name: str):
        """名前入力確認時の処理"""
        # 名前の検証
        if not name or not name.strip():
            # 名前が空の場合はデフォルト名を使用
            name = config_manager.get_text('character_creation.default_name')
        
        # 名前の文字数制限チェック
        name = name.strip()[:20]  # 最大20文字
        
        # 特殊文字の除去（アルファベット、数字、日本語のみ許可）
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ひらがなカタカナ漢字")
        # 簡易版：基本的な文字チェック
        if any(c in name for c in ['<', '>', '&', '"', "'"]):
            name = config_manager.get_text('character_creation.default_name')  # 危険な文字がある場合はデフォルト名
        
        self.character_data['name'] = name
        
        # UIを閉じて次のステップへ
        ui_manager.hide_element(self.current_ui.element_id)
        ui_manager.unregister_element(self.current_ui.element_id)
        self.current_ui = None
        
        self._next_step()
        
        logger.info(f"キャラクター名が設定されました: {name}")
    
    def _on_name_cancelled(self):
        """名前入力キャンセル時の処理"""
        # UIを閉じて前のステップに戻る
        ui_manager.hide_element(self.current_ui.element_id)
        ui_manager.unregister_element(self.current_ui.element_id)
        self.current_ui = None
        
        # キャラクター作成をキャンセル
        if self.on_cancel:
            self.on_cancel()
        
        logger.info("キャラクター作成がキャンセルされました")
    
    def _default_cancel_handler(self):
        """デフォルトのキャンセル処理"""
        # ウィザードを適切に閉じる
        self._close_wizard()
        logger.info("キャラクター作成をキャンセルしました（デフォルト処理）")
    
    def _show_race_selection(self):
        """種族選択ステップ"""
        menu = UIMenu("race_selection_menu", ui_manager.get_text("character.select_race"), 
                     character_creation_mode=True)
        
        for race_id, race_config in self.races_config.items():
            race_name = ui_manager.get_text(race_config.get('name_key', f'race.{race_id}'))
            menu.add_menu_item(
                race_name,
                self._select_race,
                [race_id]
            )
        
        # 戻るボタン
        menu.add_menu_item(
            ui_manager.get_text("menu.back"),
            self._previous_step
        )
        
        self.current_ui = menu
        ui_manager.register_element(menu)
        ui_manager.show_element(menu.element_id)
    
    def _show_stats_generation(self):
        """統計値生成ステップ"""
        # 統計値を生成
        creation_config = self.char_config.get("character_creation", {})
        method = creation_config.get("stat_roll_method", "4d6_drop_lowest")
        base_stats = StatGenerator.generate_stats(method)
        
        # 種族ボーナスを適用
        race_config = self.races_config[self.character_data['race']]
        race_bonuses = race_config.get("base_stats", {})
        final_stats = base_stats.add_bonuses(race_bonuses)
        
        self.character_data['base_stats'] = final_stats
        
        # 統計値表示
        stats_text = self._format_stats(final_stats)
        
        dialog = UIDialog(
            "stats_generation_dialog",
            ui_manager.get_text("character.generated_stats"),
            stats_text,
            buttons=[
                {
                    'text': ui_manager.get_text("character.reroll"),
                    'command': self._reroll_stats
                },
                {
                    'text': ui_manager.get_text("common.ok"),
                    'command': self._next_step
                },
                {
                    'text': ui_manager.get_text("menu.back"),
                    'command': self._previous_step
                }
            ],
            character_creation_mode=True
        )
        
        self.current_ui = dialog
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id)
    
    def _show_class_selection(self):
        """職業選択ステップ"""
        # 選択可能な職業を取得
        available_classes = StatValidator.get_available_classes(
            self.character_data['base_stats'],
            self.classes_config
        )
        
        menu = UIMenu("class_selection_menu", ui_manager.get_text("character.select_class"),
                     character_creation_mode=True)
        
        for class_id in available_classes:
            class_config = self.classes_config[class_id]
            class_name = ui_manager.get_text(class_config.get('name_key', f'class.{class_id}'))
            menu.add_menu_item(
                class_name,
                self._select_class,
                [class_id]
            )
        
        # 戻るボタン
        menu.add_menu_item(
            ui_manager.get_text("menu.back"),
            self._previous_step
        )
        
        self.current_ui = menu
        ui_manager.register_element(menu)
        ui_manager.show_element(menu.element_id)
    
    def _show_confirmation(self):
        """確認ステップ"""
        # キャラクター情報をまとめて表示
        char_info = self._format_character_info()
        
        dialog = UIDialog(
            "confirmation_dialog",
            ui_manager.get_text("character.confirm_creation"),
            char_info,
            buttons=[
                {
                    'text': ui_manager.get_text("character.create"),
                    'command': self._create_character
                },
                {
                    'text': ui_manager.get_text("menu.back"),
                    'command': self._previous_step
                },
                {
                    'text': ui_manager.get_text("common.cancel"),
                    'command': self._cancel_creation
                }
            ],
            character_creation_mode=True
        )
        
        self.current_ui = dialog
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id)
    
    def _select_race(self, race_id: str):
        """種族選択"""
        self.character_data['race'] = race_id
        logger.info(f"種族を選択: {race_id}")
        self._next_step()
    
    def _select_class(self, class_id: str):
        """職業選択"""
        self.character_data['character_class'] = class_id
        logger.info(f"職業を選択: {class_id}")
        self._next_step()
    
    def _next_step(self):
        """次のステップに進む"""
        step_order = [
            CreationStep.NAME_INPUT,
            CreationStep.RACE_SELECTION,
            CreationStep.STATS_GENERATION,
            CreationStep.CLASS_SELECTION,
            CreationStep.CONFIRMATION
        ]
        
        current_index = step_order.index(self.current_step)
        if current_index < len(step_order) - 1:
            self.current_step = step_order[current_index + 1]
            self._show_step()
    
    def _previous_step(self):
        """前のステップに戻る"""
        step_order = [
            CreationStep.NAME_INPUT,
            CreationStep.RACE_SELECTION,
            CreationStep.STATS_GENERATION,
            CreationStep.CLASS_SELECTION,
            CreationStep.CONFIRMATION
        ]
        
        current_index = step_order.index(self.current_step)
        if current_index > 0:
            self.current_step = step_order[current_index - 1]
            self._show_step()
    
    def _reroll_stats(self):
        """統計値を振り直し"""
        # 現在のダイアログを閉じる
        if self.current_ui:
            ui_manager.hide_element(self.current_ui.element_id)
            ui_manager.unregister_element(self.current_ui.element_id)
            self.current_ui = None
        
        # 統計値を再生成してステップを再表示
        self._show_stats_generation()
    
    def _create_character(self):
        """キャラクター作成実行"""
        try:
            character = Character.create_character(
                name=self.character_data['name'],
                race=self.character_data['race'],
                character_class=self.character_data['character_class'],
                base_stats=self.character_data['base_stats']
            )
            
            logger.info(f"キャラクターを作成しました: {character.name}")
            
            # コールバック実行
            if self.callback:
                self.callback(character)
            
            self._close_wizard()
            
        except Exception as e:
            logger.error(f"キャラクター作成に失敗しました: {e}")
            
            error_dialog = UIDialog(
                "creation_error_dialog",
                ui_manager.get_text("common.error"),
                f"{config_manager.get_text('character_creation.creation_failed')}: {str(e)}",
                buttons=[
                    {
                        'text': ui_manager.get_text("common.ok"),
                        'command': lambda: ui_manager.hide_element("creation_error_dialog")
                    }
                ]
            )
            
            ui_manager.register_element(error_dialog)
            ui_manager.show_element(error_dialog.element_id)
    
    def _cancel_creation(self):
        """作成キャンセル"""
        logger.info("キャラクター作成をキャンセルしました")
        self._close_wizard()
    
    def _close_wizard(self):
        """ウィザードを閉じる"""
        ui_manager.hide_element("character_creation_main")
        ui_manager.hide_element("creation_step_title")
        
        if self.current_ui:
            ui_manager.hide_element(self.current_ui.element_id)
            ui_manager.unregister_element(self.current_ui.element_id)
        
        ui_manager.unregister_element("character_creation_main")
        ui_manager.unregister_element("creation_step_title")
    
    def _format_stats(self, stats: BaseStats) -> str:
        """統計値を整形して表示"""
        return f"""{config_manager.get_text('character.strength')}: {stats.strength}
{config_manager.get_text('character.agility')}: {stats.agility}
{config_manager.get_text('character.intelligence')}: {stats.intelligence}
{config_manager.get_text('character.faith')}: {stats.faith}
{config_manager.get_text('character.luck')}: {stats.luck}"""
    
    def _format_character_info(self) -> str:
        """キャラクター情報を整形して表示"""
        race_name = ui_manager.get_text(f"race.{self.character_data['race']}")
        class_name = ui_manager.get_text(f"class.{self.character_data['character_class']}")
        stats_text = self._format_stats(self.character_data['base_stats'])
        
        return f"""{config_manager.get_text('character.name')}: {self.character_data['name']}
{config_manager.get_text('race.race')}: {race_name}
{config_manager.get_text('class.class')}: {class_name}

{stats_text}"""