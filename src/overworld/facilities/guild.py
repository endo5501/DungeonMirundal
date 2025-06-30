"""冒険者ギルド"""

from typing import Dict, List, Optional, Any, Callable
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.character import Character
from src.character.party import Party, PartyPosition
from src.ui.windows.character_creation_wizard import CharacterCreationWizard
from src.ui.window_system import MenuWindow, WindowManager
from src.ui.window_system.facility_menu_window import FacilityMenuWindow
from src.core.config_manager import config_manager
from src.utils.logger import logger

# 冒険者ギルド定数
FORMATION_DIALOG_WIDTH = 700
FORMATION_DIALOG_HEIGHT = 450
CHARACTER_LIST_DIALOG_HEIGHT = 500
CHARACTER_INFO_DIALOG_WIDTH = 500
CHARACTER_INFO_DIALOG_HEIGHT = 400


class PartyFormationWindow(MenuWindow):
    """パーティ編成専用ウィンドウ"""
    
    def __init__(self, window_id: str, menu_config: Dict[str, Any], 
                 action_handler: Optional[Callable] = None, **kwargs):
        super().__init__(window_id, menu_config, **kwargs)
        self.action_handler = action_handler
    
    def _execute_button_action(self, button) -> None:
        """ボタンアクションを実行（オーバーライド）"""
        logger.debug(f"PartyFormationWindow: ボタンアクション実行: {button.action} (id={button.id})")
        if self.action_handler:
            message_data = {
                'action': button.action,
                'button_id': button.id
            }
            logger.debug(f"PartyFormationWindow: action_handler呼び出し: {message_data}")
            self.action_handler('menu_action', message_data)
        else:
            # デフォルトの処理
            logger.debug("PartyFormationWindow: デフォルト処理実行")
            super()._execute_button_action(button)


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
    
    def _create_guild_menu_config(self):
        """Guild用のFacilityMenuWindow設定を作成"""
        menu_items = [
            {
                'id': 'character_creation',
                'label': config_manager.get_text("guild.menu.character_creation"),
                'type': 'action',
                'enabled': True
            },
            {
                'id': 'party_formation',
                'label': config_manager.get_text("guild.menu.party_formation"),
                'type': 'action',
                'enabled': self.current_party is not None
            },
            {
                'id': 'character_list',
                'label': config_manager.get_text("guild.menu.character_list"),
                'type': 'action',
                'enabled': len(self.created_characters) > 0 or (self.current_party and len(self.current_party.characters) > 0)
            },
            {
                'id': 'class_change',
                'label': config_manager.get_text("guild.menu.class_change"),
                'type': 'action',
                'enabled': self.current_party is not None and len(self.current_party.characters) > 0
            },
            {
                'id': 'exit',
                'label': config_manager.get_text("menu.exit"),
                'type': 'exit',
                'enabled': True
            }
        ]
        
        return {
            'facility_type': FacilityType.GUILD.value,
            'facility_name': config_manager.get_text("facility.guild"),
            'menu_items': menu_items,
            'party': self.current_party,
            'show_party_info': True,
            'show_gold': True
        }
    
    def _create_facility_menu_config(self) -> Dict[str, Any]:
        """施設メニュー設定を作成（WindowManager用）- BaseFacilityをオーバーライド"""
        # _create_guild_menu_config()の結果を返す
        return self._create_guild_menu_config()
    
    def show_menu(self):
        """Guildメインメニューを表示（FacilityMenuWindow使用）"""
        window_manager = WindowManager.get_instance()
        
        # メニュー設定を作成
        menu_config = self._create_guild_menu_config()
        
        # WindowManagerの正しい使用パターン: create_window -> show_window
        guild_window = window_manager.create_window(
            FacilityMenuWindow,
            'guild_main_menu',
            facility_config=menu_config
        )
        
        # メッセージハンドラーを設定
        guild_window.message_handler = self.handle_facility_message
        
        # ウィンドウを表示
        window_manager.show_window(guild_window, push_to_stack=True)
        
        logger.info(config_manager.get_text("app_log.entered_guild"))
    
    def handle_facility_message(self, message_type: str, data: dict) -> bool:
        """FacilityMenuWindowからのメッセージを処理"""
        if message_type == 'menu_item_selected':
            item_id = data.get('item_id')
            
            if item_id == 'character_creation':
                return self._show_character_creation()
            elif item_id == 'party_formation':
                return self._show_party_formation()
            elif item_id == 'character_list':
                return self._show_character_list()
            elif item_id == 'class_change':
                return self._show_class_change()
                
        elif message_type == 'facility_exit_requested':
            return self._handle_exit()
            
        return False
    
    def _handle_exit(self) -> bool:
        """施設退場処理"""
        logger.info(config_manager.get_text("app_log.left_guild"))
        
        # WindowManagerでウィンドウを閉じる
        window_manager = WindowManager.get_instance()
        if window_manager.get_active_window():
            window_manager.go_back()
            
        return True
    
    def _on_enter(self):
        """ギルド入場時の処理"""
        logger.info(config_manager.get_text("app_log.entered_guild"))
    
    def _on_exit(self):
        """ギルド退場時の処理"""
        logger.info(config_manager.get_text("app_log.left_guild"))
    
    
    def _show_character_creation(self):
        """キャラクター作成ウィザードを表示"""
        # 現在のウィンドウを隠す（WindowManagerを使用）
        window_manager = WindowManager.get_instance()
        current_window = window_manager.get_active_window()
        if current_window:
            window_manager.hide_window(current_window)
        
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
        # 新しいメニューシステムを使用
        self.show_success_dialog(
            config_manager.get_text("common.info"),
            config_manager.get_text("guild.messages.character_created").format(name=character.name)
        )
        
        logger.info(config_manager.get_text("guild.messages.new_character_created").format(name=character.name))
    
    def _on_character_creation_cancelled(self):
        """キャラクター作成キャンセル時のコールバック"""
        # メインメニューを再表示（WindowManagerを使用）
        window_manager = WindowManager.get_instance()
        if window_manager.window_stack.size() > 0:
            window_manager.show_previous_window()
        else:
            # スタックが空の場合は新しくメインメニューを表示
            self.show_menu()
        
        logger.info(config_manager.get_text("guild.messages.character_creation_cancelled"))
    
    def _create_party_formation_menu_config(self):
        """パーティ編成用のMenuWindow設定を動的に作成"""
        buttons = []
        
        # 現在のパーティ状況を表示
        buttons.append({
            'id': 'check_current',
            'text': config_manager.get_text("guild.party_formation.check_current"),
            'action': 'show_current_formation'
        })
        
        # キャラクター追加（パーティが満員でない場合）
        if len(self.current_party.characters) < 6:
            buttons.append({
                'id': 'add_character',
                'text': config_manager.get_text("guild.party_formation.add_character"),
                'action': 'show_add_character_menu'
            })
        
        # キャラクター削除（パーティにキャラクターがいる場合）
        if len(self.current_party.characters) > 0:
            buttons.append({
                'id': 'remove_character',
                'text': config_manager.get_text("guild.party_formation.remove_character"),
                'action': 'show_remove_character_menu'
            })
        
        # 位置変更（パーティに2人以上いる場合）
        if len(self.current_party.characters) > 1:
            buttons.append({
                'id': 'change_position',
                'text': config_manager.get_text("guild.party_formation.change_position"),
                'action': 'show_position_menu'
            })
        
        return {
            'title': config_manager.get_text("guild.party_formation.title"),
            'buttons': buttons
        }

    def _show_party_formation(self):
        """パーティ編成画面を表示"""
        if not self.current_party:
            self._show_error_message(config_manager.get_text("guild.messages.no_party_set"))
            return
        
        # 現在のメニューを非表示にする
        if self.menu_stack_manager:
            current_entry = self.menu_stack_manager.peek_current_menu()
            if current_entry:
                self._hide_menu_safe(current_entry.menu.menu_id)
        
        # WindowManagerを取得し、pygame統合を初期化
        from src.ui.window_system import WindowManager
        import pygame
        window_manager = WindowManager.get_instance()
        
        # pygame統合が初期化されていない場合は初期化
        if not window_manager.screen:
            screen = pygame.display.get_surface()
            clock = pygame.time.Clock()
            window_manager.initialize_pygame(screen, clock)
        
        # 動的なメニュー設定を作成
        menu_config = self._create_party_formation_menu_config()
        
        # PartyFormationWindowを作成
        formation_window = PartyFormationWindow(
            'party_formation',
            menu_config,
            action_handler=self._handle_party_formation_action
        )
        
        # ウィンドウを作成
        formation_window.create()
        logger.debug(f"PartyFormationWindow作成完了: ボタン数={len(formation_window.buttons)}")
        for i, btn in enumerate(formation_window.buttons):
            logger.debug(f"ボタン{i}: {btn.text} (action={btn.action}, ui_element={btn.ui_element})")
        
        # WindowManagerに登録して表示
        window_manager.window_registry[formation_window.window_id] = formation_window
        window_manager.show_window(formation_window, push_to_stack=True)
        logger.debug(f"PartyFormationWindow表示完了: アクティブウィンドウ={window_manager.get_active_window()}")
    
    def _handle_party_formation_action(self, message_type: str, data: dict):
        """パーティ編成メニューのアクション処理"""
        logger.debug(f"AdventurersGuild: アクション処理開始: {message_type}, {data}")
        action = data.get('action')
        
        if action == 'show_current_formation':
            logger.debug("AdventurersGuild: 現在の編成を表示")
            self._show_current_formation()
        elif action == 'show_add_character_menu':
            logger.debug("AdventurersGuild: キャラクター追加メニューを表示")
            self._show_add_character_menu()
        elif action == 'show_remove_character_menu':
            logger.debug("AdventurersGuild: キャラクター削除メニューを表示")
            self._show_remove_character_menu()
        elif action == 'show_position_menu':
            logger.debug("AdventurersGuild: 位置変更メニューを表示")
            self._show_position_menu()
        elif action == 'window_back':
            # 戻るボタンが押された場合 - WindowManagerの階層を使って戻る
            logger.debug("AdventurersGuild: パーティ編成戻るボタン処理開始")
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            
            # WindowManagerのgo_back機能を使用
            if window_manager.go_back():
                logger.debug("AdventurersGuild: WindowManagerでgo_backが成功しました")
            else:
                # WindowManagerが空になったら、メインメニューを表示
                logger.debug("AdventurersGuild: WindowManagerが空のため、元のメニューシステムに戻ります")
                if self.menu_stack_manager:
                    current_entry = self.menu_stack_manager.peek_current_menu()
                    if current_entry:
                        self._show_menu_safe(current_entry.menu, modal=True)
        else:
            logger.warning(f"AdventurersGuild: 未知のアクション: {action}")
    
    def _handle_formation_display_action(self, message_type: str, data: dict):
        """編成表示ウィンドウのアクション処理"""
        logger.debug(f"AdventurersGuild: 編成表示アクション処理: {message_type}, {data}")
        action = data.get('action')
        
        if action in ['back_to_formation_menu', 'window_back']:
            # WindowManagerのgo_back機能を使用
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            
            if window_manager.go_back():
                logger.debug("AdventurersGuild: 編成表示からWindowManagerでgo_backが成功しました")
            else:
                # パーティ編成ウィンドウを新規作成して表示
                self._show_party_formation()
        else:
            logger.warning(f"AdventurersGuild: 未知の編成表示アクション: {action}")
    
    def _handle_add_character_action(self, message_type: str, data: dict):
        """キャラクター追加ウィンドウのアクション処理"""
        logger.debug(f"AdventurersGuild: キャラクター追加アクション処理: {message_type}, {data}")
        action = data.get('action')
        
        if action and action.startswith('add_character:'):
            # キャラクターIDを取得
            character_id = action.split(':', 1)[1]
            
            # キャラクターオブジェクトを取得
            character = None
            for char in self.created_characters:
                if char.character_id == character_id:
                    character = char
                    break
            
            if character:
                # キャラクターをパーティに追加
                success = self.current_party.add_character(character)
                
                # キャラクター追加ウィンドウを閉じる
                from src.ui.window_system import WindowManager
                window_manager = WindowManager.get_instance()
                
                if 'add_character' in window_manager.window_registry:
                    add_window = window_manager.window_registry['add_character']
                    window_manager.close_window(add_window)
                
                if success:
                    # 成功メッセージを表示してパーティ編成メニューに戻る
                    self._show_success_window(f"{character.name}をパーティに追加しました")
                else:
                    # エラーメッセージを表示
                    self._show_error_window("キャラクターの追加に失敗しました")
            else:
                logger.error(f"キャラクターが見つかりません: {character_id}")
                self._show_error_window("キャラクターが見つかりません")
                
        elif action == 'window_back':
            # 戻るボタンが押された場合
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            
            if window_manager.go_back():
                logger.debug("AdventurersGuild: キャラクター追加からWindowManagerでgo_backが成功しました")
            else:
                # パーティ編成ウィンドウを新規作成して表示
                self._show_party_formation()
        else:
            logger.warning(f"AdventurersGuild: 未知のキャラクター追加アクション: {action}")
    
    def _handle_remove_character_action(self, message_type: str, data: dict):
        """キャラクター削除ウィンドウのアクション処理"""
        logger.debug(f"AdventurersGuild: キャラクター削除アクション処理: {message_type}, {data}")
        action = data.get('action')
        
        if action and action.startswith('remove_character:'):
            # キャラクターIDを取得
            character_id = action.split(':', 1)[1]
            
            # キャラクターオブジェクトを取得
            character = None
            for char in self.current_party.characters.values():
                if char.character_id == character_id:
                    character = char
                    break
            
            if character:
                # 確認ダイアログを表示
                self._show_confirmation_window(
                    f"{character.name}をパーティから削除しますか？",
                    lambda: self._confirm_remove_character(character)
                )
            else:
                logger.error(f"キャラクターが見つかりません: {character_id}")
                self._show_error_window("キャラクターが見つかりません")
                
        elif action == 'window_back':
            # 戻るボタンが押された場合
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            
            if window_manager.go_back():
                logger.debug("AdventurersGuild: キャラクター削除からWindowManagerでgo_backが成功しました")
            else:
                # パーティ編成ウィンドウを新規作成して表示
                self._show_party_formation()
        else:
            logger.warning(f"AdventurersGuild: 未知のキャラクター削除アクション: {action}")
    
    def _show_error_window(self, message: str):
        """エラーメッセージウィンドウを表示"""
        menu_config = {
            'title': "エラー",
            'buttons': [
                {
                    'id': 'ok_error',
                    'text': "OK",
                    'action': 'close_error'
                }
            ]
        }
        
        from src.ui.window_system import WindowManager
        window_manager = WindowManager.get_instance()
        
        error_window = PartyFormationWindow(
            'error_dialog',
            menu_config,
            action_handler=self._handle_error_action
        )
        
        error_window.create()
        
        # エラーメッセージをテキストラベルとして追加
        if hasattr(error_window, 'ui_manager') and error_window.ui_manager:
            import pygame_gui
            import pygame
            text_rect = pygame.Rect(20, 60, error_window.rect.width - 40, 40)
            error_window.message_label = pygame_gui.elements.UILabel(
                relative_rect=text_rect,
                text=message,
                manager=error_window.ui_manager,
                container=error_window.panel
            )
        
        window_manager.window_registry[error_window.window_id] = error_window
        window_manager.show_window(error_window, push_to_stack=True)
    
    def _show_success_window(self, message: str):
        """成功メッセージウィンドウを表示"""
        menu_config = {
            'title': "完了",
            'buttons': [
                {
                    'id': 'ok_success',
                    'text': "OK",
                    'action': 'close_success'
                }
            ]
        }
        
        from src.ui.window_system import WindowManager
        window_manager = WindowManager.get_instance()
        
        success_window = PartyFormationWindow(
            'success_dialog',
            menu_config,
            action_handler=self._handle_success_action
        )
        
        success_window.create()
        
        # 成功メッセージをテキストラベルとして追加
        if hasattr(success_window, 'ui_manager') and success_window.ui_manager:
            import pygame_gui
            import pygame
            text_rect = pygame.Rect(20, 60, success_window.rect.width - 40, 40)
            success_window.message_label = pygame_gui.elements.UILabel(
                relative_rect=text_rect,
                text=message,
                manager=success_window.ui_manager,
                container=success_window.panel
            )
        
        window_manager.window_registry[success_window.window_id] = success_window
        window_manager.show_window(success_window, push_to_stack=True)
    
    def _handle_error_action(self, message_type: str, data: dict):
        """エラーダイアログのアクション処理"""
        action = data.get('action')
        
        if action in ['close_error', 'window_back']:
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            
            if window_manager.go_back():
                logger.debug("AdventurersGuild: エラーダイアログからWindowManagerでgo_backが成功しました")
            else:
                # パーティ編成ウィンドウを新規作成して表示
                self._show_party_formation()
    
    def _handle_success_action(self, message_type: str, data: dict):
        """成功ダイアログのアクション処理"""
        action = data.get('action')
        
        if action in ['close_success', 'window_back']:
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            
            if window_manager.go_back():
                logger.debug("AdventurersGuild: 成功ダイアログからWindowManagerでgo_backが成功しました")
            else:
                # パーティ編成メニューを更新して再表示（キャラクターが追加されたため）
                self._show_party_formation()
    
    def _show_confirmation_window(self, message: str, confirm_callback):
        """確認ダイアログウィンドウを表示"""
        menu_config = {
            'title': "確認",
            'buttons': [
                {
                    'id': 'confirm_yes',
                    'text': "はい",
                    'action': 'confirm_yes'
                },
                {
                    'id': 'confirm_no',
                    'text': "いいえ",
                    'action': 'confirm_no'
                }
            ]
        }
        
        from src.ui.window_system import WindowManager
        window_manager = WindowManager.get_instance()
        
        confirmation_window = PartyFormationWindow(
            'confirmation_dialog',
            menu_config,
            action_handler=self._handle_confirmation_action
        )
        
        # コールバック関数を保存
        confirmation_window.confirm_callback = confirm_callback
        confirmation_window.create()
        
        # 確認メッセージをテキストラベルとして追加
        if hasattr(confirmation_window, 'ui_manager') and confirmation_window.ui_manager:
            import pygame_gui
            import pygame
            text_rect = pygame.Rect(20, 60, confirmation_window.rect.width - 40, 60)
            confirmation_window.message_label = pygame_gui.elements.UILabel(
                relative_rect=text_rect,
                text=message,
                manager=confirmation_window.ui_manager,
                container=confirmation_window.panel
            )
        
        window_manager.window_registry[confirmation_window.window_id] = confirmation_window
        window_manager.show_window(confirmation_window, push_to_stack=True)
    
    def _handle_confirmation_action(self, message_type: str, data: dict):
        """確認ダイアログのアクション処理"""
        action = data.get('action')
        
        from src.ui.window_system import WindowManager
        window_manager = WindowManager.get_instance()
        
        if 'confirmation_dialog' in window_manager.window_registry:
            confirmation_window = window_manager.window_registry['confirmation_dialog']
            
            if action == 'confirm_yes' and hasattr(confirmation_window, 'confirm_callback'):
                # 「はい」が押された場合、コールバックを実行
                confirmation_window.confirm_callback()
            
            # 確認ダイアログを閉じる
            window_manager.close_window(confirmation_window)
            
            if action == 'confirm_no' or action == 'window_back':
                # 「いいえ」または戻るボタンの場合、WindowManagerのgo_backを使用
                if not window_manager.go_back():
                    # go_backが失敗した場合はパーティ編成ウィンドウを表示
                    self._show_party_formation()
                    logger.debug("AdventurersGuild: 確認ダイアログからWindowManagerでgo_backが失敗、パーティ編成を表示")
    
    def _confirm_remove_character(self, character):
        """キャラクター削除を実行"""
        success = self.current_party.remove_character(character.character_id)
        
        if success:
            # 削除されたキャラクターを作成済みリストに戻す
            if character not in self.created_characters:
                self.created_characters.append(character)
            
            # 成功メッセージを表示
            self._show_success_window(f"{character.name}をパーティから削除しました")
        else:
            # エラーメッセージを表示
            self._show_error_window("キャラクターの削除に失敗しました")
    
    def _handle_position_menu_action(self, message_type: str, data: dict):
        """位置変更メニューのアクション処理"""
        logger.debug(f"AdventurersGuild: 位置変更アクション処理: {message_type}, {data}")
        action = data.get('action')
        
        if action and action.startswith('select_character_for_position:'):
            # キャラクターIDを取得
            character_id = action.split(':', 1)[1]
            
            # キャラクターオブジェクトを取得
            character = None
            for char in self.current_party.characters.values():
                if char.character_id == character_id:
                    character = char
                    break
            
            if character:
                # 新しい位置選択メニューを表示
                self._show_new_position_menu_window(character)
            else:
                logger.error(f"キャラクターが見つかりません: {character_id}")
                self._show_error_window("キャラクターが見つかりません")
                
        elif action == 'window_back':
            # 戻るボタンが押された場合
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            
            if window_manager.go_back():
                logger.debug("AdventurersGuild: 位置変更からWindowManagerでgo_backが成功しました")
            else:
                # パーティ編成ウィンドウを新規作成して表示
                self._show_party_formation()
        else:
            logger.warning(f"AdventurersGuild: 未知の位置変更アクション: {action}")
    
    def _show_new_position_menu_window(self, character):
        """新しい位置選択メニューをWindowで表示"""
        from src.character.party import PartyPosition
        
        # 利用可能な位置を取得
        available_positions = []
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
                available_positions.append((position, pos_name))
        
        if not available_positions:
            self._show_error_window("移動可能な位置がありません")
            return
        
        # 現在の位置メニューウィンドウを閉じる
        from src.ui.window_system import WindowManager
        window_manager = WindowManager.get_instance()
        
        if 'position_menu' in window_manager.window_registry:
            position_window = window_manager.window_registry['position_menu']
            window_manager.close_window(position_window)
        
        # 新しい位置選択用のメニュー設定を作成
        buttons = []
        for position, pos_name in available_positions:
            buttons.append({
                'id': f'move_to_{position.value}',
                'text': pos_name,
                'action': f'move_character:{character.character_id}:{position.value}'
            })
        
        menu_config = {
            'title': f"{character.name}の新しい位置",
            'buttons': buttons
        }
        
        # 新しい位置選択ウィンドウを作成
        new_position_window = PartyFormationWindow(
            'new_position_menu',
            menu_config,
            action_handler=self._handle_new_position_action
        )
        
        new_position_window.create()
        
        # WindowManagerに登録して表示
        window_manager.window_registry[new_position_window.window_id] = new_position_window
        window_manager.show_window(new_position_window, push_to_stack=True)
        logger.debug(f"NewPositionWindow表示完了")
    
    def _handle_new_position_action(self, message_type: str, data: dict):
        """新しい位置選択のアクション処理"""
        logger.debug(f"AdventurersGuild: 新しい位置アクション処理: {message_type}, {data}")
        action = data.get('action')
        
        if action and action.startswith('move_character:'):
            # アクションからキャラクターIDと位置を取得
            parts = action.split(':', 2)
            if len(parts) == 3:
                character_id = parts[1]
                position_value = parts[2]
                
                # キャラクターオブジェクトを取得
                character = None
                for char in self.current_party.characters.values():
                    if char.character_id == character_id:
                        character = char
                        break
                
                # 位置を取得
                from src.character.party import PartyPosition
                position = None
                for pos in PartyPosition:
                    if pos.value == position_value:
                        position = pos
                        break
                
                if character and position:
                    # 位置移動を実行
                    success = self.current_party.move_character(character.character_id, position)
                    
                    # 新しい位置選択ウィンドウを閉じる
                    from src.ui.window_system import WindowManager
                    window_manager = WindowManager.get_instance()
                    
                    if 'new_position_menu' in window_manager.window_registry:
                        new_pos_window = window_manager.window_registry['new_position_menu']
                        window_manager.close_window(new_pos_window)
                    
                    if success:
                        # 成功メッセージを表示
                        self._show_success_window(f"{character.name}の位置を変更しました")
                    else:
                        # エラーメッセージを表示
                        self._show_error_window("位置の変更に失敗しました")
                else:
                    logger.error(f"キャラクターまたは位置が見つかりません: {character_id}, {position_value}")
                    self._show_error_window("位置の変更に失敗しました")
            else:
                logger.error(f"不正なアクション形式: {action}")
                self._show_error_window("位置の変更に失敗しました")
                
        elif action == 'window_back':
            # 戻るボタンが押された場合
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            
            if window_manager.go_back():
                logger.debug("AdventurersGuild: 新しい位置選択からWindowManagerでgo_backが成功しました")
            else:
                # 位置変更メニューを表示
                self._show_position_menu()
        else:
            logger.warning(f"AdventurersGuild: 未知の新しい位置アクション: {action}")
    
    def _show_current_formation(self):
        """現在の編成を表示"""
        if not self.current_party:
            return
        
        # 現在のパーティ編成ウィンドウを完全に閉じる
        from src.ui.window_system import WindowManager
        window_manager = WindowManager.get_instance()
        
        # 既存のformation_displayがあれば閉じる
        if 'formation_display' in window_manager.window_registry:
            old_display = window_manager.window_registry['formation_display']
            window_manager.close_window(old_display)
        
        # 現在のformation_windowを完全に閉じる
        if 'party_formation' in window_manager.window_registry:
            formation_window = window_manager.window_registry['party_formation']
            window_manager.close_window(formation_window)
        
        # 編成表示用のメニュー設定を作成（戻るボタンは自動追加されるので手動では追加しない）
        formation_text = self._format_party_formation()
        menu_config = {
            'title': config_manager.get_text("guild.party_formation.current_formation_title"),
            'buttons': []  # 戻るボタンはBackButtonManagerが自動追加する
        }
        
        # 編成表示ウィンドウを作成
        formation_display_window = PartyFormationWindow(
            'formation_display',
            menu_config,
            action_handler=self._handle_formation_display_action
        )
        
        # ウィンドウ作成後に編成情報を追加
        formation_display_window.create()
        
        # 編成情報をテキストラベルとして追加
        self._add_formation_text_to_window(formation_display_window, formation_text)
        
        # WindowManagerに登録して表示
        window_manager.window_registry[formation_display_window.window_id] = formation_display_window
        window_manager.show_window(formation_display_window, push_to_stack=True)
        logger.debug(f"FormationDisplayWindow表示完了")
    
    def _add_formation_text_to_window(self, window, formation_text):
        """編成情報をウィンドウに追加"""
        if hasattr(window, 'ui_manager') and window.ui_manager and hasattr(window, 'panel'):
            import pygame_gui
            import pygame
            
            # ウィンドウのサイズを取得
            window_width = window.rect.width
            window_height = window.rect.height
            logger.debug(f"ウィンドウサイズ: {window_width}x{window_height}")
            
            # より安全なテキスト領域のサイズ計算
            margin = 20
            title_height = 40  # タイトル領域
            button_height = 40  # 戻るボタン領域
            text_top = title_height + 10  # タイトルの下に少しマージン
            text_width = max(200, window_width - (margin * 2))  # 最低200px確保
            text_height = max(100, window_height - text_top - button_height - 20)  # 最低100px確保
            
            logger.debug(f"計算されたテキスト領域: {text_width}x{text_height} (top: {text_top})")
            
            # テキスト領域を作成
            text_rect = pygame.Rect(margin, text_top, text_width, text_height)
            try:
                window.formation_label = pygame_gui.elements.UILabel(
                    relative_rect=text_rect,
                    text=formation_text,
                    manager=window.ui_manager,
                    container=window.panel
                )
                logger.debug(f"編成テキストラベルを追加しました: {text_width}x{text_height}")
            except Exception as e:
                logger.error(f"テキストラベル作成エラー: {e}")
                # フォールバック: タイトルに情報を追加
                if hasattr(window, 'title_label') and window.title_label:
                    window.title_label.set_text(f"{window.title_label.text}\n\n{formation_text}")
    
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
        # 利用可能なキャラクター（パーティに参加していない）
        available_chars = [
            char for char in self.created_characters 
            if char.character_id not in self.current_party.characters
        ]
        
        if not available_chars:
            # エラーメッセージをMenuWindowで表示
            self._show_error_window("追加可能なキャラクターがいません")
            return
        
        # 現在のパーティ編成ウィンドウを完全に閉じる
        from src.ui.window_system import WindowManager
        window_manager = WindowManager.get_instance()
        
        # 既存のadd_characterがあれば閉じる
        if 'add_character' in window_manager.window_registry:
            old_add = window_manager.window_registry['add_character']
            window_manager.close_window(old_add)
        
        if 'party_formation' in window_manager.window_registry:
            formation_window = window_manager.window_registry['party_formation']
            window_manager.close_window(formation_window)
        
        # キャラクター追加用のメニュー設定を作成
        buttons = []
        for char in available_chars:
            char_info = f"{char.name} Lv.{char.experience.level} ({char.get_race_name()}/{char.get_class_name()})"
            buttons.append({
                'id': f'add_char_{char.character_id}',
                'text': char_info,
                'action': f'add_character:{char.character_id}'
            })
        
        menu_config = {
            'title': config_manager.get_text("guild.party_formation.character_add_title"),
            'buttons': buttons
        }
        
        # キャラクター追加ウィンドウを作成
        add_char_window = PartyFormationWindow(
            'add_character',
            menu_config,
            action_handler=self._handle_add_character_action
        )
        
        add_char_window.create()
        
        # WindowManagerに登録して表示
        window_manager.window_registry[add_char_window.window_id] = add_char_window
        window_manager.show_window(add_char_window, push_to_stack=True)
        logger.debug(f"AddCharacterWindow表示完了")
    
    def _add_character_to_party(self, character: Character):
        """パーティにキャラクターを追加"""
        if not self.current_party:
            logger.warning(config_manager.get_text("guild.messages.party_not_set_warning"))
            self._show_error_message(config_manager.get_text("errors.no_party_set"))
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
        party_chars = list(self.current_party.characters.values())
        
        if not party_chars:
            # エラーメッセージをMenuWindowで表示
            self._show_error_window("削除可能なキャラクターがいません")
            return
        
        # 現在のパーティ編成ウィンドウを完全に閉じる
        from src.ui.window_system import WindowManager
        window_manager = WindowManager.get_instance()
        
        # 既存のremove_characterがあれば閉じる
        if 'remove_character' in window_manager.window_registry:
            old_remove = window_manager.window_registry['remove_character']
            window_manager.close_window(old_remove)
        
        if 'party_formation' in window_manager.window_registry:
            formation_window = window_manager.window_registry['party_formation']
            window_manager.close_window(formation_window)
        
        # キャラクター削除用のメニュー設定を作成
        buttons = []
        for char in party_chars:
            char_info = f"{char.name} Lv.{char.experience.level} ({char.get_class_name()})"
            buttons.append({
                'id': f'remove_char_{char.character_id}',
                'text': char_info,
                'action': f'remove_character:{char.character_id}'
            })
        
        menu_config = {
            'title': "キャラクター削除",
            'buttons': buttons
        }
        
        # キャラクター削除ウィンドウを作成
        remove_char_window = PartyFormationWindow(
            'remove_character',
            menu_config,
            action_handler=self._handle_remove_character_action
        )
        
        remove_char_window.create()
        
        # WindowManagerに登録して表示
        window_manager.window_registry[remove_char_window.window_id] = remove_char_window
        window_manager.show_window(remove_char_window, push_to_stack=True)
        logger.debug(f"RemoveCharacterWindow表示完了")
    
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
        party_chars = list(self.current_party.characters.values())
        
        if not party_chars:
            self._show_error_window("位置変更可能なキャラクターがいません")
            return
        
        # 現在のパーティ編成ウィンドウを完全に閉じる
        from src.ui.window_system import WindowManager
        window_manager = WindowManager.get_instance()
        
        # 既存のposition_menuがあれば閉じる
        if 'position_menu' in window_manager.window_registry:
            old_position = window_manager.window_registry['position_menu']
            window_manager.close_window(old_position)
        
        if 'party_formation' in window_manager.window_registry:
            formation_window = window_manager.window_registry['party_formation']
            window_manager.close_window(formation_window)
        
        # 位置変更用のメニュー設定を作成
        buttons = []
        for char in party_chars:
            current_pos = self.current_party.formation.get_character_position(char.character_id)
            pos_text = current_pos.value if current_pos else "不明"
            char_info = f"{char.name} ({pos_text})"
            buttons.append({
                'id': f'pos_char_{char.character_id}',
                'text': char_info,
                'action': f'select_character_for_position:{char.character_id}'
            })
        
        menu_config = {
            'title': config_manager.get_text("guild.party_formation.position_change_title"),
            'buttons': buttons
        }
        
        # 位置変更ウィンドウを作成
        position_window = PartyFormationWindow(
            'position_menu',
            menu_config,
            action_handler=self._handle_position_menu_action
        )
        
        position_window.create()
        
        # WindowManagerに登録して表示
        window_manager.window_registry[position_window.window_id] = position_window
        window_manager.show_window(position_window, push_to_stack=True)
        logger.debug(f"PositionMenuWindow表示完了")
    
    def _show_new_position_menu(self, character: Character):
        """新しい位置選択メニュー（WindowSystem版は既に実装済み）"""
        # この関数は既にWindowSystem版（_show_new_position_menu_window）で実装済み
        # 新システムではPartyFormationWindow内で処理されるため、この関数は使用されない
        logger.debug(f"_show_new_position_menu called for {character.name}, redirecting to new system")
        self._show_new_position_menu_window(character)
    
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
            self._show_error_window("パーティが設定されていません")
            return
        
        # パーティメンバーが誰もいない場合
        if not self.current_party.characters:
            self._show_error_window("パーティにメンバーがいません")
            return
        
        # レベル10以上のキャラクターを取得
        eligible_chars = []
        for character in self.current_party.characters.values():
            if character.experience.level >= 10:
                eligible_chars.append(character)
        
        # 該当者がいない場合
        if not eligible_chars:
            self._show_error_window(
                "クラスチェンジ可能なキャラクターがいません。\n\n"
                "条件:\n"
                "・レベル10以上\n"
                "・転職先クラスの要求能力値を満たす"
            )
            return
        
        # クラスチェンジ用のメニュー設定を作成
        buttons = []
        for character in eligible_chars:
            char_info = f"{character.name} (Lv.{character.experience.level} {character.get_class_name()})"
            buttons.append({
                'id': f'class_change_{character.character_id}',
                'text': char_info,
                'action': f'show_class_options:{character.character_id}'
            })
        
        menu_config = {
            'title': "クラスチェンジ",
            'buttons': buttons
        }
        
        # WindowManagerを使用してクラスチェンジウィンドウを表示
        window_manager = WindowManager.get_instance()
        
        class_change_window = PartyFormationWindow(
            'class_change_menu',
            menu_config,
            action_handler=self._handle_class_change_action
        )
        
        class_change_window.create()
        window_manager.window_registry[class_change_window.window_id] = class_change_window
        window_manager.show_window(class_change_window, push_to_stack=True)
    
    def _handle_class_change_action(self, message_type: str, data: dict):
        """クラスチェンジメニューのアクション処理"""
        logger.debug(f"AdventurersGuild: クラスチェンジアクション処理: {message_type}, {data}")
        action = data.get('action')
        
        if action and action.startswith('show_class_options:'):
            # キャラクターIDを取得
            character_id = action.split(':', 1)[1]
            
            # キャラクターオブジェクトを取得
            character = None
            for char in self.current_party.characters.values():
                if char.character_id == character_id:
                    character = char
                    break
            
            if character:
                self._show_class_change_options_window(character)
            else:
                logger.error(f"キャラクターが見つかりません: {character_id}")
                self._show_error_window("キャラクターが見つかりません")
                
        elif action == 'window_back':
            # 戻るボタンが押された場合
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            
            if window_manager.go_back():
                logger.debug("AdventurersGuild: クラスチェンジからWindowManagerでgo_backが成功しました")
            else:
                # メインメニューを表示
                self.show_menu()
        else:
            logger.warning(f"AdventurersGuild: 未知のクラスチェンジアクション: {action}")
    
    def _show_class_change_options_window(self, character: Character):
        """クラスチェンジ先の選択画面を表示（新WindowSystem版）"""
        from src.character.class_change import ClassChangeValidator, ClassChangeManager
        
        # 転職可能なクラスを取得
        available_classes = ClassChangeValidator.get_available_classes(character)
        
        if not available_classes:
            self._show_error_window(
                f"{character.name}が転職可能なクラスがありません。\n\n"
                "能力値が要求を満たしていない可能性があります。"
            )
            return
        
        # クラス選択用のメニュー設定を作成
        buttons = []
        for class_name in available_classes:
            class_info = ClassChangeManager.get_class_change_info(character, class_name)
            display_name = f"{class_info['target_name']} (HP×{class_info['hp_multiplier']:.1f} MP×{class_info['mp_multiplier']:.1f})"
            buttons.append({
                'id': f'select_class_{class_name}',
                'text': display_name,
                'action': f'confirm_class_change:{character.character_id}:{class_name}'
            })
        
        menu_config = {
            'title': f"{character.name}の転職先",
            'buttons': buttons
        }
        
        # WindowManagerを使用してクラス選択ウィンドウを表示
        window_manager = WindowManager.get_instance()
        
        class_select_window = PartyFormationWindow(
            'class_select_menu',
            menu_config,
            action_handler=self._handle_class_select_action
        )
        
        class_select_window.create()
        window_manager.window_registry[class_select_window.window_id] = class_select_window
        window_manager.show_window(class_select_window, push_to_stack=True)
    
    def _handle_class_select_action(self, message_type: str, data: dict):
        """クラス選択メニューのアクション処理"""
        logger.debug(f"AdventurersGuild: クラス選択アクション処理: {message_type}, {data}")
        action = data.get('action')
        
        if action and action.startswith('confirm_class_change:'):
            # アクションからキャラクターIDとクラス名を取得
            parts = action.split(':', 2)
            if len(parts) == 3:
                character_id = parts[1]
                target_class = parts[2]
                
                # キャラクターオブジェクトを取得
                character = None
                for char in self.current_party.characters.values():
                    if char.character_id == character_id:
                        character = char
                        break
                
                if character:
                    self._show_class_change_confirm_window(character, target_class)
                else:
                    logger.error(f"キャラクターが見つかりません: {character_id}")
                    self._show_error_window("キャラクターが見つかりません")
            else:
                logger.error(f"不正なアクション形式: {action}")
                self._show_error_window("クラスチェンジに失敗しました")
                
        elif action == 'window_back':
            # 戻るボタンが押された場合
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            
            if window_manager.go_back():
                logger.debug("AdventurersGuild: クラス選択からWindowManagerでgo_backが成功しました")
            else:
                # クラスチェンジメニューを表示
                self._show_class_change()
        else:
            logger.warning(f"AdventurersGuild: 未知のクラス選択アクション: {action}")
    
    def _show_class_change_options(self, character: Character):
        """クラスチェンジ先の選択画面を表示（互換性のため）"""
        # 新しいWindowSystem版にリダイレクト
        self._show_class_change_options_window(character)
    
    def _show_class_change_confirm_window(self, character: Character, target_class: str):
        """クラスチェンジ確認画面（新WindowSystem版）"""
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
        
        # ボタン設定
        if self.current_party.gold < 1000:
            confirm_text += "\n\n※ ゴールドが不足しています"
            buttons = [
                {
                    'id': 'back_insufficient_gold',
                    'text': "戻る",
                    'action': 'window_back'
                }
            ]
        else:
            buttons = [
                {
                    'id': 'confirm_yes',
                    'text': "はい",
                    'action': f'execute_class_change:{character.character_id}:{target_class}'
                },
                {
                    'id': 'confirm_no',
                    'text': "いいえ",
                    'action': 'window_back'
                }
            ]
        
        menu_config = {
            'title': "クラスチェンジ確認",
            'buttons': buttons
        }
        
        # WindowManagerを使用して確認ウィンドウを表示
        window_manager = WindowManager.get_instance()
        
        confirm_window = PartyFormationWindow(
            'class_change_confirm',
            menu_config,
            action_handler=self._handle_class_confirm_action
        )
        
        # 確認メッセージを保存（アクションハンドラーで使用）
        confirm_window.character = character
        confirm_window.target_class = target_class
        confirm_window.confirm_text = confirm_text
        
        confirm_window.create()
        
        # 確認メッセージをテキストラベルとして追加
        if hasattr(confirm_window, 'ui_manager') and confirm_window.ui_manager:
            import pygame_gui
            import pygame
            text_rect = pygame.Rect(20, 60, confirm_window.rect.width - 40, 200)
            confirm_window.message_label = pygame_gui.elements.UILabel(
                relative_rect=text_rect,
                text=confirm_text,
                manager=confirm_window.ui_manager,
                container=confirm_window.panel
            )
        
        window_manager.window_registry[confirm_window.window_id] = confirm_window
        window_manager.show_window(confirm_window, push_to_stack=True)
    
    def _handle_class_confirm_action(self, message_type: str, data: dict):
        """クラスチェンジ確認のアクション処理"""
        logger.debug(f"AdventurersGuild: クラスチェンジ確認アクション処理: {message_type}, {data}")
        action = data.get('action')
        
        if action and action.startswith('execute_class_change:'):
            # アクションからキャラクターIDとクラス名を取得
            parts = action.split(':', 2)
            if len(parts) == 3:
                character_id = parts[1]
                target_class = parts[2]
                
                # キャラクターオブジェクトを取得
                character = None
                for char in self.current_party.characters.values():
                    if char.character_id == character_id:
                        character = char
                        break
                
                if character:
                    self._execute_class_change_window(character, target_class)
                else:
                    logger.error(f"キャラクターが見つかりません: {character_id}")
                    self._show_error_window("キャラクターが見つかりません")
            else:
                logger.error(f"不正なアクション形式: {action}")
                self._show_error_window("クラスチェンジに失敗しました")
                
        elif action == 'window_back':
            # 戻るボタンが押された場合
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            
            if window_manager.go_back():
                logger.debug("AdventurersGuild: クラスチェンジ確認からWindowManagerでgo_backが成功しました")
            else:
                # クラス選択メニューを表示
                # ※ここでキャラクター情報が必要だが、簡単のためクラスチェンジメニューに戻る
                self._show_class_change()
        else:
            logger.warning(f"AdventurersGuild: 未知のクラスチェンジ確認アクション: {action}")
    
    def _show_class_change_confirm(self, character: Character, target_class: str):
        """クラスチェンジ確認画面（互換性のため）"""
        # 新しいWindowSystem版にリダイレクト
        self._show_class_change_confirm_window(character, target_class)
    
    def _execute_class_change_window(self, character: Character, target_class: str):
        """クラスチェンジを実行（新WindowSystem版）"""
        from src.character.class_change import ClassChangeManager
        
        # 現在の確認ウィンドウを閉じる
        window_manager = WindowManager.get_instance()
        if 'class_change_confirm' in window_manager.window_registry:
            confirm_window = window_manager.window_registry['class_change_confirm']
            window_manager.close_window(confirm_window)
        
        # ゴールドを消費
        self.current_party.gold -= 1000
        
        # クラスチェンジ実行
        success, message = ClassChangeManager.change_class(character, target_class)
        
        if success:
            self._show_success_window(message + f"\n\n残りゴールド: {self.current_party.gold}G")
        else:
            # 失敗時はゴールドを戻す
            self.current_party.gold += 1000
            self._show_error_window(message)
    
    def _execute_class_change(self, character: Character, target_class: str):
        """クラスチェンジを実行（互換性のため）"""
        # 新しいWindowSystem版にリダイレクト
        self._execute_class_change_window(character, target_class)
    
    def _back_to_class_change_menu(self, submenu=None):
        """クラスチェンジメニューに戻る（新WindowSystem対応）"""
        # WindowManagerを使用してクラスチェンジメニューを再表示
        self._show_class_change()
    
    def _return_to_party_formation(self):
        """パーティ編成メニューに戻る"""
        # WindowManagerを使用してパーティ編成メニューを再表示
        self._show_party_formation()
    
    def _show_submenu(self, submenu=None):
        """サブメニューを表示（新WindowSystemでは不要）"""
        # 新WindowSystemではウィンドウスタックで自動管理されるため何もしない
        logger.debug("_show_submenu called, but handled by WindowManager stack")
    
    def _back_to_formation_menu(self, submenu=None):
        """編成メニューに戻る"""
        # WindowManagerを使用してパーティ編成メニューを再表示
        self._show_party_formation()
    
    def _back_to_main_menu_from_submenu(self, submenu=None):
        """サブメニューからメインメニューに戻る"""
        # WindowManagerを使用してメインメニューを表示
        window_manager = WindowManager.get_instance()
        if window_manager.go_back():
            logger.debug("WindowManagerでgo_backが成功しました")
        else:
            # スタックが空の場合は新しくメインメニューを表示
            self.show_menu()
    
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