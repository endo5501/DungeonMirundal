#!/usr/bin/env python3
"""疑似3Dレンダリングの座標系検証テスト"""

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


class TestRenderingCoordinates:
    
    def test_direction_angle_mapping(self):
        """方向と角度のマッピングを検証"""
        print("=== 方向と角度のマッピング ===")
        
        # レンダラーのカメラから方向マッピングを取得
        renderer = DungeonRendererPygame()
        direction_angles = renderer.camera._direction_angles
        
        print("定義済み角度:")
        for direction, angle in direction_angles.items():
            degrees = math.degrees(angle)
            print(f"{direction.value}: {angle:.3f} rad ({degrees:.1f}°)")
        
        # レンダラーのメソッドと一致するか確認
        # (既に上で作成済み)
        
        print("\nレンダラーの変換結果:")
        for direction in Direction:
            angle = renderer.camera._direction_angles.get(direction, 0)
            degrees = math.degrees(angle)
            print(f"{direction.value}: {angle:.3f} rad ({degrees:.1f}°)")
        
        # 期待される角度と比較
        expected = {
            Direction.NORTH: -90,  # 上方向
            Direction.EAST: 0,     # 右方向
            Direction.SOUTH: 90,   # 下方向
            Direction.WEST: 180    # 左方向
        }
        
        print("\n期待される角度との比較:")
        for direction, expected_degrees in expected.items():
            actual_angle = renderer.camera._direction_angles.get(direction, 0)
            actual_degrees = math.degrees(actual_angle)
            print(f"{direction.value}: 期待値 {expected_degrees}°, 実際 {actual_degrees:.1f}°")
    
    def test_ray_start_position(self):
        """レイの開始位置の確認"""
        print("\n=== レイの開始位置 ===")
        
        # テスト用ダンジョンを作成
        dungeon_manager = DungeonManager()
        dungeon_state = dungeon_manager.create_dungeon("ray_test", "ray_seed")
        
        test_char = Character("テストキャラ", "human", "fighter")
        test_party = Party("レイテストパーティ")
        test_party.add_character(test_char)
        
        dungeon_manager.enter_dungeon("ray_test", test_party)
        
        player_pos = dungeon_manager.current_dungeon.player_position
        print(f"プレイヤー位置: ({player_pos.x}, {player_pos.y})")
        
        # レンダラーでカメラ位置を確認
        renderer = DungeonRendererPygame()
        renderer.update_camera_position(player_pos)
        
        camera_x = renderer.camera.state.x
        camera_y = renderer.camera.state.y
        print(f"カメラ位置: ({camera_x}, {camera_y})")
        
        # カメラ位置はプレイヤー位置と同期されるべき
        print(f"位置同期: カメラ({camera_x}, {camera_y}) vs プレイヤー({player_pos.x}, {player_pos.y})")
        
        # レイキャスティングシステムの確認
        print(f"レイキャスティングエンジン: {renderer.raycast_engine is not None}")
        
        # レイキャスティングの基本的な動作テスト
        ray_start = renderer.camera.get_ray_start_position(player_pos)
        print(f"レイ開始位置（カメラから）: {ray_start}")
    
    def test_coordinate_system_consistency(self):
        """座標系の一貫性をテスト"""
        print("\n=== 座標系の一貫性 ===")
        
        # ダンジョン生成器の座標変換
        generator = DungeonGenerator()
        
        print("ダンジョン生成器の方向変換:")
        for direction in Direction:
            dx, dy = generator._direction_to_delta(direction)
            print(f"{direction.value}: dx={dx}, dy={dy}")
        
        # レンダラーの角度変換
        renderer = DungeonRendererPygame()
        
        print("\nレンダラーの角度変換（cos, sin値）:")
        for direction in Direction:
            angle = renderer.camera._direction_angles.get(direction, 0)
            cos_val = math.cos(angle)
            sin_val = math.sin(angle)
            print(f"{direction.value}: cos={cos_val:.3f}, sin={sin_val:.3f}")
        
        # 一貫性チェック
        print("\n座標系の一貫性チェック:")
        for direction in Direction:
            # ダンジョン生成器のデルタ
            dx_gen, dy_gen = generator._direction_to_delta(direction)
            
            # レンダラーの三角関数値
            angle = renderer.camera._direction_angles.get(direction, 0)
            dx_render = math.cos(angle)
            dy_render = math.sin(angle)
            
            # 符号の一致チェック（小数点誤差を考慮）
            dx_match = abs(dx_gen - round(dx_render)) < 0.1
            dy_match = abs(dy_gen - round(dy_render)) < 0.1
            
            print(f"{direction.value}: X座標一致={dx_match}, Y座標一致={dy_match}")
            if not dx_match or not dy_match:
                print(f"  詳細: gen=({dx_gen}, {dy_gen}), render=({dx_render:.3f}, {dy_render:.3f})")
    
    def test_camera_position_sync(self):
        """カメラ位置の同期をテスト"""
        print("\n=== カメラ位置の同期 ===")
        
        # テストセットアップ
        dungeon_manager = DungeonManager()
        dungeon_state = dungeon_manager.create_dungeon("camera_test", "camera_seed")
        
        test_char = Character("カメラテストキャラ", "human", "fighter")
        test_party = Party("カメラテストパーティ")
        test_party.add_character(test_char)
        
        dungeon_manager.enter_dungeon("camera_test", test_party)
        
        player_pos = dungeon_manager.current_dungeon.player_position
        renderer = DungeonRendererPygame()
        
        print(f"プレイヤー初期位置: ({player_pos.x}, {player_pos.y}), 向き: {player_pos.facing.value}")
        
        # カメラ位置を更新
        renderer.update_camera_position(player_pos)
        
        print(f"カメラ位置: ({renderer.camera.state.x}, {renderer.camera.state.y})")
        print(f"カメラ角度: {math.degrees(renderer.camera.state.angle):.1f}°")
        
        # 同期チェック
        pos_match = (renderer.camera.state.x == player_pos.x and renderer.camera.state.y == player_pos.y)
        expected_angle = renderer.camera._direction_angles.get(player_pos.facing, 0)
        angle_match = abs(renderer.camera.state.angle - expected_angle) < 0.001
        
        print(f"位置同期: {pos_match}")
        print(f"角度同期: {angle_match}")
        
        if not pos_match:
            print(f"位置不一致: プレイヤー({player_pos.x}, {player_pos.y}) vs カメラ({renderer.camera.state.x}, {renderer.camera.state.y})")
        
        if not angle_match:
            print(f"角度不一致: 期待値{math.degrees(expected_angle):.1f}° vs 実際{math.degrees(renderer.camera.state.angle):.1f}°")


if __name__ == "__main__":
    print("疑似3Dレンダリングの座標系検証テスト")
    print("=" * 50)
    
    test_instance = TestRenderingCoordinates()
    
    try:
        # 方向と角度のマッピング
        test_instance.test_direction_angle_mapping()
        
        # レイの開始位置
        test_instance.test_ray_start_position()
        
        # 座標系の一貫性
        test_instance.test_coordinate_system_consistency()
        
        # カメラ位置の同期
        test_instance.test_camera_position_sync()
        
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()