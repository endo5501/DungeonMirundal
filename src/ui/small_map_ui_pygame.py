"""
小地図UI（Pygame版）

ダンジョンの周辺マップを表示するUIコンポーネント
"""

from typing import List, Tuple
import pygame

from src.ui.base_ui_pygame import UIElement
from src.dungeon.dungeon_manager import DungeonState
from src.dungeon.dungeon_generator import DungeonCell, CellType, Direction


# 小地図UI定数
SMALL_MAP_WIDTH = 180
SMALL_MAP_HEIGHT = 180
SMALL_MAP_MARGIN = 10
CELL_SIZE = 20  # より大きなセルサイズで見やすく
MIN_CELL_SIZE = 8
MAX_CELL_SIZE = 16
PLAYER_MARKER_SIZE = 10  # プレイヤーマーカーを大きく
DIRECTION_MARKER_LENGTH = 16  # 向きマーカーも長く
MAP_VIEW_RANGE = 7  # プレイヤー周辺7x7の範囲を表示

# 色定義
MAP_BACKGROUND_COLOR = (20, 20, 30)
MAP_BORDER_COLOR = (80, 80, 100)
EXPLORED_FLOOR_COLOR = (120, 120, 140)
EXPLORED_WALL_COLOR = (60, 60, 80)
UNEXPLORED_COLOR = (40, 40, 50)
PLAYER_COLOR = (255, 100, 100)
DIRECTION_COLOR = (255, 150, 150)
STAIRS_UP_COLOR = (100, 255, 100)
STAIRS_DOWN_COLOR = (100, 100, 255)
TREASURE_COLOR = (255, 255, 100)
TRAP_COLOR = (255, 100, 255)


