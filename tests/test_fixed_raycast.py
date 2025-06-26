#!/usr/bin/env python3
"""修正後のレイキャスティングテスト"""

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


class TestFixedRaycast:
    
    def test_centered_ray_start(self):
        """中央配置でのレイ開始テスト"""
        print("=== 中央配置でのレイ開始テスト ===")
        
        # テストセットアップ
        dungeon_manager = DungeonManager()
        dungeon_state = dungeon_manager.create_dungeon("fixed_test", "fixed_seed")
        
        test_char = Character("修正テストキャラ", "human", "fighter")
        test_party = Party("修正テストパーティ")
        test_party.add_character(test_char)
        
        dungeon_manager.enter_dungeon("fixed_test", test_party)
        
        player_pos = dungeon_manager.current_dungeon.player_position
        current_level = dungeon_manager.current_dungeon.levels[1]
        
        print(f"プレイヤー位置: ({player_pos.x}, {player_pos.y})")
        
        renderer = DungeonRendererPygame()
        
        # 修正後のレイ開始位置を確認
        ray_start_x, ray_start_y = renderer._get_ray_start_position(player_pos)
        print(f"レイ開始位置: ({ray_start_x}, {ray_start_y})")
        print(f"セル中央配置: {ray_start_x == player_pos.x + 0.5 and ray_start_y == player_pos.y + 0.5}")
        
        # 各方向のレイキャスティング結果
        directions = [
            (Direction.NORTH, "正面（北）"),
            (Direction.SOUTH, "背面（南）"),
            (Direction.EAST, "右（東）"),
            (Direction.WEST, "左（西）")
        ]
        
        print("\n修正後のレイキャスティング結果:")
        for direction, name in directions:
            angle = renderer._get_direction_angle(direction)
            distance, hit_wall = renderer._cast_ray(current_level, player_pos, angle)
            print(f"{name}: 距離={distance:.3f}, 壁ヒット={hit_wall}")
    
    def test_ray_progression_from_center(self):
        """中央からのレイ進行テスト"""
        print("\n=== 中央からのレイ進行テスト ===")
        
        # テストセットアップ
        dungeon_manager = DungeonManager()
        dungeon_state = dungeon_manager.create_dungeon("progression_test", "progression_seed")
        
        test_char = Character("進行テストキャラ", "human", "fighter")
        test_party = Party("進行テストパーティ")
        test_party.add_character(test_char)
        
        dungeon_manager.enter_dungeon("progression_test", test_party)
        
        player_pos = dungeon_manager.current_dungeon.player_position
        current_level = dungeon_manager.current_dungeon.levels[1]
        
        renderer = DungeonRendererPygame()
        
        print(f"プレイヤー位置: ({player_pos.x}, {player_pos.y})")
        
        # 南方向（背面）の詳細追跡
        south_angle = renderer._get_direction_angle(Direction.SOUTH)
        dx = math.cos(south_angle)
        dy = math.sin(south_angle)
        
        print(f"南方向レイ: dx={dx:.3f}, dy={dy:.3f}")
        
        ray_x, ray_y = renderer._get_ray_start_position(player_pos)
        print(f"レイ開始位置: ({ray_x:.3f}, {ray_y:.3f})")
        
        # ステップごとの追跡
        distance = 0
        for step in range(1, 6):
            ray_x += dx * 0.1  # RAYCAST_STEP_SIZE
            ray_y += dy * 0.1
            distance += 0.1
            
            grid_x, grid_y = int(ray_x), int(ray_y)
            local_x = ray_x - grid_x
            local_y = ray_y - grid_y
            
            cell = current_level.get_cell(grid_x, grid_y)
            
            print(f"\nステップ{step}:")
            print(f"  レイ座標: ({ray_x:.3f}, {ray_y:.3f})")
            print(f"  グリッド: ({grid_x}, {grid_y})")
            print(f"  ローカル: ({local_x:.3f}, {local_y:.3f})")
            
            if cell:
                print(f"  セルタイプ: {cell.cell_type.value}")
                wall_hit = renderer._is_wall_hit(cell, local_x, local_y)
                print(f"  壁ヒット: {wall_hit}")
                
                if wall_hit:
                    print(f"  >>> 壁ヒット発生 <<<")
                    break
            else:
                print(f"  セル不在")
                break
    
    def test_multiple_scenarios(self):
        """複数シナリオのテスト"""
        print("\n=== 複数シナリオのテスト ===")
        
        # 複数の異なるシードでテスト
        seeds = ["scenario1", "scenario2", "scenario3"]
        
        for i, seed in enumerate(seeds, 1):
            print(f"\n--- シナリオ{i} (seed: {seed}) ---")
            
            dungeon_manager = DungeonManager()
            dungeon_state = dungeon_manager.create_dungeon(f"scenario_{i}", seed)
            
            test_char = Character(f"シナリオ{i}キャラ", "human", "fighter")
            test_party = Party(f"シナリオ{i}パーティ")
            test_party.add_character(test_char)
            
            dungeon_manager.enter_dungeon(f"scenario_{i}", test_party)
            
            player_pos = dungeon_manager.current_dungeon.player_position
            current_level = dungeon_manager.current_dungeon.levels[1]
            
            print(f"プレイヤー位置: ({player_pos.x}, {player_pos.y})")
            
            # 現在位置のセル確認
            current_cell = current_level.get_cell(player_pos.x, player_pos.y)
            print(f"セルタイプ: {current_cell.cell_type.value}")
            
            renderer = DungeonRendererPygame()
            
            # 4方向の結果を簡潔に表示
            results = []
            for direction in Direction:
                angle = renderer._get_direction_angle(direction)
                distance, hit_wall = renderer._cast_ray(current_level, player_pos, angle)
                results.append(f"{direction.value}={distance:.2f}")
            
            print(f"レイキャスト結果: {', '.join(results)}")
            
            # 四方すべてが短距離の壁ヒットの場合は問題
            all_short = all(
                renderer._cast_ray(current_level, player_pos, renderer._get_direction_angle(d))[1] and
                renderer._cast_ray(current_level, player_pos, renderer._get_direction_angle(d))[0] < 0.2
                for d in Direction
            )
            
            if all_short:
                print("  >>> 問題: 四方すべてが短距離壁ヒット <<<")
            else:
                print("  正常: 適切な距離でのレイキャスト")


if __name__ == "__main__":
    print("修正後のレイキャスティングテスト")
    print("=" * 50)
    
    test_instance = TestFixedRaycast()
    
    try:
        # 中央配置でのレイ開始テスト
        test_instance.test_centered_ray_start()
        
        # 中央からのレイ進行テスト
        test_instance.test_ray_progression_from_center()
        
        # 複数シナリオのテスト
        test_instance.test_multiple_scenarios()
        
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()