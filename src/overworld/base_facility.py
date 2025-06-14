"""施設基底クラス"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from src.character.party import Party
from src.ui.base_ui import UIElement, UIMenu, UIDialog, ui_manager
from src.core.config_manager import config_manager
from src.utils.logger import logger


class FacilityType(Enum):
    """施設タイプ"""
    GUILD = "guild"
    INN = "inn"
    SHOP = "shop"
    TEMPLE = "temple"
    MAGIC_GUILD = "magic_guild"
    DUNGEON_ENTRANCE = "dungeon_entrance"


class FacilityResult(Enum):
    """施設操作結果"""
    SUCCESS = "success"
    CANCELLED = "cancelled"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INVALID_ACTION = "invalid_action"
    ERROR = "error"


class BaseFacility(ABC):
    """施設基底クラス"""
    
    def __init__(self, facility_id: str, facility_type: FacilityType, name_key: str):
        self.facility_id = facility_id
        self.facility_type = facility_type
        self.name_key = name_key
        self.is_active = False
        self.current_party: Optional[Party] = None
        
        # UI要素
        self.main_menu: Optional[UIMenu] = None
        self.current_dialog: Optional[UIDialog] = None
        
        logger.info(f"施設を初期化しました: {facility_id} ({facility_type.value})")
    
    def get_name(self) -> str:
        """施設名を取得"""
        return config_manager.get_text(self.name_key)
    
    def enter(self, party: Party) -> bool:
        """施設に入る"""
        if self.is_active:
            logger.warning(f"施設 {self.facility_id} は既にアクティブです")
            return False
        
        self.current_party = party
        self.is_active = True
        
        # 施設固有の入場処理
        self._on_enter()
        
        # メインメニューの表示
        self._show_main_menu()
        
        logger.info(f"パーティが施設に入りました: {self.facility_id}")
        return True
    
    def exit(self) -> bool:
        """施設から出る"""
        if not self.is_active:
            logger.warning(f"施設 {self.facility_id} はアクティブではありません")
            return False
        
        # UI要素のクリーンアップ
        self._cleanup_ui()
        
        # 施設固有の退場処理
        self._on_exit()
        
        self.current_party = None
        self.is_active = False
        
        logger.info(f"パーティが施設から出ました: {self.facility_id}")
        return True
    
    def _show_main_menu(self):
        """メインメニューの表示"""
        if self.main_menu:
            ui_manager.unregister_element(self.main_menu.element_id)
        
        menu_title = self.get_name()
        self.main_menu = UIMenu(f"{self.facility_id}_main_menu", menu_title)
        
        # 施設固有のメニュー項目を追加
        self._setup_menu_items(self.main_menu)
        
        # 共通メニュー項目（出る）
        self.main_menu.add_menu_item(
            config_manager.get_text("menu.exit"),
            self._exit_facility
        )
        
        ui_manager.register_element(self.main_menu)
        ui_manager.show_element(self.main_menu.element_id, modal=True)
    
    def _exit_facility(self):
        """施設から出る（UI用）"""
        self.exit()
        # 地上部メインメニューに戻る処理は OverworldManager が担当
    
    def _cleanup_ui(self):
        """UI要素のクリーンアップ"""
        if self.main_menu:
            ui_manager.hide_element(self.main_menu.element_id)
            ui_manager.unregister_element(self.main_menu.element_id)
            self.main_menu = None
        
        if self.current_dialog:
            ui_manager.hide_element(self.current_dialog.element_id)
            ui_manager.unregister_element(self.current_dialog.element_id)
            self.current_dialog = None
    
    def _show_dialog(self, dialog_id: str, title: str, message: str, buttons: List[Dict[str, Any]] = None):
        """ダイアログの表示"""
        if self.current_dialog:
            ui_manager.hide_element(self.current_dialog.element_id)
            ui_manager.unregister_element(self.current_dialog.element_id)
        
        if buttons is None:
            buttons = [
                {
                    'text': config_manager.get_text("common.ok"),
                    'command': self._close_dialog
                }
            ]
        
        self.current_dialog = UIDialog(dialog_id, title, message, buttons)
        ui_manager.register_element(self.current_dialog)
        ui_manager.show_element(self.current_dialog.element_id)
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        if self.current_dialog:
            ui_manager.hide_element(self.current_dialog.element_id)
            ui_manager.unregister_element(self.current_dialog.element_id)
            self.current_dialog = None
    
    def _show_success_message(self, message: str):
        """成功メッセージの表示"""
        self._show_dialog(
            f"{self.facility_id}_success",
            config_manager.get_text("common.info"),
            message
        )
    
    def _show_error_message(self, message: str):
        """エラーメッセージの表示"""
        self._show_dialog(
            f"{self.facility_id}_error",
            config_manager.get_text("common.error"),
            message
        )
    
    def _show_confirmation(self, message: str, on_confirm: Callable, on_cancel: Callable = None):
        """確認ダイアログの表示"""
        buttons = [
            {
                'text': config_manager.get_text("common.yes"),
                'command': lambda: (self._close_dialog(), on_confirm())
            },
            {
                'text': config_manager.get_text("common.no"),
                'command': lambda: (self._close_dialog(), on_cancel() if on_cancel else None)
            }
        ]
        
        self._show_dialog(
            f"{self.facility_id}_confirm",
            config_manager.get_text("common.confirm"),
            message,
            buttons
        )
    
    @abstractmethod
    def _setup_menu_items(self, menu: UIMenu):
        """施設固有のメニュー項目を設定（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def _on_enter(self):
        """施設入場時の処理（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def _on_exit(self):
        """施設退場時の処理（サブクラスで実装）"""
        pass
    
    def get_facility_data(self) -> Dict[str, Any]:
        """施設データの取得（セーブ用）"""
        return {
            'facility_id': self.facility_id,
            'facility_type': self.facility_type.value,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_facility_data(cls, data: Dict[str, Any]) -> 'BaseFacility':
        """施設データから復元（ロード用）"""
        # サブクラスで実装
        raise NotImplementedError("サブクラスで実装してください")


class FacilityManager:
    """施設管理システム"""
    
    def __init__(self):
        self.facilities: Dict[str, BaseFacility] = {}
        self.current_facility: Optional[str] = None
        
        logger.info("FacilityManagerを初期化しました")
    
    def register_facility(self, facility: BaseFacility):
        """施設を登録"""
        self.facilities[facility.facility_id] = facility
        logger.info(f"施設を登録しました: {facility.facility_id}")
    
    def unregister_facility(self, facility_id: str):
        """施設の登録を解除"""
        if facility_id in self.facilities:
            facility = self.facilities[facility_id]
            if facility.is_active:
                facility.exit()
            del self.facilities[facility_id]
            logger.info(f"施設の登録を解除しました: {facility_id}")
    
    def enter_facility(self, facility_id: str, party: Party) -> bool:
        """施設に入る"""
        if facility_id not in self.facilities:
            logger.error(f"施設が見つかりません: {facility_id}")
            return False
        
        # 現在の施設から出る
        if self.current_facility:
            self.exit_current_facility()
        
        facility = self.facilities[facility_id]
        if facility.enter(party):
            self.current_facility = facility_id
            return True
        
        return False
    
    def exit_current_facility(self) -> bool:
        """現在の施設から出る"""
        if not self.current_facility:
            return False
        
        facility = self.facilities[self.current_facility]
        if facility.exit():
            self.current_facility = None
            return True
        
        return False
    
    def get_current_facility(self) -> Optional[BaseFacility]:
        """現在の施設を取得"""
        if self.current_facility:
            return self.facilities.get(self.current_facility)
        return None
    
    def get_facility(self, facility_id: str) -> Optional[BaseFacility]:
        """指定された施設を取得"""
        return self.facilities.get(facility_id)
    
    def get_all_facilities(self) -> List[BaseFacility]:
        """全施設のリストを取得"""
        return list(self.facilities.values())
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        for facility in self.facilities.values():
            if facility.is_active:
                facility.exit()
        
        self.facilities.clear()
        self.current_facility = None
        logger.info("FacilityManagerをクリーンアップしました")


# グローバルインスタンス
facility_manager = FacilityManager()


def initialize_facilities():
    """全施設を初期化・登録"""
    from src.overworld.facilities.guild import AdventurersGuild
    from src.overworld.facilities.inn import Inn
    from src.overworld.facilities.shop import Shop
    from src.overworld.facilities.temple import Temple
    from src.overworld.facilities.magic_guild import MagicGuild
    
    # 各施設を作成・登録
    guild = AdventurersGuild()
    inn = Inn()
    shop = Shop()
    temple = Temple()
    magic_guild = MagicGuild()
    
    facility_manager.register_facility(guild)
    facility_manager.register_facility(inn)
    facility_manager.register_facility(shop)
    facility_manager.register_facility(temple)
    facility_manager.register_facility(magic_guild)
    
    logger.info("全施設の初期化・登録が完了しました")


# 施設の自動初期化
try:
    initialize_facilities()
except ImportError as e:
    logger.warning(f"施設の初期化でエラーが発生しました: {e}")
    logger.info("施設は後で手動で初期化されます")