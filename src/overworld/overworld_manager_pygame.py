"""地上部管理システム（Pygame版）"""

from typing import Optional, Callable
import pygame
from src.character.party import Party
from src.ui.base_ui_pygame import UIButton, UIText  # UIMenu: Phase 4.5で削除
from src.ui.selection_list_ui import CustomSelectionList, SelectionListData
# from src.ui.menu_stack_manager import MenuStackManager, MenuType  # WindowSystem移行により削除
from src.ui.character_status_bar import CharacterStatusBar, create_character_status_bar
from src.ui.window_system.overworld_main_window import OverworldMainWindow
from src.ui.window_system import WindowManager
from src.utils.logger import logger

# Pygame地上部システム定数
MAIN_MENU_BUTTON_WIDTH = 200
MAIN_MENU_BUTTON_HEIGHT = 50
MAIN_MENU_LEFT_COLUMN_X = 150
MAIN_MENU_RIGHT_COLUMN_X = 450
MAIN_MENU_BUTTON_SPACING = 70
MAIN_MENU_START_Y = 200
SETTINGS_BUTTON_X = 250
SETTINGS_BUTTON_WIDTH = 300
SETTINGS_BUTTON_HEIGHT = 50
SETTINGS_BUTTON_SPACING = 70
SETTINGS_START_Y = 200
DUNGEON_SELECTION_RECT_X = 100
DUNGEON_SELECTION_RECT_Y = 100
DUNGEON_SELECTION_RECT_WIDTH = 600
DUNGEON_SELECTION_RECT_HEIGHT = 500
DIALOG_BUTTON_WIDTH = 100
DIALOG_BUTTON_HEIGHT = 40
DIALOG_BUTTON_MARGIN = 60
MAX_PARTY_MEMBERS_DISPLAY = 5
MAX_SAVE_SLOTS = 5
SAVE_SLOT_RANGE_START = 1
SAVE_SLOT_RANGE_END = 6
JAPANESE_FONT_SIZE = 24
TITLE_Y_OFFSET = 80
HELP_Y_OFFSET = 120


