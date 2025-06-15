"""地上部管理システム"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.overworld.base_facility import BaseFacility, FacilityManager, facility_manager
from src.ui.base_ui import UIMenu, UIDialog, ui_manager
from src.core.config_manager import config_manager
from src.core.save_manager import save_manager
from src.utils.logger import logger


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
        
        # コールバック
        self.on_enter_dungeon: Optional[Callable] = None
        self.on_exit_game: Optional[Callable] = None
        
        self.facility_manager = facility_manager
        
        logger.info("OverworldManagerを初期化しました")
    
    def enter_overworld(self, party: Party, from_dungeon: bool = False) -> bool:
        """地上部に入る"""
        if self.is_active:
            logger.warning("地上部は既にアクティブです")
            return False
        
        self.current_party = party
        self.current_location = OverworldLocation.TOWN_CENTER
        self.is_active = True
        
        # ダンジョンから戻った場合の自動回復
        if from_dungeon:
            self._auto_recovery()
        
        # メインメニューを表示
        self._show_main_menu()
        
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
            # HP・MP全回復
            old_hp = character.derived_stats.current_hp
            old_mp = character.derived_stats.current_mp
            
            character.derived_stats.current_hp = character.derived_stats.max_hp
            character.derived_stats.current_mp = character.derived_stats.max_mp
            
            # 状態異常解除（死亡・灰化以外）
            old_status = character.status
            if character.status not in [CharacterStatus.DEAD, CharacterStatus.ASHES]:
                character.status = CharacterStatus.GOOD
            
            # 回復したキャラクターを記録
            if (old_hp < character.derived_stats.max_hp or 
                old_mp < character.derived_stats.max_mp or 
                old_status != character.status):
                recovered_characters.append(character.name)
        
        # TODO: Phase 4で魔法使用回数もリセット予定
        
        if recovered_characters:
            recovery_message = f"地上部に戻りました！\n{', '.join(recovered_characters)} が回復しました。"
            self._show_info_dialog("自動回復", recovery_message)
            logger.info(f"自動回復実行: {len(recovered_characters)} 人のキャラクターが回復")
        
        logger.info("地上部帰還時の自動回復を実行しました")
    
    def _show_main_menu(self):
        """メインメニューの表示"""
        if self.main_menu:
            ui_manager.unregister_element(self.main_menu.element_id)
        
        self.main_menu = UIMenu("overworld_main_menu", config_manager.get_text("overworld.town_center"))
        
        # 施設への移動
        self.main_menu.add_menu_item(
            config_manager.get_text("menu.facilities"),
            self._show_location_menu
        )
        
        # パーティ状況確認
        self.main_menu.add_menu_item(
            config_manager.get_text("menu.party_status"),
            self._show_party_status
        )
        
        # セーブ・ロード
        self.main_menu.add_menu_item(
            config_manager.get_text("menu.save_game"),
            self._show_save_menu
        )
        
        self.main_menu.add_menu_item(
            config_manager.get_text("menu.load_game"),
            self._show_load_menu
        )
        
        # ダンジョンへ
        self.main_menu.add_menu_item(
            config_manager.get_text("facility.dungeon_entrance"),
            self._enter_dungeon
        )
        
        # ゲーム終了
        self.main_menu.add_menu_item(
            config_manager.get_text("menu.exit"),
            self._exit_game
        )
        
        ui_manager.register_element(self.main_menu)
        ui_manager.show_element(self.main_menu.element_id, modal=True)
    
    def _show_location_menu(self):
        """施設選択メニューの表示"""
        if self.location_menu:
            ui_manager.unregister_element(self.location_menu.element_id)
        
        self.location_menu = UIMenu("location_menu", config_manager.get_text("overworld.facility_selection"))
        
        # 各施設への移動
        facilities = [
            ("guild", config_manager.get_text("facility.guild")),
            ("inn", config_manager.get_text("facility.inn")),
            ("shop", config_manager.get_text("facility.shop")),
            ("temple", config_manager.get_text("facility.temple")),
            ("magic_guild", config_manager.get_text("facility.magic_guild"))
        ]
        
        for facility_id, facility_name in facilities:
            self.location_menu.add_menu_item(
                facility_name,
                self._enter_facility,
                [facility_id]
            )
        
        # 戻る
        self.location_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu
        )
        
        ui_manager.register_element(self.location_menu)
        ui_manager.show_element(self.location_menu.element_id, modal=True)
        
        # メインメニューを隠す
        ui_manager.hide_element(self.main_menu.element_id)
    
    def _enter_facility(self, facility_id: str):
        """施設に入る"""
        if not self.current_party:
            return
        
        success = self.facility_manager.enter_facility(facility_id, self.current_party)
        
        if success:
            # 施設メニューが表示されるので、地上部メニューを隠す
            ui_manager.hide_element(self.location_menu.element_id)
            logger.info(f"施設に入りました: {facility_id}")
        else:
            self._show_error_dialog("エラー", f"施設 '{facility_id}' に入れませんでした。")
    
    def _back_to_main_menu(self):
        """メインメニューに戻る"""
        if self.location_menu:
            ui_manager.hide_element(self.location_menu.element_id)
            ui_manager.unregister_element(self.location_menu.element_id)
            self.location_menu = None
        
        ui_manager.show_element(self.main_menu.element_id)
    
    def _show_party_status(self):
        """パーティ状況表示"""
        if not self.current_party:
            return
        
        status_text = self._format_party_status()
        
        self._show_info_dialog("パーティ状況", status_text)
    
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
    
    def _show_save_menu(self):
        """セーブメニュー表示"""
        # 簡易版: クイックセーブ
        if not self.current_party:
            self._show_error_dialog("エラー", "セーブするパーティがありません")
            return
        
        game_state = {
            'location': 'overworld',
            'current_location': self.current_location.value
        }
        
        success = save_manager.save_game(
            party=self.current_party,
            slot_id=1,
            save_name=f"{self.current_party.name} - 町",
            game_state=game_state
        )
        
        if success:
            self._show_info_dialog("セーブ完了", "ゲームを保存しました")
        else:
            self._show_error_dialog("セーブ失敗", "ゲームの保存に失敗しました")
    
    def _show_load_menu(self):
        """ロードメニュー表示"""
        # 簡易版: スロット1からロード
        game_save = save_manager.load_game(1)
        
        if game_save:
            self.current_party = game_save.party
            self._show_info_dialog("ロード完了", "ゲームをロードしました")
            
            # メインメニューを更新
            self._show_main_menu()
        else:
            self._show_error_dialog("ロード失敗", "セーブデータが見つかりません")
    
    def _enter_dungeon(self):
        """ダンジョンに入る"""
        if not self.current_party:
            return
        
        # パーティの状態チェック
        conscious_members = self.current_party.get_conscious_characters()
        if not conscious_members:
            self._show_error_dialog("エラー", "意識のあるメンバーがいません")
            return
        
        # ダンジョン入場確認
        self._show_confirmation_dialog(
            "ダンジョンに入りますか？",
            self._confirm_enter_dungeon
        )
    
    def _confirm_enter_dungeon(self):
        """ダンジョン入場確認"""
        if self.on_enter_dungeon:
            self.exit_overworld()
            self.on_enter_dungeon(self.current_party)
        else:
            self._show_info_dialog("ダンジョン", "ダンジョンシステムは未実装です")
    
    def _exit_game(self):
        """ゲーム終了"""
        self._show_confirmation_dialog(
            "ゲームを終了しますか？",
            self._confirm_exit_game
        )
    
    def _confirm_exit_game(self):
        """ゲーム終了確認"""
        if self.on_exit_game:
            self.exit_overworld()
            self.on_exit_game()
        else:
            logger.info("ゲーム終了が要求されました")
    
    def _show_info_dialog(self, title: str, message: str):
        """情報ダイアログの表示"""
        dialog = UIDialog(
            "overworld_info_dialog",
            title,
            message,
            buttons=[
                {
                    'text': config_manager.get_text("common.ok"),
                    'command': self._close_dialog
                }
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id)
    
    def _show_error_dialog(self, title: str, message: str):
        """エラーダイアログの表示"""
        self._show_info_dialog(title, message)
    
    def _show_confirmation_dialog(self, message: str, on_confirm: Callable):
        """確認ダイアログの表示"""
        dialog = UIDialog(
            "overworld_confirm_dialog",
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
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id)
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        # 現在表示中のダイアログを探して閉じる
        for element_id in ["overworld_info_dialog", "overworld_confirm_dialog"]:
            element = ui_manager.get_element(element_id)
            if element:
                ui_manager.hide_element(element_id)
                ui_manager.unregister_element(element_id)
    
    def _cleanup_ui(self):
        """UI要素のクリーンアップ"""
        if self.main_menu:
            ui_manager.hide_element(self.main_menu.element_id)
            ui_manager.unregister_element(self.main_menu.element_id)
            self.main_menu = None
        
        if self.location_menu:
            ui_manager.hide_element(self.location_menu.element_id)
            ui_manager.unregister_element(self.location_menu.element_id)
            self.location_menu = None
        
        self._close_dialog()
    
    def on_facility_exit(self):
        """施設退場時のコールバック"""
        # 施設から出たら地上部メニューに戻る
        if self.is_active and self.main_menu:
            if self.location_menu:
                ui_manager.show_element(self.location_menu.element_id)
            else:
                ui_manager.show_element(self.main_menu.element_id)
    
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