"""ダンジョン生成システム"""

from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import hashlib
import random
import math

from src.utils.logger import logger


class CellType(Enum):
    """セルタイプ"""
    WALL = "wall"           # 壁
    FLOOR = "floor"         # 床
    DOOR = "door"           # ドア
    STAIRS_UP = "stairs_up" # 上階段
    STAIRS_DOWN = "stairs_down" # 下階段
    TREASURE = "treasure"   # 宝箱
    TRAP = "trap"           # トラップ
    SPECIAL = "special"     # 特殊
    BOSS = "boss"           # ボス


class DungeonAttribute(Enum):
    """ダンジョン属性"""
    PHYSICAL = "physical"   # 物理
    FIRE = "fire"           # 炎
    ICE = "ice"             # 氷
    LIGHTNING = "lightning" # 雷
    DARK = "dark"           # 闇
    LIGHT = "light"         # 光


class Direction(Enum):
    """方向"""
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


@dataclass
class DungeonCell:
    """ダンジョンセル"""
    x: int
    y: int
    cell_type: CellType = CellType.WALL
    
    # オプション情報
    has_treasure: bool = False
    has_trap: bool = False
    trap_type: Optional[str] = None
    treasure_id: Optional[str] = None
    
    # 壁情報（各方向の壁有無）
    walls: Dict[Direction, bool] = field(default_factory=lambda: {
        Direction.NORTH: True,
        Direction.SOUTH: True,
        Direction.EAST: True,
        Direction.WEST: True
    })
    
    # 探索状況
    visited: bool = False
    discovered: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'x': self.x,
            'y': self.y,
            'cell_type': self.cell_type.value,
            'has_treasure': self.has_treasure,
            'has_trap': self.has_trap,
            'trap_type': self.trap_type,
            'treasure_id': self.treasure_id,
            'walls': {direction.value: has_wall for direction, has_wall in self.walls.items()},
            'visited': self.visited,
            'discovered': self.discovered
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DungeonCell':
        """辞書から復元"""
        cell = cls(
            x=data['x'],
            y=data['y'],
            cell_type=CellType(data['cell_type'])
        )
        cell.has_treasure = data.get('has_treasure', False)
        cell.has_trap = data.get('has_trap', False)
        cell.trap_type = data.get('trap_type')
        cell.treasure_id = data.get('treasure_id')
        cell.visited = data.get('visited', False)
        cell.discovered = data.get('discovered', False)
        
        # 壁情報復元
        walls_data = data.get('walls', {})
        for direction_str, has_wall in walls_data.items():
            direction = Direction(direction_str)
            cell.walls[direction] = has_wall
        
        return cell


@dataclass
class DungeonLevel:
    """ダンジョン階層"""
    level: int
    width: int
    height: int
    attribute: DungeonAttribute
    cells: Dict[Tuple[int, int], DungeonCell] = field(default_factory=dict)
    
    # 特殊位置
    start_position: Optional[Tuple[int, int]] = None
    stairs_up_position: Optional[Tuple[int, int]] = None
    stairs_down_position: Optional[Tuple[int, int]] = None
    boss_position: Optional[Tuple[int, int]] = None
    
    # レベル特性
    encounter_rate: float = 0.1
    trap_rate: float = 0.05
    treasure_rate: float = 0.03
    
    def get_cell(self, x: int, y: int) -> Optional[DungeonCell]:
        """指定座標のセルを取得"""
        return self.cells.get((x, y))
    
    def set_cell(self, cell: DungeonCell):
        """セルを設定"""
        self.cells[(cell.x, cell.y)] = cell
    
    def is_walkable(self, x: int, y: int) -> bool:
        """歩行可能かチェック"""
        cell = self.get_cell(x, y)
        if not cell:
            return False
        
        return cell.cell_type in [
            CellType.FLOOR, 
            CellType.DOOR, 
            CellType.STAIRS_UP, 
            CellType.STAIRS_DOWN,
            CellType.TREASURE,
            CellType.SPECIAL
        ]
    
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """隣接セルの座標リストを取得"""
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbors.append((nx, ny))
        return neighbors
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'level': self.level,
            'width': self.width,
            'height': self.height,
            'attribute': self.attribute.value,
            'cells': {f"{x},{y}": cell.to_dict() for (x, y), cell in self.cells.items()},
            'start_position': self.start_position,
            'stairs_up_position': self.stairs_up_position,
            'stairs_down_position': self.stairs_down_position,
            'boss_position': self.boss_position,
            'encounter_rate': self.encounter_rate,
            'trap_rate': self.trap_rate,
            'treasure_rate': self.treasure_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DungeonLevel':
        """辞書から復元"""
        level = cls(
            level=data['level'],
            width=data['width'],
            height=data['height'],
            attribute=DungeonAttribute(data['attribute'])
        )
        
        # セル復元
        for pos_str, cell_data in data.get('cells', {}).items():
            level.cells[tuple(map(int, pos_str.split(',')))] = DungeonCell.from_dict(cell_data)
        
        level.start_position = data.get('start_position')
        level.stairs_up_position = data.get('stairs_up_position')
        level.stairs_down_position = data.get('stairs_down_position')
        level.boss_position = data.get('boss_position')
        level.encounter_rate = data.get('encounter_rate', 0.1)
        level.trap_rate = data.get('trap_rate', 0.05)
        level.treasure_rate = data.get('treasure_rate', 0.03)
        
        return level


