"""ダンジョン選択UI"""

from typing import Dict, List, Optional, Callable, Any
import yaml
from src.ui.base_ui import UIMenu, UIDialog, ui_manager
from direct.gui.DirectGui import DirectScrolledList, DirectButton
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
        """ダンジョン選択メニューをDirectScrolledListで表示"""
        # 既存のメニューがあれば削除
        if hasattr(self, 'dungeon_ui_elements'):
            self._cleanup_dungeon_ui()
        
        # DirectScrolledListを使用したダンジョン選択UIを作成
        self._create_scrolled_dungeon_list(available_dungeons)
    
    def _create_scrolled_dungeon_list(self, available_dungeons: List[Dict[str, Any]]):
        """DirectScrolledListでダンジョン一覧を作成"""
        from direct.gui.DirectGui import DirectFrame, DirectLabel
        from panda3d.core import Vec3
        
        # 背景フレーム
        background = DirectFrame(
            frameColor=(0, 0, 0, 0.8),
            frameSize=(-1.5, 1.5, -1.2, 1.0),
            pos=(0, 0, 0)
        )
        
        # タイトル
        try:
            from src.ui.font_manager import font_manager
            font = font_manager.get_default_font()
        except:
            font = None
        
        title_label = DirectLabel(
            text="ダンジョン選択",
            scale=0.08,
            pos=(0, 0, 0.8),
            text_fg=(1, 1, 0, 1),
            frameColor=(0, 0, 0, 0),
            text_font=font
        )
        
        # ダンジョンリスト用のアイテムを作成
        dungeon_items = []
        for i, dungeon in enumerate(available_dungeons):
            display_name = self._format_dungeon_display_name(dungeon)
            
            # リストアイテムとしてのボタンを作成
            item_button = DirectButton(
                text=display_name,
                scale=0.06,
                text_scale=0.8,
                text_align=0,  # 左寄せ
                command=lambda d_id=dungeon["id"]: self._select_dungeon(d_id),
                frameColor=(0.3, 0.3, 0.5, 0.8),
                text_fg=(1, 1, 1, 1),
                text_font=font,
                relief=1,  # RAISED
                borderWidth=(0.01, 0.01)
            )
            dungeon_items.append(item_button)
        
        # DirectScrolledListを作成
        self.scrolled_list = DirectScrolledList(
            # リスト表示領域
            frameSize=(-1.2, 1.2, -0.6, 0.6),
            frameColor=(0.2, 0.2, 0.3, 0.9),
            pos=(0, 0, 0.1),
            
            # アイテム設定
            numItemsVisible=8,  # 一度に表示するアイテム数を増加
            items=dungeon_items,
            forceHeight=0.08,  # アイテム間隔を制御
            itemFrame_frameSize=(-1.1, 1.1, -0.04, 0.04),
            itemFrame_pos=(0, 0, 0),
            
            # スクロールボタン位置調整
            decButton_pos=(-1.15, 0, -0.65),
            incButton_pos=(1.15, 0, -0.65),
            decButton_text="▲",
            incButton_text="▼",
            decButton_scale=0.05,
            incButton_scale=0.05,
            decButton_text_fg=(1, 1, 1, 1),
            incButton_text_fg=(1, 1, 1, 1),
            
            # デコレーション
            relief=1,  # RAISED
            borderWidth=(0.01, 0.01)
        )
        
        # キャンセルボタン
        cancel_button = DirectButton(
            text="キャンセル",
            scale=0.08,
            pos=(0, 0, -0.8),
            command=self._cancel_selection,
            frameColor=(0.7, 0.3, 0.3, 0.9),
            text_fg=(1, 1, 1, 1),
            text_font=font
        )
        
        # UI要素を管理用のコンテナに格納
        self.dungeon_ui_elements = {
            'background': background,
            'title': title_label,
            'scrolled_list': self.scrolled_list,
            'cancel_button': cancel_button
        }
        
        # 全て表示
        for element in self.dungeon_ui_elements.values():
            element.show()
    
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
        # DirectScrolledListUIをクリーンアップ
        self._cleanup_dungeon_ui()
        
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
    
    def _cleanup_dungeon_ui(self):
        """ダンジョンUI要素のクリーンアップ"""
        if hasattr(self, 'dungeon_ui_elements'):
            for element in self.dungeon_ui_elements.values():
                if element:
                    element.hide()
                    element.destroy()
            self.dungeon_ui_elements.clear()
            
        # DirectScrolledListの個別クリーンアップ
        if hasattr(self, 'scrolled_list'):
            self.scrolled_list.destroy()
            del self.scrolled_list
    
    def _cancel_selection(self):
        """選択をキャンセル"""
        # DirectScrolledListUIをクリーンアップ
        self._cleanup_dungeon_ui()
        
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