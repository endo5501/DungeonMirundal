"""ダンジョン選択UI"""

from typing import Dict, List, Optional, Callable, Any
import yaml
from src.ui.base_ui import UIMenu, UIDialog, ui_manager
from src.character.party import Party
from src.core.config_manager import config_manager
from src.utils.logger import logger


class DungeonSelectionUI:
    """ダンジョン選択UI"""
    
    def __init__(self):
        self.dungeons_config = self._load_dungeons_config()
        self.current_party: Optional[Party] = None
        self.on_dungeon_selected: Optional[Callable[[str], None]] = None
        self.on_cancel: Optional[Callable[[], None]] = None
    
    def _load_dungeons_config(self) -> Dict[str, Any]:
        """ダンジョン設定を読み込み"""
        try:
            config_path = "config/dungeons.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"ダンジョン設定の読み込みに失敗: {e}")
            return {"dungeons": {}}
    
    def show_dungeon_selection(self, party: Party, 
                             on_selected: Callable[[str], None], 
                             on_cancel: Callable[[], None]):
        """ダンジョン選択画面を表示"""
        self.current_party = party
        self.on_dungeon_selected = on_selected
        self.on_cancel = on_cancel
        
        # 利用可能なダンジョンを取得
        available_dungeons = self._get_available_dungeons(party)
        
        if not available_dungeons:
            self._show_no_dungeons_dialog()
            return
        
        self._show_dungeon_menu(available_dungeons)
    
    def _get_available_dungeons(self, party: Party) -> List[Dict[str, Any]]:
        """利用可能なダンジョンを取得"""
        available = []
        party_max_level = party.get_max_level()
        
        for dungeon_id, dungeon_info in self.dungeons_config.get("dungeons", {}).items():
            if self._check_unlock_condition(dungeon_info.get("unlock_condition", "always"), party_max_level):
                dungeon_data = {
                    "id": dungeon_id,
                    "name": dungeon_info.get("name", dungeon_id),
                    "description": dungeon_info.get("description", ""),
                    "difficulty": dungeon_info.get("difficulty", 1),
                    "recommended_level": dungeon_info.get("recommended_level", "1-20"),
                    "attribute": dungeon_info.get("attribute", "物理"),
                    "floors": dungeon_info.get("floors", 20)
                }
                available.append(dungeon_data)
        
        # 難易度順でソート
        available.sort(key=lambda x: x["difficulty"])
        return available
    
    def _check_unlock_condition(self, condition: str, party_max_level: int) -> bool:
        """アンロック条件をチェック"""
        if condition == "always":
            return True
        elif condition == "level_5":
            return party_max_level >= 5
        elif condition == "level_10":
            return party_max_level >= 10
        elif condition == "level_15":
            return party_max_level >= 15
        else:
            return True  # 不明な条件は常に許可
    
    def _show_dungeon_menu(self, available_dungeons: List[Dict[str, Any]]):
        """ダンジョン選択メニューを表示"""
        # 既存のメニューがあれば削除
        if ui_manager.get_element("dungeon_selection_menu"):
            ui_manager.unregister_element("dungeon_selection_menu")
        
        title = (f"{config_manager.get_text('dungeon.selection_title')}\n\n"
                f"{config_manager.get_text('dungeon.selection_message')}\n"
                f"{config_manager.get_text('dungeon.max_level_info').format(level=self.current_party.get_max_level())}")
        
        menu = UIMenu("dungeon_selection_menu", title)
        
        # 各ダンジョンをメニューに追加
        for dungeon in available_dungeons:
            display_name = self._format_dungeon_display_name(dungeon)
            menu.add_menu_item(
                display_name,
                lambda d_id=dungeon["id"]: self._select_dungeon(d_id)
            )
        
        # 戻るオプション
        menu.add_menu_item(config_manager.get_text("dungeon.back_option"), self._cancel_selection)
        
        ui_manager.register_element(menu)
        ui_manager.show_element(menu.element_id, modal=True)
    
    def _format_dungeon_display_name(self, dungeon: Dict[str, Any]) -> str:
        """ダンジョン表示名をフォーマット"""
        difficulty_stars = "★" * dungeon["difficulty"]
        return (f"{dungeon['name']} ({difficulty_stars})\n"
                f"推奨Lv.{dungeon['recommended_level']} | "
                f"{dungeon['attribute']}属性 | "
                f"{dungeon['floors']}階")
    
    def _select_dungeon(self, dungeon_id: str):
        """ダンジョンを選択"""
        dungeon_info = self.dungeons_config["dungeons"].get(dungeon_id)
        if not dungeon_info:
            logger.error(f"不明なダンジョンID: {dungeon_id}")
            return
        
        # 詳細確認ダイアログを表示
        self._show_dungeon_confirmation(dungeon_id, dungeon_info)
    
    def _show_dungeon_confirmation(self, dungeon_id: str, dungeon_info: Dict[str, Any]):
        """ダンジョン入場確認ダイアログ"""
        # 既存のダイアログがあれば削除
        if ui_manager.get_element("dungeon_confirmation_dialog"):
            ui_manager.unregister_element("dungeon_confirmation_dialog")
        
        difficulty_stars = "★" * dungeon_info.get("difficulty", 1)
        
        message = (
            f"『{dungeon_info.get('name', dungeon_id)}』 ({difficulty_stars})\n\n"
            f"{dungeon_info.get('description', '')}\n\n"
            f"{config_manager.get_text('dungeon.level_info').format(
                level=dungeon_info.get('recommended_level', '1-20'),
                attribute=dungeon_info.get('attribute', '物理'),
                floors=dungeon_info.get('floors', 20)
            )}\n\n"
            f"{config_manager.get_text('dungeon.confirm_enter_message')}"
        )
        
        dialog = UIDialog(
            "dungeon_confirmation_dialog",
            config_manager.get_text("dungeon.confirm_enter_title"),
            message,
            [
                {"text": config_manager.get_text("common.yes"), "command": lambda: self._confirm_dungeon_selection(dungeon_id)},
                {"text": config_manager.get_text("common.no"), "command": self._back_to_dungeon_menu}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id)
    
    def _confirm_dungeon_selection(self, dungeon_id: str):
        """ダンジョン選択を確定"""
        # ダイアログを閉じる
        ui_manager.hide_element("dungeon_confirmation_dialog")
        ui_manager.unregister_element("dungeon_confirmation_dialog")
        
        # メニューも閉じる
        ui_manager.hide_element("dungeon_selection_menu")
        ui_manager.unregister_element("dungeon_selection_menu")
        
        if self.on_dungeon_selected:
            self.on_dungeon_selected(dungeon_id)
    
    def _back_to_dungeon_menu(self):
        """ダンジョンメニューに戻る"""
        # ダイアログを閉じる
        ui_manager.hide_element("dungeon_confirmation_dialog")
        ui_manager.unregister_element("dungeon_confirmation_dialog")
        
        # 利用可能なダンジョンを再取得してメニューを再表示
        available_dungeons = self._get_available_dungeons(self.current_party)
        self._show_dungeon_menu(available_dungeons)
    
    def _cancel_selection(self):
        """選択をキャンセル"""
        # メニューを閉じる
        if ui_manager.get_element("dungeon_selection_menu"):
            ui_manager.hide_element("dungeon_selection_menu")
            ui_manager.unregister_element("dungeon_selection_menu")
        
        # ダイアログを閉じる
        if ui_manager.get_element("no_dungeons_dialog"):
            ui_manager.hide_element("no_dungeons_dialog")
            ui_manager.unregister_element("no_dungeons_dialog")
        
        if self.on_cancel:
            self.on_cancel()
    
    def _on_dungeon_selection_cancelled(self):
        """ダンジョン選択キャンセル時の処理（テスト用別名）"""
        self._cancel_selection()
    
    def _show_no_dungeons_dialog(self):
        """利用可能なダンジョンがない場合のダイアログ"""
        # 既存のダイアログがあれば削除
        if ui_manager.get_element("no_dungeons_dialog"):
            ui_manager.unregister_element("no_dungeons_dialog")
        
        dialog = UIDialog(
            "no_dungeons_dialog",
            config_manager.get_text("dungeon.selection_title"),
            config_manager.get_text("dungeon.no_dungeons_available"),
            [{"text": config_manager.get_text("dungeon.back_option"), "command": self._cancel_selection}]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id)