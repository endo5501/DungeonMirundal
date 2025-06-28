"""
BackButtonManager クラス

戻るボタンの管理と処理を担当するExtract Classリファクタリング
"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .menu_button import MenuButton
from src.utils.logger import logger


@dataclass
class BackButtonConfig:
    """戻るボタンの設定"""
    text: str = '戻る'
    id: str = 'back'
    action: str = 'window_back'
    enabled: bool = True


class BackButtonManager:
    """
    戻るボタン管理クラス
    
    Extract Classパターンにより、MenuWindowから戻るボタン関連の責任を分離
    """
    
    def __init__(self, menu_config: Dict[str, Any]):
        """
        戻るボタンマネージャーを初期化
        
        Args:
            menu_config: メニュー設定辞書
        """
        self.menu_config = menu_config
        self.back_button_config = self._create_back_button_config()
        
    def _create_back_button_config(self) -> Optional[BackButtonConfig]:
        """戻るボタン設定を作成"""
        if not self.should_add_back_button():
            return None
        
        text = self.menu_config.get('back_button_text', '戻る')
        return BackButtonConfig(text=text)
    
    def should_add_back_button(self) -> bool:
        """戻るボタンを追加する必要があるか判定"""
        # ルートメニューには戻るボタンを追加しない
        if self.menu_config.get('is_root', False):
            return False
        
        # 既に戻るボタンが存在する場合は追加しない
        for button_config in self.menu_config['buttons']:
            if button_config.get('action') == 'window_back':
                return False
        
        return True
    
    def create_back_button(self, button_rect: pygame.Rect, ui_manager: pygame_gui.UIManager, 
                          panel: pygame_gui.elements.UIPanel, style: Dict[str, Any]) -> Optional[MenuButton]:
        """
        戻るボタンを作成
        
        Args:
            button_rect: ボタンの矩形
            ui_manager: UIマネージャー
            panel: 親パネル
            style: スタイル設定
            
        Returns:
            Optional[MenuButton]: 作成された戻るボタン、不要な場合はNone
        """
        if not self.back_button_config:
            return None
        
        # pygame-guiボタンを作成
        ui_button = pygame_gui.elements.UIButton(
            relative_rect=button_rect,
            text=self.back_button_config.text,
            manager=ui_manager,
            container=panel
        )
        
        # MenuButtonオブジェクトを作成
        back_button = MenuButton(
            id=self.back_button_config.id,
            text=self.back_button_config.text,
            action=self.back_button_config.action,
            ui_element=ui_button,
            style=style
        )
        
        logger.debug(f"戻るボタンを作成: {self.back_button_config.text}")
        return back_button
    
    def handle_escape_key(self, send_message_callback) -> bool:
        """
        ESCキーが押されたときの処理
        
        Args:
            send_message_callback: メッセージ送信コールバック
            
        Returns:
            bool: ESCキーが処理された場合True
        """
        # ルートメニューの場合は何もしない
        if self.menu_config.get('is_root', False):
            return False
        
        # window_backアクションを送信
        message_data = {
            'action': 'window_back',
            'button_id': 'escape'
        }
        send_message_callback('menu_action', message_data)
        logger.debug("ESCキーによる戻るアクション実行")
        return True
    
    def get_additional_button_count(self) -> int:
        """追加される戻るボタンの数を取得"""
        return 1 if self.should_add_back_button() else 0