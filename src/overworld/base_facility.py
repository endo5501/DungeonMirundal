"""施設基底クラス"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import pygame

from src.character.party import Party
from src.ui.base_ui_pygame import UIElement, UIMenu, UIDialog, ui_manager
from src.ui.menu_stack_manager import MenuStackManager, MenuType
from src.ui.dialog_template import DialogTemplate, DialogType
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
        
        # 新しいメニューシステム
        self.menu_stack_manager: Optional[MenuStackManager] = None
        self.dialog_template: Optional[DialogTemplate] = None
        
        # 旧UIシステム（後方互換性のため）
        self.main_menu: Optional[UIMenu] = None
        self.current_dialog: Optional[UIDialog] = None
        
        # 新システム有効化フラグ
        self.use_new_menu_system = False
        
        logger.info(f"施設を初期化しました: {facility_id} ({facility_type.value})")
    
    def initialize_menu_system(self, ui_manager) -> None:
        """新しいメニューシステムを初期化"""
        try:
            self.menu_stack_manager = MenuStackManager(ui_manager)
            self.dialog_template = DialogTemplate(self.menu_stack_manager)
            self.use_new_menu_system = True
            
            # ESCキー処理のコールバック設定
            self.menu_stack_manager.on_escape_pressed = self._handle_escape_key
            
            logger.info(f"施設 {self.facility_id} の新メニューシステムを初期化しました")
            
        except Exception as e:
            logger.error(f"メニューシステム初期化エラー: {e}")
            self.use_new_menu_system = False
    
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
        if self.use_new_menu_system and self.menu_stack_manager:
            # 新システムを使用
            self._show_main_menu_new()
        else:
            # 旧システムを使用（後方互換性）
            self._show_main_menu_legacy()
    
    def _show_main_menu_new(self):
        """新しいメニューシステムでメインメニューを表示"""
        try:
            menu_title = self.get_name()
            main_menu = UIMenu(f"{self.facility_id}_main_menu", menu_title)
            
            # 施設固有のメニュー項目を追加
            self._setup_menu_items(main_menu)
            
            # 共通メニュー項目（出る）
            main_menu.add_menu_item(
                config_manager.get_text("menu.exit"),
                self._exit_facility
            )
            
            # メニュースタックにプッシュ
            self.menu_stack_manager.push_menu(
                main_menu, 
                MenuType.FACILITY_MAIN,
                {'facility_id': self.facility_id}
            )
            
            logger.info(f"新システムで施設メインメニューを表示: {self.facility_id}")
            
        except Exception as e:
            logger.error(f"新メニューシステム表示エラー: {e}")
            # フォールバックとして旧システムを使用
            self._show_main_menu_legacy()
    
    def _show_main_menu_legacy(self):
        """旧メニューシステムでメインメニューを表示（後方互換性）"""
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
        try:
            # 新システムのクリーンアップ
            if self.use_new_menu_system:
                if self.menu_stack_manager:
                    self.menu_stack_manager.clear_stack()
                if self.dialog_template:
                    self.dialog_template.cleanup_all_dialogs()
            
            # 旧システムのクリーンアップ
            if self.main_menu:
                ui_manager.hide_menu(self.main_menu.menu_id)
                self.main_menu = None
            
            if self.current_dialog:
                ui_manager.hide_dialog(self.current_dialog.dialog_id)
                self.current_dialog = None
                
            logger.debug(f"施設 {self.facility_id} のUIをクリーンアップしました")
            
        except Exception as e:
            logger.error(f"UIクリーンアップエラー: {e}")
    
    def _show_dialog(self, dialog_id: str, title: str, message: str, buttons: List[Dict[str, Any]] = None):
        """ダイアログの表示"""
        # ui_managerがNoneの場合は安全にスキップ
        if ui_manager is None:
            logger.warning(f"ui_managerがNoneのため、ダイアログ表示をスキップ: {dialog_id}")
            return
            
        if self.current_dialog:
            ui_manager.hide_dialog(self.current_dialog.dialog_id)
        
        # UIDialogの代わりにUIDialogを使用するが、引数を修正
        self.current_dialog = UIDialog(dialog_id, title, message)
        
        # ボタンがある場合は手動で追加
        if buttons:
            for i, button_data in enumerate(buttons):
                from src.ui.base_ui_pygame import UIButton
                # ボタンの位置を計算（画面内に収まるように）
                button_x = 300 + (i * 120)  # 横に並べる
                button_y = min(600, self.current_dialog.rect.y + self.current_dialog.rect.height + 10)  # 画面内に収める
                
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
        if self.use_new_menu_system and self.dialog_template:
            # 新システムを使用
            dialog = self.dialog_template.create_confirmation_dialog(
                f"{self.facility_id}_confirm",
                config_manager.get_text("common.confirm"),
                message,
                on_confirm,
                on_cancel
            )
            self.dialog_template.show_dialog(dialog)
        else:
            # 旧システムを使用
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
    
    # === 新しいメニューシステム用メソッド ===
    
    def show_submenu(self, menu: UIMenu, context: Dict[str, Any] = None) -> bool:
        """サブメニューを表示（新システム）"""
        if not self.use_new_menu_system or not self.menu_stack_manager:
            logger.warning("新メニューシステムが利用できません")
            return False
        
        try:
            self.menu_stack_manager.push_menu(
                menu, 
                MenuType.SUBMENU,
                context or {}
            )
            return True
        except Exception as e:
            logger.error(f"サブメニュー表示エラー: {e}")
            return False
    
    def show_information_dialog(self, title: str, message: str, 
                              on_close: Optional[Callable] = None) -> bool:
        """情報ダイアログを表示（新システム）"""
        if not self.use_new_menu_system or not self.dialog_template:
            logger.warning("新ダイアログシステムが利用できません")
            return False
        
        try:
            dialog = self.dialog_template.create_information_dialog(
                f"{self.facility_id}_info_{pygame.time.get_ticks()}",
                title,
                message,
                on_close
            )
            return self.dialog_template.show_dialog(dialog)
        except Exception as e:
            logger.error(f"情報ダイアログ表示エラー: {e}")
            return False
    
    def show_error_dialog(self, title: str, message: str,
                         on_close: Optional[Callable] = None) -> bool:
        """エラーダイアログを表示（新システム）"""
        if not self.use_new_menu_system or not self.dialog_template:
            logger.warning("新ダイアログシステムが利用できません")
            return False
        
        try:
            dialog = self.dialog_template.create_error_dialog(
                f"{self.facility_id}_error_{pygame.time.get_ticks()}",
                title,
                message,
                on_close
            )
            return self.dialog_template.show_dialog(dialog)
        except Exception as e:
            logger.error(f"エラーダイアログ表示エラー: {e}")
            return False
    
    def show_success_dialog(self, title: str, message: str,
                          on_close: Optional[Callable] = None) -> bool:
        """成功ダイアログを表示（新システム）"""
        if not self.use_new_menu_system or not self.dialog_template:
            logger.warning("新ダイアログシステムが利用できません")
            return False
        
        try:
            dialog = self.dialog_template.create_success_dialog(
                f"{self.facility_id}_success_{pygame.time.get_ticks()}",
                title,
                message,
                on_close
            )
            return self.dialog_template.show_dialog(dialog)
        except Exception as e:
            logger.error(f"成功ダイアログ表示エラー: {e}")
            return False
    
    def show_confirmation_dialog(self, title: str, message: str,
                               on_confirm: Optional[Callable] = None,
                               on_cancel: Optional[Callable] = None) -> bool:
        """確認ダイアログを表示（新システム）"""
        if not self.use_new_menu_system or not self.dialog_template:
            logger.warning("新ダイアログシステムが利用できません")
            return False
        
        try:
            dialog = self.dialog_template.create_confirmation_dialog(
                f"{self.facility_id}_confirm_{pygame.time.get_ticks()}",
                title,
                message,
                on_confirm,
                on_cancel
            )
            return self.dialog_template.show_dialog(dialog)
        except Exception as e:
            logger.error(f"確認ダイアログ表示エラー: {e}")
            return False
    
    def show_selection_dialog(self, title: str, message: str, 
                            selections: List[Dict[str, Any]],
                            on_select: Optional[Callable] = None,
                            on_cancel: Optional[Callable] = None) -> bool:
        """選択ダイアログを表示（新システム）"""
        if not self.use_new_menu_system or not self.dialog_template:
            logger.warning("新ダイアログシステムが利用できません")
            return False
        
        try:
            dialog = self.dialog_template.create_selection_dialog(
                f"{self.facility_id}_selection_{pygame.time.get_ticks()}",
                title,
                message,
                selections,
                on_select,
                on_cancel
            )
            return self.dialog_template.show_dialog(dialog)
        except Exception as e:
            logger.error(f"選択ダイアログ表示エラー: {e}")
            return False
    
    def back_to_previous_menu(self) -> bool:
        """前のメニューに戻る（新システム）"""
        if not self.use_new_menu_system or not self.menu_stack_manager:
            return False
        
        return self.menu_stack_manager.back_to_previous()
    
    def back_to_facility_main(self) -> bool:
        """施設メインメニューに戻る（新システム）"""
        if not self.use_new_menu_system or not self.menu_stack_manager:
            return False
        
        return self.menu_stack_manager.back_to_facility_main()
    
    def _handle_escape_key(self) -> bool:
        """ESCキー処理（新システム用コールバック）"""
        try:
            # 施設固有のESC処理があれば実行
            if hasattr(self, '_on_escape_key'):
                if self._on_escape_key():
                    return True
            
            # デフォルトの戻る処理
            return self.back_to_previous_menu()
            
        except Exception as e:
            logger.error(f"ESCキー処理エラー: {e}")
            return False
    
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
        self.ui_manager = None
        
        logger.info("FacilityManagerを初期化しました")
    
    def set_ui_manager(self, ui_manager):
        """UIマネージャーを設定"""
        self.ui_manager = ui_manager
        
        # 既存の全施設の新メニューシステムを初期化
        for facility in self.facilities.values():
            facility.initialize_menu_system(ui_manager)
        
        logger.info("FacilityManagerにUIマネージャーを設定しました")
    
    def register_facility(self, facility: BaseFacility):
        """施設を登録"""
        self.facilities[facility.facility_id] = facility
        
        # UIマネージャーが設定済みの場合は新メニューシステムを初期化
        if self.ui_manager:
            facility.initialize_menu_system(self.ui_manager)
        
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