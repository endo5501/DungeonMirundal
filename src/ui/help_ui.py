"""ヘルプ・チュートリアルUIシステム（WindowSystem統合版）"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import pygame

from src.ui.window_system import WindowManager
from src.ui.window_system.help_window import HelpWindow
from src.ui.window_system.help_enums import HelpCategory, HelpContext
from src.core.config_manager import config_manager
from src.core.input_manager import InputAction, GamepadButton
from src.utils.logger import logger


class HelpUI:
    """ヘルプ・チュートリアルUI管理クラス（WindowSystem統合版）"""
    
    def __init__(self):
        # UI状態
        self.is_open = False
        self.current_category: Optional[HelpCategory] = None
        self.callback_on_close: Optional[Callable] = None
        
        # WindowSystem統合
        self.window_manager = WindowManager.get_instance()
        self.help_window: Optional[HelpWindow] = None
        
        logger.debug("HelpUI（WindowSystem版）を初期化しました")
    
    def _get_help_window(self) -> HelpWindow:
        """HelpWindowインスタンスを取得または作成"""
        if self.help_window is None:
            # HelpWindowの初期化
            self.help_window = HelpWindow(
                window_id="help_main",
                title="ヘルプ・チュートリアル"
            )
        return self.help_window
    
    def show_help_menu(self):
        """ヘルプメインメニューを表示（WindowSystem版）"""
        try:
            help_window = self._get_help_window()
            help_window.show_main_help_menu()
            self.is_open = True
            logger.info("ヘルプメニューを表示（WindowSystem版）")
        except Exception as e:
            logger.error(f"ヘルプメニュー表示エラー: {e}")
    
    def show_category_help(self, category: str):
        """カテゴリ別ヘルプを表示（WindowSystem版）"""
        try:
            help_window = self._get_help_window()
            help_window.show_category_help(category)
            self.current_category = category
            logger.info(f"カテゴリヘルプを表示: {category}")
        except Exception as e:
            logger.error(f"カテゴリヘルプ表示エラー: {e}")
    
    def show_context_help(self, context: str):
        """コンテキストヘルプを表示（WindowSystem版）"""
        try:
            help_window = self._get_help_window()
            help_window.show_context_help(context)
            logger.info(f"コンテキストヘルプを表示: {context}")
        except Exception as e:
            logger.error(f"コンテキストヘルプ表示エラー: {e}")
    
    def show_quick_reference(self):
        """クイックリファレンスを表示（WindowSystem版）"""
        try:
            help_window = self._get_help_window()
            help_window.show_quick_reference()
            logger.info("クイックリファレンスを表示")
        except Exception as e:
            logger.error(f"クイックリファレンス表示エラー: {e}")
    
    def show_controls_guide(self):
        """操作ガイドを表示（WindowSystem版）"""
        try:
            help_window = self._get_help_window()
            help_window.show_controls_guide()
            logger.info("操作ガイドを表示")
        except Exception as e:
            logger.error(f"操作ガイド表示エラー: {e}")
    
    def show_first_time_help(self):
        """初回ヘルプを表示（WindowSystem版）"""
        try:
            help_window = self._get_help_window()
            help_window.show_first_time_help()
            logger.info("初回ヘルプを表示")
        except Exception as e:
            logger.error(f"初回ヘルプ表示エラー: {e}")
    
    def hide(self):
        """ヘルプUIを非表示（WindowSystem版）"""
        try:
            if self.help_window:
                self.help_window.close()
            self.is_open = False
            logger.info("ヘルプUIを非表示")
        except Exception as e:
            logger.error(f"ヘルプUI非表示エラー: {e}")
    
    def show(self):
        """ヘルプUIを表示（メインメニュー）"""
        self.show_help_menu()
    
    def set_callback_on_close(self, callback: Callable):
        """クローズ時コールバックを設定"""
        self.callback_on_close = callback
    
    def cleanup(self):
        """リソースクリーンアップ"""
        if self.help_window:
            self.help_window.cleanup()
            self.help_window = None
        self.is_open = False
        logger.info("HelpUIリソースをクリーンアップしました")


# グローバルインスタンス（互換性のため）
help_ui = HelpUI()