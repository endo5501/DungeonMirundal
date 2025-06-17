"""ダンジョン3D描画システム（Panda3D）"""

from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import math

try:
    from direct.showbase.ShowBase import ShowBase
    from direct.actor.Actor import Actor
    from panda3d.core import (
        Point3, Vec3, Vec4, 
        DirectionalLight, AmbientLight,
        CardMaker, TextNode,
        WindowProperties,
        CollisionTraverser, CollisionNode, CollisionSphere, CollisionHandlerQueue,
        BitMask32
    )
    from direct.gui.OnscreenText import OnscreenText
    from direct.task import Task
    PANDA3D_AVAILABLE = True
except ImportError:
    # Panda3Dが利用できない場合のダミークラス
    PANDA3D_AVAILABLE = False
    ShowBase = object

from src.dungeon.dungeon_manager import DungeonManager, DungeonState, PlayerPosition
from src.dungeon.dungeon_generator import DungeonLevel, DungeonCell, CellType, Direction, DungeonAttribute
from src.character.party import Party
from src.ui.dungeon_ui import DungeonUIManager
from src.utils.logger import logger
from src.core.config_manager import config_manager


class ViewMode(Enum):
    """表示モード"""
    FIRST_PERSON = "first_person"    # 1人称視点
    THIRD_PERSON = "third_person"    # 3人称視点
    MAP_VIEW = "map_view"            # マップビュー


