"""地上部管理システム（Pygame版）"""

from typing import Optional, Callable
import pygame
from src.character.party import Party
from src.ui.base_ui_pygame import UIMenu, UIButton, UIText
from src.ui.selection_list_ui import CustomSelectionList, SelectionListData
from src.ui.menu_stack_manager import MenuStackManager, MenuType
from src.utils.logger import logger
from src.core.config_manager import config_manager


class OverworldManager:
    """地上部管理クラス（Pygame版）"""
    
    def __init__(self):
        self.current_party: Optional[Party] = None
        self.ui_manager = None
        self.input_manager = None
        
        # コールバック
        self.enter_dungeon_callback: Optional[Callable] = None
        self.exit_game_callback: Optional[Callable] = None
        
        # UI要素
        self.main_menu: Optional[UIMenu] = None
        self.settings_menu: Optional[UIMenu] = None
        self.dungeon_selection_list: Optional[CustomSelectionList] = None
        self.is_active = False
        self.settings_active = False
        
        # MenuStackManager（統一されたメニュー管理）
        self.menu_stack_manager: Optional[MenuStackManager] = None
        
        logger.info("OverworldManager（Pygame版）を初期化しました")
    
    def set_ui_manager(self, ui_manager):
        """UIマネージャーを設定"""
        self.ui_manager = ui_manager
        
        # MenuStackManagerを初期化
        self.menu_stack_manager = MenuStackManager(ui_manager)
        self.menu_stack_manager.on_escape_pressed = self._handle_escape_from_menu_stack
        
        self._create_main_menu()
        self._create_settings_menu()
        self.setup_facility_callbacks()
        
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
        # メインメニューを再表示（モーダルとして）
        if self.main_menu:
            self.ui_manager.show_menu(self.main_menu.menu_id, modal=True)
        else:
            self._create_main_menu()
            if self.main_menu:
                self.ui_manager.show_menu(self.main_menu.menu_id, modal=True)
    
    def _create_main_menu(self):
        """メインメニューを作成（6つの施設 + 設定画面）"""
        if not self.ui_manager:
            return
        
        # メインメニュー作成（日本語対応フォント使用）
        self.main_menu = UIMenu("overworld_main", "地上マップ")
        
        # 6つの施設ボタンを作成（2列3行レイアウト）
        # 左列
        guild_button = UIButton("guild", "冒険者ギルド", 150, 200, 200, 50)
        guild_button.on_click = self._on_guild
        self.main_menu.add_element(guild_button)
        
        inn_button = UIButton("inn", "宿屋", 150, 270, 200, 50)
        inn_button.on_click = self._on_inn
        self.main_menu.add_element(inn_button)
        
        shop_button = UIButton("shop", "商店", 150, 340, 200, 50)
        shop_button.on_click = self._on_shop
        self.main_menu.add_element(shop_button)
        
        # 右列
        temple_button = UIButton("temple", "教会", 450, 200, 200, 50)
        temple_button.on_click = self._on_temple
        self.main_menu.add_element(temple_button)
        
        magic_guild_button = UIButton("magic_guild", "魔術師ギルド", 450, 270, 200, 50)
        magic_guild_button.on_click = self._on_magic_guild
        self.main_menu.add_element(magic_guild_button)
        
        dungeon_button = UIButton("enter_dungeon", "ダンジョン入口", 450, 340, 200, 50)
        dungeon_button.on_click = self._on_enter_dungeon
        self.main_menu.add_element(dungeon_button)
        
        # 設定画面への案内テキスト
        help_text = UIText("esc_help", "[ESC] 設定画面", 300, 450)
        self.main_menu.add_element(help_text)
        
        # UIマネージャーに追加
        self.ui_manager.add_menu(self.main_menu)
        
        logger.info("オーバーワールドメインメニューを作成しました（6施設対応）")
    
    def _create_settings_menu(self):
        """設定画面を作成"""
        if not self.ui_manager:
            return
        
        # 設定メニュー作成
        self.settings_menu = UIMenu("settings_menu", "設定画面")
        
        # パーティ状況ボタン
        party_status_button = UIButton("party_status", "パーティ状況", 250, 200, 300, 50)
        party_status_button.on_click = self._on_party_status
        self.settings_menu.add_element(party_status_button)
        
        # ゲームを保存ボタン
        save_button = UIButton("save_game", "ゲームを保存", 250, 270, 300, 50)
        save_button.on_click = self._on_save_game
        self.settings_menu.add_element(save_button)
        
        # ゲームをロードボタン
        load_button = UIButton("load_game", "ゲームをロード", 250, 340, 300, 50)
        load_button.on_click = self._on_load_game
        self.settings_menu.add_element(load_button)
        
        # 設定ボタン
        config_button = UIButton("config", "設定", 250, 410, 300, 50)
        config_button.on_click = self._on_config
        self.settings_menu.add_element(config_button)
        
        # 終了ボタン
        exit_button = UIButton("exit_game", "終了", 250, 480, 300, 50)
        exit_button.on_click = self._on_exit_game
        self.settings_menu.add_element(exit_button)
        
        # 戻るボタン
        back_button = UIButton("back_to_overworld", "戻る", 250, 550, 300, 50)
        back_button.on_click = self._on_back_to_overworld
        self.settings_menu.add_element(back_button)
        
        # UIマネージャーに追加（最初は非表示）
        self.ui_manager.add_menu(self.settings_menu)
        self.settings_menu.hide()
        
        logger.info("設定画面メニューを作成しました")
    
    def _on_enter_dungeon(self):
        """ダンジョン入場 - 選択画面を表示"""
        logger.info("ダンジョン入場が選択されました")
        self._show_dungeon_selection_menu()
    
    def _show_dungeon_selection_menu(self):
        """ダンジョン選択画面をUISelectionListで表示"""
        logger.info("ダンジョン選択画面を表示します")
        
        if not self.ui_manager:
            logger.error("UIマネージャーが設定されていません")
            return
        
        # メインメニューを隠す
        if self.main_menu:
            self.ui_manager.hide_menu(self.main_menu.menu_id)
        
        # UISelectionListを使用したダンジョン選択
        list_rect = pygame.Rect(100, 100, 600, 500)
        
        self.dungeon_selection_list = CustomSelectionList(
            relative_rect=list_rect,
            manager=self.ui_manager.pygame_gui_manager,
            title="ダンジョン選択"
        )
        
        # ダンジョン一覧を追加
        available_dungeons = self._get_available_dungeons()
        logger.info(f"取得したダンジョン数: {len(available_dungeons)}")
        
        if available_dungeons:
            for dungeon in available_dungeons:
                dungeon_info = self._format_dungeon_info(dungeon)
                logger.info(f"ダンジョン追加: {dungeon_info}")
                dungeon_data = SelectionListData(
                    display_text=dungeon_info,
                    data=dungeon,
                    callback=lambda d=dungeon: self._enter_selected_dungeon(d['id'])
                )
                self.dungeon_selection_list.add_item(dungeon_data)
        
        # 管理機能を追加
        new_dungeon_data = SelectionListData(
            display_text="🆕 ダンジョン新規生成",
            data=None,
            callback=self._generate_new_dungeon
        )
        self.dungeon_selection_list.add_item(new_dungeon_data)
        
        if available_dungeons:
            delete_dungeon_data = SelectionListData(
                display_text="🗑 ダンジョン破棄",
                data=None,
                callback=self._show_dungeon_deletion_menu
            )
            self.dungeon_selection_list.add_item(delete_dungeon_data)
        
        back_data = SelectionListData(
            display_text="⬅ 戻る",
            data=None,
            callback=self._close_dungeon_selection_menu
        )
        self.dungeon_selection_list.add_item(back_data)
        
        # 表示
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
        if self.enter_dungeon_callback:
            try:
                # ダンジョン選択メニューを隠す
                self.ui_manager.hide_menu("dungeon_selection_menu")
                self.is_active = False
                
                # ダンジョンに遷移
                self.enter_dungeon_callback(dungeon_id)
            except Exception as e:
                logger.error(f"ダンジョン入場エラー: {e}")
                # エラーの場合はメニューを再表示
                self._show_dungeon_selection_menu()
    
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
        # メニューを再表示
        self._show_dungeon_selection_menu()
    
    def _close_dungeon_selection_menu(self):
        """ダンジョン選択メニューを閉じて地上メニューに戻る"""
        logger.info("ダンジョン選択メニューを閉じます")
        
        # UISelectionListを非表示にして破棄
        if self.dungeon_selection_list:
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
            
            # UIダイアログでパーティ情報を表示
            from src.ui.base_ui_pygame import UIDialog, UIButton
            party_dialog = UIDialog("party_status_dialog", "パーティ状況", info_text)
            
            # OKボタンを追加
            ok_button = UIButton("party_status_ok", "OK", 400, 600, 100, 40)
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
        
        # セーブスロット選択メニューを作成
        save_slot_menu = UIMenu("save_slot_selection_menu", "セーブスロット選択")
        
        # 利用可能なセーブスロットを取得
        save_slots = self._get_save_slots()
        
        for slot in save_slots:
            slot_info = self._format_save_slot_info(slot)
            save_slot_menu.add_menu_item(
                slot_info,
                self._save_to_slot,
                [slot['slot_id']]
            )
        
        # 戻るボタン
        save_slot_menu.add_menu_item(
            "戻る",
            self._close_save_slot_selection
        )
        
        # メニューを表示
        self.ui_manager.add_menu(save_slot_menu)
        self.ui_manager.show_menu(save_slot_menu.menu_id, modal=True)
        
        logger.info("セーブスロット選択メニューを表示しました")
    
    def _show_load_slot_selection(self):
        """ロードスロット選択画面を表示"""
        logger.info("ロードスロット選択画面を表示します")
        
        if not self.ui_manager:
            logger.error("UIマネージャーが設定されていません")
            return
        
        # 設定メニューを隠す
        if self.settings_menu:
            self.ui_manager.hide_menu(self.settings_menu.menu_id)
        
        # ロードスロット選択メニューを作成
        load_slot_menu = UIMenu("load_slot_selection_menu", "ロードスロット選択")
        
        # 利用可能なセーブスロットを取得
        save_slots = self._get_save_slots()
        
        # ロード可能なスロットのみ表示
        loadable_slots = [slot for slot in save_slots if slot['is_used']]
        
        if loadable_slots:
            for slot in loadable_slots:
                slot_info = self._format_save_slot_info(slot)
                load_slot_menu.add_menu_item(
                    slot_info,
                    self._load_from_slot,
                    [slot['slot_id']]
                )
        else:
            # ロード可能なスロットがない場合
            load_slot_menu.add_menu_item(
                "ロード可能なセーブデータがありません",
                lambda: None
            )
        
        # 戻るボタン
        load_slot_menu.add_menu_item(
            "戻る",
            self._close_load_slot_selection
        )
        
        # メニューを表示
        self.ui_manager.add_menu(load_slot_menu)
        self.ui_manager.show_menu(load_slot_menu.menu_id, modal=True)
        
        logger.info("ロードスロット選択メニューを表示しました")
    
    def _get_save_slots(self):
        """セーブスロット情報を取得"""
        # TODO: 実際のセーブデータストレージから取得
        # 現在は仮のデータを返す
        import datetime
        
        return [
            {
                "slot_id": 1,
                "is_used": True,
                "save_time": "2025-06-23 10:30:00",
                "party_name": "勇者の一行",
                "play_time": "05:30:15",
                "location": "地上・冒険者ギルド",
                "party_level": 5,
                "gold": 1500
            },
            {
                "slot_id": 2,
                "is_used": False,
                "save_time": None,
                "party_name": None,
                "play_time": None,
                "location": None,
                "party_level": None,
                "gold": None
            },
            {
                "slot_id": 3,
                "is_used": True,
                "save_time": "2025-06-22 18:45:30",
                "party_name": "冒険者チーム",
                "play_time": "02:15:45",
                "location": "地上・商店",
                "party_level": 3,
                "gold": 800
            },
            {
                "slot_id": 4,
                "is_used": False,
                "save_time": None,
                "party_name": None,
                "play_time": None,
                "location": None,
                "party_level": None,
                "gold": None
            },
            {
                "slot_id": 5,
                "is_used": False,
                "save_time": None,
                "party_name": None,
                "play_time": None,
                "location": None,
                "party_level": None,
                "gold": None
            }
        ]
    
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
        logger.info("設定画面を表示（未実装）")
    
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
        """設定画面を表示"""
        if self.main_menu:
            self.ui_manager.hide_menu(self.main_menu.menu_id)
        if self.settings_menu:
            self.settings_menu.show()
        self.settings_active = True
        logger.info("設定画面を表示しました")
    
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
            
            # UIマネージャーが設定されていない場合は後で設定
            if self.ui_manager and not self.main_menu:
                self._create_main_menu()
            
            # MenuStackManagerを使用してメインメニューを表示
            if self.main_menu and self.menu_stack_manager:
                # スタックをクリアしてからROOTメニューを追加
                self.menu_stack_manager.clear_stack()
                self.menu_stack_manager.push_menu(self.main_menu, MenuType.ROOT)
            elif self.main_menu:
                # フォールバック：従来の方法
                self.ui_manager.show_menu(self.main_menu.menu_id, modal=True)
            
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
            try:
                # システムフォントで日本語フォントを試す
                font = pygame.font.SysFont('notosanscjk,noto,ipagothic,takao,hiragino,meiryo,msgothic', 24)
            except:
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
    
    def _handle_escape_from_menu_stack(self) -> bool:
        """MenuStackManagerからのESCキー処理コールバック"""
        try:
            # MenuStackManagerが現在のメニュー状態に応じて適切に処理
            # ROOTメニュー（地上マップ）の場合は設定画面表示
            # その他の場合は前のメニューに戻る
            current_entry = self.menu_stack_manager.peek_current_menu()
            
            if current_entry and current_entry.menu_type == MenuType.ROOT:
                # 地上マップから設定画面へ
                self._show_settings_menu()
                return True
            elif current_entry and current_entry.menu_type == MenuType.SETTINGS:
                # 設定画面から地上マップへ
                self._hide_settings_menu()
                self._show_main_menu()
                return True
            
            # その他の場合はMenuStackManagerにデフォルト処理を委譲
            return False
            
        except Exception as e:
            logger.error(f"ESCキー処理エラー: {e}")
            return False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理"""
        if not self.is_active:
            return False
        
        # UISelectionListのイベント処理
        if self.dungeon_selection_list:
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
                if self.dungeon_selection_list:
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