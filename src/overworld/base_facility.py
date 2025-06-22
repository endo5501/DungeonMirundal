"""施設基底クラス"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from src.character.party import Party
from src.ui.base_ui_pygame import UIElement, UIMenu, UIDialog, ui_manager
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
        
        # 直接メインメニューを表示（ウェルカムメッセージをスキップ）
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
            ui_manager.hide_menu(self.main_menu.menu_id)
        
        menu_title = self.get_name()
        self.main_menu = UIMenu(f"{self.facility_id}_main_menu", menu_title)
        
        # 施設固有のメニュー項目を追加
        self._setup_menu_items(self.main_menu)
        
        # 共通メニュー項目（出る）
        self.main_menu.add_menu_item(
            config_manager.get_text("menu.exit"),
            self._exit_facility
        )
        
        ui_manager.add_menu(self.main_menu)
        ui_manager.show_menu(self.main_menu.menu_id, modal=True)
    
    def _exit_facility(self):
        """施設から出る（UI用）"""
        logger.info(f"施設退出ボタンが押されました: {self.facility_id}")
        # FacilityManagerを通して退場処理を行う
        # これにより on_facility_exit_callback が正しく呼ばれる
        logger.info(f"デバッグ: facility_manager.current_facility = {facility_manager.current_facility}")
        result = facility_manager.exit_current_facility()
        logger.info(f"施設退出処理結果: {result}")
    
    def _cleanup_ui(self):
        """UI要素のクリーンアップ"""
        if self.main_menu:
            ui_manager.hide_menu(self.main_menu.menu_id)
            self.main_menu = None
        
        if self.current_dialog:
            ui_manager.hide_dialog(self.current_dialog.dialog_id)
            self.current_dialog = None
    
    def _show_dialog(self, dialog_id: str, title: str, message: str, buttons: List[Dict[str, Any]] = None):
        """ダイアログの表示"""
        if self.current_dialog:
            ui_manager.hide_dialog(self.current_dialog.dialog_id)
        
        # UIDialogの代わりにUIDialogを使用するが、引数を修正
        self.current_dialog = UIDialog(dialog_id, title, message)
        
        # ボタンがある場合は手動で追加
        if buttons:
            for i, button_data in enumerate(buttons):
                from src.ui.base_ui_pygame import UIButton
                # ボタンの位置を計算
                button_x = 300 + (i * 120)  # 横に並べる
                button_y = self.current_dialog.rect.y + self.current_dialog.rect.height - 50
                
                button = UIButton(f"{dialog_id}_button_{i}", button_data['text'], 
                                x=button_x, y=button_y, width=100, height=30)
                button.on_click = button_data['command']
                self.current_dialog.add_element(button)
        
        ui_manager.add_dialog(self.current_dialog)
        ui_manager.show_dialog(self.current_dialog.dialog_id)
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        if self.current_dialog:
            ui_manager.hide_dialog(self.current_dialog.dialog_id)
            self.current_dialog = None
            
            # ダイアログを閉じた後、メインメニューを再表示
            if self.main_menu:
                ui_manager.show_menu(self.main_menu.menu_id, modal=True)
    
    def _show_welcome_message(self):
        """入場時のウェルカムメッセージを表示"""
        welcome_message = self._get_welcome_message()
        
        self._show_dialog(
            f"{self.facility_id}_welcome",
            self.get_name(),
            welcome_message,
            buttons=[
                {
                    'text': config_manager.get_text("common.ok"),
                    'command': self._on_welcome_ok
                }
            ]
        )
    
    def _on_welcome_ok(self):
        """ウェルカムメッセージのOKボタンが押された時の処理"""
        self._close_dialog()
        # ウェルカムメッセージを閉じた後にメインメニューを表示
        self._show_main_menu()
    
    def _get_welcome_message(self) -> str:
        """施設のウェルカムメッセージを取得（サブクラスでオーバーライド可能）"""
        return f"{self.get_name()}へようこそ！"
    
    def _show_success_message(self, message: str):
        """成功メッセージの表示"""
        self._show_dialog(
            f"{self.facility_id}_success",
            config_manager.get_text("common.info"),
            message,
            buttons=[
                {
                    'text': config_manager.get_text("common.ok"),
                    'command': self._close_dialog
                }
            ]
        )
    
    def _show_error_message(self, message: str):
        """エラーメッセージの表示"""
        self._show_dialog(
            f"{self.facility_id}_error",
            config_manager.get_text("common.error"),
            message,
            buttons=[
                {
                    'text': config_manager.get_text("common.ok"),
                    'command': self._close_dialog
                }
            ]
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
        self.on_facility_exit_callback: Optional[Callable] = None
        
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
        logger.info(f"施設入場処理開始: {facility_id}")
        if facility_id not in self.facilities:
            logger.error(f"施設が見つかりません: {facility_id}")
            return False
        
        # 現在の施設から出る
        if self.current_facility:
            logger.info(f"現在の施設から退場: {self.current_facility}")
            self.exit_current_facility()
        
        facility = self.facilities[facility_id]
        logger.info(f"施設オブジェクトを取得: {facility}")
        if facility.enter(party):
            self.current_facility = facility_id
            logger.info(f"current_facilityを設定: {self.current_facility}")
            return True
        else:
            logger.error(f"施設のenter()がFalseを返しました: {facility_id}")
        
        return False
    
    def exit_current_facility(self) -> bool:
        """現在の施設から出る"""
        logger.info(f"退出処理開始: current_facility={self.current_facility}")
        
        if not self.current_facility:
            logger.warning("current_facilityが設定されていません")
            return False
        
        if self.current_facility not in self.facilities:
            logger.error(f"施設が見つかりません: {self.current_facility}")
            return False
        
        facility = self.facilities[self.current_facility]
        logger.info(f"施設のexit()を呼び出し: {self.current_facility}")
        
        if facility.exit():
            logger.info(f"施設退出成功: {self.current_facility}")
            self.current_facility = None
            
            # 施設退場コールバックを呼び出し
            if self.on_facility_exit_callback:
                logger.info("退場コールバックを実行")
                self.on_facility_exit_callback()
            else:
                logger.warning("退場コールバックが設定されていません")
            
            return True
        else:
            logger.error(f"施設のexit()がFalseを返しました: {self.current_facility}")
        
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
    
    def set_facility_exit_callback(self, callback: Callable):
        """施設退場時のコールバックを設定"""
        self.on_facility_exit_callback = callback
        logger.debug("施設退場コールバックを設定しました")
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        for facility in self.facilities.values():
            if facility.is_active:
                facility.exit()
        
        self.facilities.clear()
        self.current_facility = None
        self.on_facility_exit_callback = None
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


# 施設は必要時に手動で初期化
# 循環インポートを避けるため、自動初期化は行わない