class OverworldManager:
    """地上部管理クラス（Pygame版）"""
    
    def __init__(self):
        self.current_party: Optional[Party] = None
        self.ui_manager = None
        self.input_manager = None
        
        # コールバック
        self.enter_dungeon_callback: Optional[Callable] = None
        self.exit_game_callback: Optional[Callable] = None
        
        # UI要素（レガシーUIMenuは段階的削除により使用停止）
        # self.main_menu: Optional[UIMenu] = None  # WindowSystem移行により削除
        # self.settings_menu: Optional[UIMenu] = None  # WindowSystem移行により削除
        self.dungeon_selection_list: Optional[CustomSelectionList] = None
        self.is_active = False
        self.settings_active = False
        
        # MenuStackManager削除（WindowSystemへ移行）
        # self.menu_stack_manager: Optional[MenuStackManager] = None
        
        # キャラクターステータスバー
        self.character_status_bar: Optional[CharacterStatusBar] = None
        
        logger.info("OverworldManager（Pygame版）を初期化しました")
    
    def set_ui_manager(self, ui_manager):
        """UIマネージャーを設定"""
        self.ui_manager = ui_manager
        
        # WindowManagerを取得
        self.window_manager = WindowManager.get_instance()
        
        # MenuStackManagerの初期化を削除（WindowSystemへ完全移行）
        # self.menu_stack_manager = MenuStackManager(ui_manager)
        # self.menu_stack_manager.on_escape_pressed = self._handle_escape_from_menu_stack
        
        # 新WindowManagerベースのメインメニューを作成
        self._create_window_based_main_menu()
        
        # レガシーメニューは削除（WindowSystem完全移行）
        # self._create_main_menu()  # WindowSystem移行により削除
        # self._create_settings_menu()  # WindowSystem移行により削除
        self.setup_facility_callbacks()
        
        # キャラクターステータスバーを初期化
        self._initialize_character_status_bar()
        
        # FacilityManagerにもUIマネージャーを設定
        from src.overworld.base_facility import facility_manager
        facility_manager.set_ui_manager(ui_manager)
    
    def set_input_manager(self, input_manager):
        """入力マネージャーを設定"""
        self.input_manager = input_manager
    
    def set_enter_dungeon_callback(self, callback: Callable):
        """ダンジョン入場コールバックを設定"""
        self.enter_dungeon_callback = callback
    
    def set_exit_game_callback(self, callback: Callable):
        """ゲーム終了コールバックを設定"""
        self.exit_game_callback = callback
    
    def setup_facility_callbacks(self):
        """FacilityManagerのコールバックを設定"""
        try:
            from src.overworld.base_facility import facility_manager
            facility_manager.set_facility_exit_callback(self.on_facility_exit)
        except Exception as e:
            logger.error(f"FacilityManagerコールバック設定エラー: {e}")
    
    def on_facility_exit(self):
        """施設退場時のコールバック"""
        logger.info("施設から地上部に戻りました")
        
        # 統一化されたメインメニュー表示を使用
        self._show_main_menu_unified()
    
    def _create_window_based_main_menu(self):
        """WindowManagerベースのメインメニューを作成"""
        try:
            # メインメニュー設定を作成
            menu_config = self._create_main_menu_config()
            
            # OverworldMainWindowを作成
            self.overworld_main_window = OverworldMainWindow("overworld_main", menu_config)
            
            # メッセージハンドラーを設定
            self.overworld_main_window.message_handler = self.handle_main_menu_message
            
            logger.info("WindowManagerベースのメインメニューを作成しました")
        except Exception as e:
            logger.error(f"WindowManagerベースのメインメニュー作成エラー: {e}")
            self.overworld_main_window = None
    
    def _create_main_menu_config(self):
        """メインメニュー設定を作成（OverworldMainWindow用）"""
        from src.core.config_manager import config_manager
        
        menu_items = [
            {
                'id': 'guild',
                'label': config_manager.get_text("facility.guild"),
                'type': 'facility',
                'facility_id': 'guild',
                'enabled': True
            },
            {
                'id': 'inn',
                'label': config_manager.get_text("facility.inn"),
                'type': 'facility',
                'facility_id': 'inn',
                'enabled': True
            },
            {
                'id': 'shop',
                'label': config_manager.get_text("facility.shop"),
                'type': 'facility',
                'facility_id': 'shop',
                'enabled': True
            },
            {
                'id': 'temple',
                'label': config_manager.get_text("facility.temple"),
                'type': 'facility',
                'facility_id': 'temple',
                'enabled': True
            },
            {
                'id': 'magic_guild',
                'label': config_manager.get_text("facility.magic_guild"),
                'type': 'facility',
                'facility_id': 'magic_guild',
                'enabled': True
            },
            {
                'id': 'dungeon_entrance',
                'label': "ダンジョン入口",  # TODO: 翻訳ファイルに追加予定
                'type': 'action',
                'enabled': True
            }
        ]
        
        return {
            'menu_type': 'main',
            'title': config_manager.get_text("overworld.surface_map"),
            'menu_items': menu_items,
            'party': self.current_party,
            'show_party_info': True,
            'show_gold': True
        }
    
    def _create_settings_menu_config(self):
        """設定メニュー設定を作成（OverworldMainWindow用）"""
        from src.core.config_manager import config_manager
        
        categories = [
            {
                'id': 'game_menu',
                'name': config_manager.get_text("menu.settings"),
                'fields': [
                    {
                        'id': 'party_status',
                        'name': config_manager.get_text("menu.party_status"),
                        'type': 'action',
                        'enabled': self.current_party is not None,
                        'action': 'party_status'
                    },
                    {
                        'id': 'save_game',
                        'name': config_manager.get_text("menu.save_game"),
                        'type': 'action',
                        'enabled': self.current_party is not None,
                        'action': 'save_game'
                    },
                    {
                        'id': 'load_game',
                        'name': config_manager.get_text("menu.load_game"),
                        'type': 'action',
                        'enabled': True,
                        'action': 'load_game'
                    },
                    {
                        'id': 'back',
                        'name': config_manager.get_text("menu.back"),
                        'type': 'action',
                        'enabled': True,
                        'action': 'back'
                    }
                ]
            }
        ]
        
        return {
            'menu_type': 'settings',
            'categories': categories,
            'title': config_manager.get_text("menu.settings"),
            'party': self.current_party
        }
    
    def handle_main_menu_message(self, message_type: str, data: dict) -> bool:
        """メインメニューメッセージ処理（OverworldMainWindow用）"""
        logger.debug(f"handle_main_menu_message: {message_type}, data: {data}")
        
        if message_type == 'menu_item_selected':
            item_id = data.get('item_id')
            facility_id = data.get('facility_id')
            
            if facility_id:
                # 施設入場
                if facility_id == 'guild':
                    self._on_guild()
                elif facility_id == 'inn':
                    self._on_inn()
                elif facility_id == 'shop':
                    self._on_shop()
                elif facility_id == 'temple':
                    self._on_temple()
                elif facility_id == 'magic_guild':
                    self._on_magic_guild()
                else:
                    logger.warning(f"未知の施設: {facility_id}")
                    return False
                return True
            elif item_id == 'dungeon_entrance':
                # ダンジョン入場
                self._on_enter_dungeon()
                return True
            elif item_id in ['party_status', 'save_game', 'load_game']:
                # 設定メニューから選択された項目
                if item_id == 'party_status':
                    self._on_party_status()
                    return True
                elif item_id == 'save_game':
                    self._on_save_game()
                    return True
                elif item_id == 'load_game':
                    self._on_load_game()
                    return True
        
        elif message_type == 'settings_menu_requested':
            # ESCキーでの設定メニュー表示
            self._show_settings_menu()
            return True
        
        elif message_type == 'party_overview_requested':
            # パーティ全体情報表示
            self._on_party_status()
            return True
        
        elif message_type == 'character_details_requested':
            # キャラクター詳細表示（簡易実装）
            character = data.get('character')
            if character:
                logger.info(f"キャラクター詳細表示: {character.name}")
                # TODO: 詳細なキャラクター情報ダイアログの実装
            return True
        
        elif message_type == 'save_load_requested':
            # セーブ・ロード処理
            operation = data.get('operation')
            slot_id = data.get('slot_id')
            if operation == 'save':
                self._save_to_slot(slot_id)
                return True
            elif operation == 'load':
                self._load_from_slot(slot_id)
                return True
        
        elif message_type == 'back_requested':
            # 戻る処理（通常はメインメニューに戻る）
            return True
        
        logger.warning(f"未処理のメッセージタイプ: {message_type}")
        return False
    
    def _handle_overworld_action(self, message_type: str, data: dict):
        """地上部メニューのアクション処理"""
        logger.debug(f"OverworldManager: アクション処理: {message_type}, {data}")
        action = data.get('action')
        
        if action and action.startswith('enter_facility:'):
            # 施設入場処理
            facility_id = action.split(':', 1)[1]
            self._enter_facility_window_manager(facility_id)
        elif action == 'enter_dungeon':
            # ダンジョン入場処理
            self._on_enter_dungeon()
        elif action == 'show_settings':
            # 設定画面表示
            self._show_settings_window_manager()
        elif action == 'save_game':
            # セーブ処理
            self._save_game()
        elif action == 'load_game':
            # ロード処理
            self._load_game()
        elif action == 'exit_game':
            # ゲーム終了処理
            self._exit_game()
        else:
            logger.warning(f"OverworldManager: 未知のアクション: {action}")
    
    def _enter_facility_window_manager(self, facility_id: str):
        """WindowManager経由で施設に入場"""
        logger.debug(f"WindowManager経由で施設入場: {facility_id}")
        # 既存の施設入場処理を流用
        if facility_id == 'guild':
            self._on_guild()
        elif facility_id == 'inn':
            self._on_inn()
        elif facility_id == 'shop':
            self._on_shop()
        elif facility_id == 'temple':
            self._on_temple()
        elif facility_id == 'magic_guild':
            self._on_magic_guild()
    
    def _show_settings_window_manager(self):
        """WindowManager経由で設定画面を表示"""
        logger.debug("WindowManager経由で設定画面表示")
        # 既存の設定表示処理を流用
        self._on_settings()
    
    # === ハイブリッド実装統一化メソッド ===
    
    def _show_main_menu_unified(self):
        """統一化されたメインメニュー表示（WindowManager優先）"""
        try:
            # WindowManagerベースを優先
            if hasattr(self, 'overworld_main_window') and self.overworld_main_window:
                # ウィンドウをWindowManagerに登録（未登録の場合）
                if self.overworld_main_window.window_id not in self.window_manager.window_registry:
                    self.window_manager.window_registry[self.overworld_main_window.window_id] = self.overworld_main_window
                
                # WindowManagerで表示
                self.window_manager.show_window(self.overworld_main_window, push_to_stack=True)
                logger.info("WindowManagerベースでメインメニューを表示しました")
                return True
            else:
                logger.warning("OverworldMainWindowが利用できません、レガシーメニューを使用")
                return self._show_main_menu_legacy()
                
        except Exception as e:
            logger.error(f"WindowManagerベースメニュー表示エラー: {e}")
            return self._show_main_menu_legacy()
    
    def _show_main_menu_legacy(self):
        """レガシーメニューベースのメインメニュー表示（フォールバック）"""
        try:
            if self.main_menu:
                self.ui_manager.show_menu(self.main_menu.menu_id, modal=True)
            else:
                self._create_main_menu()
                if self.main_menu:
                    self.ui_manager.show_menu(self.main_menu.menu_id, modal=True)
            
            logger.info("レガシーメニューでメインメニューを表示しました")
            return True
            
        except Exception as e:
            logger.error(f"レガシーメニュー表示エラー: {e}")
            return False
    
    def _show_main_menu_window_manager(self):
        """WindowManagerベースのメインメニュー表示（テスト用）"""
        return self._show_main_menu_unified()
    
    def show_main_menu(self):
        """メインメニューを表示（統一化エントリーポイント）"""
        return self._show_main_menu_unified()
    
    def _cleanup_unified(self):
        """統一化されたクリーンアップ処理"""
        try:
            # WindowManagerベースのクリーンアップ
            if hasattr(self, 'window_manager') and self.window_manager:
                # アクティブウィンドウのクリーンアップ
                active_window = self.window_manager.get_active_window()
                if active_window:
                    self.window_manager.close_window(active_window.window_id)
            
            # レガシーUI要素のクリーンアップ
            if hasattr(self, 'ui_manager') and self.ui_manager:
                if hasattr(self, 'main_menu') and self.main_menu:
                    self.ui_manager.hide_menu(self.main_menu.menu_id)
                if hasattr(self, 'settings_menu') and self.settings_menu:
                    self.ui_manager.hide_menu(self.settings_menu.menu_id)
            
            # MenuStackManagerのクリーンアップ（削除済み）
            # WindowSystemへ移行により不要
            
            logger.info("統一化されたクリーンアップが完了しました")
            
        except Exception as e:
            logger.error(f"統一化クリーンアップエラー: {e}")
    
    def cleanup(self):
        """標準クリーンアップメソッド"""
        self._cleanup_unified()
    
    def _cleanup_ui(self):
        """UIクリーンアップメソッド"""
        self._cleanup_unified()
    
    def _cleanup_windows(self):
        """ウィンドウクリーンアップメソッド"""
        self._cleanup_unified()
    
    def show_main_menu_window_manager(self):
        """WindowManagerベースのメインメニューを表示"""
        if hasattr(self, 'overworld_main_window') and self.overworld_main_window:
            self.overworld_main_window.create()
            if self.overworld_main_window.window_id not in self.window_manager.window_registry:
                self.window_manager.window_registry[self.overworld_main_window.window_id] = self.overworld_main_window
            self.window_manager.show_window(self.overworld_main_window, push_to_stack=True)
            logger.info("WindowManagerベースのメインメニューを表示しました")
        else:
            logger.error("WindowManagerベースのメインメニューが作成されていません")
            # レガシーメニューにフォールバック
            if self.main_menu:
                self.ui_manager.show_menu(self.main_menu.menu_id, modal=True)
    
    def _create_main_menu(self):
        """メインメニュー作成（削除：WindowSystem移行済み）"""
        # UIMenuベースのメインメニューはPhase 4.5で削除
        # 既に_create_window_based_main_menu()でWindowSystemベースのメニューを作成済み
        logger.info("レガシーUIMenuメインメニューは削除されました（WindowSystem移行済み）")
        pass
    
    def _create_settings_menu(self):
        """設定メニュー作成（削除：WindowSystem移行済み）"""
        # UIMenuベースの設定メニューはPhase 4.5で削除
        # 既にOverworldMainWindowで設定メニュー機能を実装済み
        logger.info("レガシーUIMenu設定メニューは削除されました（WindowSystem移行済み）")
        pass
    
    def _on_enter_dungeon(self):
        """ダンジョン入場 - 選択画面を表示"""
        logger.info("ダンジョン入場が選択されました")
        self._show_dungeon_selection_menu()
    
    def _show_dungeon_selection_menu(self):
        """ダンジョン選択画面を表示"""
        logger.info("ダンジョン選択画面を表示します")
        
        if not self.ui_manager:
            logger.error("UIマネージャーが設定されていません")
            return
        
        # メインメニューを隠す
        if self.main_menu:
            self.ui_manager.hide_menu(self.main_menu.menu_id)
        
        # UISelectionListを使用したダンジョン選択
        list_rect = pygame.Rect(DUNGEON_SELECTION_RECT_X, DUNGEON_SELECTION_RECT_Y, DUNGEON_SELECTION_RECT_WIDTH, DUNGEON_SELECTION_RECT_HEIGHT)
        
        self.dungeon_selection_list = CustomSelectionList(
            relative_rect=list_rect,
            manager=self.ui_manager.pygame_gui_manager,
            title="ダンジョン選択"
        )
        
        # 戻るコールバックを設定
        self.dungeon_selection_list.on_back = self._close_dungeon_selection_menu
        
        # 生成済みダンジョン一覧のみを追加
        available_dungeons = self._get_available_dungeons()
        logger.info(f"取得したダンジョン数: {len(available_dungeons)}")
        
        if available_dungeons:
            for dungeon in available_dungeons:
                dungeon_info = self._format_dungeon_info(dungeon)
                logger.info(f"ダンジョン追加: {dungeon_info}")
                def create_callback(dungeon_id):
                    def callback():
                        logger.debug(f"ダンジョンコールバックが呼ばれました: {dungeon_id}")
                        self._enter_selected_dungeon(dungeon_id)
                    return callback
                
                dungeon_data = SelectionListData(
                    display_text=dungeon_info,
                    data=dungeon,
                    callback=create_callback(dungeon['id'])
                )
                self.dungeon_selection_list.add_item(dungeon_data)
        else:
            # ダンジョンがない場合のメッセージ
            no_dungeon_data = SelectionListData(
                display_text="生成されたダンジョンがありません",
                data=None,
                callback=None
            )
            self.dungeon_selection_list.add_item(no_dungeon_data)
        
        # 表示（戻るボタンは追加しない）
        self.dungeon_selection_list.show()
        
        logger.info("ダンジョン選択メニューを表示しました")
    
    
    def _get_available_dungeons(self):
        """利用可能なダンジョン一覧を取得"""
        # TODO: 実際のダンジョンデータストレージから取得
        # 現在は仮のデータを返す
        return [
            {
                "id": "main_dungeon",
                "name": "メインダンジョン",
                "difficulty": "Normal", 
                "attribute": "Mixed",
                "completed": False,
                "hash": "default"
            }
        ]
    
    def _format_dungeon_info(self, dungeon):
        """ダンジョン情報をフォーマット"""
        completed_text = " [踏破済み]" if dungeon.get('completed', False) else ""
        return f"{dungeon['name']} - {dungeon['difficulty']} ({dungeon['attribute']}){completed_text}"
    
    def _enter_selected_dungeon(self, dungeon_id):
        """選択されたダンジョンに入場"""
        logger.info(f"ダンジョン {dungeon_id} への入場を実行します")
        logger.debug(f"enter_dungeon_callback: {self.enter_dungeon_callback}")
        
        if self.enter_dungeon_callback:
            try:
                # ダンジョン選択リストを適切に非表示にする
                if hasattr(self, 'dungeon_selection_list') and self.dungeon_selection_list:
                    logger.debug("ダンジョン選択リストを非表示にします")
                    self.dungeon_selection_list.hide()
                    self.dungeon_selection_list.kill()
                    self.dungeon_selection_list = None
                
                self.is_active = False
                
                # ダンジョンに遷移
                logger.info(f"ダンジョン {dungeon_id} への遷移を開始します")
                self.enter_dungeon_callback(dungeon_id)
            except Exception as e:
                logger.error(f"ダンジョン入場エラー: {e}", exc_info=True)
                # エラーの場合は状態を復旧してメニューを再表示
                self.is_active = True
                self._show_dungeon_selection_menu()
        else:
            logger.error("enter_dungeon_callbackが設定されていません")
    
    def _generate_new_dungeon(self):
        """新規ダンジョンを生成"""
        import hashlib
        import time
        
        logger.info("新規ダンジョンを生成します")
        
        # ハッシュ値を生成
        current_time = str(time.time())
        hash_value = hashlib.md5(current_time.encode()).hexdigest()[:8]
        
        new_dungeon = {
            "id": f"dungeon_{hash_value}",
            "name": f"生成ダンジョン_{hash_value[:4]}",
            "difficulty": "Normal",
            "attribute": "Mixed", 
            "completed": False,
            "hash": hash_value,
            "generated_at": current_time
        }
        
        # TODO: 実際のダンジョンデータストレージに保存
        
        logger.info(f"新規ダンジョンを生成しました: {new_dungeon['name']}")
        
        # 成功メッセージを表示
        success_message = f"新しいダンジョン「{new_dungeon['name']}」を生成しました。"
        self._show_dungeon_generation_success(success_message)
    
    def _show_dungeon_deletion_menu(self):
        """ダンジョン削除メニューを表示"""
        logger.info("ダンジョン削除メニューを表示します")
        # TODO: 実装
        pass
    
    def _show_dungeon_generation_success(self, message):
        """ダンジョン生成成功メッセージを表示"""
        # 簡易的な成功表示（実装を簡略化）
        logger.info(f"ダンジョン生成成功: {message}")
        # ダンジョン選択メニューを閉じて地上に戻る
        self._close_dungeon_selection_menu()
    
    def _close_dungeon_selection_menu(self):
        """ダンジョン選択メニューを閉じて地上メニューに戻る"""
        logger.info("ダンジョン選択メニューを閉じます")
        
        # UISelectionListを非表示にして破棄
        if hasattr(self, 'dungeon_selection_list') and self.dungeon_selection_list:
            self.dungeon_selection_list.hide()
            self.dungeon_selection_list.kill()
            self.dungeon_selection_list = None
        
        # メインメニューを再表示
        if self.main_menu:
            self.ui_manager.show_menu(self.main_menu.menu_id, modal=True)
    
    
    def _on_enter_dungeon_old(self):
        """ダンジョン入場（旧実装）"""
        logger.info("ダンジョン入場が選択されました")
        if self.enter_dungeon_callback:
            try:
                # メインメニューを隠す
                if self.main_menu:
                    self.ui_manager.hide_menu(self.main_menu.menu_id)
                self.is_active = False
                
                # ダンジョンに遷移
                self.enter_dungeon_callback("main_dungeon")
            except Exception as e:
                logger.error(f"ダンジョン入場エラー: {e}")
                # エラーの場合はメニューを再表示
                if self.main_menu:
                    self.main_menu.show()
                self.is_active = True
    
    # === 地上施設ハンドラー ===
    
    def _on_guild(self):
        """冒険者ギルド"""
        logger.info("冒険者ギルドが選択されました")
        try:
            from src.overworld.base_facility import facility_manager, initialize_facilities
            # 施設の初期化を確実に行う
            if not facility_manager.facilities:
                initialize_facilities()
            
            success = facility_manager.enter_facility("guild", self.current_party)
            if success:
                # 施設に入ったらメインメニューを隠す
                if self.main_menu:
                    self.ui_manager.hide_menu(self.main_menu.menu_id)
            else:
                logger.error("冒険者ギルドへの入場に失敗しました")
        except Exception as e:
            logger.error(f"冒険者ギルドエラー: {e}")
            logger.info("冒険者ギルドの詳細機能を利用")
    
    def _on_inn(self):
        """宿屋"""
        logger.info("宿屋が選択されました")
        try:
            from src.overworld.base_facility import facility_manager, initialize_facilities
            # 施設の初期化を確実に行う
            if not facility_manager.facilities:
                initialize_facilities()
            
            success = facility_manager.enter_facility("inn", self.current_party)
            if success:
                # 施設に入ったらメインメニューを隠す
                if self.main_menu:
                    self.ui_manager.hide_menu(self.main_menu.menu_id)
            else:
                logger.error("宿屋への入場に失敗しました")
        except Exception as e:
            logger.error(f"宿屋エラー: {e}")
            # 基本的な回復処理をフォールバック
            if self.current_party:
                for character in self.current_party.get_living_characters():
                    character.derived_stats.current_hp = character.derived_stats.max_hp
                    character.derived_stats.current_mp = character.derived_stats.max_mp
                logger.info("パーティを回復しました（簡易版）")
    
    def _on_shop(self):
        """商店"""
        logger.info("商店が選択されました")
        try:
            from src.overworld.base_facility import facility_manager, initialize_facilities
            # 施設の初期化を確実に行う
            if not facility_manager.facilities:
                initialize_facilities()
            
            success = facility_manager.enter_facility("shop", self.current_party)
            if success:
                # 施設に入ったらメインメニューを隠す
                if self.main_menu:
                    self.ui_manager.hide_menu(self.main_menu.menu_id)
            else:
                logger.error("商店への入場に失敗しました")
        except Exception as e:
            logger.error(f"商店エラー: {e}")
    
    def _on_temple(self):
        """教会"""
        logger.info("教会が選択されました")
        try:
            from src.overworld.base_facility import facility_manager, initialize_facilities
            # 施設の初期化を確実に行う
            if not facility_manager.facilities:
                initialize_facilities()
            
            success = facility_manager.enter_facility("temple", self.current_party)
            if success:
                # 施設に入ったらメインメニューを隠す
                if self.main_menu:
                    self.ui_manager.hide_menu(self.main_menu.menu_id)
            else:
                logger.error("教会への入場に失敗しました")
        except Exception as e:
            logger.error(f"教会エラー: {e}")
    
    def _on_magic_guild(self):
        """魔術師ギルド"""
        logger.info("魔術師ギルドが選択されました")
        try:
            from src.overworld.base_facility import facility_manager, initialize_facilities
            # 施設の初期化を確実に行う
            if not facility_manager.facilities:
                initialize_facilities()
            
            success = facility_manager.enter_facility("magic_guild", self.current_party)
            if success:
                # 施設に入ったらメインメニューを隠す
                if self.main_menu:
                    self.ui_manager.hide_menu(self.main_menu.menu_id)
            else:
                logger.error("魔術師ギルドへの入場に失敗しました")
        except Exception as e:
            logger.error(f"魔術師ギルドエラー: {e}")
    
    # === 設定画面ハンドラー ===
    
    def _on_party_status(self):
        """パーティ状況表示"""
        logger.info("パーティ状況が選択されました")
        if self.current_party:
            # 詳細なパーティ情報表示
            info_text = f"パーティ: {self.current_party.name}\n"
            info_text += f"メンバー数: {len(self.current_party.get_living_characters())}人\n"
            info_text += f"ゴールド: {self.current_party.gold}G"
            
            for i, character in enumerate(self.current_party.get_living_characters()):
                info_text += f"\n{i+1}. {character.name} Lv.{character.experience.level}"
                info_text += f"  HP: {character.derived_stats.current_hp}/{character.derived_stats.max_hp}"
                info_text += f"  MP: {character.derived_stats.current_mp}/{character.derived_stats.max_mp}"
                info_text += f"  状態: {character.status.value}"
            
            # UIダイアログでパーティ情報を表示（動的サイズ調整）
            from src.ui.base_ui_pygame import UIDialog, UIButton
            
            # テキスト量に基づいてダイアログサイズを計算
            text_length = len(info_text)
            line_count = info_text.count('\n') + 1
            
            # ダイアログサイズの動的調整
            if text_length > 300:
                dialog_width = 700
            elif text_length > 150:
                dialog_width = 600
            else:
                dialog_width = 500
                
            dialog_height = min(600, max(300, 80 + line_count * 25))
            
            # 画面中央に配置
            dialog_x = (1024 - dialog_width) // 2
            dialog_y = (768 - dialog_height) // 2
            
            party_dialog = UIDialog("party_status_dialog", "パーティ状況", info_text, 
                                  dialog_x, dialog_y, dialog_width, dialog_height)
            
            # OKボタンを画面下部に配置
            ok_x = dialog_x + (dialog_width - 100) // 2
            ok_y = dialog_y + dialog_height - 60
            ok_button = UIButton("party_status_ok", "OK", ok_x, ok_y, 100, 40)
            ok_button.on_click = self._close_party_status_dialog
            party_dialog.add_element(ok_button)
            
            self.ui_manager.add_dialog(party_dialog)
            self.ui_manager.show_dialog("party_status_dialog")
            
            logger.info(f"パーティ詳細: {info_text}")
        else:
            # パーティが設定されていない場合
            from src.ui.base_ui_pygame import UIDialog, UIButton
            no_party_dialog = UIDialog("no_party_dialog", "パーティ状況", "パーティが設定されていません。")
            
            # OKボタンを追加
            ok_button = UIButton("no_party_ok", "OK", 400, 400, 100, 40)
            ok_button.on_click = self._close_party_status_dialog
            no_party_dialog.add_element(ok_button)
            
            self.ui_manager.add_dialog(no_party_dialog)
            self.ui_manager.show_dialog("no_party_dialog")
    
    def _close_party_status_dialog(self):
        """パーティ状況ダイアログを閉じる"""
        try:
            self.ui_manager.hide_dialog("party_status_dialog")
        except:
            pass
        try:
            self.ui_manager.hide_dialog("no_party_dialog")
        except:
            pass
    
    def _initialize_character_status_bar(self):
        """キャラクターステータスバーを初期化"""
        try:
            # 画面サイズを取得（デフォルト値を使用）
            screen_width = 1024
            screen_height = 768
            
            # キャラクターステータスバーを作成
            self.character_status_bar = create_character_status_bar(screen_width, screen_height)
            
            # UIマネージャーに追加（最前面に表示される永続要素として）
            if self.ui_manager and self.character_status_bar:
                self.ui_manager.add_persistent_element(self.character_status_bar)
            
            # 現在のパーティが設定されている場合は設定
            if self.current_party:
                self.character_status_bar.set_party(self.current_party)
            
            logger.info("キャラクターステータスバーを初期化しました")
            
        except Exception as e:
            logger.error(f"キャラクターステータスバー初期化エラー: {e}")
            self.character_status_bar = None
    
    def _on_save_game(self):
        """ゲームを保存 - スロット選択画面を表示"""
        logger.info("ゲーム保存が選択されました")
        self._show_save_slot_selection()
    
    def _on_load_game(self):
        """ゲームをロード - スロット選択画面を表示"""
        logger.info("ゲームロードが選択されました")
        self._show_load_slot_selection()
    
    def _show_save_slot_selection(self):
        """セーブスロット選択画面を表示"""
        logger.info("セーブスロット選択画面を表示します")
        
        if not self.ui_manager:
            logger.error("UIマネージャーが設定されていません")
            return
        
        # 設定メニューを隠す
        if self.settings_menu:
            self.ui_manager.hide_menu(self.settings_menu.menu_id)
        
        # セーブスロット選択メニューをWindowSystemで作成
        # UIMenuは削除済み - OverworldMainWindowのSAVE_LOADメニューを使用
        logger.info("セーブスロット選択はWindowSystemメニューで実装されています")
        
        # UIMenuベースの実装は削除済み - WindowSystemメニューを使用してください
        pass
    
    def _show_load_slot_selection(self):
        """ロードスロット選択画面を表示"""
        logger.info("ロードスロット選択画面を表示します")
        
        if not self.ui_manager:
            logger.error("UIマネージャーが設定されていません")
            return
        
        # 設定メニューを隠す
        if self.settings_menu:
            self.ui_manager.hide_menu(self.settings_menu.menu_id)
        
        # ロードスロット選択メニューをWindowSystemで作成
        # UIMenuは削除済み - OverworldMainWindowのSAVE_LOADメニューを使用
        logger.info("ロードスロット選択はWindowSystemメニューで実装されています")
        
        # UIMenuベースの実装は削除済み - WindowSystemメニューを使用してください
        pass
    
    def _get_save_slots(self):
        """セーブスロット情報を取得"""
        # TODO: 実際のセーブデータストレージから取得
        # 現在は仮のデータを返す
        
        slots = []
        for slot_id in range(SAVE_SLOT_RANGE_START, SAVE_SLOT_RANGE_END):
            slot_data = self._create_sample_slot_data(slot_id)
            slots.append(slot_data)
        
        return slots
    
    def _create_sample_slot_data(self, slot_id: int) -> dict:
        """サンプルスロットデータを作成"""
        if slot_id == 1:
            return {
                "slot_id": 1,
                "is_used": True,
                "save_time": "2025-06-23 10:30:00",
                "party_name": "勇者の一行",
                "play_time": "05:30:15",
                "location": "地上・冒険者ギルド",
                "party_level": 5,
                "gold": 1500
            }
        elif slot_id == 3:
            return {
                "slot_id": 3,
                "is_used": True,
                "save_time": "2025-06-22 18:45:30",
                "party_name": "冒険者チーム",
                "play_time": "02:15:45",
                "location": "地上・商店",
                "party_level": 3,
                "gold": 800
            }
        else:
            return {
                "slot_id": slot_id,
                "is_used": False,
                "save_time": None,
                "party_name": None,
                "play_time": None,
                "location": None,
                "party_level": None,
                "gold": None
            }
    
    def _format_save_slot_info(self, slot):
        """セーブスロット情報をフォーマット"""
        if slot['is_used']:
            return f"スロット {slot['slot_id']}: {slot['party_name']} ({slot['save_time']})"
        else:
            return f"スロット {slot['slot_id']}: [空き]"
    
    def _save_to_slot(self, slot_id):
        """指定されたスロットにセーブ"""
        logger.info(f"スロット {slot_id} にセーブします")
        
        # スロット情報を取得
        slots = self._get_save_slots()
        selected_slot = next((slot for slot in slots if slot['slot_id'] == slot_id), None)
        
        if selected_slot and selected_slot['is_used']:
            # 既存データがある場合は確認ダイアログを表示
            self._show_save_confirmation(slot_id, selected_slot)
        else:
            # 空きスロットの場合は直接保存
            self._execute_save(slot_id)
    
    def _show_save_confirmation(self, slot_id, existing_slot):
        """セーブ確認ダイアログを表示"""
        confirmation_message = (
            f"スロット {slot_id} を上書きしますか？\\n\\n"
            f"既存データ:\\n"
            f"パーティ: {existing_slot['party_name']}\\n"
            f"保存日時: {existing_slot['save_time']}"
        )
        
        # TODO: 確認ダイアログの実装
        # 現在は簡易的に直接保存
        logger.info(f"上書き確認: {confirmation_message}")
        self._execute_save(slot_id)
    
    def _execute_save(self, slot_id):
        """セーブを実行"""
        logger.info(f"スロット {slot_id} にセーブを実行します")
        
        # 実際のセーブ処理
        slot_name = f"save_slot_{slot_id}"
        success = self.save_overworld_state(slot_name)
        
        if success:
            logger.info(f"スロット {slot_id} にゲームを保存しました")
            # セーブ成功メッセージを表示
            self._show_save_success(slot_id)
        else:
            logger.error(f"スロット {slot_id} へのゲーム保存に失敗しました")
            # エラーメッセージを表示
            self._show_save_error(slot_id)
    
    def _load_from_slot(self, slot_id):
        """指定されたスロットからロード"""
        logger.info(f"スロット {slot_id} からロードします")
        
        # 実際のロード処理
        slot_name = f"save_slot_{slot_id}"
        success = self.load_overworld_state(slot_name)
        
        if success:
            logger.info(f"スロット {slot_id} からゲームをロードしました")
            # ロード成功後は設定画面を閉じる
            self._close_load_slot_selection()
        else:
            logger.error(f"スロット {slot_id} からのゲームロードに失敗しました")
            # エラーメッセージを表示
            self._show_load_error(slot_id)
    
    def _show_save_success(self, slot_id):
        """セーブ成功メッセージを表示"""
        logger.info(f"セーブ成功メッセージを表示: スロット {slot_id}")
        # メニューを閉じて設定画面に戻る
        self._close_save_slot_selection()
    
    def _show_save_error(self, slot_id):
        """セーブエラーメッセージを表示"""
        logger.error(f"セーブエラーメッセージを表示: スロット {slot_id}")
        # メニューに戻る
        self._show_save_slot_selection()
    
    def _show_load_error(self, slot_id):
        """ロードエラーメッセージを表示"""
        logger.error(f"ロードエラーメッセージを表示: スロット {slot_id}")
        # メニューに戻る
        self._show_load_slot_selection()
    
    def _close_save_slot_selection(self):
        """セーブスロット選択メニューを閉じて設定画面に戻る"""
        logger.info("セーブスロット選択メニューを閉じます")
        
        # セーブスロット選択メニューを隠す
        self.ui_manager.hide_menu("save_slot_selection_menu")
        
        # 設定メニューを再表示
        if self.settings_menu:
            self.ui_manager.show_menu(self.settings_menu.menu_id, modal=True)
    
    def _close_load_slot_selection(self):
        """ロードスロット選択メニューを閉じて設定画面に戻る"""
        logger.info("ロードスロット選択メニューを閉じます")
        
        # ロードスロット選択メニューを隠す
        self.ui_manager.hide_menu("load_slot_selection_menu")
        
        # 設定メニューを再表示
        if self.settings_menu:
            self.ui_manager.show_menu(self.settings_menu.menu_id, modal=True)
    
    def _on_save_game_old(self):
        """ゲームを保存（旧実装）"""
        logger.info("ゲーム保存が選択されました")
        # セーブ処理の実装
        success = self.save_overworld_state("quicksave")
        if success:
            logger.info("ゲームを保存しました")
        else:
            logger.error("ゲーム保存に失敗しました")
    
    def _on_load_game_old(self):
        """ゲームをロード（旧実装）"""
        logger.info("ゲームロードが選択されました")
        # ロード処理の実装
        success = self.load_overworld_state("quicksave")
        if success:
            logger.info("ゲームをロードしました")
        else:
            logger.error("ゲームロードに失敗しました")
    
    def _on_config(self):
        """設定"""
        logger.info("設定が選択されました")
        # ゲーム設定画面の表示
        try:
            # 新WindowSystemのSettingsWindowを使用
            from src.ui.window_system.window_manager import WindowManager
            from src.ui.window_system.settings_window import SettingsWindow
            import pygame
            
            window_manager = WindowManager.get_instance()
            # Pygameが初期化されていない場合は初期化
            if not window_manager.screen and hasattr(self, 'screen') and self.screen:
                window_manager.initialize_pygame(self.screen, pygame.time.Clock())
            
            settings_window = window_manager.create_window(
                SettingsWindow,
                window_manager=window_manager,
                rect=pygame.Rect(200, 100, 600, 500),
                window_id="main_settings_window"
            )
            settings_window.set_close_callback(self._on_settings_close)
            settings_window.show_settings_menu()
            logger.info("設定画面を表示しました")
        except Exception as e:
            logger.error(f"設定画面表示エラー: {e}")
    
    def _on_settings_close(self):
        """設定画面終了時のコールバック"""
        logger.info("設定画面が閉じられました")
        # 設定メニューに戻る
        if self.settings_menu:
            self.ui_manager.show_menu(self.settings_menu.menu_id, modal=True)
    
    def _on_back_to_overworld(self):
        """地上部に戻る"""
        logger.info("地上部に戻ります")
        self._hide_settings_menu()
        self._show_main_menu()
    
    def _on_exit_game(self):
        """ゲーム終了"""
        logger.info("ゲーム終了が選択されました")
        if self.exit_game_callback:
            self.exit_game_callback()
    
    # === 画面遷移メソッド ===
    
    def _show_settings_menu(self):
        """設定画面を表示（WindowSystem優先）"""
        try:
            # WindowSystemベースの設定メニュー表示を試行
            if hasattr(self, 'overworld_main_window') and self.overworld_main_window:
                settings_config = self._create_settings_menu_config()
                from src.ui.window_system.overworld_main_window import OverworldMenuType
                self.overworld_main_window.show_menu(OverworldMenuType.SETTINGS, settings_config)
                self.settings_active = True
                logger.info("WindowSystemベースで設定画面を表示しました")
                return
        except Exception as e:
            logger.warning(f"WindowSystemベースの設定画面表示エラー: {e}")
        
        # フォールバック: レガシーUIMenu使用
        if self.main_menu:
            self.ui_manager.hide_menu(self.main_menu.menu_id)
        if self.settings_menu:
            self.settings_menu.show()
        self.settings_active = True
        logger.info("レガシーメニューで設定画面を表示しました")
    
    def _hide_settings_menu(self):
        """設定画面を非表示"""
        if self.settings_menu:
            self.settings_menu.hide()
        self.settings_active = False
        logger.info("設定画面を非表示にしました")
    
    def _show_main_menu(self):
        """メインメニューを表示"""
        if self.main_menu:
            self.ui_manager.show_menu(self.main_menu.menu_id, modal=True)
        logger.info("メインメニューを表示しました")
    
    def enter_overworld(self, party: Party, from_dungeon: bool = False) -> bool:
        """地上部に入場"""
        try:
            self.current_party = party
            self.is_active = True
            
            # キャラクターステータスバーにパーティを設定
            if self.character_status_bar:
                self.character_status_bar.set_party(party)
            
            # UIマネージャーが設定されていない場合は後で設定
            if self.ui_manager and not self.main_menu:
                self._create_main_menu()
            
            # WindowManagerベースのメインメニューを使用
            if hasattr(self, 'overworld_main_window') and self.overworld_main_window:
                self.show_main_menu_window_manager()
            else:
                # フォールバック：従来の方法（MenuStackManager除去）
                if self.main_menu:
                    self.ui_manager.show_menu(self.main_menu.menu_id, modal=True)
                else:
                    logger.error("メインメニューが作成されていません")
            
            if from_dungeon:
                logger.info("ダンジョンから地上部に帰還しました")
            else:
                logger.info("地上部に入場しました")
            
            return True
            
        except Exception as e:
            logger.error(f"地上部入場エラー: {e}")
            return False
    
    def exit_overworld(self):
        """地上部を退場"""
        self.is_active = False
        
        # メインメニューを隠す
        if self.main_menu:
            self.ui_manager.hide_menu(self.main_menu.menu_id)
        
        logger.info("地上部を退場しました")
    
    def show_main_menu(self):
        """メインメニューを表示（外部から呼び出し可能）"""
        self._show_main_menu()
    
    def show_settings_menu(self):
        """設定メニューを表示（外部から呼び出し可能）"""
        self._show_settings_menu()
    
    def render(self, screen: pygame.Surface):
        """地上部の描画"""
        if not self.is_active:
            return
        
        # 背景色（画面によって色を変える）
        if self.settings_active:
            screen.fill((50, 50, 80))  # 設定画面：濃い青
        else:
            screen.fill((100, 150, 100))  # 地上部：緑
        
        # 背景テキスト表示（日本語フォント使用）
        try:
            from src.ui.font_manager_pygame import font_manager
            font = font_manager.get_japanese_font(24)
            if not font:
                font = font_manager.get_default_font()
        except Exception as e:
            logger.warning(f"フォントマネージャーの取得に失敗: {e}")
            # 利用可能なシステムフォントから日本語対応フォントを安全に取得
            available_fonts = pygame.font.get_fonts()
            japanese_font_candidates = ['noto', 'notosans', 'ipagothic', 'takao', 'dejavu']
            
            font = None
            for font_name in japanese_font_candidates:
                if font_name in available_fonts:
                    try:
                        font = pygame.font.SysFont(font_name, 24)
                        break
                    except:
                        continue
            
            if not font:
                font = pygame.font.Font(None, 24)
        
        if font:
            if self.settings_active:
                # 設定画面のタイトル
                try:
                    title_text = font.render("設定画面", True, (255, 255, 255))
                    title_rect = title_text.get_rect(center=(screen.get_width()//2, 80))
                    screen.blit(title_text, title_rect)
                except:
                    # 英語フォールバック
                    title_text = font.render("Settings Menu", True, (255, 255, 255))
                    title_rect = title_text.get_rect(center=(screen.get_width()//2, 80))
                    screen.blit(title_text, title_rect)
                
                # ESCキーの案内
                try:
                    help_text = font.render("[ESC] 地上部に戻る", True, (200, 200, 200))
                    help_rect = help_text.get_rect(center=(screen.get_width()//2, 120))
                    screen.blit(help_text, help_rect)
                except:
                    # 英語フォールバック
                    help_text = font.render("[ESC] Return to Overworld", True, (200, 200, 200))
                    help_rect = help_text.get_rect(center=(screen.get_width()//2, 120))
                    screen.blit(help_text, help_rect)
            else:
                # 地上部のタイトル
                try:
                    title_text = font.render("地上マップ", True, (255, 255, 255))
                    title_rect = title_text.get_rect(center=(screen.get_width()//2, 80))
                    screen.blit(title_text, title_rect)
                except:
                    # 英語フォールバック
                    title_text = font.render("Overworld Map", True, (255, 255, 255))
                    title_rect = title_text.get_rect(center=(screen.get_width()//2, 80))
                    screen.blit(title_text, title_rect)
                
                # パーティ情報
                if self.current_party:
                    try:
                        party_info = f"パーティ: {self.current_party.name} | ゴールド: {self.current_party.gold}G"
                        info_text = font.render(party_info, True, (200, 200, 200))
                        info_rect = info_text.get_rect(center=(screen.get_width()//2, 120))
                        screen.blit(info_text, info_rect)
                    except:
                        # 英語フォールバック
                        party_info = f"Party: {self.current_party.name} | Gold: {self.current_party.gold}G"
                        info_text = font.render(party_info, True, (200, 200, 200))
                        info_rect = info_text.get_rect(center=(screen.get_width()//2, 120))
                        screen.blit(info_text, info_rect)
        
        # キャラクターステータスバーの描画はUIマネージャーが行うため、ここでは描画しない
        # （UIマネージャーのelementsに追加済み）
    
    # MenuStackManager関連メソッド削除（WindowSystemへ移行）
    # def _handle_escape_from_menu_stack(self) -> bool:
    #     """MenuStackManagerからのESCキー処理コールバック"""
    #     # WindowSystemへ移行により削除
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理"""
        if not self.is_active:
            return False
        
        # UISelectionListのイベント処理
        if hasattr(self, 'dungeon_selection_list') and self.dungeon_selection_list:
            if self.dungeon_selection_list.handle_event(event):
                return True
        
        # 施設のイベント処理
        from src.overworld.base_facility import facility_manager
        current_facility = facility_manager.get_current_facility()
        if current_facility and current_facility.is_active:
            if current_facility.handle_event(event):
                return True
        
        # ESCキー処理
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # ダンジョン選択画面が表示中の場合は閉じる
                if hasattr(self, 'dungeon_selection_list') and self.dungeon_selection_list:
                    self._close_dungeon_selection_menu()
                    return True
                
                # 施設がアクティブな場合は施設にESCキー処理を委譲
                from src.overworld.base_facility import facility_manager
                current_facility = facility_manager.get_current_facility()
                
                if current_facility and current_facility.is_active:
                    # 施設側でESCキー処理を実行（施設から出る）
                    logger.info(f"施設 {current_facility.facility_id} でESCキーが押されました - 施設退出")
                    success = facility_manager.exit_current_facility()
                    if success:
                        return True
                    else:
                        logger.warning("施設退出に失敗しました")
                
                # 地上部でのESCキー処理
                if self.settings_active:
                    # 設定画面が表示中の場合は地上部に戻る
                    self._hide_settings_menu()
                    self._show_main_menu()
                else:
                    # 地上部が表示中の場合は設定画面を表示
                    self._show_settings_menu()
                return True
        
        return False
    
    def save_overworld_state(self, slot_id: str) -> bool:
        """地上部状態を保存"""
        try:
            # 簡易実装（実際の保存処理は後で実装）
            logger.info(f"地上部状態を保存しました: スロット{slot_id}")
            return True
        except Exception as e:
            logger.error(f"地上部状態保存エラー: {e}")
            return False
    
    def load_overworld_state(self, slot_id: str) -> bool:
        """地上部状態を読み込み"""
        try:
            # 簡易実装（実際の読み込み処理は後で実装）
            logger.info(f"地上部状態を読み込みました: スロット{slot_id}")
            return True
        except Exception as e:
            logger.error(f"地上部状態読み込みエラー: {e}")
            return False