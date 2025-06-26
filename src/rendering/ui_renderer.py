"""UI描画レンダラー"""

import pygame
from typing import Optional

from src.dungeon.dungeon_manager import DungeonState, PlayerPosition
from src.dungeon.dungeon_generator import DungeonLevel, Direction
from src.rendering.renderer_config import UIConfig, ColorConfig
from src.utils.logger import logger


class UIRenderer:
    """UI描画処理クラス"""
    
    def __init__(self, screen: pygame.Surface, ui_config: UIConfig = None, 
                 color_config: ColorConfig = None):
        self.screen = screen
        self.ui_config = ui_config or UIConfig()
        self.color_config = color_config or ColorConfig()
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # フォント初期化
        self._init_fonts()
    
    def _init_fonts(self):
        """フォント初期化"""
        try:
            # 日本語対応フォント
            font_names = 'notosanscjk,hiragino,meiryo,msgothic'
            self.font_small = pygame.font.SysFont(font_names, self.ui_config.font_size_small)
            self.font_medium = pygame.font.SysFont(font_names, self.ui_config.font_size_medium)
            self.font_large = pygame.font.SysFont(font_names, self.ui_config.font_size_large)
        except:
            # フォールバック
            self.font_small = pygame.font.SysFont(None, self.ui_config.font_size_small)
            self.font_medium = pygame.font.SysFont(None, self.ui_config.font_size_medium)
            self.font_large = pygame.font.SysFont(None, self.ui_config.font_size_large)
    
    def render_basic_ui(self, player_position: PlayerPosition, level: DungeonLevel):
        """基本UI描画"""
        try:
            # 位置情報表示
            pos_text = f"Position: ({player_position.x}, {player_position.y}) Level: {player_position.level}"
            text_surface = self.font_small.render(pos_text, True, self.color_config.white)
            self.screen.blit(text_surface, (self.ui_config.position_text_x, self.ui_config.position_text_y))
            
            # 向いている方向
            direction_text = f"Facing: {player_position.facing.value}"
            dir_surface = self.font_small.render(direction_text, True, self.color_config.white)
            self.screen.blit(dir_surface, (self.ui_config.position_text_x, 
                                         self.ui_config.position_text_y + 30))
            
            # 操作説明
            help_text = "WASD: Move, Space: Menu, ESC: Return"
            help_surface = self.font_small.render(help_text, True, self.color_config.gray)
            self.screen.blit(help_surface, (self.ui_config.help_text_x, 
                                          self.screen_height - self.ui_config.bottom_margin))
        except Exception as e:
            logger.warning(f"基本UI描画エラー: {e}")
    
    def render_game_ui(self, dungeon_state: DungeonState, dungeon_ui_manager=None):
        """ゲームUI描画"""
        pos = dungeon_state.player_position
        if not pos:
            return
        
        # コンパス表示
        self._render_compass(pos)
        
        # 位置情報表示
        self._render_position_info(pos)
        
        # ヘルプテキスト
        self._render_help_text()
        
        # キャラクターステータスバー
        if dungeon_ui_manager:
            try:
                dungeon_ui_manager.render_overlay()
            except Exception as e:
                logger.warning(f"ダンジョンステータスバー描画エラー: {e}")
    
    def _render_compass(self, pos: PlayerPosition):
        """コンパス描画"""
        compass_text = {
            Direction.NORTH: 'N',
            Direction.EAST: 'E',
            Direction.SOUTH: 'S',
            Direction.WEST: 'W'
        }
        compass_surface = self.font_large.render(compass_text[pos.facing], True, self.color_config.white)
        self.screen.blit(compass_surface, (self.screen_width - self.ui_config.compass_x_offset, 
                                         self.ui_config.compass_y_offset))
    
    def _render_position_info(self, pos: PlayerPosition):
        """位置情報描画"""
        position_text = f"Pos: ({pos.x}, {pos.y}) Lv: {pos.level}"
        try:
            position_surface = self.font_small.render(position_text, True, self.color_config.white)
            self.screen.blit(position_surface, (self.ui_config.position_text_x, 
                                              self.ui_config.position_text_y))
        except:
            # フォールバック
            position_surface = self.font_small.render(position_text, True, self.color_config.white)
            self.screen.blit(position_surface, (self.ui_config.position_text_x, 
                                              self.ui_config.position_text_y))
    
    def _render_help_text(self):
        """ヘルプテキスト描画"""
        help_text = "WASD: Move / QE: Turn / ESC: Menu"
        try:
            help_surface = self.font_small.render(help_text, True, self.color_config.gray)
            self.screen.blit(help_surface, (self.ui_config.help_text_x, 
                                          self.screen_height - self.ui_config.bottom_margin))
        except:
            # フォールバック
            help_surface = self.font_small.render(help_text, True, self.color_config.gray)
            self.screen.blit(help_surface, (self.ui_config.help_text_x, 
                                          self.screen_height - self.ui_config.bottom_margin))