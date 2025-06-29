"""
OverworldMainWindow クラス

地上部メインメニュー用のWindowManagerベースのウィンドウ
"""

import pygame
from typing import Dict, Any, Optional, Callable
from .menu_window import MenuWindow
from src.utils.logger import logger
from src.core.config_manager import config_manager


class OverworldMainWindow(MenuWindow):
    """
    地上部メインメニューウィンドウ
    
    6つの施設 + 設定画面のメニューを提供
    """
    
    def __init__(self, window_id: str = "overworld_main", 
                 action_handler: Optional[Callable] = None, **kwargs):
        """
        地上部メインウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            action_handler: アクションハンドラー
        """
        # 地上部メインメニュー設定を作成
        menu_config = self._create_main_menu_config()
        
        super().__init__(window_id, menu_config, **kwargs)
        self.action_handler = action_handler
        
        # ルートメニューとして設定（戻るボタンを追加しない）
        self.menu_config['is_root'] = True
        self.back_button_manager.menu_config['is_root'] = True
        
        logger.debug(f"OverworldMainWindowを初期化: {window_id}")
    
    def _create_main_menu_config(self) -> Dict[str, Any]:
        """メインメニュー設定を作成"""
        return {
            'title': config_manager.get_text("overworld.main_menu.title"),
            'is_root': True,  # ルートメニューなので戻るボタンなし
            'buttons': [
                {
                    'id': 'guild',
                    'text': config_manager.get_text("facility.guild"),
                    'action': 'enter_facility:guild'
                },
                {
                    'id': 'inn',
                    'text': config_manager.get_text("facility.inn"),
                    'action': 'enter_facility:inn'
                },
                {
                    'id': 'shop',
                    'text': config_manager.get_text("facility.shop"),
                    'action': 'enter_facility:shop'
                },
                {
                    'id': 'temple',
                    'text': config_manager.get_text("facility.temple"),
                    'action': 'enter_facility:temple'
                },
                {
                    'id': 'magic_guild',
                    'text': config_manager.get_text("facility.magic_guild"),
                    'action': 'enter_facility:magic_guild'
                },
                {
                    'id': 'dungeon',
                    'text': config_manager.get_text("overworld.main_menu.enter_dungeon"),
                    'action': 'enter_dungeon'
                },
                {
                    'id': 'settings',
                    'text': config_manager.get_text("overworld.main_menu.settings"),
                    'action': 'show_settings'
                },
                {
                    'id': 'save_game',
                    'text': config_manager.get_text("overworld.main_menu.save_game"),
                    'action': 'save_game'
                },
                {
                    'id': 'load_game',
                    'text': config_manager.get_text("overworld.main_menu.load_game"),
                    'action': 'load_game'
                },
                {
                    'id': 'exit_game',
                    'text': config_manager.get_text("overworld.main_menu.exit_game"),
                    'action': 'exit_game'
                }
            ]
        }
    
    def _execute_button_action(self, button) -> None:
        """ボタンアクションを実行（オーバーライド）"""
        logger.debug(f"OverworldMainWindow: ボタンアクション実行: {button.action} (id={button.id})")
        
        if self.action_handler:
            message_data = {
                'action': button.action,
                'button_id': button.id
            }
            logger.debug(f"OverworldMainWindow: action_handler呼び出し: {message_data}")
            self.action_handler('menu_action', message_data)
        else:
            # デフォルトの処理
            logger.debug("OverworldMainWindow: デフォルト処理実行")
            super()._execute_button_action(button)
    
    def handle_escape(self) -> bool:
        """ESCキー処理（ルートメニューなので何もしない）"""
        logger.debug("OverworldMainWindow: ESCキーが押されました（ルートメニューのため無視）")
        return True  # ESCキーを処理したことを示す