class RenderQuality(Enum):
    """レンダリング品質"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"


class DungeonRenderer:
    """ダンジョン3D描画システム"""
    
    def __init__(self, show_base_instance=None):
        if not PANDA3D_AVAILABLE:
            logger.error("Panda3Dが利用できません。3D描画は無効化されます。")
            self.enabled = False
            # 基本属性を初期化
            self.dungeon_manager = None
            self.current_party = None
            self.ui_manager = None
            return
        
        # ShowBaseインスタンスを外部から受け取る
        self.base_instance = show_base_instance
        if not self.base_instance:
            # baseグローバル変数を使用
            try:
                self.base_instance = base
            except NameError:
                logger.error("ShowBaseインスタンスが見つかりません")
                self.enabled = False
                return
        
        # 実際には別のShowBaseを作らずに、既存のものを使用
        self.enabled = True
        
        # ShowBaseメソッドの参照を設定
        self.render = self.base_instance.render
        self.camera = self.base_instance.camera
        self.cam = self.base_instance.cam
        self.win = self.base_instance.win
        self.taskMgr = self.base_instance.taskMgr
        self.loader = self.base_instance.loader
        self.setBackgroundColor = self.base_instance.setBackgroundColor
        
        # 基本設定
        self.view_mode = ViewMode.FIRST_PERSON
        self.render_quality = RenderQuality.MEDIUM
        
        # ダンジョン管理
        self.dungeon_manager: Optional[DungeonManager] = None
        self.current_party: Optional[Party] = None
        
        # レンダリング要素
        self.wall_nodes: Dict[str, Any] = {}
        self.floor_nodes: Dict[str, Any] = {}
        self.ceiling_nodes: Dict[str, Any] = {}
        self.prop_nodes: Dict[str, Any] = {}
        
        # カメラ設定
        self.camera_height = 1.7  # プレイヤーの目線の高さ
        self.fov = 75             # 視野角
        self.view_distance = 10   # 描画距離
        
        # UI要素
        self.ui_elements: Dict[str, Any] = {}
        self.ui_manager: Optional[DungeonUIManager] = None
        
        # 初期化
        self._initialize_window()
        self._initialize_camera()
        self._initialize_lighting()
        self._initialize_ui()
        self._setup_controls()
        
        logger.info("DungeonRenderer初期化完了")
    
    def _initialize_window(self):
        """ウィンドウ初期化"""
        if not self.enabled:
            return
        
        props = WindowProperties()
        # 国際化対応：ウィンドウタイトルを取得
        try:
            title = config_manager.get_text("app.title")
        except:
            title = "ダンジョンエクスプローラー"  # フォールバック
        props.setTitle(title)
        props.setSize(1024, 768)
        self.win.requestProperties(props)
        
        # 背景色設定（ダンジョンらしい暗い色）
        self.setBackgroundColor(0.1, 0.1, 0.15, 1)
    
    def _initialize_camera(self):
        """カメラ初期化"""
        if not self.enabled:
            return
        
        # カメラの基本設定
        self.camera.setPos(0, 0, self.camera_height)
        self.camera.setHpr(0, 0, 0)
        
        # 視野角設定
        lens = self.cam.node().getLens()
        lens.setFov(self.fov)
        lens.setNear(0.1)
        lens.setFar(self.view_distance)
    
    def _initialize_lighting(self):
        """照明初期化"""
        if not self.enabled:
            return
        
        # 環境光（基本的な明るさ）
        ambient_light = AmbientLight('ambient')
        ambient_light.setColor(Vec4(0.2, 0.2, 0.3, 1))
        ambient_light_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_light_np)
        
        # 方向光（松明の光をシミュレート）
        directional_light = DirectionalLight('directional')
        directional_light.setColor(Vec4(0.8, 0.7, 0.5, 1))
        directional_light.setDirection(Vec3(-1, -1, -1))
        directional_light_np = self.render.attachNewNode(directional_light)
        self.render.setLight(directional_light_np)
    
    def _initialize_ui(self):
        """UI初期化"""
        if not self.enabled:
            return
        
        # フォントを取得
        font = None
        try:
            from src.ui.font_manager import font_manager
            font = font_manager.get_default_font()
        except:
            pass
        
        # コンパス表示
        self.ui_elements['compass'] = OnscreenText(
            text='N',
            pos=(0.85, 0.85),
            scale=0.1,
            fg=(1, 1, 1, 1),
            font=font
        )
        
        # 位置情報表示
        self.ui_elements['position'] = OnscreenText(
            text=config_manager.get_text("dungeon.position_display").format(x=0, y=0, level=1),
            pos=(-0.95, 0.85),
            scale=0.06,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            font=font
        )
        
        # ヘルプテキスト
        self.ui_elements['help'] = OnscreenText(
            text=config_manager.get_text("dungeon.help_text"),
            pos=(-0.95, -0.9),
            scale=0.05,
            fg=(0.7, 0.7, 0.7, 1),
            align=TextNode.ALeft,
            font=font
        )
        
        # ダンジョンUIマネージャーの初期化
        self.ui_manager = DungeonUIManager()
        self.ui_manager.set_callback("return_overworld", self._return_to_overworld)
    
    def _setup_controls(self):
        """コントロール設定"""
        if not self.enabled:
            return
        
        # 新しい入力システムを使用する場合、直接キーバインドは不要
        # GameManagerが入力を処理し、このクラスの移動メソッドを呼び出す
        logger.info("ダンジョンレンダラーのコントロールを設定しました（入力はGameManagerで処理）")
    
    def set_dungeon_manager(self, dungeon_manager: DungeonManager):
        """ダンジョンマネージャー設定"""
        self.dungeon_manager = dungeon_manager
        logger.info("ダンジョンマネージャーを設定しました")
    
    def set_party(self, party: Party):
        """パーティ設定"""
        self.current_party = party
        if hasattr(self, 'ui_manager') and self.ui_manager:
            self.ui_manager.set_party(party)
            self.ui_manager.show_status_bar()
        logger.info(f"パーティ{party.name}を設定しました")
    
    def render_dungeon(self, dungeon_state: DungeonState) -> bool:
        """ダンジョンを描画"""
        if not self.enabled:
            logger.warning("3D描画が無効化されています")
            return False
        
        if not dungeon_state.player_position:
            logger.error("プレイヤー位置が設定されていません")
            return False
        
        # 既存の描画要素をクリア
        self._clear_scene()
        
        # 現在レベルを取得
        current_level = dungeon_state.levels.get(dungeon_state.player_position.level)
        if not current_level:
            logger.error(f"レベル{dungeon_state.player_position.level}が見つかりません")
            return False
        
        # カメラ位置更新
        self._update_camera_position(dungeon_state.player_position)
        
        # ダンジョン構造を描画
        self._render_level_geometry(current_level, dungeon_state.player_position)
        
        # プロップ（宝箱、階段など）を描画
        self._render_props(current_level, dungeon_state.player_position)
        
        # UI更新
        self._update_ui(dungeon_state)
        
        logger.debug(f"ダンジョンレベル{current_level.level}を描画しました")
        return True
    
    def _clear_scene(self):
        """シーンをクリア"""
        if not self.enabled:
            return
        
        # 既存のノードを削除
        for node_dict in [self.wall_nodes, self.floor_nodes, self.ceiling_nodes, self.prop_nodes]:
            for node in node_dict.values():
                if hasattr(node, 'removeNode'):
                    node.removeNode()
            node_dict.clear()
    
    def _update_camera_position(self, player_pos: PlayerPosition):
        """カメラ位置更新"""
        if not self.enabled:
            return
        
        # プレイヤー位置をワールド座標に変換
        world_x = player_pos.x * 2.0  # セル1つ = 2.0ユニット
        world_y = -player_pos.y * 2.0  # Panda3Dは-Y方向が奥
        
        # カメラ位置設定
        self.camera.setPos(world_x, world_y, self.camera_height)
        
        # 向き設定
        heading = self._direction_to_heading(player_pos.facing)
        self.camera.setHpr(heading, 0, 0)
    
    def _render_level_geometry(self, level: DungeonLevel, player_pos: PlayerPosition):
        """レベルジオメトリ描画"""
        if not self.enabled:
            return
        
        # 描画範囲を制限（パフォーマンス向上）
        render_range = 5
        
        for x in range(max(0, player_pos.x - render_range), 
                      min(level.width, player_pos.x + render_range + 1)):
            for y in range(max(0, player_pos.y - render_range),
                          min(level.height, player_pos.y + render_range + 1)):
                
                cell = level.get_cell(x, y)
                if not cell:
                    continue
                
                self._render_cell(cell, level.attribute)
    
    def _render_cell(self, cell: DungeonCell, attribute: DungeonAttribute):
        """セル描画"""
        if not self.enabled:
            return
        
        world_x = cell.x * 2.0
        world_y = -cell.y * 2.0
        
        if cell.cell_type == CellType.WALL:
            self._render_wall_cell(cell, world_x, world_y, attribute)
        else:
            # 床を描画
            self._render_floor(cell, world_x, world_y, attribute)
            
            # 天井を描画
            self._render_ceiling(cell, world_x, world_y, attribute)
            
            # 各方向の壁をチェック
            for direction, has_wall in cell.walls.items():
                if has_wall:
                    self._render_wall(cell, world_x, world_y, direction, attribute)
    
    def _render_wall_cell(self, cell: DungeonCell, world_x: float, world_y: float, attribute: DungeonAttribute):
        """壁セル描画"""
        if not self.enabled:
            return
        
        # 壁の色を属性に基づいて決定
        wall_color = self._get_attribute_color(attribute, 0.6)
        
        # 立方体で壁を作成（簡易実装）
        from panda3d.core import CardMaker
        
        # 6面を個別に作成
        for i, (offset, hpr) in enumerate([
            ((0, -1, 0), (0, 0, 0)),    # 前面
            ((0, 1, 0), (180, 0, 0)),   # 背面
            ((-1, 0, 0), (90, 0, 0)),   # 左面
            ((1, 0, 0), (-90, 0, 0)),   # 右面
            ((0, 0, 1), (0, 90, 0)),    # 上面
            ((0, 0, -1), (0, -90, 0))   # 下面
        ]):
            cm = CardMaker(f"wall_{cell.x}_{cell.y}_{i}")
            cm.setFrame(-1, 1, -1, 1)
            
            wall_card = self.render.attachNewNode(cm.generate())
            wall_card.setPos(world_x + offset[0], world_y + offset[1], 1 + offset[2])
            wall_card.setHpr(*hpr)
            wall_card.setColor(wall_color)
            
            self.wall_nodes[f"{cell.x}_{cell.y}_{i}"] = wall_card
    
    def _render_floor(self, cell: DungeonCell, world_x: float, world_y: float, attribute: DungeonAttribute):
        """床描画"""
        if not self.enabled:
            return
        
        floor_color = self._get_attribute_color(attribute, 0.3)
        
        cm = CardMaker(f"floor_{cell.x}_{cell.y}")
        cm.setFrame(-1, 1, -1, 1)
        
        floor_card = self.render.attachNewNode(cm.generate())
        floor_card.setPos(world_x, world_y, 0)
        floor_card.setHpr(0, -90, 0)  # 水平に配置
        floor_card.setColor(floor_color)
        
        self.floor_nodes[f"{cell.x}_{cell.y}"] = floor_card
    
    def _render_ceiling(self, cell: DungeonCell, world_x: float, world_y: float, attribute: DungeonAttribute):
        """天井描画"""
        if not self.enabled:
            return
        
        ceiling_color = self._get_attribute_color(attribute, 0.2)
        
        cm = CardMaker(f"ceiling_{cell.x}_{cell.y}")
        cm.setFrame(-1, 1, -1, 1)
        
        ceiling_card = self.render.attachNewNode(cm.generate())
        ceiling_card.setPos(world_x, world_y, 2)
        ceiling_card.setHpr(0, 90, 0)  # 水平に配置（上向き）
        ceiling_card.setColor(ceiling_color)
        
        self.ceiling_nodes[f"{cell.x}_{cell.y}"] = ceiling_card
    
    def _render_wall(self, cell: DungeonCell, world_x: float, world_y: float, direction: Direction, attribute: DungeonAttribute):
        """壁描画"""
        if not self.enabled:
            return
        
        wall_color = self._get_attribute_color(attribute, 0.5)
        
        # 方向に基づいて壁の位置と向きを決定
        offset, hpr = self._get_wall_transform(direction)
        
        cm = CardMaker(f"wall_{cell.x}_{cell.y}_{direction.value}")
        cm.setFrame(-1, 1, 0, 2)  # 高さ2ユニットの壁
        
        wall_card = self.render.attachNewNode(cm.generate())
        wall_card.setPos(world_x + offset[0], world_y + offset[1], offset[2])
        wall_card.setHpr(*hpr)
        wall_card.setColor(wall_color)
        
        self.wall_nodes[f"{cell.x}_{cell.y}_{direction.value}"] = wall_card
    
    def _render_props(self, level: DungeonLevel, player_pos: PlayerPosition):
        """プロップ（階段、宝箱など）描画"""
        if not self.enabled:
            return
        
        render_range = 5
        
        for x in range(max(0, player_pos.x - render_range),
                      min(level.width, player_pos.x + render_range + 1)):
            for y in range(max(0, player_pos.y - render_range),
                          min(level.height, player_pos.y + render_range + 1)):
                
                cell = level.get_cell(x, y)
                if not cell:
                    continue
                
                world_x = cell.x * 2.0
                world_y = -cell.y * 2.0
                
                # 階段描画
                if cell.cell_type == CellType.STAIRS_UP:
                    self._render_stairs(cell, world_x, world_y, True)
                elif cell.cell_type == CellType.STAIRS_DOWN:
                    self._render_stairs(cell, world_x, world_y, False)
                
                # 宝箱描画
                if cell.has_treasure:
                    self._render_treasure(cell, world_x, world_y)
    
    def _render_stairs(self, cell: DungeonCell, world_x: float, world_y: float, is_up: bool):
        """階段描画"""
        if not self.enabled:
            return
        
        color = Vec4(0.8, 0.8, 0.6, 1) if is_up else Vec4(0.6, 0.6, 0.8, 1)
        
        cm = CardMaker(f"stairs_{cell.x}_{cell.y}")
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        
        stairs_card = self.render.attachNewNode(cm.generate())
        stairs_card.setPos(world_x, world_y, 0.1)
        stairs_card.setHpr(0, -90, 0)
        stairs_card.setColor(color)
        
        self.prop_nodes[f"stairs_{cell.x}_{cell.y}"] = stairs_card
    
    def _render_treasure(self, cell: DungeonCell, world_x: float, world_y: float):
        """宝箱描画"""
        if not self.enabled:
            return
        
        color = Vec4(0.8, 0.6, 0.2, 1)  # 金色
        
        cm = CardMaker(f"treasure_{cell.x}_{cell.y}")
        cm.setFrame(-0.3, 0.3, 0, 0.3)
        
        treasure_card = self.render.attachNewNode(cm.generate())
        treasure_card.setPos(world_x, world_y, 0.1)
        treasure_card.setColor(color)
        
        self.prop_nodes[f"treasure_{cell.x}_{cell.y}"] = treasure_card
    
    def _get_attribute_color(self, attribute: DungeonAttribute, brightness: float) -> Vec4:
        """属性に基づいた色を取得"""
        color_map = {
            DungeonAttribute.PHYSICAL: Vec4(0.7, 0.7, 0.7, 1),      # グレー
            DungeonAttribute.FIRE: Vec4(1.0, 0.4, 0.2, 1),          # 赤
            DungeonAttribute.ICE: Vec4(0.6, 0.8, 1.0, 1),           # 青
            DungeonAttribute.LIGHTNING: Vec4(1.0, 1.0, 0.4, 1),     # 黄
            DungeonAttribute.DARK: Vec4(0.4, 0.2, 0.4, 1),          # 紫
            DungeonAttribute.LIGHT: Vec4(1.0, 1.0, 0.8, 1)          # 白
        }
        
        base_color = color_map.get(attribute, Vec4(0.5, 0.5, 0.5, 1))
        return Vec4(base_color.x * brightness, base_color.y * brightness, 
                   base_color.z * brightness, base_color.w)
    
    def _get_wall_transform(self, direction: Direction) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """壁の変換情報を取得"""
        transforms = {
            Direction.NORTH: ((0, -1, 1), (0, 0, 0)),
            Direction.SOUTH: ((0, 1, 1), (180, 0, 0)),
            Direction.EAST: ((1, 0, 1), (-90, 0, 0)),
            Direction.WEST: ((-1, 0, 1), (90, 0, 0))
        }
        return transforms[direction]
    
    def _direction_to_heading(self, direction: Direction) -> float:
        """方向をヘディング角に変換"""
        headings = {
            Direction.NORTH: 0,
            Direction.EAST: -90,
            Direction.SOUTH: 180,
            Direction.WEST: 90
        }
        return headings[direction]
    
    def _update_ui(self, dungeon_state: DungeonState):
        """UI更新"""
        if not self.enabled:
            return
        
        pos = dungeon_state.player_position
        if not pos:
            return
        
        # コンパス更新
        compass_text = {
            Direction.NORTH: 'N',
            Direction.EAST: 'E', 
            Direction.SOUTH: 'S',
            Direction.WEST: 'W'
        }
        self.ui_elements['compass'].setText(compass_text[pos.facing])
        
        # 位置情報更新
        position_text = config_manager.get_text("dungeon.position_display").format(x=pos.x, y=pos.y, level=pos.level)
        self.ui_elements['position'].setText(position_text)
    
    # 移動・回転ハンドラー
    def _move_forward(self):
        """前進"""
        if self.dungeon_manager and self.dungeon_manager.current_dungeon:
            facing = self.dungeon_manager.current_dungeon.player_position.facing
            success, message = self.dungeon_manager.move_player(facing)
            if success:
                self.render_dungeon(self.dungeon_manager.current_dungeon)
                self.update_ui()
    
    def _move_backward(self):
        """後退"""
        if self.dungeon_manager and self.dungeon_manager.current_dungeon:
            facing = self.dungeon_manager.current_dungeon.player_position.facing
            # 後退は前進の逆方向
            opposite = {
                Direction.NORTH: Direction.SOUTH,
                Direction.SOUTH: Direction.NORTH,
                Direction.EAST: Direction.WEST,
                Direction.WEST: Direction.EAST
            }
            success, message = self.dungeon_manager.move_player(opposite[facing])
            if success:
                self.render_dungeon(self.dungeon_manager.current_dungeon)
                self.update_ui()
    
    def _move_left(self):
        """左移動"""
        if self.dungeon_manager and self.dungeon_manager.current_dungeon:
            facing = self.dungeon_manager.current_dungeon.player_position.facing
            # 左移動は現在の向きから左方向
            left = {
                Direction.NORTH: Direction.WEST,
                Direction.WEST: Direction.SOUTH,
                Direction.SOUTH: Direction.EAST,
                Direction.EAST: Direction.NORTH
            }
            success, message = self.dungeon_manager.move_player(left[facing])
            if success:
                self.render_dungeon(self.dungeon_manager.current_dungeon)
                self.update_ui()
    
    def _move_right(self):
        """右移動"""
        if self.dungeon_manager and self.dungeon_manager.current_dungeon:
            facing = self.dungeon_manager.current_dungeon.player_position.facing
            # 右移動は現在の向きから右方向
            right = {
                Direction.NORTH: Direction.EAST,
                Direction.EAST: Direction.SOUTH,
                Direction.SOUTH: Direction.WEST,
                Direction.WEST: Direction.NORTH
            }
            success, message = self.dungeon_manager.move_player(right[facing])
            if success:
                self.render_dungeon(self.dungeon_manager.current_dungeon)
                self.update_ui()
    
    def _turn_left(self):
        """左回転"""
        if self.dungeon_manager and self.dungeon_manager.current_dungeon:
            facing = self.dungeon_manager.current_dungeon.player_position.facing
            left = {
                Direction.NORTH: Direction.WEST,
                Direction.WEST: Direction.SOUTH,
                Direction.SOUTH: Direction.EAST,
                Direction.EAST: Direction.NORTH
            }
            self.dungeon_manager.turn_player(left[facing])
            self.render_dungeon(self.dungeon_manager.current_dungeon)
            self.update_ui()
    
    def _turn_right(self):
        """右回転"""
        if self.dungeon_manager and self.dungeon_manager.current_dungeon:
            facing = self.dungeon_manager.current_dungeon.player_position.facing
            right = {
                Direction.NORTH: Direction.EAST,
                Direction.EAST: Direction.SOUTH,
                Direction.SOUTH: Direction.WEST,
                Direction.WEST: Direction.NORTH
            }
            self.dungeon_manager.turn_player(right[facing])
            self.render_dungeon(self.dungeon_manager.current_dungeon)
            self.update_ui()
    
    def _show_menu(self):
        """メニュー表示"""
        if hasattr(self, 'ui_manager') and self.ui_manager:
            self.ui_manager.toggle_main_menu()
        else:
            logger.info("メニュー表示（UIマネージャー未初期化）")
    
    def _return_to_overworld(self):
        """地上部に帰還"""
        if self.dungeon_manager and hasattr(self.dungeon_manager, 'return_to_overworld'):
            success = self.dungeon_manager.return_to_overworld()
            if success:
                logger.info("地上部への帰還が完了しました")
            else:
                logger.error("地上部への帰還に失敗しました")
        else:
            logger.error("地上部帰還: ダンジョンマネージャーが設定されていません")
    
    def set_game_manager(self, game_manager):
        """ゲームマネージャーを設定"""
        if hasattr(self, 'ui_manager') and self.ui_manager:
            self.ui_manager.set_managers(self.dungeon_manager, game_manager)
        logger.debug("ゲームマネージャーを設定しました")
    
    def update_ui(self):
        """UI情報を更新"""
        if not hasattr(self, 'ui_manager') or not self.ui_manager or not self.dungeon_manager:
            return
        
        # 位置情報更新
        if (self.dungeon_manager.current_dungeon and 
            self.dungeon_manager.current_dungeon.player_position):
            pos = self.dungeon_manager.current_dungeon.player_position
            location_info = f"({pos.x}, {pos.y}) レベル: {pos.level}"
            self.ui_manager.update_location(location_info)
            
            # 既存のUI要素も更新
            if 'position' in self.ui_elements:
                self.ui_elements['position'].setText(config_manager.get_text("dungeon.position_info").format(location_info=location_info))
        
        # パーティステータス更新
        self.ui_manager.update_party_status()


# グローバルインスタンス
dungeon_renderer = None

def create_renderer() -> Optional[DungeonRenderer]:
    """レンダラー作成"""
    global dungeon_renderer
    if not dungeon_renderer:
        dungeon_renderer = DungeonRenderer()
    return dungeon_renderer if dungeon_renderer.enabled else None