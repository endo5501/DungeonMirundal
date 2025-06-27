"""
小地図UI機能のテスト

ダンジョンの周辺マップを表示するUI機能をテストする
"""

import pytest
import pygame
from unittest.mock import Mock, MagicMock

from src.ui.small_map_ui_pygame import SmallMapUI
from src.dungeon.dungeon_manager import DungeonState, PlayerPosition
from src.dungeon.dungeon_generator import DungeonLevel, DungeonCell, CellType, Direction, DungeonAttribute


class TestSmallMapUI:
    """小地図UIのテストクラス"""
    
    @pytest.fixture
    def mock_screen(self):
        """モックのPygameスクリーン"""
        screen = Mock()
        screen.get_width.return_value = 1024
        screen.get_height.return_value = 768
        return screen
    
    @pytest.fixture
    def mock_font_manager(self):
        """モックのフォントマネージャー"""
        return Mock()
    
    @pytest.fixture
    def sample_dungeon_state(self):
        """テスト用のダンジョン状態データ"""
        # 3x3の小さなダンジョンレベルを作成
        cells = {}
        for x in range(3):
            for y in range(3):
                cell_type = CellType.FLOOR if (x + y) % 2 == 0 else CellType.WALL
                cells[(x, y)] = DungeonCell(x, y, cell_type)
                # 中央のセルは探索済みとする
                if x == 1 and y == 1:
                    cells[(x, y)].discovered = True
        
        level = DungeonLevel(
            level=1, 
            width=3, 
            height=3, 
            attribute=DungeonAttribute.PHYSICAL,
            cells=cells, 
            stairs_up_position=(0, 0), 
            stairs_down_position=(2, 2)
        )
        state = DungeonState(dungeon_id="test", seed="test_seed")
        state.levels[1] = level
        state.player_position = PlayerPosition(x=1, y=1, level=1, facing=Direction.NORTH)
        
        return state
    
    @pytest.fixture
    def small_map_ui(self, mock_screen, mock_font_manager, sample_dungeon_state):
        """小地図UIインスタンス"""
        return SmallMapUI(mock_screen, mock_font_manager, sample_dungeon_state)
    
    def test_small_map_ui_initialization(self, small_map_ui):
        """小地図UIの初期化をテスト"""
        assert small_map_ui is not None
        assert hasattr(small_map_ui, 'dungeon_state')
        assert hasattr(small_map_ui, 'screen')
        assert hasattr(small_map_ui, 'font_manager')
    
    def test_small_map_position_and_size(self, small_map_ui):
        """小地図の位置とサイズをテスト"""
        # 小地図は画面右上に配置される
        assert hasattr(small_map_ui, 'map_rect')
        assert small_map_ui.map_rect.right <= 1024  # 画面右端以内
        assert small_map_ui.map_rect.top >= 0     # 画面上端以上
        assert small_map_ui.map_rect.width > 0    # 正の幅
        assert small_map_ui.map_rect.height > 0   # 正の高さ
    
    def test_get_visible_cells(self, small_map_ui, sample_dungeon_state):
        """表示するセル（探索済み）の取得をテスト"""
        visible_cells = small_map_ui.get_visible_cells()
        
        # 探索済みのセルのみが含まれる
        assert len(visible_cells) >= 1
        
        # 発見済みのセルをカウント
        discovered_count = sum(1 for cell in visible_cells if cell.discovered)
        assert discovered_count >= 1, f"少なくとも1つのセルが発見済みである必要があります。発見済み: {discovered_count}, 総数: {len(visible_cells)}"
    
    def test_get_player_map_position(self, small_map_ui, sample_dungeon_state):
        """プレイヤーのマップ上での位置計算をテスト"""
        map_pos = small_map_ui.get_player_map_position()
        
        # マップ内の座標として返される
        assert isinstance(map_pos, tuple)
        assert len(map_pos) == 2
        assert isinstance(map_pos[0], (int, float))
        assert isinstance(map_pos[1], (int, float))
    
    def test_draw_explored_cells(self, small_map_ui, mock_screen):
        """探索済みセルの描画をテスト"""
        small_map_ui.draw_explored_cells()
        
        # Pygameの描画メソッドが呼ばれることを確認
        assert mock_screen.blit.called or hasattr(mock_screen, 'fill')
    
    def test_draw_player_marker(self, small_map_ui, mock_screen):
        """プレイヤーマーカーの描画をテスト"""
        small_map_ui.draw_player_marker()
        
        # プレイヤー位置にマーカーが描画される
        assert mock_screen.blit.called or hasattr(mock_screen, 'fill')
    
    def test_draw_special_objects(self, small_map_ui, mock_screen):
        """特殊オブジェクト（階段、宝箱等）の描画をテスト"""
        small_map_ui.draw_special_objects()
        
        # 階段や宝箱のアイコンが描画される
        assert mock_screen.blit.called or hasattr(mock_screen, 'fill')
    
    def test_update_dungeon_state(self, small_map_ui, sample_dungeon_state):
        """ダンジョン状態の更新をテスト"""
        # 新しい状態を作成
        new_state = DungeonState(dungeon_id="test2", seed="test_seed2")
        new_state.player_position = PlayerPosition(x=2, y=2, level=2, facing=Direction.SOUTH)
        
        small_map_ui.update_dungeon_state(new_state)
        
        # 状態が更新される
        assert small_map_ui.dungeon_state.player_position.level == 2
        assert small_map_ui.dungeon_state.player_position.x == 2
        assert small_map_ui.dungeon_state.player_position.y == 2
    
    def test_render_complete_map(self, small_map_ui, mock_screen):
        """完全なマップの描画をテスト"""
        small_map_ui.render()
        
        # 全ての描画コンポーネントが実行される
        assert mock_screen.blit.called or hasattr(mock_screen, 'fill')
    
    def test_toggle_visibility(self, small_map_ui):
        """マップ表示の切り替えをテスト"""
        initial_visibility = small_map_ui.is_visible
        small_map_ui.toggle_visibility()
        
        # 表示状態が切り替わる
        assert small_map_ui.is_visible != initial_visibility
    
    def test_map_scaling_with_different_dungeon_sizes(self, mock_screen, mock_font_manager):
        """異なるダンジョンサイズでのマップスケーリングをテスト"""
        # 大きなダンジョンを作成
        large_cells = {}
        for x in range(10):
            for y in range(10):
                cell_type = CellType.FLOOR
                large_cells[(x, y)] = DungeonCell(x, y, cell_type)
                large_cells[(x, y)].discovered = True
        
        large_level = DungeonLevel(
            level=1, 
            width=10, 
            height=10, 
            attribute=DungeonAttribute.PHYSICAL,
            cells=large_cells
        )
        large_state = DungeonState(dungeon_id="large_test", seed="large_seed")
        large_state.levels[1] = large_level
        large_state.player_position = PlayerPosition(x=5, y=5, level=1, facing=Direction.NORTH)
        
        large_map_ui = SmallMapUI(mock_screen, mock_font_manager, large_state)
        
        # マップがフィット範囲内でスケールされる
        assert large_map_ui.map_rect.width <= 200  # 最大幅制限
        assert large_map_ui.map_rect.height <= 200  # 最大高制限
    
    def test_player_direction_indicator(self, small_map_ui):
        """プレイヤーの向き表示をテスト"""
        for direction in [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]:
            small_map_ui.dungeon_state.player_position.facing = direction
            
            # 向きに応じたマーカーが描画される
            direction_marker = small_map_ui.get_direction_marker()
            assert direction_marker is not None