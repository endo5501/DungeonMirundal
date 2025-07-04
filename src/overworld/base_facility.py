"""施設基底クラス"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import pygame

from src.character.party import Party
# UIMenuとMenuStackManagerは段階的削除により使用しない
# from src.ui.menu_stack_manager import MenuStackManager, MenuType  # WindowSystem移行により削除
# from src.ui.dialog_template import DialogTemplate  # UIDialog削除により使用不可
from src.ui.window_system import WindowManager
from src.core.config_manager import config_manager
from src.utils.logger import logger

# 施設システム定数
DEFAULT_ACTIVE_STATE = False


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
        self.is_active = DEFAULT_ACTIVE_STATE
        self.current_party: Optional[Party] = None
        
        # WindowManager統合（新システム）
        self.window_manager = WindowManager.get_instance()
        
        # MenuStackManagerシステム（削除）- WindowSystemへ移行
        # self.menu_stack_manager: Optional[MenuStackManager] = None
        # self.dialog_template: Optional[DialogTemplate] = None  # UIDialog削除により使用不可
        self.ui_manager = None  # UIManager参照（レガシー互換性のため）
        
        logger.info(f"施設を初期化しました: {facility_id} ({facility_type.value})")
    
    def initialize_menu_system(self, ui_manager) -> None:
        """メニューシステムを初期化（WindowSystem対応）"""
        # UIManager参照を保持（レガシー互換性）
        self.ui_manager = ui_manager
        
        # DialogTemplateの初期化（UIDialog削除により使用不可）
        # if self.dialog_template is None:
        #     self.dialog_template = DialogTemplate(None)  # UIDialog削除により使用不可
        
        # WindowSystemではESCキー処理はWindowが直接管理
        
        logger.info(f"施設 {self.facility_id} のメニューシステムを初期化しました（WindowSystem対応）")
    
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
        self._show_main_menu_unified()
    
    def _show_main_menu_unified(self):
        """統一されたメインメニュー表示（WindowManagerのみ）"""
        # WindowManagerベースの表示のみ使用
        self._show_main_menu_window_manager()
        logger.info(f"WindowManagerで施設メインメニューを表示: {self.facility_id}")
    
    def _show_main_menu_window_manager(self):
        """WindowManagerベースメインメニュー表示（新システム）"""
        try:
            from src.ui.window_system.facility_menu_window import FacilityMenuWindow
            
            logger.info(f"[DEBUG] 施設メニュー表示開始: {self.facility_id}")
            
            menu_config = self._create_facility_menu_config()
            logger.info(f"[DEBUG] 施設 {self.facility_id} のメニュー設定: {menu_config}")
            
            # WindowManagerの正しい使用パターン: create_window -> show_window
            facility_window = self.window_manager.create_window(
                FacilityMenuWindow,
                f"{self.facility_id}_main",
                facility_config=menu_config,
                modal=False
            )
            facility_window.message_handler = self.handle_facility_message
            self.window_manager.show_window(facility_window, push_to_stack=True)
            
            logger.info(f"[DEBUG] 施設メニュー表示完了: {self.facility_id}")
            
        except ImportError:
            logger.warning("FacilityMenuWindow未実装、フォールバックが必要")
            raise
    
    
    
    # === WindowManager統合メソッド ===
    
    def _create_facility_menu_config(self) -> Dict[str, Any]:
        """施設メニュー設定を作成（WindowManager用）"""
        # 基本的な退出メニューのみ提供
        # 各施設で独自の設定メソッドをオーバーライドして使用
        menu_items = [
            {
                'id': 'exit',
                'label': config_manager.get_text("menu.exit"),
                'type': 'action',
                'enabled': True
            }
        ]
        
        return {
            'menu_type': 'facility',
            'facility_type': self.facility_type.value,
            'facility_name': self.get_name(),
            'menu_items': menu_items,
            'party': self.current_party  # FacilityMenuWindowで必要
        }
    
    def handle_facility_message(self, message_type: str, data: dict) -> bool:
        """FacilityMenuWindowからのメッセージを処理"""
        if message_type == 'menu_item_selected':
            item_id = data.get('item_id')
            
            if item_id == 'exit':
                self._exit_facility()
                return True
            else:
                # 施設固有のアクション処理
                return self._handle_facility_action(item_id, data)
        
        return False
    
    def _handle_facility_action(self, action_id: str, data: dict) -> bool:
        """施設固有のアクション処理（サブクラスでオーバーライド可能）"""
        logger.warning(f"未処理の施設アクション: {action_id} (施設: {self.facility_id})")
        return False
    
    def _exit_facility(self):
        """施設から出る（UI用）"""
        logger.info(f"施設退出ボタンが押されました: {self.facility_id}")
        # FacilityManagerを通して退場処理を行う
        # これにより on_facility_exit_callback が正しく呼ばれる
        # グローバルインスタンスを取得（circular importを避けるため）
        global facility_manager
        if 'facility_manager' in globals():
            logger.info(f"デバッグ: facility_manager.current_facility = {facility_manager.current_facility}")
            result = facility_manager.exit_current_facility()
            logger.info(f"施設退出処理結果: {result}")
        else:
            logger.warning("facility_managerが利用できません。直接退場処理を実行します。")
            self.exit()
    
    def _cleanup_ui(self):
        """UI要素のクリーンアップ"""
        try:
            # WindowManagerクリーンアップ（新システム）
            self._cleanup_ui_windows()
            
            # MenuStackManagerシステムのクリーンアップ（削除）
            # WindowSystemではWindowManagerが管理
            if hasattr(self, 'dialog_template') and self.dialog_template:
                self.dialog_template.cleanup_all_dialogs()
                
            logger.debug(f"施設 {self.facility_id} のUIをクリーンアップしました")
            
        except Exception as e:
            logger.error(f"UIクリーンアップエラー: {e}")
    
    def _cleanup_ui_windows(self):
        """WindowSystem関連のクリーンアップ"""
        try:
            if self.window_manager:
                # 施設に関連するウィンドウを閉じる
                # 複数の形式を試行する（標準形式を先に探す）
                possible_window_ids = [
                    f"{self.facility_id}_main",        # 標準形式（guild_main, inn_main）
                    f"{self.facility_id}_main_menu"    # 個別施設形式（guild_main_menu, inn_main_menu）
                ]
                
                for facility_window_id in possible_window_ids:
                    window = self.window_manager.get_window(facility_window_id)
                    if window:
                        logger.debug(f"ウィンドウをクリーンアップします: {facility_window_id}")
                        self.window_manager.close_window(window)
                        break  # 一つ見つかったら終了
                else:
                    logger.debug(f"施設 {self.facility_id} に対応するウィンドウが見つかりませんでした")
                
            logger.debug(f"施設 {self.facility_id} のWindowSystemをクリーンアップしました")
            
        except Exception as e:
            logger.error(f"WindowSystemクリーンアップエラー: {e}")
    
    
    # === WindowManagerベースダイアログシステム ===
    
    def show_information_dialog_window(self, title: str, message: str, 
                                     on_close: Optional[Callable] = None) -> bool:
        """情報ダイアログを表示（WindowManager版）"""
        try:
            from src.ui.window_system.dialog_window import DialogWindow, DialogType
            
            logger.info(f"情報ダイアログ作成開始: {title}")
            dialog_window = self.window_manager.create_window(
                DialogWindow,
                f"{self.facility_id}_info_dialog", 
                dialog_type=DialogType.INFORMATION,
                message=f"{title}\n\n{message}"
            )
            if on_close:
                dialog_window.message_handler = lambda msg_type, data: on_close() if msg_type == 'dialog_closed' else None
            
            self.window_manager.show_window(dialog_window, push_to_stack=True)
            logger.info(f"情報ダイアログ表示完了: {title}")
            return True
            
        except ImportError:
            logger.warning("DialogWindow未実装、フォールバックダイアログを使用")
            return self.show_information_dialog(title, message, on_close)
        except Exception as e:
            logger.error(f"WindowManagerダイアログエラー: {e}")
            return self.show_information_dialog(title, message, on_close)
    
    def show_error_dialog_window(self, title: str, message: str,
                               on_close: Optional[Callable] = None) -> bool:
        """エラーダイアログを表示（WindowManager版）"""
        try:
            from src.ui.window_system.dialog_window import DialogWindow, DialogType
            
            dialog_window = self.window_manager.create_window(
                DialogWindow,
                f"{self.facility_id}_error_dialog", 
                dialog_type=DialogType.ERROR,
                message=f"{title}\n\n{message}"
            )
            if on_close:
                dialog_window.message_handler = lambda msg_type, data: on_close() if msg_type == 'dialog_closed' else None
            
            self.window_manager.show_window(dialog_window, push_to_stack=True)
            return True
            
        except ImportError:
            logger.warning("DialogWindow未実装、フォールバックダイアログを使用")
            return self.show_error_dialog(title, message, on_close)
        except Exception as e:
            logger.error(f"WindowManagerエラーダイアログエラー: {e}")
            return self.show_error_dialog(title, message, on_close)
    
    def show_success_dialog_window(self, title: str, message: str,
                                 on_close: Optional[Callable] = None) -> bool:
        """成功ダイアログを表示（WindowManager版）"""
        try:
            from src.ui.window_system.dialog_window import DialogWindow, DialogType
            
            dialog_window = self.window_manager.create_window(
                DialogWindow,
                f"{self.facility_id}_success_dialog", 
                dialog_type=DialogType.SUCCESS,
                message=f"{title}\n\n{message}"
            )
            if on_close:
                dialog_window.message_handler = lambda msg_type, data: on_close() if msg_type == 'dialog_closed' else None
            
            self.window_manager.show_window(dialog_window, push_to_stack=True)
            return True
            
        except ImportError:
            logger.warning("DialogWindow未実装、フォールバックダイアログを使用")
            return self.show_success_dialog(title, message, on_close)
        except Exception as e:
            logger.error(f"WindowManager成功ダイアログエラー: {e}")
            return self.show_success_dialog(title, message, on_close)
    
    def show_confirmation_dialog_window(self, title: str, message: str,
                                      on_confirm: Optional[Callable] = None,
                                      on_cancel: Optional[Callable] = None) -> bool:
        """確認ダイアログを表示（WindowManager版）"""
        try:
            from src.ui.window_system.dialog_window import DialogWindow
            
            dialog_config = {
                'title': title,
                'message': message,
                'dialog_type': 'confirmation',
                'buttons': [
                    {'id': 'yes', 'label': 'はい', 'type': 'primary'},
                    {'id': 'no', 'label': 'いいえ', 'type': 'secondary'}
                ]
            }
            
            def handle_confirmation_message(msg_type: str, data: dict):
                if msg_type == 'dialog_button_clicked':
                    button_id = data.get('button_id')
                    if button_id == 'yes' and on_confirm:
                        on_confirm()
                    elif button_id == 'no' and on_cancel:
                        on_cancel()
            
            dialog_window = self.window_manager.create_window(
                DialogWindow,
                f"{self.facility_id}_confirm_dialog", 
                dialog_config=dialog_config
            )
            dialog_window.message_handler = handle_confirmation_message
            
            self.window_manager.show_window(dialog_window, push_to_stack=True)
            return True
            
        except ImportError:
            logger.warning("DialogWindow未実装、フォールバックダイアログを使用")
            return self.show_confirmation_dialog(title, message, on_confirm, on_cancel)
        except Exception as e:
            logger.error(f"WindowManager確認ダイアログエラー: {e}")
            return self.show_confirmation_dialog(title, message, on_confirm, on_cancel)
    
    def show_submenu_window(self, submenu_id: str, submenu_config: Dict[str, Any]) -> bool:
        """サブメニューを表示（WindowManager版）"""
        try:
            from src.ui.window_system.facility_menu_window import FacilityMenuWindow
            
            submenu_window = FacilityMenuWindow(submenu_id, submenu_config)
            submenu_window.message_handler = self.handle_facility_message
            self.window_manager.show_window(submenu_window, push_to_stack=True)
            return True
            
        except ImportError:
            logger.warning("FacilityMenuWindow未実装、フォールバックサブメニューを使用")
            return False
        except Exception as e:
            logger.error(f"WindowManagerサブメニューエラー: {e}")
            return False
    
    # === 統一インターフェース ===
    
    def _show_submenu_unified(self, submenu_config: Dict[str, Any]) -> bool:
        """統一されたサブメニュー表示"""
        try:
            submenu_id = f"{self.facility_id}_submenu_{pygame.time.get_ticks()}"
            return self.show_submenu_window(submenu_id, submenu_config)
        except Exception:
            # フォールバック処理
            return False
    
    def _show_dialog_unified(self, dialog_type: str, title: str, message: str, **kwargs) -> bool:
        """統一されたダイアログ表示"""
        try:
            if dialog_type == 'information':
                return self.show_information_dialog_window(title, message, kwargs.get('on_close'))
            elif dialog_type == 'error':
                return self.show_error_dialog_window(title, message, kwargs.get('on_close'))
            elif dialog_type == 'success':
                return self.show_success_dialog_window(title, message, kwargs.get('on_close'))
            elif dialog_type == 'confirmation':
                return self.show_confirmation_dialog_window(title, message, kwargs.get('on_confirm'), kwargs.get('on_cancel'))
            else:
                logger.warning(f"未知のダイアログタイプ: {dialog_type}")
                return False
        except Exception as e:
            logger.error(f"統一ダイアログエラー: {e}")
            return False
    
    # === WindowSystem統合メソッド ===
    
    def show_information_dialog(self, title: str, message: str, 
                              on_close: Optional[Callable] = None, 
                              buttons: Optional[List[Dict]] = None) -> bool:
        """情報ダイアログを表示"""
        try:
            # WindowManagerを使用してDialogWindowを直接作成・表示
            from src.ui.window_system.dialog_window import DialogWindow, DialogType
            from src.ui.window_system import WindowManager
            
            window_manager = WindowManager.get_instance()
            if window_manager:
                # DialogWindowを作成
                dialog_window = window_manager.create_window(
                    DialogWindow,
                    f"{self.facility_id}_info_dialog",
                    dialog_type=DialogType.INFORMATION,
                    message=f"{title}\n\n{message}"
                )
                
                # コールバック設定
                if on_close:
                    original_on_close = on_close
                    def dialog_message_handler(msg_type: str, data: dict):
                        if msg_type == 'dialog_result' or msg_type == 'close_requested':
                            original_on_close()
                    dialog_window.message_handler = dialog_message_handler
                
                # ダイアログを表示
                window_manager.show_window(dialog_window, push_to_stack=True)
                return True
            
            # フォールバック: dialog_templateが利用可能な場合
            if hasattr(self, 'dialog_template') and self.dialog_template:
                dialog = self.dialog_template.create_information_dialog(
                    f"{self.facility_id}_info_{pygame.time.get_ticks()}",
                    title,
                    message,
                    on_close
                )
                return self.dialog_template.show_dialog(dialog)
            
            # 最後のフォールバック: ログ出力のみ
            logger.info(f"情報ダイアログ: {title} - {message}")
            if on_close:
                on_close()
            return True
            
        except Exception as e:
            logger.error(f"情報ダイアログ表示エラー: {e}")
            # エラーが発生してもコールバックは実行
            if on_close:
                on_close()
            return False
    
    def show_error_dialog(self, title: str, message: str,
                         on_close: Optional[Callable] = None) -> bool:
        """エラーダイアログを表示"""
        try:
            # WindowManagerを使用してDialogWindowを直接作成・表示
            from src.ui.window_system.dialog_window import DialogWindow, DialogType
            from src.ui.window_system import WindowManager
            
            window_manager = WindowManager.get_instance()
            if window_manager:
                # DialogWindowを作成
                dialog_window = window_manager.create_window(
                    DialogWindow,
                    f"{self.facility_id}_error_dialog",
                    dialog_type=DialogType.ERROR,
                    message=f"{title}\n\n{message}"
                )
                
                # コールバック設定
                if on_close:
                    original_on_close = on_close
                    def dialog_message_handler(msg_type: str, data: dict):
                        if msg_type == 'dialog_result' or msg_type == 'close_requested':
                            original_on_close()
                    dialog_window.message_handler = dialog_message_handler
                
                # ダイアログを表示
                window_manager.show_window(dialog_window, push_to_stack=True)
                return True
            
            # フォールバック: dialog_templateが利用可能な場合
            if hasattr(self, 'dialog_template') and self.dialog_template:
                dialog = self.dialog_template.create_error_dialog(
                    f"{self.facility_id}_error_{pygame.time.get_ticks()}",
                    title,
                    message,
                    on_close
                )
                return self.dialog_template.show_dialog(dialog)
            
            # 最後のフォールバック: ログ出力のみ
            logger.error(f"エラーダイアログ: {title} - {message}")
            if on_close:
                on_close()
            return True
            
        except Exception as e:
            logger.error(f"エラーダイアログ表示エラー: {e}")
            # ダイアログ表示に失敗してもコールバックは実行
            if on_close:
                on_close()
            return False
    
    def show_success_dialog(self, title: str, message: str,
                          on_close: Optional[Callable] = None) -> bool:
        """成功ダイアログを表示"""
        try:
            # WindowManagerを使用してDialogWindowを直接作成・表示
            from src.ui.window_system.dialog_window import DialogWindow, DialogType
            from src.ui.window_system import WindowManager
            
            window_manager = WindowManager.get_instance()
            if window_manager:
                # DialogWindowを作成
                dialog_window = window_manager.create_window(
                    DialogWindow,
                    f"{self.facility_id}_success_dialog",
                    dialog_type=DialogType.SUCCESS,
                    message=f"{title}\n\n{message}"
                )
                
                # コールバック設定
                if on_close:
                    original_on_close = on_close
                    def dialog_message_handler(msg_type: str, data: dict):
                        if msg_type == 'dialog_result' or msg_type == 'close_requested':
                            original_on_close()
                    dialog_window.message_handler = dialog_message_handler
                
                # ダイアログを表示
                window_manager.show_window(dialog_window, push_to_stack=True)
                return True
            
            # フォールバック: dialog_templateが利用可能な場合
            if hasattr(self, 'dialog_template') and self.dialog_template:
                dialog = self.dialog_template.create_success_dialog(
                    f"{self.facility_id}_success_{pygame.time.get_ticks()}",
                    title,
                    message,
                    on_close
                )
                success = self.dialog_template.show_dialog(dialog)
                # ダイアログ表示に失敗した場合、コールバックを直接実行
                if not success and on_close:
                    logger.info("ダイアログ表示失敗、コールバックを直接実行")
                    on_close()
                return success
            
            # 最後のフォールバック: ログ出力のみ
            logger.info(f"成功ダイアログ: {title} - {message}")
            if on_close:
                on_close()
            return True
            
        except Exception as e:
            logger.error(f"成功ダイアログ表示エラー: {e}")
            # エラーが発生してもコールバックは実行
            if on_close:
                on_close()
            return False
    
    def show_confirmation_dialog(self, title: str, message: str,
                               on_confirm: Optional[Callable] = None,
                               on_cancel: Optional[Callable] = None) -> bool:
        """確認ダイアログを表示"""
        try:
            # WindowManagerを使用してDialogWindowを直接作成・表示
            from src.ui.window_system.dialog_window import DialogWindow, DialogType, DialogResult
            from src.ui.window_system import WindowManager
            
            window_manager = WindowManager.get_instance()
            if window_manager:
                # DialogWindowを作成
                dialog_window = window_manager.create_window(
                    DialogWindow,
                    f"{self.facility_id}_confirm_dialog",
                    dialog_type=DialogType.CONFIRMATION,
                    message=f"{title}\n\n{message}"
                )
                
                # コールバック設定
                def confirmation_message_handler(msg_type: str, data: dict):
                    if msg_type == 'dialog_result':
                        result = data.get('result')
                        if result == DialogResult.YES and on_confirm:
                            on_confirm()
                        elif result == DialogResult.NO and on_cancel:
                            on_cancel()
                
                dialog_window.message_handler = confirmation_message_handler
                
                # ダイアログを表示
                window_manager.show_window(dialog_window, push_to_stack=True)
                return True
            
            # フォールバック: dialog_templateが利用可能な場合
            if hasattr(self, 'dialog_template') and self.dialog_template:
                dialog = self.dialog_template.create_confirmation_dialog(
                    f"{self.facility_id}_confirm_{pygame.time.get_ticks()}",
                    title,
                    message,
                    on_confirm,
                    on_cancel
                )
                return self.dialog_template.show_dialog(dialog)
            
            # 最後のフォールバック: ログ出力のみ
            logger.info(f"確認ダイアログ: {title} - {message}")
            if on_confirm:
                on_confirm()
            return True
            
        except Exception as e:
            logger.error(f"確認ダイアログ表示エラー: {e}")
            return False
    
    def show_selection_dialog(self, title: str, message: str, 
                            selections: List[Dict[str, Any]],
                            on_select: Optional[Callable] = None,
                            on_cancel: Optional[Callable] = None) -> bool:
        """選択ダイアログを表示"""
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
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理（派生クラスでオーバーライド可能）"""
        # UISelectionListのイベント処理（派生クラスで実装）
        return self._handle_ui_selection_events(event)
    
    def _handle_ui_selection_events(self, event: pygame.event.Event) -> bool:
        """UISelectionListのイベント処理（派生クラスでオーバーライド）"""
        return False
    
    def _check_pygame_gui_manager(self) -> bool:
        """pygame_gui_managerが利用可能かチェック"""
        try:
            from src.ui.base_ui_pygame import ui_manager
            if not hasattr(ui_manager, 'pygame_gui_manager') or ui_manager.pygame_gui_manager is None:
                logger.warning(f"{self.facility_id}: pygame_gui_managerが利用できません")
                return False
            return True
        except ImportError:
            logger.warning(f"{self.facility_id}: ui_managerのインポートに失敗しました")
            return False
    
    def _get_effective_ui_manager(self):
        """有効なUIマネージャーを取得（WindowSystem対応）"""
        # UIManager参照を直接返す
        return self.ui_manager
    
    
    def back_to_previous_menu(self) -> bool:
        """前のメニューに戻る（WindowSystem対応）"""
        # WindowManagerのgo_back機能を使用
        if self.window_manager:
            return self.window_manager.go_back()
        return False
    
    
    
    
    
    def back_to_facility_main(self) -> bool:
        """施設メインメニューに戻る（WindowSystem対応）"""
        # 施設を退出してメインメニューに戻る
        return self.exit()
    
    def _handle_escape_key(self) -> bool:
        """ESCキー処理（WindowSystem対応）"""
        try:
            # 施設固有のESC処理があれば実行
            if hasattr(self, '_on_escape_key'):
                if self._on_escape_key():
                    return True
            
            # WindowSystemでは各Windowが独自にESCキー処理を管理
            # デフォルトは施設を退出
            return self.exit()
            
        except Exception as e:
            logger.error(f"ESCキー処理エラー: {e}")
            return False
    
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
        
        # WindowManager統合
        self.window_manager = WindowManager.get_instance()
        
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
        
        # 前提条件チェック
        if not self._validate_exit_conditions():
            return False
        
        facility = self.facilities[self.current_facility]
        logger.info(f"施設のexit()を呼び出し: {self.current_facility}")
        
        if facility.exit():
            return self._handle_successful_exit()
        else:
            logger.error(f"施設のexit()がFalseを返しました: {self.current_facility}")
            return False
    
    def _validate_exit_conditions(self) -> bool:
        """退出条件をバリデーション"""
        if not self.current_facility:
            logger.warning("current_facilityが設定されていません")
            return False
        
        if self.current_facility not in self.facilities:
            logger.error(f"施設が見つかりません: {self.current_facility}")
            return False
        
        return True
    
    def _handle_successful_exit(self) -> bool:
        """成功した退出処理"""
        logger.info(f"施設退出成功: {self.current_facility}")
        self.current_facility = None
        
        # 施設退場コールバックを呼び出し
        if self.on_facility_exit_callback:
            logger.info("退場コールバックを実行")
            self.on_facility_exit_callback()
        else:
            logger.warning("退場コールバックが設定されていません")
        
        return True
    
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
    
    def set_window_manager(self, window_manager: WindowManager):
        """WindowManagerを設定"""
        self.window_manager = window_manager
        
        # 全施設にもWindowManagerを設定
        for facility in self.facilities.values():
            facility.window_manager = window_manager
        
        logger.info("FacilityManagerにWindowManagerを設定しました")
    
    def _cleanup_all_windows(self):
        """全施設のWindowSystemクリーンアップ"""
        try:
            for facility in self.facilities.values():
                if hasattr(facility, '_cleanup_ui_windows'):
                    facility._cleanup_ui_windows()
            
            logger.info("全施設のWindowSystemをクリーンアップしました")
            
        except Exception as e:
            logger.error(f"WindowSystemクリーンアップエラー: {e}")
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        # WindowSystemクリーンアップ
        self._cleanup_all_windows()
        
        # 施設クリーンアップ
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