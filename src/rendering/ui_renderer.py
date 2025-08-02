"""UI描画レンダラー"""

import pygame
from typing import Optional

from src.dungeon.dungeon_manager import DungeonState, PlayerPosition
from src.dungeon.dungeon_generator import DungeonLevel, Direction
from src.rendering.renderer_config import UIConfig, ColorConfig
from src.utils.logger import logger


class UIRenderer:
    """UI描画処理クラス"""
    
    def __init__(self, screen: pygame.Surface, ui_config: Optional[UIConfig] = None, 
                 color_config: Optional[ColorConfig] = None):
        self.screen = screen
        self.ui_config = ui_config if ui_config is not None else UIConfig()
        self.color_config = color_config if color_config is not None else ColorConfig()
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # フォント初期化
        self._init_fonts()
    
    def _init_fonts(self):
        """フォント初期化"""
        # 利用可能なシステムフォントを取得
        available_fonts = pygame.font.get_fonts()
        japanese_font_candidates = ['noto', 'notosans', 'ipagothic', 'takao', 'dejavu']
        
        # 利用可能な日本語フォントを探す
        selected_font = None
        for font_name in japanese_font_candidates:
            if font_name in available_fonts:
                selected_font = font_name
                break
        
        try:
            if selected_font:
                self.font_small = pygame.font.SysFont(selected_font, self.ui_config.font_size_small)
                self.font_medium = pygame.font.SysFont(selected_font, self.ui_config.font_size_medium)
                self.font_large = pygame.font.SysFont(selected_font, self.ui_config.font_size_large)
            else:
                # フォールバック：Pygameデフォルト
                self.font_small = pygame.font.Font(None, self.ui_config.font_size_small)
                self.font_medium = pygame.font.Font(None, self.ui_config.font_size_medium)
                self.font_large = pygame.font.Font(None, self.ui_config.font_size_large)
        except:
            # 最終フォールバック
            self.font_small = pygame.font.Font(None, self.ui_config.font_size_small)
            self.font_medium = pygame.font.Font(None, self.ui_config.font_size_medium)
            self.font_large = pygame.font.Font(None, self.ui_config.font_size_large)
    
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
            
            # 現在のセル情報
            current_cell = level.get_cell(player_position.x, player_position.y)
            if current_cell:
                cell_info = self._get_cell_type_text(current_cell.cell_type)
                cell_surface = self.font_small.render(cell_info, True, self.color_config.yellow)
                self.screen.blit(cell_surface, (self.ui_config.position_text_x, 
                                              self.ui_config.position_text_y + 60))
            
            # 操作説明
            help_text = "WASD: Move, E: Use Stairs, P: Menu, ESC: Return"
            help_surface = self.font_small.render(help_text, True, self.color_config.gray)
            self.screen.blit(help_surface, (self.ui_config.help_text_x, 
                                          self.screen_height - self.ui_config.bottom_margin))
        except Exception as e:
            logger.warning(f"基本UI描画エラー: {e}")
    
    def _get_cell_type_text(self, cell_type) -> str:
        """セルタイプの表示テキストを取得"""
        from src.dungeon.dungeon_generator import CellType
        
        type_map = {
            CellType.FLOOR: "Floor",
            CellType.WALL: "Wall", 
            CellType.DOOR: "Door",
            CellType.STAIRS_UP: "Stairs (Up) - Press E to use",
            CellType.STAIRS_DOWN: "Stairs (Down) - Press E to use",
            CellType.EXIT: "Exit to Overworld - Press E to use",
            CellType.TREASURE: "Treasure",
            CellType.TRAP: "Trap",
            CellType.SPECIAL: "Special",
            CellType.BOSS: "Boss"
        }
        
        return type_map.get(cell_type, "Unknown")
    
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
        
        # ダンジョンUIマネージャーのオーバーレイ（ステータスバー、小地図等）
        if dungeon_ui_manager:
            try:
                # ダンジョン状態を更新して小地図を最新状態にする
                if hasattr(dungeon_ui_manager, 'set_dungeon_state'):
                    dungeon_ui_manager.set_dungeon_state(dungeon_state)
                
                # オーバーレイを描画（ステータスバーと小地図を含む）
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