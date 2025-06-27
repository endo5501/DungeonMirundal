"""設定画面UIシステム"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from src.ui.base_ui_pygame import UIElement, UIButton, UIText, UIMenu, UIDialog, UIState, ui_manager
from src.core.config_manager import config_manager
# input_managerは動的にインポート（循環インポート回避）
# from src.core.input_manager import input_manager
from src.utils.logger import logger

# 設定UI定数
SETTINGS_CONFIG_DIR = "config"
SETTINGS_FILE_NAME = "user_settings.yaml"
GAME_SETTINGS_CONFIG = "game_settings"
USER_SETTINGS_KEY = "user_settings"

# デフォルト設定値
DEFAULT_LANGUAGE = "ja"
DEFAULT_DIFFICULTY = "normal"
DEFAULT_BATTLE_SPEED = "normal"
DEFAULT_MESSAGE_SPEED = "normal"
DEFAULT_ANALOG_DEADZONE = 0.3
DEFAULT_ANALOG_SENSITIVITY = 1.0
DEFAULT_MASTER_VOLUME = 1.0
DEFAULT_MUSIC_VOLUME = 0.8
DEFAULT_SFX_VOLUME = 0.9
DEFAULT_VOICE_VOLUME = 1.0
DEFAULT_RESOLUTION = "1024x768"
DEFAULT_UI_SCALE = 1.0
DEFAULT_FEEDBACK_LEVEL = "normal"


class SettingsCategory(Enum):
    """設定カテゴリ"""
    GAMEPLAY = "gameplay"       # ゲームプレイ
    CONTROLS = "controls"       # 操作設定
    AUDIO = "audio"            # 音声設定
    GRAPHICS = "graphics"      # 表示設定
    ACCESSIBILITY = "accessibility"  # アクセシビリティ


class SettingsUI:
    """設定画面UI管理クラス"""
    
    def __init__(self):
        # UI状態
        self.is_open = False
        self.current_category: Optional[SettingsCategory] = None
        self.callback_on_close: Optional[Callable] = None
        
        # 設定値
        self.current_settings = self._load_current_settings()
        self.pending_changes = {}
        
        logger.info("SettingsUIを初期化しました")
    
    def _load_current_settings(self) -> Dict[str, Any]:
        """現在の設定を読み込み"""
        try:
            import yaml
            from pathlib import Path
            
            # ユーザー設定ファイルから読み込み
            config_file = Path(SETTINGS_CONFIG_DIR) / SETTINGS_FILE_NAME
            if config_file.exists():
                return self._load_user_settings_file(config_file)
            else:
                return self._load_fallback_settings()
        except Exception as e:
            logger.warning(f"設定読み込みエラー: {e}")
            # デフォルト設定を返す
            return self._get_default_settings()
    
    def _load_user_settings_file(self, config_file):
        """ユーザー設定ファイルを読み込み"""
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            user_settings = yaml.safe_load(f) or {}
            default_settings = self._get_default_settings()
            default_settings.update(user_settings)
            return default_settings
    
    def _load_fallback_settings(self):
        """フォールバック設定を読み込み"""
        game_config = config_manager.load_config(GAME_SETTINGS_CONFIG)
        user_settings = game_config.get(USER_SETTINGS_KEY, {})
        default_settings = self._get_default_settings()
        default_settings.update(user_settings)
        return default_settings
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            # ゲームプレイ
            "auto_save": True,
            "language": DEFAULT_LANGUAGE,
            "difficulty": DEFAULT_DIFFICULTY,
            "battle_speed": DEFAULT_BATTLE_SPEED,
            "message_speed": DEFAULT_MESSAGE_SPEED,
            "confirm_actions": True,
            
            # 操作設定
            "controller_enabled": True,
            "keyboard_enabled": True,
            "analog_deadzone": DEFAULT_ANALOG_DEADZONE,
            "analog_sensitivity": DEFAULT_ANALOG_SENSITIVITY,
            "vibration_enabled": True,
            
            # 音声設定
            "master_volume": DEFAULT_MASTER_VOLUME,
            "music_volume": DEFAULT_MUSIC_VOLUME,
            "sfx_volume": DEFAULT_SFX_VOLUME,
            "voice_volume": DEFAULT_VOICE_VOLUME,
            "mute_on_focus_loss": True,
            
            # 表示設定
            "fullscreen": False,
            "resolution": DEFAULT_RESOLUTION,
            "vsync": True,
            "show_fps": False,
            "ui_scale": DEFAULT_UI_SCALE,
            
            # アクセシビリティ
            "feedback_level": DEFAULT_FEEDBACK_LEVEL,
            "high_contrast": False,
            "large_text": False,
            "color_blind_mode": "none",
            "screen_reader": False
        }
    
    def show_settings_menu(self):
        """設定メインメニューを表示"""
        from src.core.config_manager import config_manager
        settings_menu = UIMenu("settings_main", config_manager.get_text("menu.settings"))
        
        # カテゴリ別設定（国際化対応）
        categories = [
            (SettingsCategory.GAMEPLAY, config_manager.get_text("settings.category.gameplay")),
            (SettingsCategory.CONTROLS, config_manager.get_text("settings.category.controls")),
            (SettingsCategory.AUDIO, config_manager.get_text("settings.category.audio")),
            (SettingsCategory.GRAPHICS, config_manager.get_text("settings.category.graphics")),
            (SettingsCategory.ACCESSIBILITY, config_manager.get_text("settings.category.accessibility"))
        ]
        
        for category, title in categories:
            settings_menu.add_menu_item(
                title,
                self._show_category_settings,
                [category]
            )
        
        # 設定の初期化
        settings_menu.add_menu_item(
            config_manager.get_text("settings.reset_confirm"),
            self._show_reset_confirmation
        )
        
        # 新規ゲーム開始
        settings_menu.add_menu_item(
            config_manager.get_text("settings.new_game"),
            self._show_new_game_confirmation
        )
        
        # 変更の保存
        if self.pending_changes:
            settings_menu.add_menu_item(
                config_manager.get_text("settings.save_changes"),
                self._save_settings
            )
            settings_menu.add_menu_item(
                config_manager.get_text("settings.discard_changes"),
                self._discard_changes
            )
        
        settings_menu.add_menu_item(
            config_manager.get_text("menu.close"),
            self._close_settings_ui
        )
        
        try:
            if ui_manager is not None:
                ui_manager.add_menu(settings_menu)
                ui_manager.show_menu(settings_menu.menu_id, modal=True)
            else:
                logger.error("ui_managerが初期化されていないため、メニューを表示できません")
        except Exception as e:
            logger.error(f"メニュー表示中にエラーが発生しました: {e}")
        self.is_open = True
        
        logger.info("設定メニューを表示")
    
    def _show_category_settings(self, category: SettingsCategory):
        """カテゴリ別設定を表示"""
        self.current_category = category
        
        if category == SettingsCategory.GAMEPLAY:
            self._show_gameplay_settings()
        elif category == SettingsCategory.CONTROLS:
            self._show_controls_settings()
        elif category == SettingsCategory.AUDIO:
            self._show_audio_settings()
        elif category == SettingsCategory.GRAPHICS:
            self._show_graphics_settings()
        elif category == SettingsCategory.ACCESSIBILITY:
            self._show_accessibility_settings()
    
    def _show_gameplay_settings(self):
        """ゲームプレイ設定を表示"""
        gameplay_menu = UIMenu("gameplay_settings", config_manager.get_text("settings.gameplay_settings"))
        
        # 言語設定
        language = self._get_setting_value("language")
        language_text = {"ja": "日本語", "en": "English"}.get(language, language)
        gameplay_menu.add_menu_item(
            f"言語 / Language: {language_text}",
            self._cycle_setting,
            ["language", ["ja", "en"]]
        )
        
        # オートセーブ
        auto_save = self._get_setting_value("auto_save")
        status = config_manager.get_text("ui.settings.enabled") if auto_save else config_manager.get_text("ui.settings.disabled")
        gameplay_menu.add_menu_item(
            config_manager.get_text("ui.settings.auto_save").format(status=status),
            self._toggle_setting,
            ["auto_save"]
        )
        
        # 難易度
        difficulty = self._get_setting_value("difficulty")
        difficulty_text = {"easy": "簡単", "normal": "普通", "hard": "難しい"}.get(difficulty, difficulty)
        gameplay_menu.add_menu_item(
            f"難易度: {difficulty_text}",
            self._cycle_setting,
            ["difficulty", ["easy", "normal", "hard"]]
        )
        
        # 戦闘速度
        battle_speed = self._get_setting_value("battle_speed")
        speed_text = {"slow": "遅い", "normal": "普通", "fast": "速い"}.get(battle_speed, battle_speed)
        gameplay_menu.add_menu_item(
            f"戦闘速度: {speed_text}",
            self._cycle_setting,
            ["battle_speed", ["slow", "normal", "fast"]]
        )
        
        # メッセージ速度
        message_speed = self._get_setting_value("message_speed")
        msg_speed_text = {"slow": "遅い", "normal": "普通", "fast": "速い", "instant": "瞬間"}.get(message_speed, message_speed)
        gameplay_menu.add_menu_item(
            f"メッセージ速度: {msg_speed_text}",
            self._cycle_setting,
            ["message_speed", ["slow", "normal", "fast", "instant"]]
        )
        
        # 確認ダイアログ
        confirm_actions = self._get_setting_value("confirm_actions")
        status = config_manager.get_text("ui.settings.enabled") if confirm_actions else config_manager.get_text("ui.settings.disabled")
        gameplay_menu.add_menu_item(
            config_manager.get_text("ui.settings.confirm_actions").format(status=status),
            self._toggle_setting,
            ["confirm_actions"]
        )
        
        gameplay_menu.add_menu_item(
            config_manager.get_text("settings.back"),
            self._back_to_main_settings
        )
        
        try:
            if ui_manager is not None:
                ui_manager.add_menu(gameplay_menu)
                ui_manager.show_menu(gameplay_menu.menu_id, modal=True)
            else:
                logger.error("ui_managerが初期化されていないため、ゲームプレイ設定メニューを表示できません")
        except Exception as e:
            logger.error(f"ゲームプレイ設定メニュー表示中にエラーが発生しました: {e}")
    
    def _show_controls_settings(self):
        """操作設定を表示"""
        controls_menu = UIMenu("controls_settings", config_manager.get_text("settings.controls_settings"))
        
        # コントローラー有効
        controller_enabled = self._get_setting_value("controller_enabled")
        status = config_manager.get_text("ui.settings.enabled") if controller_enabled else config_manager.get_text("ui.settings.disabled")
        controls_menu.add_menu_item(
            config_manager.get_text("ui.settings.controller").format(status=status),
            self._toggle_setting,
            ["controller_enabled"]
        )
        
        # アナログスティック感度
        sensitivity = self._get_setting_value("analog_sensitivity")
        controls_menu.add_menu_item(
            f"スティック感度: {sensitivity:.1f}",
            self._adjust_setting,
            ["analog_sensitivity", 0.1, 0.1, 3.0]
        )
        
        # デッドゾーン
        deadzone = self._get_setting_value("analog_deadzone")
        controls_menu.add_menu_item(
            f"デッドゾーン: {deadzone:.1f}",
            self._adjust_setting,
            ["analog_deadzone", 0.1, 0.0, 0.8]
        )
        
        # 振動
        vibration = self._get_setting_value("vibration_enabled")
        status = config_manager.get_text("ui.settings.enabled") if vibration else config_manager.get_text("ui.settings.disabled")
        controls_menu.add_menu_item(
            f"振動: {status}",
            self._toggle_setting,
            ["vibration_enabled"]
        )
        
        # キーバインド設定
        controls_menu.add_menu_item(
            config_manager.get_text("settings.keybind_settings"),
            self._show_keybind_settings
        )
        
        controls_menu.add_menu_item(
            config_manager.get_text("settings.back"),
            self._back_to_main_settings
        )
        
        try:
            if ui_manager is not None:
                ui_manager.add_menu(controls_menu)
                ui_manager.show_menu(controls_menu.menu_id, modal=True)
            else:
                logger.error("ui_managerが初期化されていないため、コントロール設定メニューを表示できません")
        except Exception as e:
            logger.error(f"コントロール設定メニュー表示中にエラーが発生しました: {e}")
    
    def _show_audio_settings(self):
        """音声設定を表示"""
        audio_menu = UIMenu("audio_settings", config_manager.get_text("settings.audio_settings"))
        
        # マスター音量
        master_volume = self._get_setting_value("master_volume")
        audio_menu.add_menu_item(
            f"マスター音量: {int(master_volume * 100)}%",
            self._adjust_setting,
            ["master_volume", 0.1, 0.0, 1.0]
        )
        
        # 音楽音量
        music_volume = self._get_setting_value("music_volume")
        audio_menu.add_menu_item(
            f"音楽音量: {int(music_volume * 100)}%",
            self._adjust_setting,
            ["music_volume", 0.1, 0.0, 1.0]
        )
        
        # 効果音音量
        sfx_volume = self._get_setting_value("sfx_volume")
        audio_menu.add_menu_item(
            f"効果音音量: {int(sfx_volume * 100)}%",
            self._adjust_setting,
            ["sfx_volume", 0.1, 0.0, 1.0]
        )
        
        # フォーカス喪失時ミュート
        mute_on_focus_loss = self._get_setting_value("mute_on_focus_loss")
        status = config_manager.get_text("ui.settings.enabled") if mute_on_focus_loss else config_manager.get_text("ui.settings.disabled")
        audio_menu.add_menu_item(
            config_manager.get_text("ui.settings.mute_on_focus_loss").format(status=status),
            self._toggle_setting,
            ["mute_on_focus_loss"]
        )
        
        audio_menu.add_menu_item(
            config_manager.get_text("settings.back"),
            self._back_to_main_settings
        )
        
        try:
            if ui_manager is not None:
                ui_manager.add_menu(audio_menu)
                ui_manager.show_menu(audio_menu.menu_id, modal=True)
            else:
                logger.error("ui_managerが初期化されていないため、音声設定メニューを表示できません")
        except Exception as e:
            logger.error(f"音声設定メニュー表示中にエラーが発生しました: {e}")
    
    def _show_graphics_settings(self):
        """表示設定を表示"""
        graphics_menu = UIMenu("graphics_settings", config_manager.get_text("settings.graphics_settings"))
        
        # フルスクリーン
        fullscreen = self._get_setting_value("fullscreen")
        status = config_manager.get_text("ui.settings.enabled") if fullscreen else config_manager.get_text("ui.settings.disabled")
        graphics_menu.add_menu_item(
            config_manager.get_text("ui.settings.fullscreen").format(status=status),
            self._toggle_setting,
            ["fullscreen"]
        )
        
        # 解像度
        resolution = self._get_setting_value("resolution")
        graphics_menu.add_menu_item(
            f"解像度: {resolution}",
            self._cycle_setting,
            ["resolution", ["800x600", "1024x768", "1280x720", "1920x1080"]]
        )
        
        # VSync
        vsync = self._get_setting_value("vsync")
        graphics_menu.add_menu_item(
            f"VSync: {'有効' if vsync else '無効'}",
            self._toggle_setting,
            ["vsync"]
        )
        
        # FPS表示
        show_fps = self._get_setting_value("show_fps")
        graphics_menu.add_menu_item(
            f"FPS表示: {'有効' if show_fps else '無効'}",
            self._toggle_setting,
            ["show_fps"]
        )
        
        # UIスケール
        ui_scale = self._get_setting_value("ui_scale")
        graphics_menu.add_menu_item(
            f"UIサイズ: {int(ui_scale * 100)}%",
            self._adjust_setting,
            ["ui_scale", 0.1, 0.5, 2.0]
        )
        
        graphics_menu.add_menu_item(
            config_manager.get_text("settings.back"),
            self._back_to_main_settings
        )
        
        try:
            if ui_manager is not None:
                ui_manager.add_menu(graphics_menu)
                ui_manager.show_menu(graphics_menu.menu_id, modal=True)
            else:
                logger.error("ui_managerが初期化されていないため、グラフィック設定メニューを表示できません")
        except Exception as e:
            logger.error(f"グラフィック設定メニュー表示中にエラーが発生しました: {e}")
    
    def _show_accessibility_settings(self):
        """アクセシビリティ設定を表示"""
        accessibility_menu = UIMenu("accessibility_settings", config_manager.get_text("settings.accessibility_settings"))
        
        # フィードバックレベル
        feedback_level = self._get_setting_value("feedback_level")
        feedback_text = {
            "silent": "無音",
            "minimal": "最小限",
            "normal": "通常",
            "verbose": "詳細"
        }.get(feedback_level, feedback_level)
        accessibility_menu.add_menu_item(
            f"フィードバック: {feedback_text}",
            self._cycle_setting,
            ["feedback_level", ["silent", "minimal", "normal", "verbose"]]
        )
        
        # ハイコントラスト
        high_contrast = self._get_setting_value("high_contrast")
        accessibility_menu.add_menu_item(
            f"ハイコントラスト: {'有効' if high_contrast else '無効'}",
            self._toggle_setting,
            ["high_contrast"]
        )
        
        # 大きな文字
        large_text = self._get_setting_value("large_text")
        accessibility_menu.add_menu_item(
            f"大きな文字: {'有効' if large_text else '無効'}",
            self._toggle_setting,
            ["large_text"]
        )
        
        # 色覚異常対応
        color_blind_mode = self._get_setting_value("color_blind_mode")
        color_text = {
            "none": "なし",
            "protanopia": "1型（赤）",
            "deuteranopia": "2型（緑）",
            "tritanopia": "3型（青）"
        }.get(color_blind_mode, color_blind_mode)
        accessibility_menu.add_menu_item(
            f"色覚サポート: {color_text}",
            self._cycle_setting,
            ["color_blind_mode", ["none", "protanopia", "deuteranopia", "tritanopia"]]
        )
        
        accessibility_menu.add_menu_item(
            config_manager.get_text("settings.back"),
            self._back_to_main_settings
        )
        
        try:
            if ui_manager is not None:
                ui_manager.add_menu(accessibility_menu)
                ui_manager.show_menu(accessibility_menu.menu_id, modal=True)
            else:
                logger.error("ui_managerが初期化されていないため、アクセシビリティ設定メニューを表示できません")
        except Exception as e:
            logger.error(f"アクセシビリティ設定メニュー表示中にエラーが発生しました: {e}")
    
    def _show_keybind_settings(self):
        """キーバインド設定を表示"""
        keybind_menu = UIMenu("keybind_settings", config_manager.get_text("settings.keybind_settings"))
        
        # 現在のキーバインドを表示
        current_bindings = [
            ("移動（前）", "W"),
            ("移動（後）", "S"),
            ("回転（左）", "A"),
            ("回転（右）", "D"),
            ("メニュー", "TAB"),
            ("決定", "Enter"),
            ("キャンセル", "ESC"),
            ("インベントリ", "I"),
            ("魔法", "M"),
            ("装備", "C"),
            ("ヘルプ", "H")
        ]
        
        for action, key in current_bindings:
            keybind_menu.add_menu_item(
                f"{action}: {key}",
                self._change_keybind,
                [action, key]
            )
        
        keybind_menu.add_menu_item(
            config_manager.get_text("settings.reset_keybinds"),
            self._reset_keybinds
        )
        
        keybind_menu.add_menu_item(
            config_manager.get_text("settings.back"),
            self._show_controls_settings
        )
        
        try:
            if ui_manager is not None:
                ui_manager.add_menu(keybind_menu)
                ui_manager.show_menu(keybind_menu.menu_id, modal=True)
            else:
                logger.error("ui_managerが初期化されていないため、キーバインド設定メニューを表示できません")
        except Exception as e:
            logger.error(f"キーバインド設定メニュー表示中にエラーが発生しました: {e}")
    
    def _get_setting_value(self, key: str) -> Any:
        """設定値を取得（保留中の変更を優先）"""
        if key in self.pending_changes:
            return self.pending_changes[key]
        return self.current_settings.get(key, self._get_default_settings()[key])
    
    def _toggle_setting(self, key: str):
        """設定のON/OFF切り替え"""
        current_value = self._get_setting_value(key)
        self.pending_changes[key] = not current_value
        self._refresh_current_menu()
    
    def _cycle_setting(self, key: str, values: List[Any]):
        """設定の循環切り替え"""
        current_value = self._get_setting_value(key)
        try:
            current_index = values.index(current_value)
            next_index = (current_index + 1) % len(values)
        except ValueError:
            next_index = 0
        
        self.pending_changes[key] = values[next_index]
        self._refresh_current_menu()
    
    def _adjust_setting(self, key: str, step: float, min_val: float, max_val: float):
        """設定の数値調整"""
        current_value = self._get_setting_value(key)
        new_value = min(max_val, max(min_val, current_value + step))
        self.pending_changes[key] = round(new_value, 1)
        self._refresh_current_menu()
    
    def _change_keybind(self, action: str, current_key: str):
        """キーバインド変更"""
        # キー入力待ちダイアログを表示
        dialog_text = f"【{action}】\\n\\n新しいキーを押してください\\n\\n現在: {current_key}"
        
        dialog = UIDialog(
            "keybind_input",
            "キーバインド変更",
            dialog_text
        )
        
        # ボタンを手動で追加
        from src.ui.base_ui_pygame import UIButton
        cancel_button = UIButton("cancel_keybind", "キャンセル",
                               x=dialog.rect.x + dialog.rect.width - 130, y=dialog.rect.y + dialog.rect.height - 50,
                               width=100, height=30)
        cancel_button.on_click = self._close_dialog
        dialog.add_element(cancel_button)
        
        try:
            if ui_manager is not None:
                ui_manager.add_dialog(dialog)
                ui_manager.show_dialog(dialog.dialog_id)
            else:
                logger.error("ui_managerが初期化されていないため、ダイアログを表示できません")
        except Exception as e:
            logger.error(f"ダイアログ表示中にエラーが発生しました: {e}")
    
    def _reset_keybinds(self):
        """キーバインドを初期化"""
        # 確認ダイアログ
        confirm_text = "キーバインドを初期設定に戻しますか？\\n\\n現在の設定は失われます。"
        
        dialog = UIDialog(
            "reset_keybinds_confirm",
            "キーバインド初期化",
            confirm_text
        )
        
        # ボタンを手動で追加
        from src.ui.base_ui_pygame import UIButton
        yes_button = UIButton("yes_reset_keybinds", "はい",
                             x=dialog.rect.x + 50, y=dialog.rect.y + dialog.rect.height - 50,
                             width=100, height=30)
        yes_button.on_click = self._execute_keybind_reset
        dialog.add_element(yes_button)
        
        no_button = UIButton("no_reset_keybinds", "いいえ",
                            x=dialog.rect.x + dialog.rect.width - 130, y=dialog.rect.y + dialog.rect.height - 50,
                            width=100, height=30)
        no_button.on_click = self._close_dialog
        dialog.add_element(no_button)
        
        try:
            if ui_manager is not None:
                ui_manager.add_dialog(dialog)
                ui_manager.show_dialog(dialog.dialog_id)
            else:
                logger.error("ui_managerが初期化されていないため、ダイアログを表示できません")
        except Exception as e:
            logger.error(f"ダイアログ表示中にエラーが発生しました: {e}")
    
    def _execute_keybind_reset(self):
        """キーバインド初期化を実行"""
        # InputManagerのデフォルトバインディングを復元
        try:
            from src.core.input_manager import input_manager
            if hasattr(input_manager, '_setup_default_bindings'):
                input_manager._setup_default_bindings()
        except ImportError:
            logger.warning("input_managerの読み込みに失敗しました")
        
        self._show_message("キーバインドを初期設定に戻しました")
    
    def _save_settings(self):
        """設定を保存"""
        if not self.pending_changes:
            self._show_message("保存する変更がありません")
            return
        
        try:
            # 現在の設定に変更をマージ
            self.current_settings.update(self.pending_changes)
            
            # 設定ファイルに保存
            self._save_settings_to_file()
            
            # 変更を適用
            self._apply_settings()
            
            # 保留中の変更をクリア
            self.pending_changes.clear()
            
            self._show_message("設定を保存しました")
            logger.info("設定が保存されました")
            
        except Exception as e:
            self._show_message(f"設定の保存に失敗しました: {str(e)}")
            logger.error(f"設定保存エラー: {e}")
    
    def _save_settings_to_file(self):
        """設定をファイルに保存"""
        try:
            import yaml
            from pathlib import Path
            
            # 設定ファイルパス
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "user_settings.yaml"
            
            # 現在の設定を保存
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.current_settings, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"設定ファイルに保存しました: {config_file}")
        except Exception as e:
            logger.error(f"設定ファイル保存エラー: {e}")
            raise
    
    def _apply_settings(self):
        """設定を適用"""
        # 各システムに設定を適用
        try:
            # 言語設定の適用
            language = self.current_settings.get("language", "ja")
            config_manager.set_language(language)
            logger.info(f"言語を設定しました: {language}")
            
            # 入力システムに適用（動的インポート）
            try:
                from src.core.input_manager import input_manager
                if hasattr(input_manager, 'analog_deadzone'):
                    input_manager.analog_deadzone = self.current_settings.get("analog_deadzone", 0.3)
                    input_manager.analog_sensitivity = self.current_settings.get("analog_sensitivity", 1.0)
                    input_manager.controller_enabled = self.current_settings.get("controller_enabled", True)
            except ImportError:
                logger.warning("input_managerの読み込みに失敗しました")
            
            # フィードバックシステムに適用
            feedback_level = self.current_settings.get("feedback_level", "normal")
            # feedback_systemがあれば適用（循環インポート回避のため条件付き）
            
            logger.info("設定を各システムに適用しました")
            
        except Exception as e:
            logger.error(f"設定適用エラー: {e}")
    
    def _discard_changes(self):
        """変更を破棄"""
        self.pending_changes.clear()
        self._show_message("変更を破棄しました")
        self._back_to_main_settings()
    
    def _show_reset_confirmation(self):
        """設定初期化の確認"""
        confirm_text = "すべての設定を初期値に戻しますか？\\n\\n現在の設定は失われます。"
        
        dialog = UIDialog(
            "reset_settings_confirm",
            "設定初期化",
            confirm_text
        )
        
        # ボタンを手動で追加
        from src.ui.base_ui_pygame import UIButton
        yes_button = UIButton("yes_reset_settings", "はい",
                             x=dialog.rect.x + 50, y=dialog.rect.y + dialog.rect.height - 50,
                             width=100, height=30)
        yes_button.on_click = self._reset_all_settings
        dialog.add_element(yes_button)
        
        no_button = UIButton("no_reset_settings", "いいえ",
                            x=dialog.rect.x + dialog.rect.width - 130, y=dialog.rect.y + dialog.rect.height - 50,
                            width=100, height=30)
        no_button.on_click = self._close_dialog
        dialog.add_element(no_button)
        
        try:
            if ui_manager is not None:
                ui_manager.add_dialog(dialog)
                ui_manager.show_dialog(dialog.dialog_id)
            else:
                logger.error("ui_managerが初期化されていないため、ダイアログを表示できません")
        except Exception as e:
            logger.error(f"ダイアログ表示中にエラーが発生しました: {e}")
    
    def _reset_all_settings(self):
        """すべての設定を初期化"""
        self.current_settings = self._get_default_settings()
        self.pending_changes.clear()
        
        try:
            self._save_settings_to_file()
            self._apply_settings()
            self._show_message("設定を初期化しました")
            logger.info("設定が初期化されました")
        except Exception as e:
            self._show_message(f"設定の初期化に失敗しました: {str(e)}")
            logger.error(f"設定初期化エラー: {e}")
    
    def _refresh_current_menu(self):
        """現在のメニューを再表示"""
        if self.current_category:
            self._show_category_settings(self.current_category)
    
    def show(self):
        """設定UIを表示"""
        self.show_settings_menu()
    
    def hide(self):
        """設定UIを非表示"""
        try:
            if ui_manager is not None:
                ui_manager.hide_menu("settings_main")
        except Exception as e:
            logger.warning(f"設定UI非表示処理でエラーが発生しました: {e}")
        self.is_open = False
        logger.debug("設定UIを非表示にしました")
    
    def destroy(self):
        """設定UIを破棄"""
        self.hide()
        self.current_category = None
        self.pending_changes.clear()
        logger.debug("SettingsUIを破棄しました")
    
    def set_close_callback(self, callback: Callable):
        """閉じるコールバックを設定"""
        self.callback_on_close = callback
    
    def _back_to_main_settings(self):
        """メイン設定に戻る"""
        self.current_category = None
        # 現在のメニューを隠す
        try:
            if ui_manager is not None:
                ui_manager.hide_all()
        except Exception as e:
            logger.warning(f"メニューを隠す際にエラーが発生しました: {e}")
        # メイン設定メニューを再表示
        self.show_settings_menu()
    
    def _close_settings_ui(self):
        """設定UIを閉じる"""
        if self.pending_changes:
            # 未保存の変更がある場合の確認
            confirm_text = "未保存の変更があります。\\n\\n保存せずに閉じますか？"
            
            dialog = UIDialog(
                "unsaved_changes_confirm",
                "未保存の変更",
                confirm_text
            )
            
            # ボタンを手動で追加
            from src.ui.base_ui_pygame import UIButton
            save_button = UIButton("save_close", "保存して閉じる",
                                  x=dialog.rect.x + 20, y=dialog.rect.y + dialog.rect.height - 50,
                                  width=120, height=30)
            save_button.on_click = self._save_and_close
            dialog.add_element(save_button)
            
            nosave_button = UIButton("nosave_close", "保存せずに閉じる",
                                    x=dialog.rect.x + 150, y=dialog.rect.y + dialog.rect.height - 50,
                                    width=120, height=30)
            nosave_button.on_click = self._close_without_saving
            dialog.add_element(nosave_button)
            
            back_button = UIButton("back_unsaved", "戻る",
                                  x=dialog.rect.x + dialog.rect.width - 80, y=dialog.rect.y + dialog.rect.height - 50,
                                  width=60, height=30)
            back_button.on_click = self._close_dialog
            dialog.add_element(back_button)
            
            try:
                if ui_manager is not None:
                    ui_manager.add_dialog(dialog)
                    ui_manager.show_dialog(dialog.dialog_id)
                else:
                    logger.error("ui_managerが初期化されていないため、ダイアログ要素を表示できません")
            except Exception as e:
                logger.error(f"ダイアログ要素表示中にエラーが発生しました: {e}")
        else:
            self._actually_close()
    
    def _save_and_close(self):
        """保存してから閉じる"""
        self._save_settings()
        self._actually_close()
    
    def _close_without_saving(self):
        """保存せずに閉じる"""
        self.pending_changes.clear()
        self._actually_close()
    
    def _actually_close(self):
        """実際に閉じる"""
        self.hide()
        if self.callback_on_close:
            self.callback_on_close()
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        try:
            if ui_manager is not None:
                ui_manager.hide_all()
            else:
                logger.warning("ui_managerが初期化されていません")
        except Exception as e:
            logger.error(f"ダイアログを閉じる際にエラーが発生しました: {e}")
    
    def _show_message(self, message: str):
        """メッセージを表示"""
        dialog = UIDialog(
            "settings_message",
            "設定",
            message
        )
        
        # ボタンを手動で追加
        from src.ui.base_ui_pygame import UIButton
        ok_button = UIButton("ok_message", "OK",
                            x=dialog.rect.x + dialog.rect.width // 2 - 50, y=dialog.rect.y + dialog.rect.height - 50,
                            width=100, height=30)
        ok_button.on_click = self._close_dialog
        dialog.add_element(ok_button)
        
        try:
            if ui_manager is not None:
                ui_manager.add_dialog(dialog)
                ui_manager.show_dialog(dialog.dialog_id)
            else:
                logger.error("ui_managerが初期化されていないため、ダイアログを表示できません")
        except Exception as e:
            logger.error(f"ダイアログ表示中にエラーが発生しました: {e}")
    
    def _show_new_game_confirmation(self):
        """新規ゲーム開始の確認"""
        confirm_text = "新規ゲームを開始しますか？\n\n警告: 現在のすべてのセーブデータが削除されます。\nこの操作は取り消せません。"
        
        dialog = UIDialog(
            "new_game_confirm",
            "新規ゲーム開始確認",
            confirm_text
        )
        
        # ボタンを手動で追加
        from src.ui.base_ui_pygame import UIButton
        confirm_button = UIButton("confirm_new_game", "新規ゲーム開始", 
                                 x=dialog.rect.x + 50, y=dialog.rect.y + dialog.rect.height - 50,
                                 width=150, height=30)
        confirm_button.on_click = self._show_final_new_game_confirmation
        dialog.add_element(confirm_button)
        
        cancel_button = UIButton("cancel_new_game", "キャンセル",
                                x=dialog.rect.x + dialog.rect.width - 150, y=dialog.rect.y + dialog.rect.height - 50,
                                width=100, height=30)
        cancel_button.on_click = self._close_dialog
        dialog.add_element(cancel_button)
        
        try:
            if ui_manager is not None:
                ui_manager.add_dialog(dialog)
                ui_manager.show_dialog(dialog.dialog_id)
            else:
                logger.error("ui_managerが初期化されていないため、ダイアログを表示できません")
        except Exception as e:
            logger.error(f"ダイアログ表示中にエラーが発生しました: {e}")
    
    def _show_final_new_game_confirmation(self):
        """新規ゲーム開始の最終確認"""
        final_text = "本当に新規ゲームを開始しますか？\n\n現在のプレイデータ:\n• キャラクター\n• パーティ\n• アイテム\n• ダンジョン進行状況\n\nすべてが削除されます。"
        
        dialog = UIDialog(
            "new_game_final_confirm",
            "最終確認",
            final_text,
            width=500, height=300
        )
        
        # ボタンを手動で追加
        from src.ui.base_ui_pygame import UIButton
        execute_button = UIButton("execute_new_game", "はい、新規ゲームを開始", 
                                 x=dialog.rect.x + 30, y=dialog.rect.y + dialog.rect.height - 50,
                                 width=200, height=30)
        execute_button.on_click = self._execute_new_game
        dialog.add_element(execute_button)
        
        cancel_button = UIButton("cancel_final", "キャンセル",
                                x=dialog.rect.x + dialog.rect.width - 130, y=dialog.rect.y + dialog.rect.height - 50,
                                width=100, height=30)
        cancel_button.on_click = self._close_dialog
        dialog.add_element(cancel_button)
        
        try:
            if ui_manager is not None:
                ui_manager.add_dialog(dialog)
                ui_manager.show_dialog(dialog.dialog_id)
            else:
                logger.error("ui_managerが初期化されていないため、ダイアログを表示できません")
        except Exception as e:
            logger.error(f"ダイアログ表示中にエラーが発生しました: {e}")
    
    def _execute_new_game(self):
        """新規ゲームを実行"""
        try:
            # セーブデータをクリア
            self._clear_all_save_data()
            
            # 成功メッセージ
            self._show_message("新規ゲームを開始しました。\\nタイトル画面に戻ります。")
            
            # タイトル画面に戻る処理
            self._return_to_title()
            
        except Exception as e:
            logger.error(f"新規ゲーム開始エラー: {e}")
            self._show_message(f"新規ゲーム開始に失敗しました: {str(e)}")
    
    def _clear_all_save_data(self):
        """すべてのセーブデータをクリア"""
        import shutil
        from pathlib import Path
        
        logger.info("セーブデータのクリアを開始します")
        
        # セーブディレクトリのパス
        save_dirs = [
            Path("saves"),
            Path("saves/characters"),
            Path("saves/parties"),
            Path("saves/dungeons"),
            Path("saves/game_state")
        ]
        
        # 各ディレクトリをクリア
        for save_dir in save_dirs:
            if save_dir.exists():
                try:
                    # ディレクトリ内のファイルを削除
                    for file in save_dir.glob("*"):
                        if file.is_file():
                            file.unlink()
                            logger.debug(f"削除: {file}")
                except Exception as e:
                    logger.error(f"ディレクトリ {save_dir} のクリアに失敗: {e}")
        
        # デフォルトパーティを再作成
        self._create_default_party()
        
        logger.info("セーブデータのクリアが完了しました")
    
    def _create_default_party(self):
        """デフォルトパーティを作成"""
        try:
            from src.character.party import Party
            from src.core.save_manager import save_manager
            
            # デフォルトパーティを作成
            default_party = Party("新しい冒険者")
            
            # セーブ
            save_manager.save_party(default_party)
            
            logger.info("デフォルトパーティを作成しました")
        except Exception as e:
            logger.error(f"デフォルトパーティ作成エラー: {e}")
    
    def _return_to_title(self):
        """タイトル画面に戻る"""
        try:
            # 現在の画面をすべて閉じる
            self._actually_close()
            
            # GameManagerに通知（存在する場合）
            try:
                from src.core.game_manager import GameManager
                # GameManagerインスタンスは通常グローバルで管理されるため、
                # ここではクラスメソッドやシングルトンパターンが必要
                # 実装に応じて調整が必要
                logger.info("タイトル画面への遷移を実行します")
                # 実際の実装では、アプリケーション全体の状態を管理する
                # システムが必要です
            except ImportError:
                logger.warning("GameManagerへのアクセスに失敗しました")
                
        except Exception as e:
            logger.error(f"タイトル画面への遷移エラー: {e}")


# グローバルインスタンス
settings_ui = SettingsUI()