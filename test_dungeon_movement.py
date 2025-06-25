#!/usr/bin/env python3
"""ダンジョン移動システムのテスト"""

import pytest
import pygame
import math
from unittest.mock import Mock, patch, MagicMock
from src.rendering.dungeon_renderer_pygame import DungeonRendererPygame
from src.dungeon.dungeon_manager import DungeonManager, PlayerPosition, DungeonState, Direction
from src.dungeon.dungeon_generator import DungeonLevel, DungeonCell, CellType


class TestDungeonMovement:
    """ダンジョン移動システムのテスト"""
    
    def setup_method(self):
        """テスト前の初期化"""
        pygame.init()
        
        # レンダラーとマネージャーの初期化
        self.renderer = DungeonRendererPygame()
        self.dungeon_manager = DungeonManager()
        
        # ダンジョン作成
        self.dungeon_state = self.dungeon_manager.create_dungeon("test_dungeon", "test_seed")
        self.dungeon_manager.current_dungeon = self.dungeon_state
        
        # レンダラーにマネージャーを設定
        self.renderer.set_dungeon_manager(self.dungeon_manager)
    
    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if pygame.get_init():
            pygame.quit()
    
    def test_camera_angle_mapping(self):
        """カメラ角度マッピングのテスト"""
        test_cases = [
            (Direction.NORTH, -math.pi/2, "北を向いているとき、カメラは-90度（上向き）"),
            (Direction.EAST, 0, "東を向いているとき、カメラは0度（右向き）"),
            (Direction.SOUTH, math.pi/2, "南を向いているとき、カメラは90度（下向き）"),
            (Direction.WEST, math.pi, "西を向いているとき、カメラは180度（左向き）")
        ]
        
        for direction, expected_angle, description in test_cases:
            # プレイヤーの向きを設定
            player_pos = PlayerPosition(x=5, y=5, level=1, facing=direction)
            
            # カメラ位置を更新
            self.renderer.update_camera_position(player_pos)
            
            # 角度を確認
            assert abs(self.renderer.camera_angle - expected_angle) < 0.01, \
                f"{description}: 期待値={math.degrees(expected_angle)}度, 実際={math.degrees(self.renderer.camera_angle)}度"
    
    def test_ray_casting_direction(self):
        """レイキャスティングの方向テスト"""
        # モックレベルを作成（10x10、壁なし）
        mock_level = Mock(spec=DungeonLevel)
        mock_level.width = 10
        mock_level.height = 10
        
        # すべてのセルを通路にする
        def get_cell(x, y):
            if 0 <= x < 10 and 0 <= y < 10:
                cell = Mock(spec=DungeonCell)
                cell.cell_type = CellType.FLOOR
                cell.walls = {
                    Direction.NORTH: False,
                    Direction.SOUTH: False,
                    Direction.EAST: False,
                    Direction.WEST: False
                }
                return cell
            return None
        
        mock_level.get_cell = get_cell
        
        # 各方向でレイキャストをテスト
        test_cases = [
            (Direction.NORTH, 5, 5, "北向きレイ"),
            (Direction.EAST, 5, 5, "東向きレイ"),
            (Direction.SOUTH, 5, 5, "南向きレイ"),
            (Direction.WEST, 5, 5, "西向きレイ")
        ]
        
        for direction, x, y, description in test_cases:
            player_pos = PlayerPosition(x=x, y=y, level=1, facing=direction)
            self.renderer.update_camera_position(player_pos)
            
            # カメラの正面方向にレイをキャスト
            distance, hit_wall = self.renderer._cast_ray(mock_level, player_pos, self.renderer.camera_angle)
            
            # 壁がないので、最大距離まで到達するはず
            assert distance >= self.renderer.view_distance * 0.9, \
                f"{description}: レイが予期せず短い距離で停止しました"
    
    def test_movement_and_view_consistency(self):
        """移動方向と視界の一貫性テスト"""
        # 北を向いてWキーで前進
        self.dungeon_manager.turn_player(Direction.NORTH)
        player_pos = self.dungeon_manager.current_dungeon.player_position
        initial_y = player_pos.y
        
        # 前進（北へ移動）
        success, message = self.dungeon_manager.move_player(Direction.NORTH)
        
        if success:
            # Y座標が減少するはず（北は-Y方向）
            assert player_pos.y < initial_y, "北向きで前進したのにY座標が減少していない"
            
            # カメラ更新
            self.renderer.update_camera_position(player_pos)
            
            # カメラ角度が北向き（-90度）であることを確認
            assert abs(self.renderer.camera_angle - (-math.pi/2)) < 0.01, \
                "北を向いているのにカメラ角度が正しくない"
    
    def test_strafe_movement(self):
        """横移動（ストレイフ）のテスト"""
        # 北を向いている状態で開始
        self.dungeon_manager.turn_player(Direction.NORTH)
        player_pos = self.dungeon_manager.current_dungeon.player_position
        initial_x = player_pos.x
        initial_y = player_pos.y
        
        # 左移動（Aキー）のシミュレーション
        self.renderer._move_left()
        
        # 西（左）に移動したはず
        assert player_pos.x < initial_x, "左移動でX座標が減少していない"
        assert player_pos.y == initial_y, "左移動でY座標が変化してしまった"
        
        # 向きは北のままのはず
        assert player_pos.facing == Direction.NORTH, "左移動で向きが変わってしまった"
    
    def test_wall_collision_in_view(self):
        """視界内の壁の検出テスト"""
        # モックレベルを作成（壁あり）
        mock_level = Mock(spec=DungeonLevel)
        mock_level.width = 10
        mock_level.height = 10
        
        def get_cell(x, y):
            if x == 5 and y == 3:
                # プレイヤーの北に壁を配置
                cell = Mock(spec=DungeonCell)
                cell.cell_type = CellType.WALL
                return cell
            elif 0 <= x < 10 and 0 <= y < 10:
                cell = Mock(spec=DungeonCell)
                cell.cell_type = CellType.FLOOR
                cell.walls = {
                    Direction.NORTH: False,
                    Direction.SOUTH: False,
                    Direction.EAST: False,
                    Direction.WEST: False
                }
                return cell
            return None
        
        mock_level.get_cell = get_cell
        
        # プレイヤーは(5,5)で北を向く
        player_pos = PlayerPosition(x=5, y=5, level=1, facing=Direction.NORTH)
        self.renderer.update_camera_position(player_pos)
        
        # 北方向にレイキャスト
        distance, hit_wall = self.renderer._cast_ray(mock_level, player_pos, self.renderer.camera_angle)
        
        # 壁に当たるはず（距離は約2）
        assert hit_wall, "北の壁が検出されなかった"
        assert distance < 3, f"壁までの距離が予想より遠い: {distance}"
    
    def test_coordinate_system_consistency(self):
        """座標系の一貫性テスト"""
        # ダンジョンの座標系:
        # - X軸: 東が正、西が負
        # - Y軸: 南が正、北が負（画面座標系と同じ）
        
        # 数学的な角度:
        # - 0度: 東（+X）
        # - 90度: 南（+Y）
        # - 180度: 西（-X）
        # - 270度: 北（-Y）
        
        # 各方向での移動デルタ
        deltas = self.dungeon_manager._direction_to_delta
        
        assert deltas(Direction.NORTH) == (0, -1), "北の移動デルタが正しくない"
        assert deltas(Direction.SOUTH) == (0, 1), "南の移動デルタが正しくない"
        assert deltas(Direction.EAST) == (1, 0), "東の移動デルタが正しくない"
        assert deltas(Direction.WEST) == (-1, 0), "西の移動デルタが正しくない"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])