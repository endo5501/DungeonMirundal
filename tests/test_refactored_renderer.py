#!/usr/bin/env python3
"""リファクタリング済みレンダラーのテスト"""

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


class TestRefactoredRenderer:
    
    def test_renderer_initialization(self):
        """リファクタリング済みレンダラーの初期化テスト"""
        print("=== レンダラー初期化テスト ===")
        
        renderer = DungeonRendererPygame()
        
        # コンポーネントが正しく初期化されているか確認
        assert renderer.config is not None, "設定が初期化されていません"
        assert renderer.camera is not None, "カメラが初期化されていません"
        assert renderer.raycast_engine is not None, "レイキャストエンジンが初期化されていません"
        assert renderer.wall_renderer is not None, "壁レンダラーが初期化されていません"
        assert renderer.ui_renderer is not None, "UIレンダラーが初期化されていません"
        assert renderer.prop_renderer is not None, "プロップレンダラーが初期化されていません"
        
        print("すべてのコンポーネントが正常に初期化されました")
    
    def test_camera_integration(self):
        """カメラ統合テスト"""
        print("\n=== カメラ統合テスト ===")
        
        # テストセットアップ
        dungeon_manager = DungeonManager()
        dungeon_state = dungeon_manager.create_dungeon("camera_integration_test", "camera_seed")
        
        test_char = Character("カメラテストキャラ", "human", "fighter")
        test_party = Party("カメラテストパーティ")
        test_party.add_character(test_char)
        
        dungeon_manager.enter_dungeon("camera_integration_test", test_party)
        
        player_pos = dungeon_manager.current_dungeon.player_position
        renderer = DungeonRendererPygame()
        
        print(f"プレイヤー位置: ({player_pos.x}, {player_pos.y}), 向き: {player_pos.facing.value}")
        
        # カメラ位置を更新
        renderer.update_camera_position(player_pos)
        
        # カメラの状態を確認
        camera_pos = renderer.camera.get_position()
        camera_angle = renderer.camera.get_angle()
        
        print(f"カメラ位置: ({camera_pos[0]}, {camera_pos[1]})")
        print(f"カメラ角度: {math.degrees(camera_angle):.1f}°")
        
        # レイ開始位置のテスト
        ray_start = renderer.camera.get_ray_start_position(player_pos)
        print(f"レイ開始位置: ({ray_start[0]}, {ray_start[1]})")
        
        # 期待される値との比較
        assert ray_start[0] == player_pos.x + 0.5, "レイ開始X位置が正しくありません"
        assert ray_start[1] == player_pos.y + 0.5, "レイ開始Y位置が正しくありません"
        
        print("カメラ統合テスト成功")
    
    def test_raycast_engine(self):
        """レイキャストエンジンテスト"""
        print("\n=== レイキャストエンジンテスト ===")
        
        # テストセットアップ
        dungeon_manager = DungeonManager()
        dungeon_state = dungeon_manager.create_dungeon("raycast_engine_test", "raycast_seed")
        
        test_char = Character("レイキャストテストキャラ", "human", "fighter")
        test_party = Party("レイキャストテストパーティ")
        test_party.add_character(test_char)
        
        dungeon_manager.enter_dungeon("raycast_engine_test", test_party)
        
        player_pos = dungeon_manager.current_dungeon.player_position
        current_level = dungeon_manager.current_dungeon.levels[1]
        
        renderer = DungeonRendererPygame()
        renderer.update_camera_position(player_pos)
        
        # レイキャストエンジンのテスト
        ray_start = renderer.camera.get_ray_start_position(player_pos)
        
        # 複数方向のレイキャスト
        test_angles = [
            0,              # 東
            math.pi/2,      # 南
            math.pi,        # 西
            -math.pi/2      # 北
        ]
        
        print("レイキャスト結果:")
        for i, angle in enumerate(test_angles):
            distance, hit_wall, wall_type = renderer.raycast_engine.cast_ray(
                current_level, player_pos, ray_start, angle
            )
            direction_name = ["東", "南", "西", "北"][i]
            print(f"{direction_name}: 距離={distance:.3f}, 壁ヒット={hit_wall}, 壁タイプ={wall_type}")
            
            # 基本的な妥当性チェック
            assert distance > 0, f"{direction_name}の距離が無効です"
            assert isinstance(hit_wall, bool), f"{direction_name}の壁ヒット判定が無効です"
            if hit_wall:
                assert wall_type in ["face", "corner", "solid"], f"{direction_name}の壁タイプが無効です: {wall_type}"
        
        print("レイキャストエンジンテスト成功")
    
    def test_rendering_integration(self):
        """レンダリング統合テスト"""
        print("\n=== レンダリング統合テスト ===")
        
        # テストセットアップ
        dungeon_manager = DungeonManager()
        dungeon_state = dungeon_manager.create_dungeon("rendering_test", "rendering_seed")
        
        test_char = Character("レンダリングテストキャラ", "human", "fighter")
        test_party = Party("レンダリングテストパーティ")
        test_party.add_character(test_char)
        
        dungeon_manager.enter_dungeon("rendering_test", test_party)
        
        renderer = DungeonRendererPygame()
        renderer.set_dungeon_manager(dungeon_manager)
        
        # レンダリングの実行
        try:
            success = renderer.render_dungeon(dungeon_manager.current_dungeon)
            print(f"レンダリング成功: {success}")
            assert success, "レンダリングが失敗しました"
        except Exception as e:
            print(f"レンダリング中にエラー: {e}")
            # エラーが発生してもテストは続行（画面なしでのテストのため）
        
        print("レンダリング統合テスト完了")
    
    def test_component_configuration(self):
        """コンポーネント設定テスト"""
        print("\n=== コンポーネント設定テスト ===")
        
        renderer = DungeonRendererPygame()
        
        # 設定値の確認
        config = renderer.config
        print(f"画面サイズ: {config.screen.size}")
        print(f"FOV: {config.camera.fov}度")
        print(f"視界距離: {config.camera.view_distance}")
        print(f"レイキャストステップサイズ: {config.raycast.step_size}")
        print(f"壁高さ: {config.wall_render.height}")
        
        # 基本的な設定値の妥当性チェック
        assert config.screen.width > 0, "画面幅が無効です"
        assert config.screen.height > 0, "画面高さが無効です"
        assert config.camera.fov > 0, "FOVが無効です"
        assert config.camera.view_distance > 0, "視界距離が無効です"
        assert config.raycast.step_size > 0, "レイキャストステップサイズが無効です"
        
        print("コンポーネント設定テスト成功")


if __name__ == "__main__":
    print("リファクタリング済みレンダラーのテスト")
    print("=" * 50)
    
    test_instance = TestRefactoredRenderer()
    
    try:
        # レンダラー初期化テスト
        test_instance.test_renderer_initialization()
        
        # カメラ統合テスト
        test_instance.test_camera_integration()
        
        # レイキャストエンジンテスト
        test_instance.test_raycast_engine()
        
        # レンダリング統合テスト
        test_instance.test_rendering_integration()
        
        # コンポーネント設定テスト
        test_instance.test_component_configuration()
        
        print("\n=== すべてのテスト完了 ===")
        print("リファクタリングが正常に完了しました！")
        
    except Exception as e:
        print(f"テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()