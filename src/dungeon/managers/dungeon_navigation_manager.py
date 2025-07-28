"""ダンジョンナビゲーション管理"""

from typing import Dict, Optional, Tuple, List
from ..dungeon_generator import DungeonLevel, DungeonCell, CellType, Direction
from .dungeon_state_manager import DungeonState, PlayerPosition
from src.utils.logger import logger


class DungeonNavigationManager:
    """ダンジョンナビゲーション管理"""
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
        
        # 地上部帰還コールバック
        self.return_to_overworld_callback = None
        
        logger.debug("DungeonNavigationManager初期化完了")
    
    def set_return_to_overworld_callback(self, callback):
        """地上部帰還コールバックを設定"""
        self.return_to_overworld_callback = callback
        logger.debug("地上部帰還コールバックを設定しました")
    
    def return_to_overworld(self) -> bool:
        """地上部に帰還"""
        current_dungeon = self.state_manager.get_current_dungeon()
        if not current_dungeon:
            logger.warning("現在アクティブなダンジョンがありません")
            return False
        
        # ダンジョンを退出
        success = self.state_manager.exit_dungeon()
        
        if success and self.return_to_overworld_callback:
            # 地上部帰還コールバックを実行
            logger.info("地上部帰還処理を開始します")
            return self.return_to_overworld_callback()
        
        return success
    
    def use_stairs(self) -> Tuple[bool, str, Optional[str]]:
        """階段または出口を使用
        
        Returns:
            Tuple[bool, str, Optional[str]]: (成功フラグ, メッセージ, 階段タイプ)
        """
        current_dungeon = self.state_manager.get_current_dungeon()
        if not current_dungeon or not current_dungeon.player_position:
            return False, "ダンジョンに入っていません", None
        
        pos = current_dungeon.player_position
        current_level = current_dungeon.levels.get(pos.level)
        
        if not current_level:
            return False, "現在のレベルが見つかりません", None
        
        # 現在位置のセルを取得
        current_cell = current_level.get_cell(pos.x, pos.y)
        if not current_cell:
            return False, "現在位置が無効です", None
        
        # セルタイプに応じて処理
        if current_cell.cell_type == CellType.STAIRS_UP:
            # 上階段使用
            success, message = self.change_level(pos.level - 1)
            return success, message, "up"
            
        elif current_cell.cell_type == CellType.STAIRS_DOWN:
            # 下階段使用
            success, message = self.change_level(pos.level + 1)
            return success, message, "down"
            
        elif current_cell.cell_type == CellType.EXIT:
            # 地上への出口使用
            success = self.return_to_overworld()
            if success:
                return True, "地上へ戻ります", "exit"
            else:
                return False, "地上へ戻れませんでした", "exit"
        else:
            return False, "ここには階段がありません", None
    
    def move_player(self, direction: Direction) -> Tuple[bool, str]:
        """プレイヤーを移動"""
        current_dungeon = self.state_manager.get_current_dungeon()
        if not current_dungeon or not current_dungeon.player_position:
            return False, "ダンジョンに入っていません"
        
        pos = current_dungeon.player_position
        current_level = current_dungeon.levels.get(pos.level)
        
        if not current_level:
            return False, "現在のレベルが見つかりません"
        
        # 移動先座標を計算
        dx, dy = self._direction_to_delta(direction)
        new_x, new_y = pos.x + dx, pos.y + dy
        
        # 境界チェック
        if not (0 <= new_x < current_level.width and 0 <= new_y < current_level.height):
            return False, "ダンジョンの境界です"
        
        # 現在のセルから移動可能かチェック
        current_cell = current_level.get_cell(pos.x, pos.y)
        if not current_cell or current_cell.walls.get(direction, True):
            return False, "壁があり移動できません"
        
        # 移動先セルが歩行可能かチェック
        target_cell = current_level.get_cell(new_x, new_y)
        if not target_cell or not current_level.is_walkable(new_x, new_y):
            return False, "移動先に進めません"
        
        # 移動実行
        pos.x, pos.y = new_x, new_y
        current_dungeon.steps_taken += 1
        
        # セルを発見済みにする
        if pos.level not in current_dungeon.discovered_cells:
            current_dungeon.discovered_cells[pos.level] = []
        
        if (new_x, new_y) not in current_dungeon.discovered_cells[pos.level]:
            current_dungeon.discovered_cells[pos.level].append((new_x, new_y))
            target_cell.discovered = True
        
        target_cell.visited = True
        
        logger.debug(f"プレイヤーが移動: ({pos.x}, {pos.y}) レベル{pos.level}")
        return True, f"移動しました"
    
    def turn_player(self, direction: Direction) -> bool:
        """プレイヤーの向きを変更"""
        current_dungeon = self.state_manager.get_current_dungeon()
        if not current_dungeon or not current_dungeon.player_position:
            return False
        
        current_dungeon.player_position.facing = direction
        logger.debug(f"プレイヤーが{direction.value}を向きました")
        return True
    
    def turn_player_left(self) -> bool:
        """プレイヤーを左に回転"""
        current_dungeon = self.state_manager.get_current_dungeon()
        if not current_dungeon or not current_dungeon.player_position:
            return False
        
        current_facing = current_dungeon.player_position.facing
        
        # 左回転のマッピング
        left_mapping = {
            Direction.NORTH: Direction.WEST,
            Direction.WEST: Direction.SOUTH,
            Direction.SOUTH: Direction.EAST,
            Direction.EAST: Direction.NORTH
        }
        
        new_direction = left_mapping.get(current_facing, Direction.NORTH)
        return self.turn_player(new_direction)
    
    def turn_player_right(self) -> bool:
        """プレイヤーを右に回転"""
        current_dungeon = self.state_manager.get_current_dungeon()
        if not current_dungeon or not current_dungeon.player_position:
            return False
        
        current_facing = current_dungeon.player_position.facing
        
        # 右回転のマッピング
        right_mapping = {
            Direction.NORTH: Direction.EAST,
            Direction.EAST: Direction.SOUTH,
            Direction.SOUTH: Direction.WEST,
            Direction.WEST: Direction.NORTH
        }
        
        new_direction = right_mapping.get(current_facing, Direction.NORTH)
        return self.turn_player(new_direction)
    
    def change_level(self, target_level: int) -> Tuple[bool, str]:
        """レベルを変更（階段使用）"""
        current_dungeon = self.state_manager.get_current_dungeon()
        if not current_dungeon or not current_dungeon.player_position:
            return False, "ダンジョンに入っていません"
        
        pos = current_dungeon.player_position
        current_level = current_dungeon.levels.get(pos.level)
        
        if not current_level:
            return False, "現在のレベルが見つかりません"
        
        # 現在位置の階段チェック
        current_cell = current_level.get_cell(pos.x, pos.y)
        if not current_cell:
            return False, "現在位置が無効です"
        
        # 上階段チェック
        if (target_level == pos.level - 1 and 
            current_cell.cell_type == CellType.STAIRS_UP and
            target_level >= 1):
            
            # 目標レベルが存在しない場合は生成
            if target_level not in current_dungeon.levels:
                new_level = self.state_manager.generator.generate_level(target_level, current_dungeon.dungeon_id)
                current_dungeon.levels[target_level] = new_level
            
            # プレイヤー位置を下階段に設定
            target_level_data = current_dungeon.levels[target_level]
            if target_level_data.stairs_down_position:
                pos.x, pos.y = target_level_data.stairs_down_position
                pos.level = target_level
                return True, f"レベル{target_level}に上がりました"
        
        # 下階段チェック
        elif (target_level == pos.level + 1 and 
              current_cell.cell_type == CellType.STAIRS_DOWN and
              target_level <= 20):  # デフォルト最大レベル
            
            # 目標レベルが存在しない場合は生成
            if target_level not in current_dungeon.levels:
                new_level = self.state_manager.generator.generate_level(target_level, current_dungeon.dungeon_id)
                current_dungeon.levels[target_level] = new_level
            
            # プレイヤー位置を上階段に設定
            target_level_data = current_dungeon.levels[target_level]
            if target_level_data.stairs_up_position:
                pos.x, pos.y = target_level_data.stairs_up_position
                pos.level = target_level
                return True, f"レベル{target_level}に下りました"
        
        return False, "ここには階段がありません"
    
    def get_current_cell(self) -> Optional[DungeonCell]:
        """現在位置のセルを取得"""
        current_dungeon = self.state_manager.get_current_dungeon()
        if not current_dungeon or not current_dungeon.player_position:
            return None
        
        pos = current_dungeon.player_position
        current_level = current_dungeon.levels.get(pos.level)
        
        if not current_level:
            return None
        
        return current_level.get_cell(pos.x, pos.y)
    
    def get_visible_cells(self, vision_range: int = 1) -> List[Tuple[int, int, DungeonCell]]:
        """視界内のセルを取得"""
        current_dungeon = self.state_manager.get_current_dungeon()
        if not current_dungeon or not current_dungeon.player_position:
            return []
        
        pos = current_dungeon.player_position
        current_level = current_dungeon.levels.get(pos.level)
        
        if not current_level:
            return []
        
        visible_cells = []
        
        # 視界範囲内のセルを取得
        for dx in range(-vision_range, vision_range + 1):
            for dy in range(-vision_range, vision_range + 1):
                x, y = pos.x + dx, pos.y + dy
                
                if 0 <= x < current_level.width and 0 <= y < current_level.height:
                    cell = current_level.get_cell(x, y)
                    if cell:
                        visible_cells.append((x, y, cell))
        
        return visible_cells
    
    def can_move_to(self, x: int, y: int, level: int) -> bool:
        """指定した座標に移動可能かチェック"""
        current_dungeon = self.state_manager.get_current_dungeon()
        if not current_dungeon:
            return False
        
        # レベルの存在確認
        if level not in current_dungeon.levels:
            return False
        
        dungeon_level = current_dungeon.levels[level]
        
        # 境界チェック
        if not (0 <= x < dungeon_level.width and 0 <= y < dungeon_level.height):
            return False
        
        # セルの存在確認
        cell = dungeon_level.get_cell(x, y)
        if not cell:
            return False
        
        # 移動可能なセルタイプかチェック
        passable_types = {
            CellType.FLOOR, CellType.STAIRS_UP, CellType.STAIRS_DOWN,
            CellType.DOOR, CellType.EXIT, CellType.TREASURE,
            CellType.BOSS, CellType.SPECIAL
        }
        
        return cell.cell_type in passable_types
    
    def _direction_to_delta(self, direction: Direction) -> Tuple[int, int]:
        """方向をデルタ座標に変換"""
        direction_map = {
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0)
        }
        return direction_map[direction]