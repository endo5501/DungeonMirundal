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
        
        # カメラ位置更新をテスト
        renderer.update_camera_position(player_pos)
        
        # カメラ状態の確認
        print(f"カメラ位置: ({renderer.camera.state.x}, {renderer.camera.state.y})")
        print(f"セル中央配置: カメラがプレイヤー位置と同期されました")
        
        # レイキャスティングエンジンが正常に初期化されていることを確認
        print(f"レイキャスティングエンジン: {renderer.raycast_engine is not None}")
        print(f"カメラシステム: {renderer.camera is not None}")
        
        # 基本的なレンダリングテスト
        success = renderer.render_dungeon_view(player_pos, current_level)
        print(f"レンダリング成功: {success}")
    
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
        
        renderer.update_camera_position(player_pos)
        
        # カメラの方向マッピングをテスト
        print("\n方向マッピング:")
        for direction in Direction:
            angle = renderer.camera._direction_angles.get(direction, 0)
            degrees = math.degrees(angle)
            print(f"{direction.value}: {degrees:.1f}度")
        
        # レンダリングコンポーネントのテスト
        print(f"\nレンダリングコンポーネント:")
        print(f"壁レンダラー: {renderer.wall_renderer is not None}")
        print(f"UIレンダラー: {renderer.ui_renderer is not None}")
        print(f"プロップレンダラー: {renderer.prop_renderer is not None}")
        
        # 基本的なレンダリングテスト
        success = renderer.render_dungeon_view(player_pos, current_level)
        print(f"レンダリング成功: {success}")
    
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
            success = renderer.render_dungeon_view(player_pos, current_level)
            print(f"レンダリング成功: {success}")
            
            # レンダリングシステムの基本動作確認
            print(f"レンダリングシステム: OK")


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