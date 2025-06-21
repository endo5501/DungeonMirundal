"""地上部管理システム（Pygame版）"""

from typing import Optional, Callable
import pygame
from src.character.party import Party
from src.ui.base_ui_pygame import UIMenu, UIButton, UIText
from src.utils.logger import logger
from src.core.config_manager import config_manager


class OverworldManager:
    """地上部管理クラス（Pygame版）"""
    
    def __init__(self):
        self.current_party: Optional[Party] = None
        self.ui_manager = None
        self.input_manager = None
        
        # コールバック
        self.enter_dungeon_callback: Optional[Callable] = None
        self.exit_game_callback: Optional[Callable] = None
        
        # UI要素
        self.main_menu: Optional[UIMenu] = None
        self.is_active = False
        
        logger.info("OverworldManager（Pygame版）を初期化しました")
    
    def set_ui_manager(self, ui_manager):
        """UIマネージャーを設定"""
        self.ui_manager = ui_manager
        self._create_main_menu()
    
    def set_input_manager(self, input_manager):
        """入力マネージャーを設定"""
        self.input_manager = input_manager
    
    def set_enter_dungeon_callback(self, callback: Callable):
        """ダンジョン入場コールバックを設定"""
        self.enter_dungeon_callback = callback
    
    def set_exit_game_callback(self, callback: Callable):
        """ゲーム終了コールバックを設定"""
        self.exit_game_callback = callback
    
    def _create_main_menu(self):
        """メインメニューを作成"""
        if not self.ui_manager:
            return
        
        # メインメニュー作成（英語版で確実に表示）
        self.main_menu = UIMenu("overworld_main", "Adventurer's Guild")
        
        # ダンジョンボタン
        dungeon_button = UIButton("enter_dungeon", "Enter Dungeon", 250, 200, 300, 50)
        dungeon_button.on_click = self._on_enter_dungeon
        self.main_menu.add_element(dungeon_button)
        
        # パーティ情報ボタン
        party_button = UIButton("party_info", "Party Info", 250, 270, 300, 50)
        party_button.on_click = self._on_party_info
        self.main_menu.add_element(party_button)
        
        # 宿屋ボタン
        inn_button = UIButton("inn", "Inn", 250, 340, 300, 50)
        inn_button.on_click = self._on_inn
        self.main_menu.add_element(inn_button)
        
        # ゲーム終了ボタン
        exit_button = UIButton("exit_game", "Exit Game", 250, 410, 300, 50)
        exit_button.on_click = self._on_exit_game
        self.main_menu.add_element(exit_button)
        
        # UIマネージャーに追加
        self.ui_manager.add_menu(self.main_menu)
        
        logger.info("オーバーワールドメインメニューを作成しました")
    
    def _on_enter_dungeon(self):
        """ダンジョン入場"""
        logger.info("ダンジョン入場が選択されました")
        if self.enter_dungeon_callback:
            try:
                # メインメニューを隠す
                if self.main_menu:
                    self.main_menu.hide()
                self.is_active = False
                
                # ダンジョンに遷移
                self.enter_dungeon_callback("main_dungeon")
            except Exception as e:
                logger.error(f"ダンジョン入場エラー: {e}")
                # エラーの場合はメニューを再表示
                if self.main_menu:
                    self.main_menu.show()
                self.is_active = True
    
    def _on_party_info(self):
        """パーティ情報表示"""
        logger.info("パーティ情報が選択されました")
        if self.current_party:
            # 簡易パーティ情報表示
            info_text = f"パーティ: {self.current_party.name}\\n"
            info_text += f"メンバー数: {len(self.current_party.get_living_characters())}人\\n"
            info_text += f"ゴールド: {self.current_party.gold}G"
            
            logger.info(f"パーティ情報: {info_text}")
    
    def _on_inn(self):
        """宿屋"""
        logger.info("宿屋が選択されました")
        if self.current_party:
            # 簡易回復処理
            for character in self.current_party.get_living_characters():
                character.derived_stats.current_hp = character.derived_stats.max_hp
                character.derived_stats.current_mp = character.derived_stats.max_mp
            
            logger.info("パーティを回復しました")
    
    def _on_exit_game(self):
        """ゲーム終了"""
        logger.info("ゲーム終了が選択されました")
        if self.exit_game_callback:
            self.exit_game_callback()
    
    def enter_overworld(self, party: Party, from_dungeon: bool = False) -> bool:
        """地上部に入場"""
        try:
            self.current_party = party
            self.is_active = True
            
            # UIマネージャーが設定されていない場合は後で設定
            if self.ui_manager and not self.main_menu:
                self._create_main_menu()
            
            # メインメニューを表示
            if self.main_menu:
                self.main_menu.show()
            
            if from_dungeon:
                logger.info("ダンジョンから地上部に帰還しました")
            else:
                logger.info("地上部に入場しました")
            
            return True
            
        except Exception as e:
            logger.error(f"地上部入場エラー: {e}")
            return False
    
    def exit_overworld(self):
        """地上部を退場"""
        self.is_active = False
        
        # メインメニューを隠す
        if self.main_menu:
            self.main_menu.hide()
        
        logger.info("地上部を退場しました")
    
    def render(self, screen: pygame.Surface):
        """地上部の描画"""
        if not self.is_active:
            return
        
        # 背景色（地上部らしい色）
        screen.fill((100, 150, 100))
        
        # 背景テキスト表示
        if self.ui_manager and self.ui_manager.default_font:
            font = self.ui_manager.default_font
            
            # タイトル
            title_text = font.render("冒険者ギルド", True, (255, 255, 255))
            title_rect = title_text.get_rect(center=(screen.get_width()//2, 80))
            screen.blit(title_text, title_rect)
            
            # パーティ情報
            if self.current_party:
                party_info = f"パーティ: {self.current_party.name} | ゴールド: {self.current_party.gold}G"
                info_text = font.render(party_info, True, (200, 200, 200))
                info_rect = info_text.get_rect(center=(screen.get_width()//2, 120))
                screen.blit(info_text, info_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理"""
        if not self.is_active:
            return False
        
        # ESCキーでゲーム終了
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_exit_game()
                return True
        
        return False
    
    def save_overworld_state(self, slot_id: str) -> bool:
        """地上部状態を保存"""
        try:
            # 簡易実装（実際の保存処理は後で実装）
            logger.info(f"地上部状態を保存しました: スロット{slot_id}")
            return True
        except Exception as e:
            logger.error(f"地上部状態保存エラー: {e}")
            return False
    
    def load_overworld_state(self, slot_id: str) -> bool:
        """地上部状態を読み込み"""
        try:
            # 簡易実装（実際の読み込み処理は後で実装）
            logger.info(f"地上部状態を読み込みました: スロット{slot_id}")
            return True
        except Exception as e:
            logger.error(f"地上部状態読み込みエラー: {e}")
            return False