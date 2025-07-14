#!/usr/bin/env python3
"""ダンジョンビューの問題検証用テスト"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dungeon.dungeon_manager import DungeonManager, PlayerPosition
from src.dungeon.dungeon_generator import DungeonGenerator, CellType, Direction
from src.character.party import Party
from src.character.character import Character


def print_dungeon_map(level):
    """ダンジョンマップをテキスト形式で出力"""
    print(f"\n=== ダンジョンレベル {level.level} ===")
    print(f"サイズ: {level.width} x {level.height}")
    print(f"属性: {level.attribute.value}")
    print(f"開始位置: {level.start_position}")
    print(f"上階段位置: {level.stairs_up_position}")
    print(f"下階段位置: {level.stairs_down_position}")
    print(f"ボス位置: {level.boss_position}")
    print()
    
    # マップの文字表現
    symbol_map = {
        CellType.WALL: '█',
        CellType.FLOOR: '.',
        CellType.STAIRS_UP: '↑',
        CellType.STAIRS_DOWN: '↓',
        CellType.TREASURE: '$',
        CellType.TRAP: '×',
        CellType.BOSS: 'B'
    }
    
    # マップを描画
    print("マップ:")
    for y in range(level.height):
        row = ""
        for x in range(level.width):
            cell = level.get_cell(x, y)
            if cell:
                symbol = symbol_map.get(cell.cell_type, '?')
                
                # 特殊な位置をマーク
                if level.start_position and (x, y) == level.start_position:
                    symbol = 'S'  # 開始位置
                elif cell.has_treasure:
                    symbol = '$'  # 宝箱
                elif cell.has_trap:
                    symbol = '×'  # トラップ
                    
                row += symbol
            else:
                row += '?'
        print(row)
    
    print("\n凡例:")
    print("█: 壁, .: 床, S: 開始位置, ↑: 上階段, ↓: 下階段")
    print("$: 宝箱, ×: トラップ, B: ボス")


class TestDungeonViewDebug:
    
    def test_coordinate_system(self):
        """座標系の検証"""
        print("=== 座標系検証 ===")
        
        # 方向と座標変換の検証
        generator = DungeonGenerator()
        
        print("方向と座標変換:")
        for direction in Direction:
            dx, dy = generator._direction_to_delta(direction)
            print(f"{direction.value}: dx={dx}, dy={dy}")
        
        print("\n座標系の説明:")
        print("- X軸: 東方向（右）が正")
        print("- Y軸: 南方向（下）が正")
        print("- 原点(0,0)は左上角")
    
    def test_player_position_and_movement(self):
        """プレイヤー位置と移動可能性をテスト"""
        print("=== プレイヤー位置と移動テスト ===")
        
        # ダンジョンマネージャーを作成
        dungeon_manager = DungeonManager()
        
        # テスト用ダンジョンを作成
        dungeon_state = dungeon_manager.create_dungeon("test_dungeon", "test_seed")
        
        # 仮のキャラクターとパーティを作成
        test_char = Character("テストキャラ", "human", "fighter")
        test_party = Party("テストパーティ")
        test_party.add_character(test_char)
        
        # ダンジョンに入る
        success = dungeon_manager.enter_dungeon("test_dungeon", test_party)
        assert success, "ダンジョンに入れませんでした"
        
        current_dungeon = dungeon_manager.current_dungeon
        player_pos = current_dungeon.player_position
        current_level = current_dungeon.levels[1]
        
        print(f"初期プレイヤー位置: ({player_pos.x}, {player_pos.y}), 向き: {player_pos.facing.value}")
        
        # 現在位置のセル情報を確認
        current_cell = current_level.get_cell(player_pos.x, player_pos.y)
        assert current_cell is not None, "現在位置にセルがありません（問題あり）"
        
        print(f"現在のセルタイプ: {current_cell.cell_type.value}")
        print(f"現在の位置が歩行可能: {current_level.is_walkable(player_pos.x, player_pos.y)}")
        print(f"壁情報: {[(dir.value, has_wall) for dir, has_wall in current_cell.walls.items()]}")
        
        # セルタイプが床であることを確認
        assert current_cell.cell_type == CellType.FLOOR, f"開始位置が床ではありません: {current_cell.cell_type}"
        
        # 歩行可能であることを確認
        assert current_level.is_walkable(player_pos.x, player_pos.y), "開始位置が歩行不可能です"
        
        # 各方向への移動を試行
        print("\n各方向への移動テスト:")
        movement_results = {}
        for direction in Direction:
            success, message = dungeon_manager.move_player(direction)
            movement_results[direction] = (success, message)
            if success:
                new_pos = current_dungeon.player_position
                print(f"{direction.value}: 成功 - 新位置 ({new_pos.x}, {new_pos.y})")
                # 元の位置に戻す
                dungeon_manager.current_dungeon.player_position = PlayerPosition(
                    x=player_pos.x, y=player_pos.y, level=1, facing=player_pos.facing
                )
            else:
                print(f"{direction.value}: 失敗 - {message}")
        
        # マップを出力
        print_dungeon_map(current_level)
        
        # 少なくとも1方向は移動可能であることを確認
        successful_moves = [dir for dir, (success, _) in movement_results.items() if success]
        assert len(successful_moves) > 0, "どの方向にも移動できません。プレイヤーが壁に囲まれています。"
        
        print(f"移動可能な方向: {[dir.value for dir in successful_moves]}")
    
    def test_dungeon_boundary_check(self):
        """ダンジョンの境界チェック"""
        print("=== ダンジョン境界チェック ===")
        
        dungeon_manager = DungeonManager()
        dungeon_state = dungeon_manager.create_dungeon("boundary_test", "boundary_seed")
        
        test_char = Character("テストキャラ", "human", "fighter")
        test_party = Party("境界テストパーティ")
        test_party.add_character(test_char)
        
        dungeon_manager.enter_dungeon("boundary_test", test_party)
        
        current_level = dungeon_manager.current_dungeon.levels[1]
        
        # 境界付近の座標をチェック
        boundary_coords = [
            (0, 0), (current_level.width-1, 0),  # 上端
            (0, current_level.height-1), (current_level.width-1, current_level.height-1),  # 下端
        ]
        
        print("境界座標のセルタイプ:")
        for x, y in boundary_coords:
            cell = current_level.get_cell(x, y)
            if cell:
                print(f"({x}, {y}): {cell.cell_type.value}")
            else:
                print(f"({x}, {y}): セル不在")


if __name__ == "__main__":
    print("ダンジョンビューの問題検証テスト")
    print("=" * 50)
    
    test_instance = TestDungeonViewDebug()
    
    try:
        # 座標系検証
        test_instance.test_coordinate_system()
        
        # プレイヤー位置と移動テスト
        test_instance.test_player_position_and_movement()
        
        # 境界チェック
        test_instance.test_dungeon_boundary_check()
        
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()