class SmallMapUI(UIElement):
    """小地図UIコンポーネント"""
    
    def __init__(self, screen: pygame.Surface, font_manager, dungeon_state: DungeonState):
        """
        小地図UIを初期化
        
        Args:
            screen: Pygameスクリーン
            font_manager: フォントマネージャー
            dungeon_state: ダンジョン状態
        """
        # 画面右上に配置
        screen_width = screen.get_width()
        x = screen_width - SMALL_MAP_WIDTH - SMALL_MAP_MARGIN
        y = SMALL_MAP_MARGIN
        
        super().__init__(x, y, SMALL_MAP_WIDTH, SMALL_MAP_HEIGHT)
        
        self.screen = screen
        self.font_manager = font_manager
        self.dungeon_state = dungeon_state
        self.is_visible = True
        
        # マップサーフェス
        self.map_surface = pygame.Surface((SMALL_MAP_WIDTH, SMALL_MAP_HEIGHT))
        self.map_rect = pygame.Rect(x, y, SMALL_MAP_WIDTH, SMALL_MAP_HEIGHT)
        
        # マップスケール計算
        self._calculate_map_scale()
        
    
    def _calculate_map_scale(self):
        """マップのスケールを計算（固定サイズの周辺マップ用）"""
        if not self.dungeon_state.player_position:
            self.cell_size = CELL_SIZE
            self.map_offset_x = 0
            self.map_offset_y = 0
            return
        
        # 固定サイズの周辺マップとして設計
        self.cell_size = CELL_SIZE
        
        # プレイヤー位置を中心にした固定範囲のマップ
        player_x = self.dungeon_state.player_position.x
        player_y = self.dungeon_state.player_position.y
        
        # マップの中央にプレイヤーを配置するためのオフセット計算
        map_center_x = SMALL_MAP_WIDTH // 2
        map_center_y = SMALL_MAP_HEIGHT // 2
        
        # プレイヤーをマップ中央に配置するためのオフセット
        self.map_offset_x = map_center_x - (player_x * self.cell_size) - (self.cell_size // 2)
        self.map_offset_y = map_center_y - (player_y * self.cell_size) - (self.cell_size // 2)
    
    def get_visible_cells(self) -> List[DungeonCell]:
        """表示可能な（探索済み）セルを取得（プレイヤー周辺の範囲のみ）"""
        if not self.dungeon_state.player_position:
            return []
        
        current_level = self.dungeon_state.player_position.level
        if current_level not in self.dungeon_state.levels:
            return []
        
        level_data = self.dungeon_state.levels[current_level]
        visible_cells = []
        
        # プレイヤー位置を中心とした範囲を計算
        player_x = self.dungeon_state.player_position.x
        player_y = self.dungeon_state.player_position.y
        half_range = MAP_VIEW_RANGE // 2
        
        for x in range(player_x - half_range, player_x + half_range + 1):
            for y in range(player_y - half_range, player_y + half_range + 1):
                cell = level_data.cells.get((x, y))
                if cell:
                    # 探索済みまたは訪問済みのセルのみ表示
                    if hasattr(cell, 'discovered') and cell.discovered:
                        visible_cells.append(cell)
                    elif hasattr(cell, 'visited') and cell.visited:
                        visible_cells.append(cell)
        
        return visible_cells
    
    def get_player_map_position(self) -> Tuple[int, int]:
        """プレイヤーのマップ上での位置を計算"""
        if not self.dungeon_state.player_position:
            return (SMALL_MAP_WIDTH // 2, SMALL_MAP_HEIGHT // 2)
        
        player_x = self.dungeon_state.player_position.x
        player_y = self.dungeon_state.player_position.y
        
        map_x = player_x * self.cell_size + self.map_offset_x + self.cell_size // 2
        map_y = player_y * self.cell_size + self.map_offset_y + self.cell_size // 2
        
        return (map_x, map_y)
    
    def get_direction_marker(self) -> Tuple[int, int]:
        """プレイヤーの向きマーカーの終点座標を計算"""
        if not self.dungeon_state.player_position:
            return self.get_player_map_position()
        
        player_map_x, player_map_y = self.get_player_map_position()
        direction = self.dungeon_state.player_position.facing
        
        # 方向に応じたオフセット
        direction_offsets = {
            Direction.NORTH: (0, -DIRECTION_MARKER_LENGTH),
            Direction.SOUTH: (0, DIRECTION_MARKER_LENGTH),
            Direction.EAST: (DIRECTION_MARKER_LENGTH, 0),
            Direction.WEST: (-DIRECTION_MARKER_LENGTH, 0)
        }
        
        offset_x, offset_y = direction_offsets.get(direction, (0, 0))
        
        return (player_map_x + offset_x, player_map_y + offset_y)
    
    def draw_explored_cells(self):
        """探索済みセルを描画"""
        visible_cells = self.get_visible_cells()
        
        for cell in visible_cells:
            cell_x = cell.x * self.cell_size + self.map_offset_x
            cell_y = cell.y * self.cell_size + self.map_offset_y
            
            # セルの色を決定
            if cell.cell_type == CellType.WALL:
                color = EXPLORED_WALL_COLOR
            else:
                color = EXPLORED_FLOOR_COLOR
            
            # セルを描画
            pygame.draw.rect(
                self.map_surface,
                color,
                (cell_x, cell_y, self.cell_size, self.cell_size)
            )
    
    def draw_special_objects(self):
        """特殊オブジェクト（階段、宝箱等）を描画"""
        visible_cells = self.get_visible_cells()
        
        for cell in visible_cells:
            cell_x = cell.x * self.cell_size + self.map_offset_x + self.cell_size // 2
            cell_y = cell.y * self.cell_size + self.map_offset_y + self.cell_size // 2
            
            # 階段
            if cell.cell_type == CellType.STAIRS_UP:
                pygame.draw.circle(self.map_surface, STAIRS_UP_COLOR, (cell_x, cell_y), self.cell_size // 2)
            elif cell.cell_type == CellType.STAIRS_DOWN:
                pygame.draw.circle(self.map_surface, STAIRS_DOWN_COLOR, (cell_x, cell_y), self.cell_size // 2)
            
            # 宝箱
            if hasattr(cell, 'has_treasure') and cell.has_treasure:
                pygame.draw.rect(
                    self.map_surface,
                    TREASURE_COLOR,
                    (cell_x - 1, cell_y - 1, 3, 3)
                )
            
            # トラップ
            if hasattr(cell, 'has_trap') and cell.has_trap:
                pygame.draw.circle(self.map_surface, TRAP_COLOR, (cell_x, cell_y), 1)
    
    def draw_player_marker(self):
        """プレイヤーマーカーを描画"""
        if not self.dungeon_state.player_position:
            return
        
        player_map_x, player_map_y = self.get_player_map_position()
        
        # プレイヤー位置のマーカー
        pygame.draw.circle(
            self.map_surface,
            PLAYER_COLOR,
            (player_map_x, player_map_y),
            PLAYER_MARKER_SIZE // 2
        )
        
        # 向きを示すライン
        direction_end_x, direction_end_y = self.get_direction_marker()
        pygame.draw.line(
            self.map_surface,
            DIRECTION_COLOR,
            (player_map_x, player_map_y),
            (direction_end_x, direction_end_y),
            2
        )
    
    def update_dungeon_state(self, new_state: DungeonState):
        """ダンジョン状態を更新"""
        self.dungeon_state = new_state
        self._calculate_map_scale()
    
    def toggle_visibility(self):
        """表示の切り替え"""
        self.is_visible = not self.is_visible
    
    def render(self):
        """小地図を描画"""
        if not self.is_visible:
            return
        
        # プレイヤー移動に追従するため、毎フレームマップスケールを再計算
        self._calculate_map_scale()
        
        # 背景をクリア
        self.map_surface.fill(MAP_BACKGROUND_COLOR)
        
        # 境界線を描画
        pygame.draw.rect(self.map_surface, MAP_BORDER_COLOR, self.map_surface.get_rect(), 2)
        
        # 探索済みセルを描画
        self.draw_explored_cells()
        
        # 特殊オブジェクトを描画
        self.draw_special_objects()
        
        # プレイヤーマーカーを描画
        self.draw_player_marker()
        
        # メインスクリーンに描画
        self.screen.blit(self.map_surface, self.map_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理"""
        # マップ表示切り替え（Mキー）
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                self.toggle_visibility()
                return True
        
        return False