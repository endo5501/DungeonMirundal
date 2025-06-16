"""地上部管理システム"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.overworld.base_facility import BaseFacility, FacilityManager, facility_manager
from src.ui.base_ui import UIMenu, UIDialog, ui_manager
from src.ui.dungeon_selection_ui import DungeonSelectionUI
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
        self.settings_menu_active = False
        self.dungeon_selection_ui = DungeonSelectionUI()
        
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
            ui_manager.unregister_element(self.main_menu.element_id)
        
        self.main_menu = UIMenu("overworld_main_menu", config_manager.get_text("overworld.surface_map"), alignment="left")
        
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
        
        ui_manager.register_element(self.main_menu)
        ui_manager.show_element(self.main_menu.element_id, modal=True)
    
    def show_settings_menu(self):
        """設定画面の表示（ESCキー用）"""
        if self.location_menu:
            ui_manager.unregister_element(self.location_menu.element_id)
        
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
        
        ui_manager.register_element(self.location_menu)
        ui_manager.show_element(self.location_menu.element_id, modal=True)
        
        # メインメニューを隠す
        if self.main_menu:
            ui_manager.hide_element(self.main_menu.element_id)
        
        logger.info("設定画面を表示しました")
    
    def _enter_facility(self, facility_id: str):
        """施設に入る"""
        if not self.current_party:
            return
        
        success = self.facility_manager.enter_facility(facility_id, self.current_party)
        
        if success:
            # 施設メニューが表示されるので、地上部メニューを隠す
            # メニューの状態を記録してから隠す
            self.main_menu_was_visible = False
            self.settings_menu_was_visible = False
            
            if self.main_menu:
                try:
                    # UIManagerに登録されているかチェックしてから隠す
                    main_element = ui_manager.get_element(self.main_menu.element_id)
                    if main_element:
                        # メニューが表示状態かチェック（簡易版）
                        try:
                            # 現在表示されているかどうかを記録
                            self.main_menu_was_visible = True
                            ui_manager.hide_element(self.main_menu.element_id)
                            logger.debug(f"メインメニューを隠しました: {self.main_menu.element_id}")
                        except Exception as hide_error:
                            logger.warning(f"メインメニューの非表示処理でエラー: {hide_error}")
                    else:
                        logger.warning("隠すべきメインメニューがUIManagerに見つかりません")
                except Exception as check_error:
                    logger.warning(f"メインメニューの状態チェックでエラー: {check_error}")
            
            # 設定メニューがアクティブな場合も隠す
            if self.settings_menu_active and self.location_menu:
                try:
                    settings_element = ui_manager.get_element(self.location_menu.element_id)
                    if settings_element:
                        self.settings_menu_was_visible = True
                        ui_manager.hide_element(self.location_menu.element_id)
                        logger.debug(f"設定メニューを隠しました: {self.location_menu.element_id}")
                except Exception as hide_error:
                    logger.warning(f"設定メニューの非表示処理でエラー: {hide_error}")
            
            logger.info(f"施設に入りました: {facility_id} (main_menu_was_visible: {self.main_menu_was_visible}, settings_menu_was_visible: {self.settings_menu_was_visible})")
        else:
            self._show_error_dialog("エラー", f"施設 '{facility_id}' に入れませんでした。")
    
    def _back_to_main_menu(self):
        """メインメニューに戻る"""
        if self.location_menu:
            ui_manager.hide_element(self.location_menu.element_id)
            ui_manager.unregister_element(self.location_menu.element_id)
            self.location_menu = None
        
        self.settings_menu_active = False
        
        if self.main_menu:
            ui_manager.show_element(self.main_menu.element_id)
        
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
            self._back_to_settings_menu
        )
        
        ui_manager.register_element(party_menu)
        ui_manager.show_element(party_menu.element_id, modal=True)
        
        # 設定メニューを隠す
        if self.location_menu:
            ui_manager.hide_element(self.location_menu.element_id)
    
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
        """パーティ全体情報を表示"""
        if not self.current_party:
            return
        
        status_text = f"【{self.current_party.name}】\n\n"
        status_text += f"ゴールド: {self.current_party.gold}G\n"
        status_text += f"メンバー数: {len(self.current_party.characters)}\n\n"
        
        # パーティの総合戦闘力
        total_hp = sum(char.derived_stats.max_hp for char in self.current_party.get_all_characters())
        total_mp = sum(char.derived_stats.max_mp for char in self.current_party.get_all_characters())
        avg_level = sum(char.experience.level for char in self.current_party.get_all_characters()) / len(self.current_party.characters) if self.current_party.characters else 0
        
        status_text += f"【パーティ戦力】\n"
        status_text += f"平均レベル: {avg_level:.1f}\n"
        status_text += f"総HP: {total_hp}\n"
        status_text += f"総MP: {total_mp}\n\n"
        
        # 職業構成
        status_text += "【職業構成】\n"
        class_counts = {}
        for character in self.current_party.get_all_characters():
            class_name = character.get_class_name()
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        for class_name, count in class_counts.items():
            status_text += f"{class_name}: {count}人\n"
        
        status_text += "\n【メンバー一覧】\n"
        for character in self.current_party.get_all_characters():
            status_line = f"• {character.name} Lv.{character.experience.level} "
            status_line += f"({character.get_race_name()}/{character.get_class_name()}) "
            status_line += f"[{character.status.value}]"
            status_text += status_line + "\n"
        
        self._show_info_dialog("パーティ全体情報", status_text)
    
    def _show_character_details(self, character):
        """キャラクター詳細情報を表示"""
        details_text = f"【{character.name}】\n\n"
        
        # 基本情報
        details_text += f"種族: {character.get_race_name()}\n"
        details_text += f"職業: {character.get_class_name()}\n"
        details_text += f"レベル: {character.experience.level}\n"
        details_text += f"経験値: {character.experience.current_xp}\n"
        details_text += f"状態: {character.status.value}\n\n"
        
        # HP/MP
        details_text += f"【生命力・魔力】\n"
        details_text += f"HP: {character.derived_stats.current_hp} / {character.derived_stats.max_hp}\n"
        details_text += f"MP: {character.derived_stats.current_mp} / {character.derived_stats.max_mp}\n\n"
        
        # 基本能力値
        details_text += f"【基本能力値】\n"
        details_text += f"力: {character.base_stats.strength}\n"
        details_text += f"知恵: {character.base_stats.intelligence}\n"
        details_text += f"信仰心: {character.base_stats.faith}\n"
        details_text += f"素早さ: {character.base_stats.agility}\n"
        details_text += f"運: {character.base_stats.luck}\n"
        details_text += f"体力: {character.base_stats.vitality}\n\n"
        
        # 戦闘能力
        details_text += f"【戦闘能力】\n"
        details_text += f"攻撃力: {character.derived_stats.attack_power}\n"
        details_text += f"防御力: {character.derived_stats.defense}\n"
        details_text += f"命中率: {character.derived_stats.accuracy}\n"
        details_text += f"回避率: {character.derived_stats.evasion}\n"
        details_text += f"クリティカル率: {character.derived_stats.critical_chance}\n\n"
        
        # 装備品情報
        details_text += f"【装備品】\n"
        equipment = character.equipment
        if equipment.weapon:
            details_text += f"武器: {equipment.weapon.get_name()}\n"
        else:
            details_text += "武器: なし\n"
            
        if equipment.armor:
            details_text += f"防具: {equipment.armor.get_name()}\n"
        else:
            details_text += "防具: なし\n"
            
        if equipment.shield:
            details_text += f"盾: {equipment.shield.get_name()}\n"
        else:
            details_text += "盾: なし\n"
            
        if equipment.accessory:
            details_text += f"装飾品: {equipment.accessory.get_name()}\n"
        else:
            details_text += "装飾品: なし\n"
        
        # 個人インベントリ
        details_text += f"\n【所持品】\n"
        personal_inventory = character.get_personal_inventory()
        if personal_inventory and personal_inventory.slots:
            item_count = 0
            for slot in personal_inventory.slots:
                if not slot.is_empty():
                    item_instance = slot.item_instance
                    if item_instance:
                        details_text += f"• {item_instance.get_display_name()}"
                        if item_instance.quantity > 1:
                            details_text += f" x{item_instance.quantity}"
                        details_text += "\n"
                        item_count += 1
            
            if item_count == 0:
                details_text += "なし\n"
        else:
            details_text += "なし\n"
        
        # TODO: Phase 4で魔法習得情報追加
        details_text += f"\n【習得魔法】\n"
        details_text += "Phase 4で実装予定\n"
        
        self._show_info_dialog(f"{character.name} の詳細", details_text)
    
    def _back_to_settings_menu(self):
        """設定メニューに戻る"""
        # パーティ状況メニューを隠す
        ui_manager.hide_element("party_status_menu")
        ui_manager.unregister_element("party_status_menu")
        
        # 設定メニューを再表示
        if self.location_menu:
            ui_manager.show_element(self.location_menu.element_id)
    
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
            self._back_to_settings_menu
        )
        
        # 現在のメニューを隠してロードメニューを表示
        if self.location_menu:
            ui_manager.hide_element(self.location_menu.element_id)
        
        ui_manager.register_element(load_menu)
        ui_manager.show_element(load_menu.element_id, modal=True)
    
    def _load_selected_save(self, slot_id: int):
        """選択されたセーブデータをロード"""
        game_save = save_manager.load_game(slot_id)
        
        if game_save:
            self.current_party = game_save.party
            self._show_info_dialog("ロード完了", f"スロット {slot_id} のデータをロードしました")
            
            # メインメニューを更新
            self._back_to_main_menu()
        else:
            self._show_error_dialog("ロード失敗", "セーブデータの読み込みに失敗しました")
    
    def _back_to_settings_menu(self):
        """設定メニューに戻る"""
        ui_manager.hide_element("load_game_menu")
        ui_manager.unregister_element("load_game_menu")
        
        # 設定メニューを再表示（メインメニューは表示しない）
        if self.location_menu:
            ui_manager.show_element(self.location_menu.element_id)
        else:
            # 設定メニューが存在しない場合は新規作成
            self.show_settings_menu()
    
    def _enter_dungeon(self):
        """ダンジョンに入る"""
        if not self.current_party:
            return
        
        # パーティの状態チェック
        conscious_members = self.current_party.get_conscious_characters()
        if not conscious_members:
            self._show_error_dialog("エラー", "意識のあるメンバーがいません")
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
        # テキストキャッシュをリロードして最新の設定を取得
        config_manager.reload_all()
        
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
                settings_element = ui_manager.get_element(self.location_menu.element_id)
                if settings_element:
                    try:
                        ui_manager.show_element(self.location_menu.element_id)
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
                    main_element = ui_manager.get_element(self.main_menu.element_id)
                    if main_element:
                        try:
                            # 強制的に表示
                            ui_manager.show_element(self.main_menu.element_id)
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
                                ui_manager.hide_element(self.main_menu.element_id)
                                ui_manager.unregister_element(self.main_menu.element_id)
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