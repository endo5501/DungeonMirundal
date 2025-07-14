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
        
        print(f"カメラ位置: ({renderer.camera.state.x}, {renderer.camera.state.y})")
        print(f"カメラ角度: {math.degrees(renderer.camera.state.angle):.1f}°")
        
        # 基本的なレンダリングテスト
        success = renderer.render_dungeon_view(player_pos, current_level)
        print(f"レンダリング成功: {success}")
        
        # レンダリングコンポーネントの確認
        print(f"\nレンダリングコンポーネント:")
        print(f"レイキャストエンジン: {renderer.raycast_engine is not None}")
        print(f"壁レンダラー: {renderer.wall_renderer is not None}")
        print(f"UIレンダラー: {renderer.ui_renderer is not None}")
        
        # 方向マッピングの確認
        print(f"\n方向マッピング:")
        for direction in Direction:
            angle = renderer.camera._direction_angles.get(direction, 0)
            degrees = math.degrees(angle)
            print(f"{direction.value}: {degrees:.1f}度")
    
    
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
            # 簡易的なセル境界テスト
            at_boundary = (local_x <= 0.1 or local_x >= 0.9 or local_y <= 0.1 or local_y >= 0.9)
            print(f"{name} ({local_x}, {local_y}): 境界付近={at_boundary}")
    
    def test_render_method_availability(self):
        """レンダリングメソッドの可用性チェック"""
        print("\n=== レンダリングメソッドの可用性 ===")
        
        renderer = DungeonRendererPygame()
        
        
        # コンポーネントの確認
        print("レンダラーコンポーネント:")
        components = ['camera', 'raycast_engine', 'wall_renderer', 'ui_renderer', 'prop_renderer']
        for component in components:
            has_component = hasattr(renderer, component)
            print(f"{component}: {'○' if has_component else '×'}")
            
            if has_component:
                comp_obj = getattr(renderer, component)
                print(f"  タイプ: {type(comp_obj).__name__}")
        
        # 基本的なメソッドの確認
        print("\n基本的なメソッド:")
        basic_methods = ['render_dungeon', 'render_dungeon_view', 'update_camera_position']
        for method_name in basic_methods:
            has_method = hasattr(renderer, method_name)
            print(f"{method_name}: {'○' if has_method else '×'}")


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