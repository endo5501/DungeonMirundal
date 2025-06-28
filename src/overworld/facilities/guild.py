"""冒険者ギルド"""

from typing import Dict, List, Optional, Any
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.character import Character
from src.character.party import Party, PartyPosition
from src.ui.base_ui_pygame import UIMenu, UIDialog
from src.ui.character_creation import CharacterCreationWizard
from src.core.config_manager import config_manager
from src.utils.logger import logger

# 冒険者ギルド定数
FORMATION_DIALOG_WIDTH = 700
FORMATION_DIALOG_HEIGHT = 450
CHARACTER_LIST_DIALOG_HEIGHT = 500
CHARACTER_INFO_DIALOG_WIDTH = 500
CHARACTER_INFO_DIALOG_HEIGHT = 400


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
        logger.info(config_manager.get_text("app_log.entered_guild"))
    
    def _on_exit(self):
        """ギルド退場時の処理"""
        logger.info(config_manager.get_text("app_log.left_guild"))
    
    def _show_character_creation(self):
        """キャラクター作成ウィザードを表示"""
        # メインメニューを隠す（menu_stack_managerを使用）
        if self.menu_stack_manager and self.menu_stack_manager.peek_current_menu():
            current_menu_entry = self.menu_stack_manager.peek_current_menu()
            self._hide_menu_safe(current_menu_entry.menu.menu_id)
        
        # キャラクター作成ウィザードを起動
        wizard = CharacterCreationWizard(callback=self._on_character_created)
        # キャンセル時のコールバックを設定
        wizard.on_cancel = self._on_character_creation_cancelled
        wizard.start()
    
    def _on_character_created(self, character: Character):
        """キャラクター作成完了時のコールバック"""
        logger.info(config_manager.get_text("guild.messages.character_creation_completed").format(name=character.name))
        
        self.created_characters.append(character)
        
        # 成功メッセージ（ダイアログが閉じられた後、_close_dialogでメインメニューが自動表示される）
        self._show_success_message(config_manager.get_text("guild.messages.character_created").format(name=character.name))
        
        logger.info(config_manager.get_text("guild.messages.new_character_created").format(name=character.name))
    
    def _on_character_creation_cancelled(self):
        """キャラクター作成キャンセル時のコールバック"""
        # メインメニューを再表示（menu_stack_managerを使用）
        if self.menu_stack_manager and self.menu_stack_manager.get_current_menu():
            current_menu = self.menu_stack_manager.get_current_menu()
            ui_mgr = self._get_effective_ui_manager()
            if ui_mgr:
                ui_mgr.show_menu(current_menu.menu_id, modal=True)
        
        logger.info(config_manager.get_text("guild.messages.character_creation_cancelled"))
    
    def _show_party_formation(self):
        """パーティ編成画面を表示"""
        if not self.current_party:
            self._show_error_message(config_manager.get_text("guild.messages.no_party_set"))
            return
        
        # 利用可能なキャラクターの種類を確認（後続機能で使用予定）
        # available_chars = self.created_characters.copy()
        # party_chars = list(self.current_party.characters.values())
        
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
        
        # 戻る（画面下部固定）
        formation_menu.add_back_button(
            config_manager.get_text("menu.back"),
            self._back_to_main_menu_from_submenu,
            [formation_menu]
        )
        
        # メインメニューを隠して編成メニューを表示
        if self.menu_stack_manager:
            current_entry = self.menu_stack_manager.peek_current_menu()
            if current_entry:
                self._hide_menu_safe(current_entry.menu.menu_id)
        
        self._show_menu_safe(formation_menu, modal=True)
    
    def _show_current_formation(self):
        """現在の編成を表示"""
        if not self.current_party:
            return
        
        formation_text = self._format_party_formation()
        self._show_dialog(
            "current_formation_dialog",
            config_manager.get_text("guild.party_formation.current_formation_title"),
            formation_text,
            buttons=[
                {
                    'text': config_manager.get_text("menu.back"),
                    'command': self._close_current_formation_dialog
                }
            ],
            width=FORMATION_DIALOG_WIDTH,  # パーティ編成表示に十分な幅
            height=FORMATION_DIALOG_HEIGHT  # 複数キャラクターの情報表示に十分な高さ
        )
    
    def _close_current_formation_dialog(self):
        """現在の編成ダイアログを閉じてパーティ編成メニューに戻る"""
        if self.current_dialog:
            ui_mgr = self._get_effective_ui_manager()
            if ui_mgr:
                ui_mgr.hide_dialog(self.current_dialog.dialog_id)
            self.current_dialog = None
            
            # パーティ編成メニューを再表示（モーダルとして）
            if ui_mgr:
                ui_mgr.show_menu("party_formation_menu", modal=True)
    
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
            self._show_error_message(self.config_manager.get_text("errors.no_addable_characters"))
            return
        
        for char in available_chars:
            char_info = f"{char.name} Lv.{char.experience.level} ({char.get_race_name()}/{char.get_class_name()})"
            add_menu.add_menu_item(
                char_info,
                self._add_character_to_party,
                [char]
            )
        
        add_menu.add_back_button(
            config_manager.get_text("menu.back"),
            self._back_to_formation_menu,
            [add_menu]
        )
        
        self._show_submenu(add_menu)
    
    def _add_character_to_party(self, character: Character):
        """パーティにキャラクターを追加"""
        if not self.current_party:
            logger.warning(config_manager.get_text("guild.messages.party_not_set_warning"))
            self._show_error_message(self.config_manager.get_text("errors.no_party_set"))
            return
        
        try:
            success = self.current_party.add_character(character)
            
            if success:
                self._show_success_message(config_manager.get_text("guild.messages.character_added_success").format(name=character.name))
                # 追加後はメインメニューに戻る - すべてのサブメニューを閉じる
                self._close_all_submenus_and_return_to_main()
            else:
                self._show_error_message(config_manager.get_text("guild.messages.character_add_failed"))
                
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
        
        remove_menu.add_back_button(
            config_manager.get_text("menu.back"),
            self._back_to_formation_menu,
            [remove_menu]
        )
        
        self._show_submenu(remove_menu)
    
    def _remove_character_from_party(self, character: Character):
        """パーティからキャラクターを削除"""
        self._show_confirmation(
            f"{character.name} をパーティから削除しますか？",
            lambda confirmed=None: self._confirm_remove_character(character) if confirmed else None
        )
    
    def _confirm_remove_character(self, character: Character):
        """キャラクター削除確認"""
        if not self.current_party:
            return
        
        success = self.current_party.remove_character(character.character_id)
        
        # 削除確認メニューを閉じる
        self._hide_menu_safe("remove_character_menu")
        
        if success:
            # 削除されたキャラクターを作成済みリストに戻す
            if character not in self.created_characters:
                self.created_characters.append(character)
            
            self._show_dialog(
                "character_remove_success",
                "キャラクター削除完了",
                config_manager.get_text("guild.messages.character_remove_success").format(name=character.name),
                buttons=[
                    {
                        'text': config_manager.get_text("common.ok"),
                        'command': lambda: self._return_to_party_formation()
                    }
                ]
            )
        else:
            self._show_error_message(config_manager.get_text("guild.messages.character_remove_failed"))
    
    def _show_position_menu(self):
        """位置変更メニュー"""
        position_menu = UIMenu("position_menu", config_manager.get_text("guild.party_formation.position_change_title"))
        
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
        
        position_menu.add_back_button(
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
            # 現在空いている位置のみ表示（現在位置は除外）
            current_char_id = self.current_party.formation.positions[position]
            if current_char_id is None:
                new_pos_menu.add_menu_item(
                    pos_name,
                    self._move_character_to_position,
                    [character, position]
                )
        
        new_pos_menu.add_back_button(
            config_manager.get_text("menu.back"),
            self._show_position_menu
        )
        
        self._show_submenu(new_pos_menu)
    
    def _move_character_to_position(self, character: Character, position: PartyPosition):
        """キャラクターを指定位置に移動"""
        success = self.current_party.move_character(character.character_id, position)
        
        # サブメニューを閉じる
        self._hide_menu_safe("new_position_menu")
        
        if success:
            self._show_dialog(
                "position_change_success",
                config_manager.get_text("guild.party_formation.position_change_title"),
                config_manager.get_text("guild.messages.character_position_changed").format(name=character.name, position=""),
                buttons=[
                    {
                        'text': config_manager.get_text("common.ok"),
                        'command': lambda: self._return_to_party_formation()
                    }
                ]
            )
        else:
            self._show_error_message(config_manager.get_text("guild.messages.character_position_change_failed"))
    
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
            char_list_text,
            buttons=[
                {
                    'text': config_manager.get_text("menu.back"),
                    'command': self._close_dialog
                }
            ],
            width=750,  # キャラクター詳細情報表示に十分な幅
            height=CHARACTER_LIST_DIALOG_HEIGHT  # 複数キャラクターのリスト表示に十分な高さ
        )
    
    def _show_class_change(self):
        """クラスチェンジ画面を表示"""
        if not self.current_party:
            self._show_error_message("パーティが設定されていません")
            return
        
        # パーティメンバーが誰もいない場合
        if not self.current_party.characters:
            self._show_error_message("パーティにメンバーがいません")
            return
        
        # クラスチェンジ可能なキャラクターを選択
        class_change_menu = UIMenu("class_change_menu", "クラスチェンジ")
        
        for position, character in self.current_party.characters.items():
            # レベル10以上のキャラクターのみ表示
            if character.experience.level >= 10:
                char_info = f"{character.name} (Lv.{character.experience.level} {character.get_class_name()})"
                class_change_menu.add_menu_item(
                    char_info,
                    self._show_class_change_options,
                    [character]
                )
        
        # 該当者がいない場合
        if len(class_change_menu.elements) == 0:
            self._show_dialog(
                "no_eligible_dialog",
                "クラスチェンジ",
                "クラスチェンジ可能なキャラクターがいません。\n\n"
                "条件:\n"
                "・レベル10以上\n"
                "・転職先クラスの要求能力値を満たす",
                buttons=[
                    {
                        'text': "戻る",
                        'command': self._close_dialog
                    }
                ]
            )
            return
        
        class_change_menu.add_menu_item(
            "戻る",
            self._back_to_main_menu_from_submenu,
            [class_change_menu]
        )
        
        self._show_submenu(class_change_menu)
    
    def _show_class_change_options(self, character: Character):
        """クラスチェンジ先の選択画面を表示"""
        from src.character.class_change import ClassChangeValidator, ClassChangeManager
        
        # 転職可能なクラスを取得
        available_classes = ClassChangeValidator.get_available_classes(character)
        
        if not available_classes:
            self._show_dialog(
                "no_available_classes",
                "転職先がありません",
                f"{character.name}が転職可能なクラスがありません。\n\n"
                "能力値が要求を満たしていない可能性があります。",
                buttons=[
                    {
                        'text': "戻る",
                        'command': self._close_dialog
                    }
                ]
            )
            return
        
        # クラス選択メニュー
        class_select_menu = UIMenu("class_select_menu", f"{character.name}の転職先")
        
        for class_name in available_classes:
            class_info = ClassChangeManager.get_class_change_info(character, class_name)
            display_name = f"{class_info['target_name']} (HP×{class_info['hp_multiplier']:.1f} MP×{class_info['mp_multiplier']:.1f})"
            class_select_menu.add_menu_item(
                display_name,
                self._show_class_change_confirm,
                [character, class_name]
            )
        
        class_select_menu.add_menu_item(
            "戻る",
            self._back_to_class_change_menu,
            [class_select_menu]
        )
        
        self._show_submenu(class_select_menu)
    
    def _show_class_change_confirm(self, character: Character, target_class: str):
        """クラスチェンジ確認画面"""
        from src.character.class_change import ClassChangeManager
        
        class_info = ClassChangeManager.get_class_change_info(character, target_class)
        
        confirm_text = (
            f"【クラスチェンジ確認】\n\n"
            f"{character.name}\n"
            f"{class_info['current_name']} → {class_info['target_name']}\n\n"
            f"注意:\n"
            f"・レベルが1に戻ります\n"
            f"・経験値が0になります\n"
            f"・HP/MPが再計算されます\n"
            f"・費用: 1000G\n\n"
            f"本当にクラスチェンジしますか？"
        )
        
        # ゴールドチェック
        if self.current_party.gold < 1000:
            confirm_text += "\n\n※ ゴールドが不足しています"
            buttons = [
                {
                    'text': "戻る",
                    'command': self._close_dialog
                }
            ]
        else:
            buttons = [
                {
                    'text': "はい",
                    'command': lambda: self._execute_class_change(character, target_class)
                },
                {
                    'text': "いいえ",
                    'command': self._close_dialog
                }
            ]
        
        self._show_dialog(
            "class_change_confirm",
            "クラスチェンジ確認",
            confirm_text,
            buttons=buttons,
            width=CHARACTER_INFO_DIALOG_WIDTH,
            height=CHARACTER_INFO_DIALOG_HEIGHT
        )
    
    def _execute_class_change(self, character: Character, target_class: str):
        """クラスチェンジを実行"""
        from src.character.class_change import ClassChangeManager
        
        self._close_dialog()
        
        # ゴールドを消費
        self.current_party.gold -= 1000
        
        # クラスチェンジ実行
        success, message = ClassChangeManager.change_class(character, target_class)
        
        if success:
            self._show_success_message(message + f"\n\n残りゴールド: {self.current_party.gold}G")
        else:
            # 失敗時はゴールドを戻す
            self.current_party.gold += 1000
            self._show_error_message(message)
    
    def _back_to_class_change_menu(self, submenu: UIMenu):
        """クラスチェンジメニューに戻る"""
        self._hide_menu_safe(submenu.menu_id)
        # クラスチェンジメニューを再表示
        self._show_class_change()
    
    def _return_to_party_formation(self):
        """パーティ編成メニューに戻る"""
        self._close_dialog()
        self._show_party_formation()
    
    def _show_submenu(self, submenu: UIMenu):
        """サブメニューを表示"""
        # 現在のメニューを隠してサブメニューを表示
        self._hide_menu_safe("party_formation_menu")
        self._show_menu_safe(submenu, modal=True)
    
    def _back_to_formation_menu(self, submenu: UIMenu):
        """編成メニューに戻る"""
        self._hide_menu_safe(submenu.menu_id)
        # 編成メニューを再表示
        ui_mgr = self._get_effective_ui_manager()
        if ui_mgr:
            ui_mgr.show_menu("party_formation_menu")
    
    def _back_to_main_menu_from_submenu(self, submenu: UIMenu):
        """サブメニューからメインメニューに戻る"""
        self._hide_menu_safe(submenu.menu_id)
        if self.menu_stack_manager:
            self.menu_stack_manager.back_to_facility_main()
    
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
            self._hide_menu_safe(menu_id)
                
        
        # メインメニューを表示
        if self.menu_stack_manager:
            self.menu_stack_manager.back_to_facility_main()
    
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
                if self.menu_stack_manager:
                    try:
                        self.menu_stack_manager.back_to_facility_main()
                    except Exception:
                        pass  # 最後の手段が失敗しても続行