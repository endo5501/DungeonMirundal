"""ダンジョン選択ウィンドウ

WindowSystemベースのダンジョン選択UI
"""

import pygame
import pygame_gui
from typing import Dict, List, Any, Optional, Callable
import hashlib
import random
from datetime import datetime

from .window import Window, WindowState
from src.utils.logger import logger


class DungeonInfo:
    """ダンジョン情報データクラス"""
    
    def __init__(self, hash_value: str, difficulty: int, floors: int, explored: bool = False):
        self.hash_value = hash_value
        self.difficulty = difficulty
        self.floors = floors
        self.explored = explored
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'hash_value': self.hash_value,
            'difficulty': self.difficulty,
            'floors': self.floors,
            'explored': self.explored,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DungeonInfo':
        """辞書から復元"""
        instance = cls(
            hash_value=data['hash_value'],
            difficulty=data['difficulty'],
            floors=data['floors'],
            explored=data.get('explored', False)
        )
        if 'created_at' in data:
            instance.created_at = datetime.fromisoformat(data['created_at'])
        return instance


class DungeonSelectionWindow(Window):
    """ダンジョン選択ウィンドウ
    
    WindowSystemベースのダンジョン選択UI
    仕様:
    - ダンジョン一覧UIと[選択]、[新規作成]、[削除]、[街に戻る]ボタン表示
    - ダンジョン一覧：ハッシュ値、難易度、階数、探索済みかどうかを表示
    - [選択]: 選択中のハッシュ値から生成されるダンジョンに遷移
    - [新規作成]: ランダムなハッシュ値、難易度、階数を一覧に登録
    - [削除]: 選択中のダンジョンを削除
    - [街に戻る]: 地上メニューに戻る
    """
    
    def __init__(self, window_id: str = "dungeon_selection", parent: Optional[Window] = None):
        """ダンジョン選択ウィンドウを初期化"""
        super().__init__(window_id, parent, modal=True)
        
        self.selected_index = 0
        
        # ダンジョンリスト
        self.dungeons: List[DungeonInfo] = []
        
        # コールバック
        self.on_dungeon_selected: Optional[Callable[[str], None]] = None
        self.on_cancelled: Optional[Callable[[], None]] = None
        
        # GameManagerの参照
        self.game_manager = None
        
        # UI要素
        self.container: Optional[pygame_gui.elements.UIPanel] = None
        self.title_label: Optional[pygame_gui.elements.UILabel] = None
        self.dungeon_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.select_button: Optional[pygame_gui.elements.UIButton] = None
        self.create_button: Optional[pygame_gui.elements.UIButton] = None
        self.delete_button: Optional[pygame_gui.elements.UIButton] = None
        self.back_button: Optional[pygame_gui.elements.UIButton] = None
        
        # GameManagerの参照を取得
        self._get_game_manager()
        
        logger.info("DungeonSelectionWindowを初期化しました")
    
    def _get_game_manager(self):
        """GameManagerの参照を取得"""
        try:
            # main.pyからGameManagerを取得
            import main
            if hasattr(main, 'game_manager') and main.game_manager:
                self.game_manager = main.game_manager
                logger.info("GameManagerの参照を取得しました")
                # セーブデータからダンジョン一覧を読み込み
                self._load_dungeons_from_save()
            else:
                logger.warning("GameManagerが見つかりません")
        except Exception as e:
            logger.error(f"GameManager取得エラー: {e}")
    
    def _load_dungeons_from_save(self):
        """セーブデータからダンジョン一覧を読み込み"""
        if not self.game_manager:
            return
        
        try:
            dungeon_data_list = self.game_manager.get_dungeon_list()
            self.dungeons = []
            
            for dungeon_data in dungeon_data_list:
                dungeon_info = DungeonInfo.from_dict(dungeon_data)
                self.dungeons.append(dungeon_info)
            
            logger.info(f"セーブデータから {len(self.dungeons)} のダンジョンを読み込みました")
        except Exception as e:
            logger.error(f"ダンジョン一覧読み込みエラー: {e}")
    
    def hide_ui_elements(self) -> None:
        """UI要素を非表示にする"""
        if self.container:
            self.container.visible = False
        logger.debug(f"DungeonSelectionWindow UI要素を非表示: {self.window_id}")
    
    def show_ui_elements(self) -> None:
        """UI要素を表示する"""
        if self.container:
            self.container.visible = True
        logger.debug(f"DungeonSelectionWindow UI要素を表示: {self.window_id}")
    
    def destroy_ui_elements(self) -> None:
        """UI要素を破棄する"""
        # 子要素を明示的に削除
        if self.title_label:
            self.title_label.kill()
            self.title_label = None
        
        if self.dungeon_list:
            self.dungeon_list.kill()
            self.dungeon_list = None
        
        if self.select_button:
            self.select_button.kill()
            self.select_button = None
        
        if self.create_button:
            self.create_button.kill()
            self.create_button = None
        
        if self.delete_button:
            self.delete_button.kill()
            self.delete_button = None
        
        if self.back_button:
            self.back_button.kill()
            self.back_button = None
        
        # メインコンテナを最後に削除
        if self.container:
            self.container.kill()
            self.container = None
        
        logger.debug(f"DungeonSelectionWindow UI要素を破棄: {self.window_id}")
    
    def set_callbacks(self, on_selected: Callable[[str], None], on_cancelled: Callable[[], None]):
        """コールバックを設定
        
        Args:
            on_selected: ダンジョン選択時のコールバック
            on_cancelled: キャンセル時のコールバック
        """
        self.on_dungeon_selected = on_selected
        self.on_cancelled = on_cancelled
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            self.ui_manager = window_manager.ui_manager
        
        if not self.ui_manager:
            logger.error("UIManagerが取得できませんでした")
            return
        
        # ウィンドウのサイズと位置
        window_rect = pygame.Rect(150, 100, 700, 500)
        self.rect = window_rect
        
        # メインコンテナパネル
        self.container = pygame_gui.elements.UIPanel(
            relative_rect=window_rect,
            starting_height=2,
            manager=self.ui_manager,
            object_id="#dungeon_selection_panel"
        )
        
        # タイトルラベル
        title_rect = pygame.Rect(20, 20, 660, 40)
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="ダンジョン選択",
            manager=self.ui_manager,
            container=self.container,
            object_id="#dungeon_selection_title"
        )
        
        # ダンジョンリスト（上部）
        list_rect = pygame.Rect(20, 70, 660, 300)
        self.dungeon_list = pygame_gui.elements.UISelectionList(
            relative_rect=list_rect,
            item_list=self._get_dungeon_list_items(),
            manager=self.ui_manager,
            container=self.container,
            object_id="#dungeon_list"
        )
        
        # ボタン（下部）
        button_width = 150
        button_height = 40
        button_y = 400
        button_spacing = 20
        
        # [選択]ボタン
        select_rect = pygame.Rect(20, button_y, button_width, button_height)
        self.select_button = pygame_gui.elements.UIButton(
            relative_rect=select_rect,
            text="選択",
            manager=self.ui_manager,
            container=self.container,
            object_id="#select_dungeon_button"
        )
        
        # [新規作成]ボタン
        create_x = 20 + button_width + button_spacing
        create_rect = pygame.Rect(create_x, button_y, button_width, button_height)
        self.create_button = pygame_gui.elements.UIButton(
            relative_rect=create_rect,
            text="新規作成",
            manager=self.ui_manager,
            container=self.container,
            object_id="#create_dungeon_button"
        )
        
        # [削除]ボタン
        delete_x = create_x + button_width + button_spacing
        delete_rect = pygame.Rect(delete_x, button_y, button_width, button_height)
        self.delete_button = pygame_gui.elements.UIButton(
            relative_rect=delete_rect,
            text="削除",
            manager=self.ui_manager,
            container=self.container,
            object_id="#delete_dungeon_button"
        )
        
        # [街に戻る]ボタン
        back_x = delete_x + button_width + button_spacing
        back_rect = pygame.Rect(back_x, button_y, button_width, button_height)
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=back_rect,
            text="街に戻る",
            manager=self.ui_manager,
            container=self.container,
            object_id="#back_to_town_button"
        )
        
        self._update_button_states()
        
        # デバッグ: ボタンの状態を確認
        logger.info(f"新規作成ボタン状態: visible={self.create_button.visible}, enabled={self.create_button.is_enabled}")
        logger.info(f"街に戻るボタン状態: visible={self.back_button.visible}, enabled={self.back_button.is_enabled}")
        logger.info(f"選択ボタン状態: visible={self.select_button.visible}, enabled={self.select_button.is_enabled}")
        
        self.state = WindowState.SHOWN
        logger.info("DungeonSelectionWindowのUI要素を作成しました")
    
    def destroy(self) -> None:
        """UI要素を破棄"""
        # 親クラスのdestroyを呼び出してUI要素を完全に破棄
        super().destroy()
        logger.info("DungeonSelectionWindowのUI要素を破棄しました")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理
        
        Args:
            event: Pygameイベント
            
        Returns:
            bool: イベントが処理された場合True
        """
        if self.state != WindowState.SHOWN:
            return False
        
        # デバッグ: イベント検出をログ
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            logger.info(f"DungeonSelectionWindow: UI_BUTTON_PRESSED検出: {event.ui_element}")
        
        # pygame-guiイベント処理
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.select_button:
                logger.info("選択ボタンがクリックされました")
                self._on_select_dungeon()
                return True
            elif event.ui_element == self.create_button:
                logger.info("新規作成ボタンがクリックされました")
                self._on_create_dungeon()
                return True
            elif event.ui_element == self.delete_button:
                logger.info("削除ボタンがクリックされました")
                self._on_delete_dungeon()
                return True
            elif event.ui_element == self.back_button:
                logger.info("街に戻るボタンがクリックされました")
                self._on_back_to_town()
                return True
        
        elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.dungeon_list:
                selection = self.dungeon_list.get_single_selection()
                if selection:
                    # 選択されたアイテムのインデックスを取得
                    try:
                        self.selected_index = self.dungeon_list.item_list.index(selection)
                        logger.info(f"ダンジョン選択変更: インデックス={self.selected_index}, アイテム={selection}")
                    except ValueError:
                        # アイテムが見つからない場合
                        self.selected_index = 0
                        logger.warning(f"選択されたアイテムが見つかりません: {selection}")
                else:
                    self.selected_index = None
                
                self._update_button_states()
                return True
        
        return False
    
    def handle_escape(self) -> bool:
        """ESCキーの処理"""
        logger.info("ESCキーでダンジョン選択ウィンドウを閉じます")
        self._on_back_to_town()
        return True
    
    def _get_dungeon_list_items(self) -> List[str]:
        """ダンジョンリスト表示用の文字列を生成"""
        items = []
        for i, dungeon in enumerate(self.dungeons):
            explored_text = "探索済み" if dungeon.explored else "未探索"
            item_text = f"{i+1}. {dungeon.hash_value[:8]}... 難易度: {dungeon.difficulty} 階数: {dungeon.floors}F {explored_text}"
            items.append(item_text)
        
        if not items:
            items.append("ダンジョンがありません。新規作成してください。")
        
        return items
    
    def _update_button_states(self):
        """ボタンの有効/無効状態を更新"""
        has_dungeons = len(self.dungeons) > 0
        
        if self.select_button:
            self.select_button.enable() if has_dungeons else self.select_button.disable()
        if self.delete_button:
            self.delete_button.enable() if has_dungeons else self.delete_button.disable()
    
    def _generate_random_dungeon(self) -> DungeonInfo:
        """ランダムダンジョンを生成"""
        # ランダムハッシュ値生成
        random_seed = f"{datetime.now().isoformat()}_{random.randint(1000, 9999)}"
        hash_value = hashlib.md5(random_seed.encode()).hexdigest()
        
        # ランダム難易度（1-10）
        difficulty = random.randint(1, 10)
        
        # ランダム階数（難易度に応じて調整、5-25階）
        min_floors = max(5, difficulty)
        max_floors = max(min_floors, min(25, difficulty * 3))
        floors = random.randint(min_floors, max_floors)
        
        return DungeonInfo(hash_value, difficulty, floors)
    
    def _on_select_dungeon(self):
        """ダンジョン選択処理"""
        if not self.dungeons:
            logger.warning("選択可能なダンジョンがありません")
            return
        
        if self.selected_index is None or self.selected_index >= len(self.dungeons):
            self.selected_index = 0
        
        selected_dungeon = self.dungeons[self.selected_index]
        logger.info(f"ダンジョン選択: {selected_dungeon.hash_value}")
        
        # WindowManagerで適切に破棄する
        from src.ui.window_system import WindowManager
        window_manager = WindowManager.get_instance()
        window_manager.close_window(self)
        
        if self.on_dungeon_selected:
            self.on_dungeon_selected(selected_dungeon.hash_value)
    
    def _on_create_dungeon(self):
        """新規ダンジョン作成処理"""
        new_dungeon = self._generate_random_dungeon()
        self.dungeons.append(new_dungeon)
        
        logger.info(f"新規ダンジョン作成: ハッシュ={new_dungeon.hash_value[:8]}..., 難易度={new_dungeon.difficulty}, 階数={new_dungeon.floors}")
        
        # セーブデータに保存
        if self.game_manager:
            dungeon_dict = new_dungeon.to_dict()
            success = self.game_manager.add_dungeon_to_list(dungeon_dict)
            if success:
                logger.info("ダンジョン情報をセーブデータに保存しました")
            else:
                logger.warning("ダンジョン情報の保存に失敗しました")
        
        # リスト更新
        if self.dungeon_list:
            self.dungeon_list.set_item_list(self._get_dungeon_list_items())
        
        self._update_button_states()
    
    def _on_delete_dungeon(self):
        """ダンジョン削除処理"""
        if not self.dungeons:
            logger.warning("削除可能なダンジョンがありません")
            return
        
        if self.selected_index is None or self.selected_index >= len(self.dungeons):
            self.selected_index = 0
        
        deleted_dungeon = self.dungeons.pop(self.selected_index)
        logger.info(f"ダンジョン削除: {deleted_dungeon.hash_value[:8]}...")
        
        # セーブデータからも削除
        if self.game_manager:
            success = self.game_manager.remove_dungeon_from_list(deleted_dungeon.hash_value)
            if success:
                logger.info("ダンジョン情報をセーブデータから削除しました")
            else:
                logger.warning("ダンジョン情報の削除に失敗しました")
        
        # 選択インデックス調整
        if self.selected_index >= len(self.dungeons) and self.dungeons:
            self.selected_index = len(self.dungeons) - 1
        
        # リスト更新
        if self.dungeon_list:
            self.dungeon_list.set_item_list(self._get_dungeon_list_items())
        
        self._update_button_states()
    
    def _on_back_to_town(self):
        """街に戻る処理"""
        logger.info("街に戻ります")
        
        # WindowManagerで適切に破棄する
        from src.ui.window_system import WindowManager
        window_manager = WindowManager.get_instance()
        window_manager.close_window(self)
        
        if self.on_cancelled:
            self.on_cancelled()
    
    def update(self, time_delta: float) -> None:
        """更新処理
        
        Args:
            time_delta: フレーム間の時間差
        """
        # 現在は特に処理なし
        pass