class DungeonGenerator:
    """ダンジョン生成器"""
    
    def __init__(self, seed: str = "default"):
        self.seed = seed
        self.hash_seed = hashlib.md5(seed.encode()).hexdigest()
        
        # デフォルト設定
        self.default_width = 20
        self.default_height = 20
        self.min_room_size = 3
        self.max_room_size = 8
        self.max_rooms = 8
        
        logger.info(f"DungeonGeneratorを初期化: seed={seed}")
    
    def generate_level(self, level: int) -> DungeonLevel:
        """指定レベルのダンジョン階層を生成"""
        # レベル固有のシードを生成
        level_seed = hashlib.md5(f"{self.hash_seed}_{level}".encode()).hexdigest()
        rng = random.Random(int(level_seed[:8], 16))
        
        # レベル特性を決定
        attribute = self._determine_level_attribute(level, rng)
        width, height = self._determine_level_size(level, rng)
        
        # ダンジョンレベル作成
        dungeon_level = DungeonLevel(
            level=level,
            width=width,
            height=height,
            attribute=attribute
        )
        
        # レベル特性を設定
        dungeon_level.encounter_rate = min(0.05 + level * 0.01, 0.25)
        dungeon_level.trap_rate = min(0.02 + level * 0.005, 0.15)
        dungeon_level.treasure_rate = min(0.01 + level * 0.002, 0.08)
        
        # ダンジョン構造生成
        self._generate_structure(dungeon_level, rng)
        
        # 特殊要素配置
        self._place_special_elements(dungeon_level, rng)
        
        logger.info(f"ダンジョンレベル{level}を生成: {attribute.value}, {width}x{height}")
        return dungeon_level
    
    def _get_max_floors_for_dungeon(self, dungeon_id: str) -> int:
        """ダンジョンの最大フロア数を取得"""
        try:
            import yaml
            with open("config/dungeons.yaml", 'r', encoding='utf-8') as f:
                dungeons_config = yaml.safe_load(f)
            
            dungeon_info = dungeons_config.get("dungeons", {}).get(dungeon_id, {})
            return dungeon_info.get("floors", 20)
        except Exception:
            return 20  # デフォルト値
    
    def _determine_level_attribute(self, level: int, rng: random.Random) -> DungeonAttribute:
        """レベル属性を決定"""
        # レベルに基づく属性決定ロジック
        if level <= 3:
            return DungeonAttribute.PHYSICAL
        elif level <= 6:
            return rng.choice([DungeonAttribute.PHYSICAL, DungeonAttribute.FIRE])
        elif level <= 10:
            return rng.choice([DungeonAttribute.FIRE, DungeonAttribute.ICE, DungeonAttribute.LIGHTNING])
        elif level <= 15:
            return rng.choice([DungeonAttribute.ICE, DungeonAttribute.LIGHTNING, DungeonAttribute.DARK])
        else:
            return rng.choice([DungeonAttribute.DARK, DungeonAttribute.LIGHT])
    
    def _determine_level_size(self, level: int, rng: random.Random) -> Tuple[int, int]:
        """レベルサイズを決定"""
        # レベルが深いほど大きくなる傾向
        base_size = self.default_width + level // 3
        variance = rng.randint(-3, 3)
        
        width = max(15, min(30, base_size + variance))
        height = max(15, min(30, base_size + variance))
        
        return width, height
    
    def _generate_structure(self, dungeon_level: DungeonLevel, rng: random.Random):
        """ダンジョン構造を生成"""
        # 全体を壁で初期化
        for x in range(dungeon_level.width):
            for y in range(dungeon_level.height):
                cell = DungeonCell(x, y, CellType.WALL)
                dungeon_level.set_cell(cell)
        
        # 部屋を生成
        rooms = self._generate_rooms(dungeon_level, rng)
        
        # 通路で部屋を接続
        self._connect_rooms(dungeon_level, rooms, rng)
        
        # 壁情報を更新
        self._update_wall_info(dungeon_level)
    
    def _generate_rooms(self, dungeon_level: DungeonLevel, rng: random.Random) -> List[Tuple[int, int, int, int]]:
        """部屋を生成"""
        rooms = []
        attempts = 0
        max_attempts = 100
        
        while len(rooms) < self.max_rooms and attempts < max_attempts:
            attempts += 1
            
            # ランダムな部屋サイズと位置
            room_width = rng.randint(self.min_room_size, self.max_room_size)
            room_height = rng.randint(self.min_room_size, self.max_room_size)
            
            x = rng.randint(1, dungeon_level.width - room_width - 1)
            y = rng.randint(1, dungeon_level.height - room_height - 1)
            
            new_room = (x, y, room_width, room_height)
            
            # 他の部屋と重複チェック
            if not self._rooms_overlap(new_room, rooms):
                rooms.append(new_room)
                
                # 部屋内を床にする
                for rx in range(x, x + room_width):
                    for ry in range(y, y + room_height):
                        cell = dungeon_level.get_cell(rx, ry)
                        if cell:
                            cell.cell_type = CellType.FLOOR
        
        logger.debug(f"生成された部屋数: {len(rooms)}")
        return rooms
    
    def _rooms_overlap(self, room1: Tuple[int, int, int, int], rooms: List[Tuple[int, int, int, int]]) -> bool:
        """部屋の重複をチェック"""
        x1, y1, w1, h1 = room1
        
        for x2, y2, w2, h2 in rooms:
            # バッファを含めた重複チェック
            if (x1 < x2 + w2 + 1 and x1 + w1 + 1 > x2 and
                y1 < y2 + h2 + 1 and y1 + h1 + 1 > y2):
                return True
        
        return False
    
    def _connect_rooms(self, dungeon_level: DungeonLevel, rooms: List[Tuple[int, int, int, int]], rng: random.Random):
        """部屋を通路で接続"""
        if len(rooms) < 2:
            return
        
        # 最小スパニングツリーで部屋を接続
        connected = [0]  # 最初の部屋から開始
        unconnected = list(range(1, len(rooms)))
        
        while unconnected:
            # 接続済みの部屋から最も近い未接続の部屋を見つける
            min_distance = float('inf')
            best_connected = 0
            best_unconnected = 0
            
            for conn_idx in connected:
                for unconn_idx in unconnected:
                    distance = self._room_distance(rooms[conn_idx], rooms[unconn_idx])
                    if distance < min_distance:
                        min_distance = distance
                        best_connected = conn_idx
                        best_unconnected = unconn_idx
            
            # 通路を作成
            self._create_corridor(dungeon_level, rooms[best_connected], rooms[best_unconnected], rng)
            
            # 接続リストを更新
            connected.append(best_unconnected)
            unconnected.remove(best_unconnected)
        
        # 追加の接続を作成（サイクルを作るため）
        extra_connections = rng.randint(1, max(1, len(rooms) // 3))
        for _ in range(extra_connections):
            room1_idx = rng.randint(0, len(rooms) - 1)
            room2_idx = rng.randint(0, len(rooms) - 1)
            if room1_idx != room2_idx:
                self._create_corridor(dungeon_level, rooms[room1_idx], rooms[room2_idx], rng)
    
    def _room_distance(self, room1: Tuple[int, int, int, int], room2: Tuple[int, int, int, int]) -> float:
        """部屋間の距離を計算"""
        x1, y1, w1, h1 = room1
        x2, y2, w2, h2 = room2
        
        center1_x, center1_y = x1 + w1 // 2, y1 + h1 // 2
        center2_x, center2_y = x2 + w2 // 2, y2 + h2 // 2
        
        return math.sqrt((center2_x - center1_x) ** 2 + (center2_y - center1_y) ** 2)
    
    def _create_corridor(self, dungeon_level: DungeonLevel, room1: Tuple[int, int, int, int], 
                        room2: Tuple[int, int, int, int], rng: random.Random):
        """2つの部屋を通路で接続"""
        x1, y1, w1, h1 = room1
        x2, y2, w2, h2 = room2
        
        # 部屋の中心点を計算
        center1_x, center1_y = x1 + w1 // 2, y1 + h1 // 2
        center2_x, center2_y = x2 + w2 // 2, y2 + h2 // 2
        
        # L字型の通路を作成
        if rng.choice([True, False]):
            # 水平 -> 垂直
            self._create_horizontal_corridor(dungeon_level, center1_x, center2_x, center1_y)
            self._create_vertical_corridor(dungeon_level, center1_y, center2_y, center2_x)
        else:
            # 垂直 -> 水平
            self._create_vertical_corridor(dungeon_level, center1_y, center2_y, center1_x)
            self._create_horizontal_corridor(dungeon_level, center1_x, center2_x, center2_y)
    
    def _create_horizontal_corridor(self, dungeon_level: DungeonLevel, x1: int, x2: int, y: int):
        """水平通路を作成"""
        start_x, end_x = min(x1, x2), max(x1, x2)
        for x in range(start_x, end_x + 1):
            if 0 <= x < dungeon_level.width and 0 <= y < dungeon_level.height:
                cell = dungeon_level.get_cell(x, y)
                if cell and cell.cell_type == CellType.WALL:
                    cell.cell_type = CellType.FLOOR
    
    def _create_vertical_corridor(self, dungeon_level: DungeonLevel, y1: int, y2: int, x: int):
        """垂直通路を作成"""
        start_y, end_y = min(y1, y2), max(y1, y2)
        for y in range(start_y, end_y + 1):
            if 0 <= x < dungeon_level.width and 0 <= y < dungeon_level.height:
                cell = dungeon_level.get_cell(x, y)
                if cell and cell.cell_type == CellType.WALL:
                    cell.cell_type = CellType.FLOOR
    
    def _update_wall_info(self, dungeon_level: DungeonLevel):
        """壁情報を更新"""
        for (x, y), cell in dungeon_level.cells.items():
            if cell.cell_type != CellType.WALL:
                # 各方向の壁をチェック
                for direction in Direction:
                    dx, dy = self._direction_to_delta(direction)
                    neighbor_x, neighbor_y = x + dx, y + dy
                    
                    neighbor_cell = dungeon_level.get_cell(neighbor_x, neighbor_y)
                    if neighbor_cell and neighbor_cell.cell_type == CellType.WALL:
                        cell.walls[direction] = True
                    else:
                        cell.walls[direction] = False
    
    def _direction_to_delta(self, direction: Direction) -> Tuple[int, int]:
        """方向をデルタ座標に変換"""
        direction_map = {
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0)
        }
        return direction_map[direction]
    
    def _place_special_elements(self, dungeon_level: DungeonLevel, rng: random.Random):
        """特殊要素（階段、宝箱、トラップ）を配置"""
        floor_cells = [(pos, cell) for pos, cell in dungeon_level.cells.items() 
                      if cell.cell_type == CellType.FLOOR]
        
        if not floor_cells:
            return
        
        # 開始位置を設定（最初の部屋の中央付近）
        start_pos, start_cell = floor_cells[0]
        dungeon_level.start_position = start_pos
        
        # 上階段を配置（レベル1以外）
        if dungeon_level.level > 1:
            up_pos, up_cell = rng.choice(floor_cells)
            up_cell.cell_type = CellType.STAIRS_UP
            dungeon_level.stairs_up_position = up_pos
            floor_cells.remove((up_pos, up_cell))
        
        # 下階段を配置（最終レベル以外）
        max_floors = self._get_max_floors_for_dungeon(dungeon_id)
        if dungeon_level.level < max_floors:
            down_pos, down_cell = rng.choice(floor_cells)
            down_cell.cell_type = CellType.STAIRS_DOWN
            dungeon_level.stairs_down_position = down_pos
            floor_cells.remove((down_pos, down_cell))
        
        # ボス配置（最終レベルのみ）
        if dungeon_level.level == max_floors:
            boss_pos, boss_cell = rng.choice(floor_cells)
            boss_cell.cell_type = CellType.BOSS
            dungeon_level.boss_position = boss_pos
            floor_cells.remove((boss_pos, boss_cell))
        
        # 宝箱配置
        treasure_count = max(1, int(len(floor_cells) * dungeon_level.treasure_rate))
        for _ in range(treasure_count):
            if floor_cells:
                pos, cell = rng.choice(floor_cells)
                cell.has_treasure = True
                cell.treasure_id = f"treasure_{dungeon_level.level}_{pos[0]}_{pos[1]}"
                floor_cells.remove((pos, cell))
        
        # トラップ配置
        trap_count = max(0, int(len(floor_cells) * dungeon_level.trap_rate))
        for _ in range(trap_count):
            if floor_cells:
                pos, cell = rng.choice(floor_cells)
                cell.has_trap = True
                cell.trap_type = rng.choice(["poison", "paralysis", "damage", "teleport"])
                floor_cells.remove((pos, cell))
        
        logger.debug(f"特殊要素配置完了: 宝箱{treasure_count}, トラップ{trap_count}")


# グローバルインスタンス
dungeon_generator = DungeonGenerator()