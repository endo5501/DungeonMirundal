"""ダンジョン階段使用確認ダイアログ"""

import pygame
import pygame_gui
from typing import Optional, Callable

from src.utils.logger import logger


class DungeonStairsDialog:
    """階段使用確認ダイアログウィンドウ（シンプル版）"""
    
    def __init__(self, ui_manager: pygame_gui.UIManager, 
                 stairs_type: str,
                 on_confirm: Optional[Callable] = None,
                 on_cancel: Optional[Callable] = None):
        """
        Args:
            ui_manager: pygame_gui UIマネージャー
            stairs_type: 階段タイプ ("up", "down", "exit")
            on_confirm: 確認時のコールバック
            on_cancel: キャンセル時のコールバック
        """
        self.ui_manager = ui_manager
        self.stairs_type = stairs_type
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        
        # ダイアログのサイズと位置
        window_width = 400
        window_height = 200
        window_rect = pygame.Rect(0, 0, window_width, window_height)
        window_rect.center = (ui_manager.window_resolution[0] // 2,
                             ui_manager.window_resolution[1] // 2)
        
        # UIConfirmationDialogを作成
        self.window = pygame_gui.windows.UIConfirmationDialog(
            rect=window_rect,
            manager=ui_manager,
            window_title=self._get_dialog_title(stairs_type),
            action_long_desc=self._get_confirmation_message(stairs_type),
            action_short_name='はい',
            blocking=False  # blocking=Falseに変更してテスト
        )
        
        logger.info(f"階段確認ダイアログを表示: {stairs_type}, window={self.window}")
        logger.info(f"ダイアログUIマネージャー: {ui_manager}")
        logger.info(f"on_confirm設定: {self.on_confirm is not None}")
        logger.info(f"on_cancel設定: {self.on_cancel is not None}")
    
    def _get_dialog_title(self, stairs_type: str) -> str:
        """階段タイプに応じたダイアログタイトルを取得"""
        titles = {
            "up": "上の階へ移動",
            "down": "下の階へ移動",
            "exit": "地上へ戻る"
        }
        return titles.get(stairs_type, "階段を使用")
    
    def process_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
            if event.ui_element == self.window:
                logger.info(f"階段使用を確認: {self.stairs_type}")
                if self.on_confirm:
                    self.on_confirm()
                return True
        elif event.type == pygame_gui.UI_WINDOW_CLOSE:
            if event.ui_element == self.window:
                logger.info("階段使用をキャンセル")
                if self.on_cancel:
                    self.on_cancel()
                return True
        
        return False
    
    def _get_confirmation_message(self, stairs_type: str) -> str:
        """階段タイプに応じた確認メッセージを取得"""
        messages = {
            "up": "上の階へ移動しますか？",
            "down": "下の階へ移動しますか？",
            "exit": "地上へ戻りますか？<br>（ダンジョンから退出します）"
        }
        return messages.get(stairs_type, "階段を使用しますか？")
    
    def kill(self):
        """ダイアログを閉じる"""
        if hasattr(self, 'window') and self.window:
            self.window.kill()
            self.window = None
    
    def update(self, time_delta: float):
        """更新処理"""
        if hasattr(self, 'window') and self.window:
            self.window.update(time_delta)