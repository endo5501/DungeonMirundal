"""ダンジョン疑似3D描画システム（Pygame）"""

from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import math
import pygame

from src.dungeon.dungeon_manager import DungeonManager, DungeonState, PlayerPosition
from src.dungeon.dungeon_generator import DungeonLevel, DungeonCell, CellType, Direction, DungeonAttribute
from src.character.party import Party
from src.utils.logger import logger
from src.core.config_manager import config_manager


class ViewMode(Enum):
    """表示モード"""
    FIRST_PERSON = "first_person"    # 1人称視点
    THIRD_PERSON = "third_person"    # 3人称視点
    MAP_VIEW = "map_view"            # マップビュー


class RenderQuality(Enum):
    """レンダリング品質"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"


class DungeonRenderer:
    """ダンジョン疑似3D描画システム（Pygame版）"""
    
    def __init__(self, screen: pygame.Surface):
        """初期化"""
        logger.info("DungeonRenderer（Pygame版）初期化開始")
        
        # 画面参照
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # 基本設定
        self.enabled = True
        self.view_mode = ViewMode.FIRST_PERSON
        self.render_quality = RenderQuality.MEDIUM
        
        # ダンジョン管理
        self.dungeon_manager: Optional[DungeonManager] = None
        self.current_party: Optional[Party] = None
        
        # カメラ設定
        self.camera_height = 1.7  # プレイヤーの目線の高さ
        self.fov = 70             # 視野角
        self.view_distance = 10   # 描画距離
        
        # 疑似3D描画用パラメータ
        self.horizon_y = self.height // 2  # 水平線のY座標
        self.wall_height = 200             # 基準壁の高さ
        
        # 色定義
        self.colors = {
            'wall': (100, 100, 100),
            'floor': (50, 50, 50),
            'ceiling': (30, 30, 30),
            'door': (139, 69, 19),
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255)
        }
        
        # フォント初期化
        try:
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
        except:
            self.font = None
            self.small_font = None
        
        # UI要素
        self.ui_manager = None
        self.ui_elements: Dict[str, Any] = {}
        
        logger.info("DungeonRenderer（Pygame版）初期化完了")
    
    def set_dungeon_manager(self, dungeon_manager: DungeonManager):
        """ダンジョンマネージャーを設定"""
        self.dungeon_manager = dungeon_manager
        logger.info("ダンジョンマネージャーを設定しました")
    
    def set_party(self, party: Party):
        """パーティを設定"""
        self.current_party = party
        logger.info(f"パーティを設定しました: {party.name}")
    
    def render_dungeon_view(self, player_pos: PlayerPosition, dungeon_level: DungeonLevel):
        """ダンジョンビューを描画"""
        if not self.enabled:
            return
        
        # 背景をクリア
        self.screen.fill(self.colors['black'])
        
        # 疑似3D描画
        self._render_pseudo_3d(player_pos, dungeon_level)
        
        # UI要素を描画
        self._render_ui()
    
    def _render_pseudo_3d(self, player_pos: PlayerPosition, dungeon_level: DungeonLevel):
        """疑似3D描画のメイン処理"""
        # プレイヤーの位置と向きを取得
        px, py = player_pos.x, player_pos.y
        direction = player_pos.direction
        
        # 描画距離分だけ前方を確認して描画
        for distance in range(1, self.view_distance + 1):
            self._render_depth_slice(px, py, direction, distance, dungeon_level)
    
    def _render_depth_slice(self, px: int, py: int, direction: Direction, distance: int, dungeon_level: DungeonLevel):
        """指定距離のスライスを描画"""
        # 遠近法による壁の高さと幅を計算
        perspective_factor = 1.0 / distance
        wall_height = int(self.wall_height * perspective_factor)
        
        # 距離に応じた描画幅
        render_width = max(1, int(self.width * perspective_factor * 0.5))
        
        # 前方、左、右のセルをチェック
        positions = self._get_view_positions(px, py, direction, distance)
        
        for i, (check_x, check_y) in enumerate(positions):
            if dungeon_level.is_valid_position(check_x, check_y):
                cell = dungeon_level.get_cell(check_x, check_y)
                
                # セルの種類に応じて描画
                self._render_cell_at_distance(cell, i, distance, wall_height, render_width)
    
    def _get_view_positions(self, px: int, py: int, direction: Direction, distance: int) -> List[Tuple[int, int]]:
        """視界内の位置を取得"""
        positions = []
        
        # 方向ベクトルを計算
        dx, dy = self._get_direction_vector(direction)
        
        # 前方の位置
        front_x = px + dx * distance
        front_y = py + dy * distance
        
        # 左右の位置も計算（簡単な実装）
        positions.append((front_x, front_y))
        
        return positions
    
    def _get_direction_vector(self, direction: Direction) -> Tuple[int, int]:
        """方向からベクトルを計算"""
        vectors = {
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0)
        }
        return vectors.get(direction, (0, -1))
    
    def _render_cell_at_distance(self, cell: DungeonCell, position_index: int, distance: int, wall_height: int, render_width: int):
        """指定距離のセルを描画"""
        if not cell:
            return
        
        # 画面上の位置を計算
        center_x = self.width // 2
        top_y = self.horizon_y - wall_height // 2
        bottom_y = self.horizon_y + wall_height // 2
        
        # セルの種類に応じた色を選択
        if cell.cell_type == CellType.WALL:
            color = self.colors['wall']
        elif cell.cell_type == CellType.DOOR:
            color = self.colors['door']
        elif cell.cell_type == CellType.FLOOR:
            # 床は描画しない（背景色のまま）
            return
        else:
            color = self.colors['wall']
        
        # 距離に応じて暗くする
        darken_factor = max(0.2, 1.0 - (distance - 1) * 0.15)
        color = tuple(int(c * darken_factor) for c in color)
        
        # 壁を描画
        rect = pygame.Rect(center_x - render_width // 2, top_y, render_width, wall_height)
        pygame.draw.rect(self.screen, color, rect)
        
        # エッジを描画（立体感を出すため）
        if render_width > 2:
            pygame.draw.rect(self.screen, tuple(min(255, int(c * 1.2)) for c in color), rect, 1)
    
    def _render_ui(self):
        """UI要素を描画"""
        if not self.font:
            return
        
        # パーティ情報表示
        if self.current_party:
            party_text = f"パーティ: {self.current_party.name}"
            text_surface = self.font.render(party_text, True, self.colors['white'])
            self.screen.blit(text_surface, (10, 10))
            
            # HP表示
            y_offset = 35
            for i, character in enumerate(self.current_party.get_living_characters()):
                hp_text = f"{character.name}: HP {character.derived_stats.current_hp}/{character.derived_stats.max_hp}"
                hp_surface = self.small_font.render(hp_text, True, self.colors['white'])
                self.screen.blit(hp_surface, (10, y_offset + i * 20))
        
        # コンパス表示
        if self.dungeon_manager and self.dungeon_manager.current_dungeon:
            pos = self.dungeon_manager.current_dungeon.player_position
            direction_text = f"向き: {pos.direction.value}"
            dir_surface = self.font.render(direction_text, True, self.colors['white'])
            self.screen.blit(dir_surface, (self.width - 150, 10))
            
            # 座標表示
            coord_text = f"座標: ({pos.x}, {pos.y})"
            coord_surface = self.font.render(coord_text, True, self.colors['white'])
            self.screen.blit(coord_surface, (self.width - 150, 35))
    
    def _move_forward(self):
        """前進"""
        if self.dungeon_manager:
            self.dungeon_manager.move_player_forward()
    
    def _move_backward(self):
        """後退"""
        if self.dungeon_manager:
            self.dungeon_manager.move_player_backward()
    
    def _turn_left(self):
        """左回転"""
        if self.dungeon_manager:
            self.dungeon_manager.turn_player_left()
    
    def _turn_right(self):
        """右回転"""
        if self.dungeon_manager:
            self.dungeon_manager.turn_player_right()
    
    def _move_left(self):
        """左移動"""
        if self.dungeon_manager:
            # 左に90度回転してから前進、その後元の向きに戻る
            original_direction = self.dungeon_manager.current_dungeon.player_position.direction
            self.dungeon_manager.turn_player_left()
            self.dungeon_manager.move_player_forward()
            # 元の向きに戻す（右に3回回転）
            for _ in range(3):
                self.dungeon_manager.turn_player_right()
    
    def _move_right(self):
        """右移動"""
        if self.dungeon_manager:
            # 右に90度回転してから前進、その後元の向きに戻る
            original_direction = self.dungeon_manager.current_dungeon.player_position.direction
            self.dungeon_manager.turn_player_right()
            self.dungeon_manager.move_player_forward()
            # 元の向きに戻す（左に3回回転）
            for _ in range(3):
                self.dungeon_manager.turn_player_left()
    
    def update_ui(self):
        """UI更新"""
        # UI更新処理（必要に応じて実装）
        pass
    
    def cleanup(self):
        """クリーンアップ"""
        logger.info("DungeonRenderer（Pygame版）をクリーンアップしました")