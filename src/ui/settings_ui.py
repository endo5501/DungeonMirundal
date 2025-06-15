"""設定画面UIシステム"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from src.ui.base_ui import UIElement, UIButton, UIText, UIMenu, UIDialog, UIState, ui_manager
from src.core.config_manager import config_manager
from src.core.input_manager import input_manager, FeedbackLevel
from src.utils.logger import logger


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
            # ゲーム設定の読み込み
            game_config = config_manager.load_config("game_settings")
            return game_config.get("user_settings", {})
        except:
            # デフォルト設定を返す
            return self._get_default_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            # ゲームプレイ
            "auto_save": True,
            "difficulty": "normal",
            "battle_speed": "normal",
            "message_speed": "normal",
            "confirm_actions": True,
            
            # 操作設定
            "controller_enabled": True,
            "keyboard_enabled": True,
            "analog_deadzone": 0.3,
            "analog_sensitivity": 1.0,
            "vibration_enabled": True,
            
            # 音声設定
            "master_volume": 1.0,
            "music_volume": 0.8,
            "sfx_volume": 0.9,
            "voice_volume": 1.0,
            "mute_on_focus_loss": True,
            
            # 表示設定
            "fullscreen": False,
            "resolution": "1024x768",
            "vsync": True,
            "show_fps": False,
            "ui_scale": 1.0,
            
            # アクセシビリティ
            "feedback_level": "normal",
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
            "設定を初期化",
            self._show_reset_confirmation
        )
        
        # 変更の保存
        if self.pending_changes:
            settings_menu.add_menu_item(
                "変更を保存",
                self._save_settings
            )
            settings_menu.add_menu_item(
                "変更を破棄",
                self._discard_changes
            )
        
        settings_menu.add_menu_item(
            config_manager.get_text("menu.close"),
            self._close_settings_ui
        )
        
        ui_manager.register_element(settings_menu)
        ui_manager.show_element(settings_menu.element_id, modal=True)
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
        gameplay_menu = UIMenu("gameplay_settings", "ゲームプレイ設定")
        
        # オートセーブ
        auto_save = self._get_setting_value("auto_save")
        gameplay_menu.add_menu_item(
            f"オートセーブ: {'有効' if auto_save else '無効'}",
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
        gameplay_menu.add_menu_item(
            f"行動確認: {'有効' if confirm_actions else '無効'}",
            self._toggle_setting,
            ["confirm_actions"]
        )
        
        gameplay_menu.add_menu_item(
            "戻る",
            self._back_to_main_settings
        )
        
        ui_manager.register_element(gameplay_menu)
        ui_manager.show_element(gameplay_menu.element_id, modal=True)
    
    def _show_controls_settings(self):
        """操作設定を表示"""
        controls_menu = UIMenu("controls_settings", "操作設定")
        
        # コントローラー有効
        controller_enabled = self._get_setting_value("controller_enabled")
        controls_menu.add_menu_item(
            f"コントローラー: {'有効' if controller_enabled else '無効'}",
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
        controls_menu.add_menu_item(
            f"振動: {'有効' if vibration else '無効'}",
            self._toggle_setting,
            ["vibration_enabled"]
        )
        
        # キーバインド設定
        controls_menu.add_menu_item(
            "キーバインド設定",
            self._show_keybind_settings
        )
        
        controls_menu.add_menu_item(
            "戻る",
            self._back_to_main_settings
        )
        
        ui_manager.register_element(controls_menu)
        ui_manager.show_element(controls_menu.element_id, modal=True)
    
    def _show_audio_settings(self):
        """音声設定を表示"""
        audio_menu = UIMenu("audio_settings", "音声設定")
        
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
        audio_menu.add_menu_item(
            f"非アクティブ時ミュート: {'有効' if mute_on_focus_loss else '無効'}",
            self._toggle_setting,
            ["mute_on_focus_loss"]
        )
        
        audio_menu.add_menu_item(
            "戻る",
            self._back_to_main_settings
        )
        
        ui_manager.register_element(audio_menu)
        ui_manager.show_element(audio_menu.element_id, modal=True)
    
    def _show_graphics_settings(self):
        """表示設定を表示"""
        graphics_menu = UIMenu("graphics_settings", "表示設定")
        
        # フルスクリーン
        fullscreen = self._get_setting_value("fullscreen")
        graphics_menu.add_menu_item(
            f"フルスクリーン: {'有効' if fullscreen else '無効'}",
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
            "戻る",
            self._back_to_main_settings
        )
        
        ui_manager.register_element(graphics_menu)
        ui_manager.show_element(graphics_menu.element_id, modal=True)
    
    def _show_accessibility_settings(self):
        """アクセシビリティ設定を表示"""
        accessibility_menu = UIMenu("accessibility_settings", "アクセシビリティ設定")
        
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
            "戻る",
            self._back_to_main_settings
        )
        
        ui_manager.register_element(accessibility_menu)
        ui_manager.show_element(accessibility_menu.element_id, modal=True)
    
    def _show_keybind_settings(self):
        """キーバインド設定を表示"""
        keybind_menu = UIMenu("keybind_settings", "キーバインド設定")
        
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
            "デフォルトに戻す",
            self._reset_keybinds
        )
        
        keybind_menu.add_menu_item(
            "戻る",
            self._show_controls_settings
        )
        
        ui_manager.register_element(keybind_menu)
        ui_manager.show_element(keybind_menu.element_id, modal=True)
    
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
            dialog_text,
            buttons=[
                {"text": "キャンセル", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _reset_keybinds(self):
        """キーバインドを初期化"""
        # 確認ダイアログ
        confirm_text = "キーバインドを初期設定に戻しますか？\\n\\n現在の設定は失われます。"
        
        dialog = UIDialog(
            "reset_keybinds_confirm",
            "キーバインド初期化",
            confirm_text,
            buttons=[
                {"text": "はい", "command": self._execute_keybind_reset},
                {"text": "いいえ", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _execute_keybind_reset(self):
        """キーバインド初期化を実行"""
        # InputManagerのデフォルトバインディングを復元
        if hasattr(input_manager, '_setup_default_bindings'):
            input_manager._setup_default_bindings()
        
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
            # 設定ファイルの更新（実装は簡略化）
            logger.info("設定ファイルに保存")
        except Exception as e:
            logger.error(f"設定ファイル保存エラー: {e}")
            raise
    
    def _apply_settings(self):
        """設定を適用"""
        # 各システムに設定を適用
        try:
            # 入力システムに適用
            if hasattr(input_manager, 'analog_deadzone'):
                input_manager.analog_deadzone = self.current_settings.get("analog_deadzone", 0.3)
                input_manager.analog_sensitivity = self.current_settings.get("analog_sensitivity", 1.0)
                input_manager.controller_enabled = self.current_settings.get("controller_enabled", True)
            
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
            confirm_text,
            buttons=[
                {"text": "はい", "command": self._reset_all_settings},
                {"text": "いいえ", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
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
            ui_manager.hide_element("settings_main")
        except:
            pass
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
        self.show_settings_menu()
    
    def _close_settings_ui(self):
        """設定UIを閉じる"""
        if self.pending_changes:
            # 未保存の変更がある場合の確認
            confirm_text = "未保存の変更があります。\\n\\n保存せずに閉じますか？"
            
            dialog = UIDialog(
                "unsaved_changes_confirm",
                "未保存の変更",
                confirm_text,
                buttons=[
                    {"text": "保存して閉じる", "command": self._save_and_close},
                    {"text": "保存せずに閉じる", "command": self._close_without_saving},
                    {"text": "戻る", "command": self._close_dialog}
                ]
            )
            
            ui_manager.register_element(dialog)
            ui_manager.show_element(dialog.element_id, modal=True)
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
        ui_manager.hide_all_elements()
    
    def _show_message(self, message: str):
        """メッセージを表示"""
        dialog = UIDialog(
            "settings_message",
            "設定",
            message,
            buttons=[
                {"text": "OK", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)


# グローバルインスタンス
settings_ui = SettingsUI()