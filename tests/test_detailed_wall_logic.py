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
        """壁ヒット判定の詳細分析（簡易版）"""
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
        renderer.update_camera_position(player_pos)
        
        # 基本的なレンダリングテスト
        success = renderer.render_dungeon_view(player_pos, current_level)
        print(f"レンダリング成功: {success}")
        
        # カメラシステムのテスト
        print(f"カメラ位置: ({renderer.camera.state.x}, {renderer.camera.state.y})")
        print(f"カメラ角度: {math.degrees(renderer.camera.state.angle):.1f}°")
    
    def test_specific_case_analysis(self):
        """特定ケースの分析（簡易版）"""
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
        
        # 基本的なセル構造テスト
        print(f"\nセル基本情報:")
        print(f"  セルタイプ: {test_cell.cell_type.value}")
        print(f"  座標: ({test_cell.x}, {test_cell.y})")
        print(f"  壁の数: {sum(test_cell.walls.values())}")
        
        # レンダリングコンポーネントの確認
        print(f"\nレンダリングコンポーネント:")
        print(f"  レイキャストエンジン: {renderer.raycast_engine is not None}")
        print(f"  壁レンダラー: {renderer.wall_renderer is not None}")


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