"""冒険者ギルド"""

from typing import Dict, List, Optional, Any
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.character import Character
from src.character.party import Party, PartyPosition
from src.ui.base_ui_pygame import UIMenu, UIDialog, ui_manager
from src.ui.character_creation import CharacterCreationWizard
from src.core.config_manager import config_manager
from src.utils.logger import logger


class AdventurersGuild(BaseFacility):
    """冒険者ギルド"""
    
    def __init__(self):
        super().__init__(
            facility_id="guild",
            facility_type=FacilityType.GUILD,
            name_key="facility.guild"
        )
        
        # 作成済みキャラクターの一時保存
        self.created_characters: List[Character] = []
    
    def _setup_menu_items(self, menu: UIMenu):
        """ギルド固有のメニュー項目を設定"""
        menu.add_menu_item(
            config_manager.get_text("guild.menu.character_creation"),
            self._show_character_creation
        )
        
        menu.add_menu_item(
            config_manager.get_text("guild.menu.party_formation"),
            self._show_party_formation
        )
        
        menu.add_menu_item(
            config_manager.get_text("guild.menu.character_list"),
            self._show_character_list
        )
        
        menu.add_menu_item(
            config_manager.get_text("guild.menu.class_change"),
            self._show_class_change
        )
    
    def _on_enter(self):
        """ギルド入場時の処理"""
        logger.info("冒険者ギルドに入りました")
    
    def _on_exit(self):
        """ギルド退場時の処理"""
        logger.info("冒険者ギルドから出ました")
    
    def _show_character_creation(self):
        """キャラクター作成ウィザードを表示"""
        # メインメニューを隠す
        if self.main_menu:
            ui_manager.hide_menu(self.main_menu.menu_id)
        
        # キャラクター作成ウィザードを起動
        wizard = CharacterCreationWizard(callback=self._on_character_created)
        # キャンセル時のコールバックを設定
        wizard.on_cancel = self._on_character_creation_cancelled
        wizard.start()
    
    def _on_character_created(self, character: Character):
        """キャラクター作成完了時のコールバック"""
        logger.info(f"キャラクター作成完了コールバック開始: {character.name}")
        
        self.created_characters.append(character)
        
        # 成功メッセージ
        self._show_success_message(config_manager.get_text("guild.messages.character_created").format(name=character.name))
        
        # メインメニューを再表示
        if self.main_menu:
            logger.info("ギルドメインメニューを再表示")
            ui_manager.show_menu(self.main_menu.menu_id, modal=True)
        else:
            logger.warning("main_menuが存在しません")
        
        logger.info(f"新しいキャラクターを作成: {character.name}")
    
    def _on_character_creation_cancelled(self):
        """キャラクター作成キャンセル時のコールバック"""
        # メインメニューを再表示
        if self.main_menu:
            ui_manager.show_menu(self.main_menu.menu_id, modal=True)
        
        logger.info("キャラクター作成がキャンセルされ、ギルドメインメニューに戻りました")
    
    def _show_party_formation(self):
        """パーティ編成画面を表示"""
        if not self.current_party:
            self._show_error_message(config_manager.get_text("guild.messages.no_party_set"))
            return
        
        # 利用可能なキャラクター（作成済み + 現在のパーティメンバー）
        available_chars = self.created_characters.copy()
        party_chars = list(self.current_party.characters.values())
        
        # パーティ編成メニューを作成
        formation_menu = UIMenu("party_formation_menu", config_manager.get_text("guild.party_formation.title"))
        
        # 現在のパーティ状況を表示
        formation_menu.add_menu_item(
            config_manager.get_text("guild.party_formation.check_current"),
            self._show_current_formation
        )
        
        # キャラクター追加
        if len(self.current_party.characters) < 6:
            formation_menu.add_menu_item(
                config_manager.get_text("guild.party_formation.add_character"),
                self._show_add_character_menu
            )
        
        # キャラクター削除
        if len(self.current_party.characters) > 0:
            formation_menu.add_menu_item(
                config_manager.get_text("guild.party_formation.remove_character"),
                self._show_remove_character_menu
            )
        
        # 位置変更
        if len(self.current_party.characters) > 1:
            formation_menu.add_menu_item(
                config_manager.get_text("guild.party_formation.change_position"),
                self._show_position_menu
            )
        
        # 戻る
        formation_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [formation_menu]
        )
        
        # メインメニューを隠して編成メニューを表示
        if self.main_menu:
            ui_manager.hide_menu(self.main_menu.menu_id)
        
        ui_manager.add_menu(formation_menu)
        ui_manager.show_menu(formation_menu.menu_id, modal=True)
    
    def _show_current_formation(self):
        """現在の編成を表示"""
        if not self.current_party:
            return
        
        formation_text = self._format_party_formation()
        self._show_dialog(
            "current_formation_dialog",
            config_manager.get_text("guild.party_formation.current_formation_title"),
            formation_text
        )
    
    def _format_party_formation(self) -> str:
        """パーティ編成をフォーマット"""
        if not self.current_party:
            return config_manager.get_text("guild.messages.no_party_set")
        
        lines = [config_manager.get_text("guild.party_formation.party_name").format(name=self.current_party.name)]
        lines.append("")
        
        # 前衛
        lines.append(config_manager.get_text("guild.party_formation.front_row"))
        front_chars = self.current_party.get_front_row_characters()
        for i, char in enumerate(front_chars):
            if char:
                lines.append(f"  {i+1}. {char.name} Lv.{char.experience.level} ({char.get_class_name()})")
            else:
                lines.append(f"  {i+1}. {config_manager.get_text('guild.party_formation.empty_slot')}")
        
        # 後衛
        lines.append("")
        lines.append(config_manager.get_text("guild.party_formation.back_row"))
        back_chars = self.current_party.get_back_row_characters()
        for i, char in enumerate(back_chars):
            if char:
                lines.append(f"  {i+1}. {char.name} Lv.{char.experience.level} ({char.get_class_name()})")
            else:
                lines.append(f"  {i+1}. {config_manager.get_text('guild.party_formation.empty_slot')}")
        
        return "\n".join(lines)
    
    def _show_add_character_menu(self):
        """キャラクター追加メニュー"""
        add_menu = UIMenu("add_character_menu", config_manager.get_text("guild.party_formation.character_add_title"))
        
        # 利用可能なキャラクター（パーティに参加していない）
        available_chars = [
            char for char in self.created_characters 
            if char.character_id not in self.current_party.characters
        ]
        
        if not available_chars:
            self._show_error_message("追加可能なキャラクターがいません")
            return
        
        for char in available_chars:
            char_info = f"{char.name} Lv.{char.experience.level} ({char.get_race_name()}/{char.get_class_name()})"
            add_menu.add_menu_item(
                char_info,
                self._add_character_to_party,
                [char]
            )
        
        add_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_formation_menu,
            [add_menu]
        )
        
        self._show_submenu(add_menu)
    
    def _add_character_to_party(self, character: Character):
        """パーティにキャラクターを追加"""
        if not self.current_party:
            logger.warning("パーティが設定されていないため、キャラクターを追加できません")
            self._show_error_message("パーティが設定されていません")
            return
        
        try:
            success = self.current_party.add_character(character)
            
            if success:
                self._show_success_message(f"{character.name} をパーティに追加しました")
                # 追加後はメインメニューに戻る - すべてのサブメニューを閉じる
                self._close_all_submenus_and_return_to_main()
            else:
                self._show_error_message("キャラクターの追加に失敗しました")
                
        except Exception as e:
            logger.error(f"キャラクター追加処理でエラーが発生しました: {e}")
            self._show_error_message(f"キャラクター追加でエラーが発生しました: {str(e)}")
            # エラーが発生しても最低限メインメニューに戻る
            try:
                self._back_to_main_menu_fallback()
            except Exception:
                pass  # フォールバックが失敗しても続行
    
    def _show_remove_character_menu(self):
        """キャラクター削除メニュー"""
        remove_menu = UIMenu("remove_character_menu", "キャラクター削除")
        
        party_chars = list(self.current_party.characters.values())
        
        for char in party_chars:
            char_info = f"{char.name} Lv.{char.experience.level} ({char.get_class_name()})"
            remove_menu.add_menu_item(
                char_info,
                self._remove_character_from_party,
                [char]
            )
        
        remove_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_formation_menu,
            [remove_menu]
        )
        
        self._show_submenu(remove_menu)
    
    def _remove_character_from_party(self, character: Character):
        """パーティからキャラクターを削除"""
        self._show_confirmation(
            f"{character.name} をパーティから削除しますか？",
            lambda: self._confirm_remove_character(character)
        )
    
    def _confirm_remove_character(self, character: Character):
        """キャラクター削除確認"""
        if not self.current_party:
            return
        
        success = self.current_party.remove_character(character.character_id)
        
        if success:
            # 削除されたキャラクターを作成済みリストに戻す
            if character not in self.created_characters:
                self.created_characters.append(character)
            
            self._show_success_message(f"{character.name} をパーティから削除しました")
        else:
            self._show_error_message("キャラクターの削除に失敗しました")
        
        # 編成メニューに戻る
        self._show_party_formation()
    
    def _show_position_menu(self):
        """位置変更メニュー"""
        position_menu = UIMenu("position_menu", "位置変更")
        
        party_chars = list(self.current_party.characters.values())
        
        for char in party_chars:
            current_pos = self.current_party.formation.get_character_position(char.character_id)
            pos_text = current_pos.value if current_pos else "不明"
            char_info = f"{char.name} ({pos_text})"
            
            position_menu.add_menu_item(
                char_info,
                self._show_new_position_menu,
                [char]
            )
        
        position_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._back_to_formation_menu,
            [position_menu]
        )
        
        self._show_submenu(position_menu)
    
    def _show_new_position_menu(self, character: Character):
        """新しい位置選択メニュー"""
        new_pos_menu = UIMenu("new_position_menu", f"{character.name} の新しい位置")
        
        positions = [
            (PartyPosition.FRONT_1, "前衛1"),
            (PartyPosition.FRONT_2, "前衛2"),
            (PartyPosition.FRONT_3, "前衛3"),
            (PartyPosition.BACK_1, "後衛1"),
            (PartyPosition.BACK_2, "後衛2"),
            (PartyPosition.BACK_3, "後衛3")
        ]
        
        for position, pos_name in positions:
            # 現在空いている位置のみ表示
            current_char_id = self.current_party.formation.positions[position]
            if current_char_id is None or current_char_id == character.character_id:
                new_pos_menu.add_menu_item(
                    pos_name,
                    self._move_character_to_position,
                    [character, position]
                )
        
        new_pos_menu.add_menu_item(
            config_manager.get_text("menu.back"),
            self._show_position_menu
        )
        
        self._show_submenu(new_pos_menu)
    
    def _move_character_to_position(self, character: Character, position: PartyPosition):
        """キャラクターを指定位置に移動"""
        success = self.current_party.move_character(character.character_id, position)
        
        if success:
            self._show_success_message(f"{character.name} を移動しました")
        else:
            self._show_error_message("位置の変更に失敗しました")
        
        # 編成メニューに戻る
        self._show_party_formation()
    
    def _show_character_list(self):
        """キャラクター一覧表示"""
        # 重複を避けるため、character_idベースで一意のキャラクターリストを作成
        all_characters = {}
        
        # 作成済みキャラクターを追加
        for char in self.created_characters:
            all_characters[char.character_id] = char
        
        # パーティメンバーを追加（重複は上書きされる）
        for char in self.current_party.characters.values():
            all_characters[char.character_id] = char
        
        all_chars = list(all_characters.values())
        
        if not all_chars:
            self._show_error_message("キャラクターがいません")
            return
        
        char_list_text = "【作成済みキャラクター一覧】\n\n"
        
        for char in all_chars:
            in_party = char.character_id in self.current_party.characters
            party_status = " (パーティ中)" if in_party else " (待機中)"
            
            char_info = f"{char.name} Lv.{char.experience.level}\n"
            char_info += f"  {char.get_race_name()}/{char.get_class_name()}\n"
            char_info += f"  HP:{char.derived_stats.current_hp}/{char.derived_stats.max_hp} "
            char_info += f"MP:{char.derived_stats.current_mp}/{char.derived_stats.max_mp}"
            char_info += party_status + "\n\n"
            
            char_list_text += char_info
        
        self._show_dialog(
            "character_list_dialog",
            "キャラクター一覧",
            char_list_text
        )
    
    def _show_class_change(self):
        """クラスチェンジ（未実装）"""
        self._show_dialog(
            "class_change_dialog",
            "クラスチェンジ",
            "クラスチェンジ機能は未実装です。\n将来のアップデートで追加予定です。"
        )
    
    def _show_submenu(self, submenu: UIMenu):
        """サブメニューを表示"""
        # 現在のメニューを隠す
        ui_manager.hide_menu("party_formation_menu")
        
        ui_manager.add_menu(submenu)
        ui_manager.show_menu(submenu.menu_id, modal=True)
    
    def _back_to_formation_menu(self, submenu: UIMenu):
        """編成メニューに戻る"""
        ui_manager.hide_menu(submenu.menu_id)
        
        
        # 編成メニューを再表示
        ui_manager.show_menu("party_formation_menu")
    
    def _back_to_main_menu_from_submenu(self, submenu: UIMenu):
        """サブメニューからメインメニューに戻る"""
        ui_manager.hide_menu(submenu.menu_id)
        
        
        if self.main_menu:
            ui_manager.show_menu(self.main_menu.menu_id)
    
    def _back_to_main_menu_fallback(self):
        """フォールバック: 直接メインメニューに戻る"""
        # アクティブなサブメニューを全て非表示にする
        possible_menus = [
            "party_formation_menu",
            "add_character_menu", 
            "remove_character_menu",
            "position_menu",
            "new_position_menu"
        ]
        
        for menu_id in possible_menus:
            ui_manager.hide_menu(menu_id)
                
        
        # メインメニューを表示
        if self.main_menu:
            ui_manager.show_menu(self.main_menu.menu_id)
    
    def _close_all_submenus_and_return_to_main(self):
        """すべてのサブメニューを閉じてメインメニューに戻る"""
        try:
            # 既存の_back_to_main_menu_from_submenuの動作をエミュレート
            # フォールバック処理を実行
            self._back_to_main_menu_fallback()
        except Exception as e:
            logger.warning(f"メニュー遷移でエラーが発生しました: {e}")
            # エラーが発生した場合は強制的にフォールバック処理を実行
            try:
                self._back_to_main_menu_fallback()
            except Exception as fallback_error:
                logger.error(f"フォールバック処理でもエラーが発生しました: {fallback_error}")
                # 最後の手段：基本的なメインメニュー表示
                if self.main_menu:
                    try:
                        ui_manager.show_menu(self.main_menu.menu_id)
                    except Exception:
                        pass  # 最後の手段が失敗しても続行