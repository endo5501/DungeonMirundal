"""地上部管理システム"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.overworld.base_facility import BaseFacility, FacilityManager, facility_manager
from src.ui.base_ui_pygame import UIMenu, UIDialog, ui_manager
from src.ui.window_system import WindowManager
try:
    from src.ui.dungeon_selection_ui import DungeonSelectionUI
except ImportError:
    # ダンジョン選択UIが未実装の場合はMockを使用
    DungeonSelectionUI = None
from src.core.config_manager import config_manager
from src.core.save_manager import save_manager
from src.utils.logger import logger

# 地上部システム定数
MAX_SAVE_SLOTS = 5
SAVE_SLOT_RANGE_START = 1
SAVE_SLOT_RANGE_END = 6
MAX_DISPLAY_CHARACTERS = 3
MAX_DISPLAY_ITEMS = 5
DEFAULT_DIALOG_WIDTH_SMALL = 500
DEFAULT_DIALOG_WIDTH_MEDIUM = 600
DEFAULT_DIALOG_WIDTH_LARGE = 700
DEFAULT_DIALOG_HEIGHT_MIN = 300
DEFAULT_DIALOG_HEIGHT_MAX = 600
DIALOG_LINE_HEIGHT = 25
DIALOG_MARGIN = 80
SCREEN_WIDTH_DEFAULT = 1024
SCREEN_HEIGHT_DEFAULT = 768
BUTTON_WIDTH_DEFAULT = 100
BUTTON_HEIGHT_DEFAULT = 40
BUTTON_MARGIN = 60
TEXT_LENGTH_THRESHOLD_SMALL = 150
TEXT_LENGTH_THRESHOLD_LARGE = 300
HP_MP_FULL_RECOVERY = 1.0
DIALOG_CENTER_DIVISOR = 2
FIRST_ELEMENT_INDEX = 0
EMPTY_RECOVERY_COUNT = 0

# ダイアログID定数
DIALOG_ID_INFO = "overworld_info_dialog"
DIALOG_ID_CONFIRM = "overworld_confirm_dialog"
DIALOG_IDS_ALL = [DIALOG_ID_INFO, DIALOG_ID_CONFIRM]


class OverworldLocation(Enum):
    """地上部の場所"""
    TOWN_CENTER = "town_center"
    GUILD = "guild"
    INN = "inn"
    SHOP = "shop"
    TEMPLE = "temple"
    MAGIC_GUILD = "magic_guild"
    DUNGEON_ENTRANCE = "dungeon_entrance"


class OverworldManager:
    """地上部管理クラス"""
    
    def __init__(self):
        self.current_party: Optional[Party] = None
        self.current_location = OverworldLocation.TOWN_CENTER
        self.is_active = False
        
        # UI要素
        self.main_menu: Optional[UIMenu] = None
        self.location_menu: Optional[UIMenu] = None
        self.settings_menu_active = False
        self.dungeon_selection_ui = DungeonSelectionUI() if DungeonSelectionUI else None
        
        # コールバック
        self.on_enter_dungeon: Optional[Callable] = None
        self.on_exit_game: Optional[Callable] = None
        self.input_manager_ref: Optional[Any] = None
        
        self.facility_manager = facility_manager
        # 施設退場時のコールバックを設定
        self.facility_manager.set_facility_exit_callback(self.on_facility_exit)
        
        # 施設入場前のメニュー状態を記録するフラグ
        self.main_menu_was_visible = False
        self.settings_menu_was_visible = False
        
        # WindowManager統合
        self.window_manager = WindowManager.get_instance()
        self.main_window = None
        
        logger.info("OverworldManagerを初期化しました")
    
    def enter_overworld(self, party: Party, from_dungeon: bool = False) -> bool:
        """地上部に入る"""
        if self.is_active:
            logger.warning("地上部は既にアクティブです")
            return False
        
        self.current_party = party
        self.current_location = OverworldLocation.TOWN_CENTER
        self.is_active = True
        self.settings_menu_active = False
        
        # 入力管理との連携
        self._setup_input_handling()
        
        # ダンジョンから戻った場合の自動回復
        if from_dungeon:
            self._auto_recovery()
        
        # メインメニューを表示（新システム優先）
        self._show_main_menu_window()
        
        logger.info(f"パーティが地上部に入りました: {party.name}")
        return True
    
    def exit_overworld(self) -> bool:
        """地上部から出る"""
        if not self.is_active:
            logger.warning("地上部はアクティブではありません")
            return False
        
        # UI要素のクリーンアップ
        self._cleanup_ui()
        
        # 現在の施設から出る
        self.facility_manager.exit_current_facility()
        
        self.current_party = None
        self.current_location = OverworldLocation.TOWN_CENTER
        self.is_active = False
        
        logger.info("パーティが地上部から出ました")
        return True
    
    def _auto_recovery(self):
        """地上部帰還時の自動回復システム"""
        if not self.current_party:
            return
        
        recovered_characters = []
        
        for character in self.current_party.get_all_characters():
            character_recovered = self._recover_character(character)
            if character_recovered:
                recovered_characters.append(character.name)
        
        # TODO: Phase 4で魔法使用回数もリセット予定
        
        if recovered_characters:
            self._show_recovery_message(recovered_characters)
        
        logger.info("地上部帰還時の自動回復を実行しました")
    
    def _recover_character(self, character) -> bool:
        """キャラクターを回復し、回復したかどうかを返す"""
        # HP・MP全回復
        old_hp = character.derived_stats.current_hp
        old_mp = character.derived_stats.current_mp
        
        character.derived_stats.current_hp = character.derived_stats.max_hp
        character.derived_stats.current_mp = character.derived_stats.max_mp
        
        # 状態異常解除（死亡・灰化以外）
        old_status = character.status
        if character.status not in [CharacterStatus.DEAD, CharacterStatus.ASHES]:
            character.status = CharacterStatus.GOOD
        
        # 回復したかどうかを判定
        return (old_hp < character.derived_stats.max_hp or 
                old_mp < character.derived_stats.max_mp or 
                old_status != character.status)
    
    def _show_recovery_message(self, recovered_characters: List[str]):
        """回復メッセージを表示"""
        recovery_message = f"地上部に戻りました！\n{', '.join(recovered_characters)} が回復しました。"
        self._show_info_dialog("自動回復", recovery_message)
        logger.info(f"自動回復実行: {len(recovered_characters)} 人のキャラクターが回復")
    
    def _setup_input_handling(self):
        """入力処理のセットアップ"""
        if self.input_manager_ref:
            # ESCキー（メニューアクション）のハンドリング
            self.input_manager_ref.bind_action("menu", self._on_menu_key)
            logger.debug("地上部入力ハンドリングを設定しました")
    
    def _on_menu_key(self, action: str, pressed: bool, input_type: Any):
        """メニューキー（ESC）の処理"""
        if not pressed or not self.is_active:
            return
        
        # 現在設定画面が表示されている場合は閉じる
        if self.settings_menu_active:
            self._back_to_main_menu()
        else:
            # 地上マップから設定画面を表示
            self.show_settings_menu()
    
    def set_input_manager(self, input_manager):
        """入力管理システムの参照を設定"""
        self.input_manager_ref = input_manager
    
    def _show_main_menu(self):
        """地上マップメニューの表示（直接施設アクセス）"""
        if self.main_menu:
            ui_manager.hide_menu(self.main_menu.menu_id)
        
        self.main_menu = UIMenu("overworld_main_menu", config_manager.get_text("overworld.surface_map"))
        
        # 各施設への直接アクセス
        facilities = [
            ("guild", config_manager.get_text("facility.guild")),
            ("inn", config_manager.get_text("facility.inn")),
            ("shop", config_manager.get_text("facility.shop")),
            ("temple", config_manager.get_text("facility.temple")),
            ("magic_guild", config_manager.get_text("facility.magic_guild"))
        ]
        
        for facility_id, facility_name in facilities:
            self.main_menu.add_menu_item(
                facility_name,
                self._enter_facility,
                [facility_id]
            )
        
        # ダンジョン入口
        self.main_menu.add_menu_item(
            config_manager.get_text("facility.dungeon_entrance"),
            self._enter_dungeon
        )
        
        ui_manager.add_menu(self.main_menu)
        ui_manager.show_menu(self.main_menu.menu_id, modal=True)
    
    # === WindowManagerベースの新メソッド ===
    
    def _show_main_menu_window(self):
        """メインメニューをWindowManagerで表示（新システム）"""
        try:
            from src.ui.window_system.overworld_main_window import OverworldMainWindow
            
            # メニュー設定を作成
            menu_config = self._create_main_menu_config()
            
            # OverworldMainWindowを作成
            self.main_window = OverworldMainWindow('overworld_main', menu_config)
            
            # メッセージハンドラーを設定
            self.main_window.message_handler = self.handle_main_menu_message
            
            # ウィンドウを表示
            self.window_manager.show_window(self.main_window, push_to_stack=True)
            
            logger.info("WindowManagerでメインメニューを表示しました")
            
        except ImportError:
            # OverworldMainWindowが未実装の場合はレガシーメソッドを使用
            logger.warning("OverworldMainWindow未実装、レガシーメニューを使用")
            self._show_main_menu()
    
    def _create_main_menu_config(self):
        """メインメニュー設定を作成（OverworldMainWindow用）"""
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
    
    def handle_main_menu_message(self, message_type: str, data: dict) -> bool:
        """メインメニューメッセージ処理（OverworldMainWindow用）"""
        logger.debug(f"handle_main_menu_message: {message_type}, data: {data}")
        
        if message_type == 'menu_item_selected':
            item_id = data.get('item_id')
            facility_id = data.get('facility_id')
            
            if facility_id:
                # 施設入場
                return self._enter_facility(facility_id)
            elif item_id == 'dungeon_entrance':
                # ダンジョン入場
                return self._enter_dungeon()
            elif item_id in ['party_status', 'save_game', 'load_game']:
                # 設定メニューから選択された項目
                if item_id == 'party_status':
                    return self._show_party_status_window()
                elif item_id == 'save_game':
                    return self._show_save_menu_window()
                elif item_id == 'load_game':
                    return self._show_load_menu_window()
        
        elif message_type == 'settings_menu_requested':
            # ESCキーでの設定メニュー表示
            return self._show_settings_menu_window()
        
        elif message_type == 'party_overview_requested':
            # パーティ全体情報表示
            return self._show_party_status_window()
        
        elif message_type == 'character_details_requested':
            # キャラクター詳細表示
            character = data.get('character')
            return self._show_character_details_window(character)
        
        elif message_type == 'save_load_requested':
            # セーブ・ロード処理
            operation = data.get('operation')
            slot_id = data.get('slot_id')
            if operation == 'save':
                return self._save_to_slot(slot_id)
            elif operation == 'load':
                return self._load_selected_save(slot_id)
        
        elif message_type == 'back_requested':
            # 戻る処理
            return self._go_back_to_main_menu()
        
        logger.warning(f"未処理のメッセージタイプ: {message_type}")
        return False
    
    def _show_character_details_window(self, character):
        """キャラクター詳細ウィンドウ表示"""
        if not character:
            logger.warning("キャラクターが指定されていません")
            return False
        
        # 簡単な実装：ダイアログで表示
        char_info = f"{character.name} (Lv.{character.experience.level})"
        char_info += f"\nHP: {character.derived_stats.current_hp}/{character.derived_stats.max_hp}"
        char_info += f"\nMP: {character.derived_stats.current_mp}/{character.derived_stats.max_mp}"
        char_info += f"\n状態: {character.status.value}"
        
        self._show_info_dialog("キャラクター詳細", char_info)
        return True
    
    def _go_back_to_main_menu(self):
        """メインメニューに戻る"""
        if hasattr(self, 'main_window') and self.main_window:
            # OverworldMainWindowの_go_backメソッドを使用
            return self.main_window._go_back()
        return False
    
    # === WindowManagerベースの新メソッド（パーティ・セーブ・ロード・設定） ===
    
    def _show_party_status_window(self):
        """パーティ状況をWindowManagerで表示"""
        if not self.current_party:
            logger.warning("パーティが設定されていません")
            return False
        
        try:
            # OverworldMainWindowでパーティ状況メニューを表示
            party_config = {
                'menu_type': 'party_status',
                'party': self.current_party
            }
            
            if hasattr(self, 'main_window') and self.main_window:
                from src.ui.window_system.overworld_main_window import OverworldMenuType
                self.main_window.show_menu(OverworldMenuType.PARTY_STATUS, party_config)
                return True
            
            logger.warning("メインウィンドウが見つかりません")
            return False
            
        except Exception as e:
            logger.error(f"パーティ状況表示エラー: {e}")
            return False
    
    def _show_save_menu_window(self):
        """セーブメニューをWindowManagerで表示"""
        try:
            # OverworldMainWindowでセーブメニューを表示
            save_config = {
                'menu_type': 'save_load',
                'operation': 'save',
                'max_slots': 5
            }
            
            if hasattr(self, 'main_window') and self.main_window:
                from src.ui.window_system.overworld_main_window import OverworldMenuType
                self.main_window.show_menu(OverworldMenuType.SAVE_LOAD, save_config)
                return True
            
            logger.warning("メインウィンドウが見つかりません")
            return False
            
        except Exception as e:
            logger.error(f"セーブメニュー表示エラー: {e}")
            return False
    
    def _show_load_menu_window(self):
        """ロードメニューをWindowManagerで表示"""
        try:
            # OverworldMainWindowでロードメニューを表示
            load_config = {
                'menu_type': 'save_load',
                'operation': 'load',
                'max_slots': 5
            }
            
            if hasattr(self, 'main_window') and self.main_window:
                from src.ui.window_system.overworld_main_window import OverworldMenuType
                self.main_window.show_menu(OverworldMenuType.SAVE_LOAD, load_config)
                return True
            
            logger.warning("メインウィンドウが見つかりません")
            return False
            
        except Exception as e:
            logger.error(f"ロードメニュー表示エラー: {e}")
            return False
    
    def _show_settings_menu_window(self):
        """設定メニューをWindowManagerで表示"""
        try:
            # OverworldMainWindowで設定メニューを表示
            settings_config = self._create_settings_menu_config()
            
            if hasattr(self, 'main_window') and self.main_window:
                from src.ui.window_system.overworld_main_window import OverworldMenuType
                self.main_window.show_menu(OverworldMenuType.SETTINGS, settings_config)
                return True
            
            logger.warning("メインウィンドウが見つかりません")
            return False
            
        except Exception as e:
            logger.error(f"設定メニュー表示エラー: {e}")
            return False
    
    def _handle_exit_game(self):
        """ゲーム終了処理"""
        try:
            # 終了確認ダイアログを表示
            confirm_data = {
                'title': 'ゲーム終了',
                'message': 'ゲームを終了しますか？',
                'action': 'exit_game'
            }
            
            # 現在のメインウィンドウにメッセージを送信
            if hasattr(self, 'main_window') and self.main_window:
                return self.main_window.handle_message('show_exit_confirmation', confirm_data)
            
            logger.warning("メインウィンドウが見つかりません")
            return False
            
        except Exception as e:
            logger.error(f"ゲーム終了処理エラー: {e}")
            return False
    
    def _create_settings_menu_config(self):
        """設定メニュー設定を作成"""
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
    
    def _create_party_status_config(self):
        """パーティステータス設定を作成"""
        return {
            'party': self.current_party,
            'display_mode': 'status_view',
            'show_detailed_stats': True
        }
    
    def _create_save_menu_config(self):
        """セーブメニュー設定を作成"""
        return {
            'menu_type': 'save_load',
            'operation': 'save',
            'party': self.current_party,
            'max_slots': MAX_SAVE_SLOTS
        }
    
    def _create_load_menu_config(self):
        """ロードメニュー設定を作成"""
        return {
            'menu_type': 'save_load',
            'operation': 'load',
            'max_slots': MAX_SAVE_SLOTS
        }
    
    def _show_settings_menu_window(self):
        """設定メニューをWindowManagerで表示"""
        try:
            from src.ui.window_system.settings_window import SettingsWindow
            
            config = self._create_settings_menu_config()
            settings_window = SettingsWindow('settings_menu', config)
            settings_window.message_handler = self.handle_settings_message
            
            self.window_manager.show_window(settings_window, push_to_stack=True)
            
        except ImportError:
            # SettingsWindowが未実装の場合はレガシーメソッドを使用
            logger.warning("SettingsWindow未実装、レガシー設定メニューを使用")
            self.show_settings_menu()
    
    def handle_settings_message(self, message_type: str, data: dict) -> bool:
        """設定メニューメッセージ処理"""
        if message_type == 'menu_item_selected':
            item_id = data.get('item_id')
            
            if item_id == 'party_status':
                return self._show_party_status()
            elif item_id == 'save_game':
                return self._show_save_menu()
            elif item_id == 'load_game':
                return self._show_load_menu()
            elif item_id == 'back':
                return self._back_to_main_menu()
                
        return False
    
    def _show_dungeon_selection_window(self):
        """ダンジョン選択をWindowManagerで表示"""
        # TODO: DungeonSelectionWindowの実装後に追加
        logger.info("ダンジョン選択ウィンドウ（実装予定）")
        if self.dungeon_selection_ui:
            # レガシー実装を使用
            self.dungeon_selection_ui.show()
    
    def _handle_overworld_exit(self) -> bool:
        """オーバーワールド退場処理"""
        return self.exit_overworld()
    
    def handle_escape_key(self) -> bool:
        """ESCキー処理（WindowManager対応）"""
        if not self.is_active:
            return False
        
        # 設定メニューが表示されている場合は戻る
        if self.settings_menu_active:
            return self._back_to_main_menu()
        
        # 通常状態では設定メニューを表示
        self._show_settings_menu_window()
        return True
    
    def _back_to_main_menu(self) -> bool:
        """メインメニューに戻る"""
        self.settings_menu_active = False
        
        # WindowManagerでback操作
        if self.window_manager.get_active_window():
            self.window_manager.go_back()
        
        return True
    
    def show_settings_menu(self):
        """設定画面の表示（ESCキー用）"""
        if self.location_menu:
            ui_manager.hide_menu(self.location_menu.menu_id)
        
        self.location_menu = UIMenu("settings_menu", config_manager.get_text("menu.settings"))
        self.settings_menu_active = True
        
        # パーティ状況確認
        self.location_menu.add_menu_item(
            config_manager.get_text("menu.party_status"),
            self._show_party_status
        )
        
        # セーブ・ロード
        self.location_menu.add_menu_item(
            config_manager.get_text("menu.save_game"),
            self._show_save_menu
        )
        
        self.location_menu.add_menu_item(
            config_manager.get_text("menu.load_game"),
            self._show_load_menu
        )
        
        # ゲーム設定
        self.location_menu.add_menu_item(
            config_manager.get_text("menu.game_settings"),
            self._show_game_settings
        )
        
        # ゲーム終了
        self.location_menu.add_menu_item(
            config_manager.get_text("menu.exit"),
            self._exit_game
        )
        
        # 戻る
        self.location_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu
        )
        
        ui_manager.add_menu(self.location_menu)
        ui_manager.show_menu(self.location_menu.menu_id, modal=True)
        
        # メインメニューを隠す
        if self.main_menu:
            ui_manager.hide_menu(self.main_menu.menu_id)
        
        logger.info("設定画面を表示しました")
    
    def _enter_facility(self, facility_id: str):
        """施設に入る"""
        if not self.current_party:
            return
        
        logger.info(f"FacilityManagerの状態: 登録済み施設={list(self.facility_manager.facilities.keys())}")
        success = self.facility_manager.enter_facility(facility_id, self.current_party)
        
        if success:
            self._hide_menus_for_facility_entry()
            logger.info(f"施設に入りました: {facility_id} (main_menu_was_visible: {self.main_menu_was_visible}, settings_menu_was_visible: {self.settings_menu_was_visible})")
        else:
            self._show_error_dialog("エラー", f"施設 '{facility_id}' に入れませんでした。")
    
    def _hide_menus_for_facility_entry(self):
        """施設入場時のメニュー隠し処理"""
        # メニューの状態を記録してから隠す
        self.main_menu_was_visible = False
        self.settings_menu_was_visible = False
        
        self._hide_main_menu_for_facility()
        self._hide_settings_menu_for_facility()
    
    def _hide_main_menu_for_facility(self):
        """施設入場時のメインメニュー隠し処理"""
        if self.main_menu:
            try:
                # 現在表示されているかどうかを記録
                self.main_menu_was_visible = True
                ui_manager.hide_menu(self.main_menu.menu_id)
                logger.debug(f"メインメニューを隠しました: {self.main_menu.menu_id}")
            except Exception as hide_error:
                logger.warning(f"メインメニューの非表示処理でエラー: {hide_error}")
    
    def _hide_settings_menu_for_facility(self):
        """施設入場時の設定メニュー隠し処理"""
        # 設定メニューがアクティブな場合も隠す
        if self.settings_menu_active and self.location_menu:
            try:
                self.settings_menu_was_visible = True
                ui_manager.hide_menu(self.location_menu.menu_id)
                logger.debug(f"設定メニューを隠しました: {self.location_menu.menu_id}")
            except Exception as hide_error:
                logger.warning(f"設定メニューの非表示処理でエラー: {hide_error}")
    
    def _back_to_main_menu(self):
        """メインメニューに戻る"""
        if self.location_menu:
            ui_manager.hide_menu(self.location_menu.menu_id)
            self.location_menu = None
        
        self.settings_menu_active = False
        
        if self.main_menu:
            ui_manager.show_menu(self.main_menu.menu_id)
        
        logger.debug("メインメニューに戻りました")
    
    def _show_party_status(self):
        """パーティ状況表示"""
        if not self.current_party:
            return
        
        # 詳細パーティ状況メニューを表示
        party_menu = UIMenu("party_status_menu", "パーティ状況")
        
        # パーティ全体情報
        party_menu.add_menu_item(
            "パーティ全体情報",
            self._show_party_overview
        )
        
        # 各キャラクターの詳細情報
        for i, character in enumerate(self.current_party.get_all_characters()):
            char_info = f"{character.name} (Lv.{character.experience.level})"
            party_menu.add_menu_item(
                char_info,
                self._show_character_details,
                [character]
            )
        
        party_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            lambda: self._back_to_settings_menu(from_party_status=True)
        )
        
        ui_manager.add_menu(party_menu)
        ui_manager.show_menu(party_menu.menu_id, modal=True)
        
        # 設定メニューを隠す
        if self.location_menu:
            ui_manager.hide_menu(self.location_menu.menu_id)
    
    def _format_party_status(self) -> str:
        """パーティ状況をフォーマット"""
        if not self.current_party:
            return "パーティが設定されていません"
        
        lines = [
            f"パーティ名: {self.current_party.name}",
            f"ゴールド: {self.current_party.gold}G",
            f"メンバー数: {len(self.current_party.characters)}",
            ""
        ]
        
        for character in self.current_party.get_all_characters():
            status_line = f"{character.name} Lv.{character.experience.level} "
            status_line += f"({character.get_race_name()}/{character.get_class_name()}) "
            status_line += f"HP:{character.derived_stats.current_hp}/{character.derived_stats.max_hp} "
            status_line += f"MP:{character.derived_stats.current_mp}/{character.derived_stats.max_mp} "
            status_line += f"[{character.status.value}]"
            lines.append(status_line)
        
        return "\n".join(lines)
    
    def _show_party_overview(self):
        """パーティ全体情報をタイル形式で表示"""
        if not self.current_party:
            return
        
        # パーティの統計情報を計算
        characters = self.current_party.get_all_characters()
        total_hp = sum(char.derived_stats.max_hp for char in characters)
        total_mp = sum(char.derived_stats.max_mp for char in characters)
        avg_level = sum(char.experience.level for char in characters) / len(characters) if characters else 0
        
        # 職業構成を計算
        class_counts = {}
        for character in characters:
            class_name = character.get_class_name()
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        class_list = "\n".join([f"{cls}: {count}人" for cls, count in class_counts.items()])
        
        # メンバー一覧を作成
        member_list = "\n".join([
            f"{char.name} Lv.{char.experience.level}\n({char.get_race_name()}/{char.get_class_name()})\n[{char.status.value}]"
            for char in characters[:MAX_DISPLAY_CHARACTERS]  # 最大表示人数まで表示
        ])
        
        # タイルデータを作成
        tiles_data = [
            {
                'title': 'パーティ基本情報',
                'content': f"名前: {self.current_party.name}\nゴールド: {self.current_party.gold}G\nメンバー数: {len(characters)}人"
            },
            {
                'title': 'パーティ戦力',
                'content': f"平均レベル: {avg_level:.1f}\n総HP: {total_hp}\n総MP: {total_mp}"
            },
            {
                'title': '職業構成',
                'content': class_list if class_list else "なし"
            },
            {
                'title': 'メンバー一覧',
                'content': member_list if member_list else "なし"
            },
            {
                'title': '状態異常',
                'content': f"正常: {sum(1 for char in characters if char.status == CharacterStatus.GOOD)}人\n異常: {sum(1 for char in characters if char.status != CharacterStatus.GOOD)}人"
            },
            {
                'title': '探索状況',
                'content': "地上部\n準備完了\n探索可能"
            }
        ]
        
        # 簡易テキスト形式でダイアログを作成・表示
        tile_text = f"【{self.current_party.name}】パーティ全体情報\n\n"
        for tile in tiles_data:
            tile_text += f"■ {tile['title']}\n{tile['content']}\n\n"
        
        dialog = UIDialog(
            "party_overview_dialog",
            f"【{self.current_party.name}】パーティ全体情報",
            tile_text
        )
        
        ui_manager.add_dialog(dialog)
        ui_manager.show_dialog(dialog.dialog_id)
    
    def _show_character_details(self, character):
        """キャラクター詳細情報をタイル形式で表示（エラーハンドリング付き）"""
        try:
            # 基本情報
            basic_info = f"種族: {character.get_race_name()}\n職業: {character.get_class_name()}\nレベル: {character.experience.level}\n経験値: {character.experience.current_xp}\n状態: {character.status.value}"
            
            # HP/MP情報
            hp_mp_info = f"HP: {character.derived_stats.current_hp} / {character.derived_stats.max_hp}\nMP: {character.derived_stats.current_mp} / {character.derived_stats.max_mp}"
            
            # 基本能力値
            base_stats = f"力: {character.base_stats.strength}\n知恵: {character.base_stats.intelligence}\n信仰心: {character.base_stats.faith}\n素早さ: {character.base_stats.agility}\n運: {character.base_stats.luck}\n体力: {character.base_stats.vitality}"
            
            # 戦闘能力
            combat_stats = f"攻撃力: {character.derived_stats.attack_power}\n防御力: {character.derived_stats.defense}\n命中率: {character.derived_stats.accuracy}\n回避率: {character.derived_stats.evasion}\nクリティカル率: {character.derived_stats.critical_chance}"
            
            # 装備品情報
            equipment_info = ""
            try:
                equipment = character.equipment
                weapon = equipment.weapon.get_name() if hasattr(equipment, 'weapon') and equipment.weapon else "なし"
                armor = equipment.armor.get_name() if hasattr(equipment, 'armor') and equipment.armor else "なし"
                shield = equipment.shield.get_name() if hasattr(equipment, 'shield') and equipment.shield else "なし"
                accessory = equipment.accessory.get_name() if hasattr(equipment, 'accessory') and equipment.accessory else "なし"
                equipment_info = f"武器: {weapon}\n防具: {armor}\n盾: {shield}\n装飾品: {accessory}"
            except (AttributeError, Exception) as e:
                equipment_info = "装備情報を取得できません"
                logger.warning(f"装備情報取得エラー: {e}")
            
            # 個人インベントリ
            inventory_info = ""
            try:
                personal_inventory = character.get_personal_inventory()
                if personal_inventory and hasattr(personal_inventory, 'slots') and personal_inventory.slots:
                    items = []
                    for slot in personal_inventory.slots[:MAX_DISPLAY_ITEMS]:  # 最大表示アイテム数まで表示
                        if hasattr(slot, 'is_empty') and not slot.is_empty():
                            item_instance = slot.item_instance
                            if item_instance:
                                item_name = item_instance.get_display_name()
                                if hasattr(item_instance, 'quantity') and item_instance.quantity > 1:
                                    item_name += f" x{item_instance.quantity}"
                                items.append(item_name)
                    inventory_info = "\n".join(items) if items else "なし"
                else:
                    inventory_info = "なし"
            except (AttributeError, Exception) as e:
                inventory_info = "インベントリ情報を取得できません"
                logger.warning(f"インベントリ情報取得エラー: {e}")
            
            # タイルデータを作成
            tiles_data = [
                {
                    'title': '基本情報',
                    'content': basic_info
                },
                {
                    'title': '生命力・魔力',
                    'content': hp_mp_info
                },
                {
                    'title': '基本能力値',
                    'content': base_stats
                },
                {
                    'title': '戦闘能力',
                    'content': combat_stats
                },
                {
                    'title': '装備品',
                    'content': equipment_info
                },
                {
                    'title': '所持品',
                    'content': inventory_info
                }
            ]
            
            # 簡易テキスト形式でダイアログを作成・表示
            char_text = f"【{character.name}】詳細情報\n\n"
            for tile in tiles_data:
                char_text += f"■ {tile['title']}\n{tile['content']}\n\n"
            
            dialog = UIDialog(
                f"character_details_{character.name}",
                f"【{character.name}】詳細情報",
                char_text
            )
            
            ui_manager.add_dialog(dialog)
            ui_manager.show_dialog(dialog.dialog_id)
            
        except (AttributeError, Exception) as e:
            logger.error(f"キャラクター詳細表示エラー: {e}")
            self._show_error_dialog("エラー", f"キャラクター情報の表示中にエラーが発生しました")
    
    def _back_to_settings_menu(self):
        """設定メニューに戻る"""
        # パーティ状況メニューを隠す
        ui_manager.hide_menu("party_status_menu")
        
        # 設定メニューを再表示
        if self.location_menu:
            ui_manager.show_menu(self.location_menu.menu_id)
    
    def _show_save_menu(self):
        """セーブスロット選択メニュー表示"""
        if not self.current_party:
            self._show_error_dialog("エラー", "セーブするパーティがありません")
            return
        
        # 現在のセーブスロット状況を取得
        save_slots = save_manager.get_save_slots()
        save_slot_info = {slot.slot_id: slot for slot in save_slots}
        
        # セーブスロット選択メニューを作成
        save_menu = UIMenu("save_slot_menu", "セーブスロット選択")
        
        # セーブスロットを表示
        for slot_id in range(SAVE_SLOT_RANGE_START, SAVE_SLOT_RANGE_END):
            if slot_id in save_slot_info:
                slot = save_slot_info[slot_id]
                slot_text = f"スロット {slot_id}: {slot.name} (Lv.{slot.party_level}) [{slot.last_saved.strftime('%m/%d %H:%M')}]"
            else:
                slot_text = f"スロット {slot_id}: [空]"
            
            save_menu.add_menu_item(
                slot_text,
                self._save_to_slot,
                [slot_id]
            )
        
        save_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            lambda: self._back_to_settings_menu(from_save_menu=True)
        )
        
        # 現在のメニューを隠してセーブメニューを表示
        if self.location_menu:
            ui_manager.hide_menu(self.location_menu.menu_id)
        
        ui_manager.add_menu(save_menu)
        ui_manager.show_menu(save_menu.menu_id, modal=True)
    
    def _save_to_slot(self, slot_id: int):
        """指定されたスロットにセーブ"""
        if not self.current_party:
            self._show_error_dialog("エラー", "セーブするパーティがありません")
            return
        
        # 既存のセーブがある場合は確認
        save_slots = save_manager.get_save_slots()
        existing_save = next((slot for slot in save_slots if slot.slot_id == slot_id), None)
        
        if existing_save:
            self._show_confirmation_dialog(
                f"スロット {slot_id} には既にセーブデータがあります。\n上書きしますか？",
                lambda: self._confirm_save_to_slot(slot_id)
            )
        else:
            self._confirm_save_to_slot(slot_id)
    
    def _confirm_save_to_slot(self, slot_id: int):
        """セーブ実行"""
        game_state = {
            'location': 'overworld',
            'current_location': self.current_location.value
        }
        
        success = save_manager.save_game(
            party=self.current_party,
            slot_id=slot_id,
            save_name=f"{self.current_party.name} - 町",
            game_state=game_state
        )
        
        if success:
            self._show_info_dialog("セーブ完了", f"スロット {slot_id} にゲームを保存しました")
            # セーブメニューに戻る
            self._back_to_settings_menu(from_save_menu=True)
        else:
            self._show_error_dialog("セーブ失敗", "ゲームの保存に失敗しました。\n詳細はログを確認してください。")
    
    def _show_load_menu(self):
        """ロードメニュー表示"""
        # セーブスロット一覧を取得
        save_slots = save_manager.get_save_slots()
        
        if not save_slots:
            self._show_error_dialog("ロードエラー", "利用可能なセーブデータがありません")
            return
        
        # セーブデータ選択メニューを作成
        load_menu = UIMenu("load_game_menu", "セーブデータ選択")
        
        for slot in save_slots:
            slot_info = f"スロット {slot.slot_id}: {slot.name} (Lv.{slot.party_level})"
            load_menu.add_menu_item(
                slot_info,
                self._load_selected_save,
                [slot.slot_id]
            )
        
        load_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            lambda: self._back_to_settings_menu(from_load_menu=True)
        )
        
        # 現在のメニューを隠してロードメニューを表示
        if self.location_menu:
            ui_manager.hide_menu(self.location_menu.menu_id)
        
        ui_manager.add_menu(load_menu)
        ui_manager.show_menu(load_menu.menu_id, modal=True)
    
    def _load_selected_save(self, slot_id: int):
        """選択されたセーブデータをロード"""
        game_save = save_manager.load_game(slot_id)
        
        if game_save:
            self.current_party = game_save.party
            self._show_info_dialog("ロード完了", f"スロット {slot_id} のデータをロードしました")
            
            # 設定メニューに戻る（メインメニューと重複しないように）
        else:
            self._show_error_dialog("ロード失敗", "セーブデータの読み込みに失敗しました")
    
    def _back_to_settings_menu(self, from_party_status=False, from_save_menu=False, from_load_menu=False):
        """設定メニューに戻る"""
        # パーティ状況メニューからの場合
        if from_party_status:
            ui_manager.hide_menu("party_status_menu")
            # ui_manager.unregister_element("party_status_menu") - 不要
        elif from_save_menu:
            # セーブメニューからの場合
            ui_manager.hide_menu("save_slot_menu")
            # ui_manager.unregister_element("save_slot_menu") - 不要
        else:
            # ロードメニューからの場合
            ui_manager.hide_menu("load_game_menu")
            # ui_manager.unregister_element("load_game_menu") - 不要
        
        # 設定メニューを再表示（メインメニューは表示しない）
        if self.location_menu:
            ui_manager.show_menu(self.location_menu.menu_id)
        else:
            # 設定メニューが存在しない場合は新規作成
            self.show_settings_menu()
    
    def _enter_dungeon(self):
        """ダンジョンに入る"""
        if not self.current_party:
            return
        
        # パーティの状態チェック（生存しているメンバーがいるか確認）
        living_members = self.current_party.get_living_characters()
        if not living_members:
            self._show_error_dialog("エラー", "生存しているメンバーがいません")
            return
        
        # ダンジョン選択UIを表示
        self.dungeon_selection_ui.show_dungeon_selection(
            self.current_party,
            self._on_dungeon_selected,
            self._on_dungeon_selection_cancelled
        )
    
    def _on_dungeon_selected(self, dungeon_id: str):
        """ダンジョンが選択された時の処理"""
        if self.on_enter_dungeon:
            try:
                # ダンジョン遷移を試行（UIは保持）
                self.on_enter_dungeon(dungeon_id)
                # 成功した場合のみexit_overworld()を呼び出し
                self.exit_overworld()
            except Exception as e:
                # ダンジョン遷移に失敗した場合、エラーメッセージを表示してメニューを復元
                logger.error(f"ダンジョン遷移に失敗しました: {e}")
                self._show_dungeon_entrance_error(str(e))
                self._show_main_menu()
    
    def _on_dungeon_selection_cancelled(self):
        """ダンジョン選択がキャンセルされた時の処理"""
        # メインメニューに戻る
        self._show_main_menu()
    
    def _confirm_enter_dungeon(self):
        """ダンジョン入場確認（旧バージョン・互換性維持）"""
        if self.on_enter_dungeon:
            self.exit_overworld()
            self.on_enter_dungeon("main_dungeon")
        else:
            self._show_info_dialog("ダンジョン", "ダンジョンシステムは未実装です")
    
    def _exit_game(self):
        """ゲーム終了"""
        self._show_confirmation_dialog(
            config_manager.get_text("system.exit_confirm"),
            self._confirm_exit_game
        )
    
    def _confirm_exit_game(self):
        """ゲーム終了確認"""
        if self.on_exit_game:
            self.exit_overworld()
            self.on_exit_game()
        else:
            logger.info("ゲーム終了が要求されました")
    
    def _show_game_settings(self):
        """ゲーム設定画面の表示"""
        settings_text = "ゲーム設定\n\n"
        settings_text += f"言語: {config_manager.current_language}\n"
        settings_text += f"音量: {config_manager.get_config('game_config', 'audio', {}).get('master_volume', 0.8):.1f}\n"
        settings_text += f"フルスクリーン: {config_manager.get_config('game_config', 'window', {}).get('fullscreen', False)}\n"
        settings_text += "\n設定変更は今後のアップデートで対応予定です。"
        
        self._show_info_dialog("ゲーム設定", settings_text)
    
    def _show_info_dialog(self, title: str, message: str):
        """情報ダイアログの表示"""
        dialog = UIDialog(
            DIALOG_ID_INFO,
            title,
            message,
            buttons=[
                {
                    'text': config_manager.get_text("common.ok"),
                    'command': self._close_dialog
                }
            ]
        )
        
        ui_manager.add_dialog(dialog)
        ui_manager.show_dialog(dialog.dialog_id)
    
    def _show_error_dialog(self, title: str, message: str):
        """エラーダイアログの表示"""
        self._show_info_dialog(title, message)
    
    def _show_confirmation_dialog(self, message: str, on_confirm: Callable):
        """確認ダイアログの表示"""
        # テキストキャッシュをリロードして最新の設定を取得
        config_manager.reload_all()
        
        dialog = UIDialog(
            DIALOG_ID_CONFIRM,
            config_manager.get_text("common.confirm"),
            message,
            buttons=[
                {
                    'text': config_manager.get_text("common.yes"),
                    'command': lambda: (self._close_dialog(), on_confirm())
                },
                {
                    'text': config_manager.get_text("common.no"),
                    'command': self._close_dialog
                }
            ]
        )
        
        ui_manager.add_dialog(dialog)
        ui_manager.show_dialog(dialog.dialog_id)
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        # 現在表示中のダイアログを探して閉じる
        for dialog_id in DIALOG_IDS_ALL:
            ui_manager.hide_dialog(dialog_id)
    
    def _cleanup_ui(self):
        """UI要素のクリーンアップ"""
        if self.main_menu:
            ui_manager.hide_menu(self.main_menu.menu_id)
            # ui_manager.unregister_element(self.main_menu.menu_id) - 不要
            self.main_menu = None
        
        if self.location_menu:
            ui_manager.hide_menu(self.location_menu.menu_id)
            # ui_manager.unregister_element(self.location_menu.menu_id) - 不要
            self.location_menu = None
        
        self._close_dialog()
    
    def _emergency_menu_recovery(self):
        """緊急メニュー復元処理"""
        logger.info("緊急メニュー復元を開始します")
        
        try:
            # 全てのUI要素をクリーンアップ
            self._cleanup_ui()
            
            # 状態をリセット
            self.settings_menu_active = False
            
            # メインメニューを強制再生成
            self._show_main_menu()
            
            logger.info("緊急メニュー復元が完了しました")
            
        except Exception as e:
            logger.error(f"緊急メニュー復元中にエラー: {e}")
            raise
    
    def _show_dungeon_entrance_error(self, error_message: str):
        """ダンジョン入場エラー表示"""
        error_title = config_manager.get_text("dungeon.entrance_error_title", "ダンジョン入場エラー")
        error_prefix = config_manager.get_text("dungeon.entrance_error_prefix", "ダンジョンに入場できませんでした:")
        
        ui_manager.show_dialog(
            title=error_title,
            message=f"{error_prefix}\n{error_message}"
        )
    
    def _emergency_overworld_reset(self):
        """緊急地上部リセット処理"""
        logger.critical("緊急地上部リセットを実行します")
        
        try:
            # パーティ情報を保持
            saved_party = self.current_party
            
            # 地上部を一度完全にリセット
            self.exit_overworld()
            
            # パーティがある場合は再入場
            if saved_party:
                self.enter_overworld(saved_party)
                logger.info("緊急リセット後、パーティを地上部に復帰させました")
            else:
                # パーティがない場合は最低限のメニューを表示
                self.is_active = True
                self._show_main_menu()
                logger.warning("パーティ情報なしで地上部をリセットしました")
                
        except Exception as e:
            logger.critical(f"緊急地上部リセットでエラー: {e}")
            # 最終的にアプリケーションの終了も検討する必要がある
    
    def on_facility_exit(self):
        """施設退場時のコールバック"""
        # 施設から出たら地上部メニューに戻る
        if not self.is_active:
            return
        
        logger.info("【重要】施設退場処理を開始します - コールバックが正常に呼ばれました")
        logger.debug("施設退場処理を開始します")
        
        try:
            # 最初に確実にメニューが表示されることを保証する
            menu_restored = False
            
            logger.debug(f"施設退場前の状態: main_menu_was_visible={self.main_menu_was_visible}, settings_menu_was_visible={self.settings_menu_was_visible}, settings_menu_active={self.settings_menu_active}")
            
            # 設定画面が表示されている場合はそちらを表示
            if self.settings_menu_active and self.location_menu:
                # 設定メニューが正常に存在するか確認
                if self.location_menu.menu_id in ui_manager.menus:
                    try:
                        ui_manager.show_menu(self.location_menu.menu_id)
                        menu_restored = True
                        logger.debug("設定メニューに戻りました")
                    except Exception as show_error:
                        logger.warning(f"設定メニューの表示に失敗: {show_error}")
                        # 設定メニューが破損している場合は状態をリセット
                        self.settings_menu_active = False
                        self.location_menu = None
                else:
                    # 設定メニューが破棄されている場合は状態をリセット
                    logger.warning("設定メニューが見つからないため状態をリセットします")
                    self.settings_menu_active = False
                    self.location_menu = None
            
            # 設定メニューが表示できなかった場合、またはそもそも設定メニューが非アクティブの場合
            if not menu_restored:
                # 施設入場前の状態に基づいてメニューを復元
                if self.main_menu_was_visible and self.main_menu:
                    # メインメニューが入場前に表示されていた場合
                    if self.main_menu.menu_id in ui_manager.menus:
                        try:
                            # 強制的に表示
                            ui_manager.show_menu(self.main_menu.menu_id)
                            menu_restored = True
                            logger.debug("メインメニューを復元しました（入場前状態に基づく）")
                        except Exception as show_error:
                            logger.warning(f"メインメニューの復元に失敗: {show_error}")
                    else:
                        logger.warning("復元すべきメインメニューがUIManagerに見つかりません")
                
                # メインメニューの復元に失敗した場合、または入場前に表示されていなかった場合
                if not menu_restored:
                    logger.warning("メインメニューの復元に失敗または不要なため、新しいメニューを表示します")
                    try:
                        # 既存のメニューをクリーンアップしてから再生成
                        if self.main_menu:
                            try:
                                ui_manager.hide_menu(self.main_menu.menu_id)
                                # ui_manager.unregister_element(self.main_menu.menu_id) - 不要
                            except:
                                pass  # クリーンアップに失敗しても続行
                        
                        self._show_main_menu()
                        menu_restored = True
                        logger.info("メインメニューを再生成しました")
                    except Exception as regen_error:
                        logger.error(f"メインメニュー再生成に失敗: {regen_error}")
            
            # 状態フラグをリセット
            self.main_menu_was_visible = False
            self.settings_menu_was_visible = False
            
            # 何らかの方法でメニューが復元されたかを確認
            if not menu_restored:
                logger.error("全てのメニュー復元方法が失敗しました")
                raise RuntimeError("メニューの復元に完全に失敗しました")
            
        except Exception as e:
            # 全ての復元処理が失敗した場合の最終的なフェイルセーフ
            logger.error(f"施設退場時のメニュー復元でエラーが発生: {e}")
            logger.info("緊急メニュー復元を実行します")
            
            try:
                # UI状態をクリアして再生成
                self._emergency_menu_recovery()
                logger.info("緊急メニュー復元が完了しました")
            except Exception as recovery_error:
                logger.critical(f"緊急メニュー復元も失敗: {recovery_error}")
                # 最後の手段：地上部をリセット
                logger.critical("最終手段として地上部リセットを実行します")
                self._emergency_overworld_reset()
    
    def get_current_party(self) -> Optional[Party]:
        """現在のパーティを取得"""
        return self.current_party
    
    def set_enter_dungeon_callback(self, callback: Callable):
        """ダンジョン入場コールバックを設定"""
        self.on_enter_dungeon = callback
    
    def set_exit_game_callback(self, callback: Callable):
        """ゲーム終了コールバックを設定"""
        self.on_exit_game = callback


# グローバルインスタンス
overworld_manager = OverworldManager()