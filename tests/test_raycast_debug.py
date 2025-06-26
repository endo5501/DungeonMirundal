#!/usr/bin/env python3
"""レイキャスティングの詳細デバッグテスト"""

import pytest
import sys
import os
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dungeon.dungeon_manager import DungeonManager, PlayerPosition
from src.dungeon.dungeon_generator import DungeonGenerator, CellType, Direction
from src.rendering.dungeon_renderer_pygame import DungeonRendererPygame
from src.character.party import Party
from src.character.character import Character


class TestRaycastDebug:
    
    def test_initial_raycast_state(self):
        """初期レイキャスティング状態を調査"""
        print("=== 初期レイキャスティング状態 ===")
        
        # テストセットアップ
        dungeon_manager = DungeonManager()
        dungeon_state = dungeon_manager.create_dungeon("raycast_test", "raycast_seed")
        
        test_char = Character("レイキャストテストキャラ", "human", "fighter")
        test_party = Party("レイキャストテストパーティ")
        test_party.add_character(test_char)
        
        dungeon_manager.enter_dungeon("raycast_test", test_party)
        
        player_pos = dungeon_manager.current_dungeon.player_position
        current_level = dungeon_manager.current_dungeon.levels[1]
        
        print(f"プレイヤー位置: ({player_pos.x}, {player_pos.y}), 向き: {player_pos.facing.value}")
        
        # 現在位置のセル詳細
        current_cell = current_level.get_cell(player_pos.x, player_pos.y)
        print(f"現在のセル: タイプ={current_cell.cell_type.value}")
        print(f"壁情報: {[(dir.value, has_wall) for dir, has_wall in current_cell.walls.items()]}")
        
        # レンダラーを初期化
        renderer = DungeonRendererPygame()
        renderer.update_camera_position(player_pos)
        
        print(f"カメラ位置: ({renderer.camera_x}, {renderer.camera_y})")
        print(f"カメラ角度: {math.degrees(renderer.camera_angle):.1f}°")
        
        # 複数方向にレイキャストを実行
        test_angles = [
            renderer.camera_angle,  # 正面
            renderer.camera_angle - math.pi/4,  # 左45度
            renderer.camera_angle + math.pi/4,  # 右45度
            renderer.camera_angle + math.pi,  # 背面
        ]
        
        angle_names = ["正面", "左45度", "右45度", "背面"]
        
        print("\nレイキャスティング結果:")
        for i, angle in enumerate(test_angles):
            distance, hit_wall = renderer._cast_ray(current_level, player_pos, angle)
            print(f"{angle_names[i]}: 距離={distance:.3f}, 壁ヒット={hit_wall}")
            
            # レイの詳細を追跡
            self._trace_ray_details(renderer, current_level, player_pos, angle, angle_names[i])
    
    def _trace_ray_details(self, renderer, level, player_pos, angle, angle_name):
        """レイの詳細を追跡"""
        print(f"\n--- {angle_name}のレイ詳細 ---")
        
        dx = math.cos(angle)
        dy = math.sin(angle)
        
        print(f"レイ方向ベクトル: dx={dx:.3f}, dy={dy:.3f}")
        
        ray_x, ray_y = renderer._get_ray_start_position(player_pos)
        distance = 0
        step_count = 0
        max_steps = 10  # 最初の10ステップを追跡
        
        print(f"開始位置: ({ray_x:.3f}, {ray_y:.3f})")
        
        while distance < renderer.view_distance and step_count < max_steps:
            ray_x, ray_y, distance = renderer._advance_ray(ray_x, ray_y, dx, dy, distance)
            step_count += 1
            
            # 範囲外チェック
            if renderer._is_ray_out_of_bounds(ray_x, ray_y, level):
                print(f"ステップ{step_count}: 範囲外 ({ray_x:.3f}, {ray_y:.3f})")
                break
            
            grid_x, grid_y = int(ray_x), int(ray_y)
            cell = level.get_cell(grid_x, grid_y)
            
            if cell:
                is_wall_hit = renderer._is_wall_hit(cell, ray_x - grid_x, ray_y - grid_y)
                print(f"ステップ{step_count}: グリッド({grid_x}, {grid_y}), 座標({ray_x:.3f}, {ray_y:.3f}), セル={cell.cell_type.value}, 壁ヒット={is_wall_hit}")
                
                if is_wall_hit:
                    break
            else:
                print(f"ステップ{step_count}: セル不在 ({ray_x:.3f}, {ray_y:.3f})")
                break
    
    def test_surrounding_wall_check(self):
        """周囲の壁チェック"""
        print("\n=== 周囲の壁チェック ===")
        
        # テストセットアップ
        dungeon_manager = DungeonManager()
        dungeon_state = dungeon_manager.create_dungeon("wall_test", "wall_seed")
        
        test_char = Character("壁テストキャラ", "human", "fighter")
        test_party = Party("壁テストパーティ")
        test_party.add_character(test_char)
        
        dungeon_manager.enter_dungeon("wall_test", test_party)
        
        player_pos = dungeon_manager.current_dungeon.player_position
        current_level = dungeon_manager.current_dungeon.levels[1]
        
        print(f"プレイヤー位置: ({player_pos.x}, {player_pos.y})")
        
        # 周囲8方向のセルをチェック
        directions = [
            (-1, -1, "左上"), (-1, 0, "左"), (-1, 1, "左下"),
            (0, -1, "上"), (0, 0, "中央"), (0, 1, "下"),
            (1, -1, "右上"), (1, 0, "右"), (1, 1, "右下")
        ]
        
        print("周囲のセル状況:")
        for dx, dy, name in directions:
            x = player_pos.x + dx
            y = player_pos.y + dy
            
            if 0 <= x < current_level.width and 0 <= y < current_level.height:
                cell = current_level.get_cell(x, y)
                if cell:
                    walkable = current_level.is_walkable(x, y)
                    print(f"{name} ({x}, {y}): {cell.cell_type.value}, 歩行可能={walkable}")
                else:
                    print(f"{name} ({x}, {y}): セル不在")
            else:
                print(f"{name} ({x}, {y}): 範囲外")
    
    def test_wall_collision_logic(self):
        """壁衝突ロジックのテスト"""
        print("\n=== 壁衝突ロジック ===")
        
        # テストセットアップ
        dungeon_manager = DungeonManager()
        dungeon_state = dungeon_manager.create_dungeon("collision_test", "collision_seed")
        
        test_char = Character("衝突テストキャラ", "human", "fighter")
        test_party = Party("衝突テストパーティ")
        test_party.add_character(test_char)
        
        dungeon_manager.enter_dungeon("collision_test", test_party)
        
        player_pos = dungeon_manager.current_dungeon.player_position
        current_level = dungeon_manager.current_dungeon.levels[1]
        current_cell = current_level.get_cell(player_pos.x, player_pos.y)
        
        renderer = DungeonRendererPygame()
        
        print(f"現在位置: ({player_pos.x}, {player_pos.y})")
        print(f"セルタイプ: {current_cell.cell_type.value}")
        
        # セル境界での壁衝突をテスト
        test_positions = [
            (0.05, 0.5, "西境界"),
            (0.95, 0.5, "東境界"),
            (0.5, 0.05, "北境界"),
            (0.5, 0.95, "南境界"),
            (0.5, 0.5, "中央")
        ]
        
        print("壁衝突テスト:")
        for local_x, local_y, name in test_positions:
            is_collision = renderer._check_wall_collision(current_cell, local_x, local_y)
            print(f"{name} ({local_x}, {local_y}): 衝突={is_collision}")
    
    def test_render_method_availability(self):
        """レンダリングメソッドの可用性チェック"""
        print("\n=== レンダリングメソッドの可用性 ===")
        
        renderer = DungeonRendererPygame()
        
        # 必要なメソッドが存在するかチェック
        required_methods = [
            '_render_floor_and_ceiling',
            '_render_walls_raycast',
            '_render_props_3d',
            '_cast_ray',
            '_is_wall_hit',
            '_check_wall_collision'
        ]
        
        print("必要なメソッドのチェック:")
        for method_name in required_methods:
            has_method = hasattr(renderer, method_name)
            print(f"{method_name}: {'あり' if has_method else '不在'}")


if __name__ == "__main__":
    print("レイキャスティングの詳細デバッグテスト")
    print("=" * 50)
    
    test_instance = TestRaycastDebug()
    
    try:
        # 初期レイキャスティング状態
        test_instance.test_initial_raycast_state()
        
        # 周囲の壁チェック
        test_instance.test_surrounding_wall_check()
        
        # 壁衝突ロジック
        test_instance.test_wall_collision_logic()
        
        # レンダリングメソッドの可用性
        test_instance.test_render_method_availability()
        
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()