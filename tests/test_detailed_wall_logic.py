#!/usr/bin/env python3
"""壁衝突ロジックの詳細デバッグテスト"""

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


class TestDetailedWallLogic:
    
    def test_wall_hit_analysis(self):
        """壁ヒット判定の詳細分析"""
        print("=== 壁ヒット判定の詳細分析 ===")
        
        # テストセットアップ
        dungeon_manager = DungeonManager()
        dungeon_state = dungeon_manager.create_dungeon("wall_analysis", "wall_analysis_seed")
        
        test_char = Character("壁分析キャラ", "human", "fighter")
        test_party = Party("壁分析パーティ")
        test_party.add_character(test_char)
        
        dungeon_manager.enter_dungeon("wall_analysis", test_party)
        
        player_pos = dungeon_manager.current_dungeon.player_position
        current_level = dungeon_manager.current_dungeon.levels[1]
        current_cell = current_level.get_cell(player_pos.x, player_pos.y)
        
        print(f"プレイヤー位置: ({player_pos.x}, {player_pos.y})")
        print(f"セルタイプ: {current_cell.cell_type.value}")
        print(f"壁情報: {[(dir.value, has_wall) for dir, has_wall in current_cell.walls.items()]}")
        
        renderer = DungeonRendererPygame()
        
        # 背面方向の詳細テスト（南方向：プレイヤーから見て後ろ）
        camera_angle = renderer._get_direction_angle(player_pos.facing)
        south_angle = camera_angle + math.pi  # 180度回転（背面）
        
        print(f"\nカメラ角度: {math.degrees(camera_angle):.1f}°")
        print(f"南向き角度: {math.degrees(south_angle):.1f}°")
        
        # 南方向のレイキャスティングを手動実行
        dx = math.cos(south_angle)
        dy = math.sin(south_angle)
        
        print(f"南向きレイ方向: dx={dx:.3f}, dy={dy:.3f}")
        
        ray_x, ray_y = float(player_pos.x), float(player_pos.y)
        
        # ステップごとの詳細
        for step in range(1, 6):
            ray_x += dx * 0.1  # RAYCAST_STEP_SIZE
            ray_y += dy * 0.1
            
            grid_x, grid_y = int(ray_x), int(ray_y)
            local_x = ray_x - grid_x
            local_y = ray_y - grid_y
            
            # セルを取得
            cell = current_level.get_cell(grid_x, grid_y)
            
            print(f"\nステップ{step}:")
            print(f"  レイ座標: ({ray_x:.3f}, {ray_y:.3f})")
            print(f"  グリッド座標: ({grid_x}, {grid_y})")
            print(f"  ローカル座標: ({local_x:.3f}, {local_y:.3f})")
            
            if cell:
                print(f"  セルタイプ: {cell.cell_type.value}")
                print(f"  セル壁情報: {[(dir.value, has_wall) for dir, has_wall in cell.walls.items()]}")
                
                # 各方向の境界チェック
                threshold = 0.05
                west_hit = local_x <= threshold and cell.walls.get(Direction.WEST, False)
                east_hit = local_x >= (1.0 - threshold) and cell.walls.get(Direction.EAST, False)
                north_hit = local_y <= threshold and cell.walls.get(Direction.NORTH, False)
                south_hit = local_y >= (1.0 - threshold) and cell.walls.get(Direction.SOUTH, False)
                
                print(f"  境界チェック結果:")
                print(f"    西境界ヒット: {west_hit} (local_x={local_x:.3f} <= {threshold}, 壁={cell.walls.get(Direction.WEST, False)})")
                print(f"    東境界ヒット: {east_hit} (local_x={local_x:.3f} >= {1.0-threshold}, 壁={cell.walls.get(Direction.EAST, False)})")
                print(f"    北境界ヒット: {north_hit} (local_y={local_y:.3f} <= {threshold}, 壁={cell.walls.get(Direction.NORTH, False)})")
                print(f"    南境界ヒット: {south_hit} (local_y={local_y:.3f} >= {1.0-threshold}, 壁={cell.walls.get(Direction.SOUTH, False)})")
                
                wall_collision = renderer._check_wall_collision(cell, local_x, local_y)
                is_wall_hit = renderer._is_wall_hit(cell, local_x, local_y)
                
                print(f"  壁衝突: {wall_collision}")
                print(f"  壁ヒット: {is_wall_hit}")
                
                if is_wall_hit:
                    print(f"  >>> 壁ヒット発生 <<<")
                    break
            else:
                print(f"  セル不在")
                break
    
    def test_specific_case_analysis(self):
        """特定ケースの分析"""
        print("\n=== 特定ケースの分析 ===")
        
        renderer = DungeonRendererPygame()
        
        # 問題のケースを再現
        from src.dungeon.dungeon_generator import DungeonCell
        
        # 床セルを作成（実際のテストケースと同じ壁構成）
        test_cell = DungeonCell(1, 6, CellType.FLOOR)
        test_cell.walls = {
            Direction.NORTH: True,
            Direction.SOUTH: False,
            Direction.EAST: False,
            Direction.WEST: True
        }
        
        print("テストセル壁情報:")
        print(f"  北: {test_cell.walls[Direction.NORTH]}")
        print(f"  南: {test_cell.walls[Direction.SOUTH]}")
        print(f"  東: {test_cell.walls[Direction.EAST]}")  
        print(f"  西: {test_cell.walls[Direction.WEST]}")
        
        # 問題の座標での判定テスト
        test_coordinates = [
            (0.0, 0.1, "レイが南に進んで同じセルの南部分"),
            (0.0, 0.5, "レイが南に進んでセル中央"),
            (0.0, 0.9, "レイが南に進んでセル南境界"),
            (0.0, 1.0, "レイが南に進んでセル南端"),
        ]
        
        print("\n座標別壁衝突テスト:")
        for local_x, local_y, description in test_coordinates:
            collision = renderer._check_wall_collision(test_cell, local_x, local_y)
            wall_hit = renderer._is_wall_hit(test_cell, local_x, local_y)
            print(f"{description}: 衝突={collision}, 壁ヒット={wall_hit}")


if __name__ == "__main__":
    print("壁衝突ロジックの詳細デバッグテスト")
    print("=" * 60)
    
    test_instance = TestDetailedWallLogic()
    
    try:
        # 壁ヒット判定の詳細分析
        test_instance.test_wall_hit_analysis()
        
        # 特定ケースの分析  
        test_instance.test_specific_case_analysis()
        
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()