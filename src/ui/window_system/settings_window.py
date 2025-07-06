"""
SettingsWindow クラス

設定画面表示用のウィンドウ
"""

import pygame
import pygame_gui
from pathlib import Path
from typing import Dict, List, Any, Optional

from .window import Window
from .settings_types import (
    SettingsField, SettingsTab, SettingsFieldType
)
from .settings_validator import SettingsValidator
from .settings_loader import SettingsLoader
from .settings_layout_manager import SettingsLayoutManager
from src.utils.logger import logger


class SettingsWindow(Window):
    """
    設定ウィンドウクラス
    
    ゲーム設定の表示と変更を行う
    """
    
    def __init__(self, window_id: str, settings_config: Dict[str, Any], 
                 parent: Optional[Window] = None, modal: bool = True):
        """
        設定ウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            settings_config: 設定ウィンドウ設定辞書
            parent: 親ウィンドウ
            modal: モーダルウィンドウかどうか
        """
        super().__init__(window_id, parent, modal)
        
        # 設定の検証
        self._validate_config(settings_config)
        
        self.settings_config = settings_config
        self.tabs: List[SettingsTab] = []
        self.current_tab_index = 0
        
        # 設定ファイルパス（先に設定）
        self.settings_file_path = Path("config/user_settings.yaml")
        
        # Extract Classによる専門クラス
        self.validator = SettingsValidator()
        self.loader = SettingsLoader(self.settings_file_path)
        self.layout_manager = SettingsLayoutManager()
        
        # 設定値管理
        self.current_settings = self._load_current_settings()
        self.pending_changes: Dict[str, Any] = {}
        
        # UI要素
        self.tab_container: Optional[pygame_gui.core.UIElement] = None
        self.content_container: Optional[pygame_gui.core.UIElement] = None
        
        logger.debug(f"SettingsWindowを初期化: {window_id}")
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """設定の構造を検証"""
        if 'categories' not in config:
            raise ValueError("Settings config must contain 'categories'")
        
        if not isinstance(config['categories'], list):
            raise ValueError("Settings config 'categories' must be a list")
        
        if len(config['categories']) == 0:
            raise ValueError("Settings config 'categories' cannot be empty")
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            self._initialize_ui_manager()
            self._calculate_layout()
            self._create_panel()
            self._create_title_if_needed()
            self._create_tab_container()
            self._create_content_container()
            self._create_tabs()
            self._create_fields()
        
        logger.debug(f"SettingsWindow UI要素を作成: {self.window_id}")
    
    def _initialize_ui_manager(self) -> None:
        """UIManagerを初期化"""
        # WindowManagerのUIManagerを使用
        from .window_manager import WindowManager
        window_manager = WindowManager()
        if window_manager.ui_manager is not None:
            self.ui_manager = window_manager.ui_manager
        else:
            # フォールバック: 独自のUIManagerを作成
            screen_width = 1024
            screen_height = 768
            self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
    
    def _calculate_layout(self) -> None:
        """設定画面のレイアウトを計算"""
        has_title = 'title' in self.settings_config
        
        # Extract Methodパターン適用
        self.rect = self.layout_manager.calculate_settings_rect(has_title)
    
    def _create_panel(self) -> None:
        """設定パネルを作成"""
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager
        )
    
    def _create_title_if_needed(self) -> None:
        """タイトルラベルを作成（必要な場合）"""
        if 'title' in self.settings_config:
            title_rect = self.layout_manager.calculate_title_rect(self.rect)
            self.title_label = pygame_gui.elements.UILabel(
                relative_rect=title_rect,
                text=self.settings_config['title'],
                manager=self.ui_manager,
                container=self.panel
            )
    
    def _create_ui_container(self, container_type: str) -> None:
        """統一UIコンテナ作成メソッド"""
        has_title = 'title' in self.settings_config
        
        # コンテナタイプごとの設定
        container_configs = {
            'tab': {
                'rect_method': lambda: self.layout_manager.calculate_tab_container_rect(self.rect, has_title),
                'element_class': pygame_gui.elements.UIPanel,
                'attribute_name': 'tab_container'
            },
            'content': {
                'rect_method': lambda: self.layout_manager.calculate_content_container_rect(self.rect, has_title),
                'element_class': pygame_gui.elements.UIScrollingContainer,
                'attribute_name': 'content_container'
            }
        }
        
        if container_type not in container_configs:
            raise ValueError(f"不正なコンテナタイプ: {container_type}")
        
        config = container_configs[container_type]
        rect = config['rect_method']()
        element = config['element_class'](
            relative_rect=rect,
            manager=self.ui_manager,
            container=self.panel
        )
        setattr(self, config['attribute_name'], element)
    
    def _create_tab_container(self) -> None:
        """タブコンテナを作成"""
        self._create_ui_container('tab')
    
    def _create_content_container(self) -> None:
        """コンテンツコンテナを作成"""
        self._create_ui_container('content')
    
    
    def _create_tabs(self) -> None:
        """タブを作成"""
        tab_width = (self.rect.width - 80) // len(self.settings_config['categories'])
        
        for i, category_config in enumerate(self.settings_config['categories']):
            tab_id = category_config['id'] if isinstance(category_config, dict) else category_config
            tab_label = category_config.get('label', tab_id) if isinstance(category_config, dict) else tab_id
            
            # タブボタンを作成
            tab_x = i * tab_width
            tab_rect = pygame.Rect(tab_x, 0, tab_width, 40)
            tab_button = pygame_gui.elements.UIButton(
                relative_rect=tab_rect,
                text=tab_label,
                manager=self.ui_manager,
                container=self.tab_container
            )
            
            # SettingsTabオブジェクトを作成
            settings_tab = SettingsTab(
                tab_id=tab_id,
                label=tab_label,
                fields=[],
                is_active=(i == 0),
                ui_element=tab_button
            )
            
            self.tabs.append(settings_tab)
    
    def _create_fields(self) -> None:
        """フィールドを作成"""
        y_position = 20
        
        for category_config in self.settings_config['categories']:
            if isinstance(category_config, dict) and 'fields' in category_config:
                for field_config in category_config['fields']:
                    field = self._create_field(field_config, y_position)
                    
                    # フィールドを対応するタブに追加
                    tab = next((t for t in self.tabs if t.tab_id == category_config['id']), None)
                    if tab:
                        tab.fields.append(field)
                    
                    y_position += 60
    
    def _create_field(self, field_config: Dict[str, Any], y_position: int) -> SettingsField:
        """個別フィールドを作成"""
        field_type = SettingsFieldType(field_config['type'])
        field_id = field_config['id']
        
        # ラベルを作成
        label_rect = pygame.Rect(20, y_position, 200, 25)
        label_text = field_config.get('label', field_id)
        
        label = pygame_gui.elements.UILabel(
            relative_rect=label_rect,
            text=label_text,
            manager=self.ui_manager,
            container=self.content_container
        )
        
        # 入力要素を作成
        input_rect = pygame.Rect(240, y_position, 300, 25)
        ui_element = self._create_input_element(field_type, input_rect, field_config)
        
        # SettingsFieldオブジェクトを作成
        settings_field = SettingsField(
            field_id=field_id,
            label=field_config.get('label', field_id),
            field_type=field_type,
            category=field_config.get('category', ''),
            default_value=field_config.get('default'),
            current_value=self.current_settings.get(field_id, field_config.get('default')),
            min_value=field_config.get('min'),
            max_value=field_config.get('max'),
            options=field_config.get('options'),
            ui_element=ui_element,
            description=field_config.get('description'),
            requires_restart=field_config.get('requires_restart', False)
        )
        
        # 現在の値をUI要素に設定
        self._set_ui_element_value(ui_element, field_type, settings_field.current_value)
        
        return settings_field
    
    def _create_input_element(self, field_type: SettingsFieldType, rect: pygame.Rect, 
                            config: Dict[str, Any]) -> pygame_gui.core.UIElement:
        """入力要素を作成"""
        if field_type == SettingsFieldType.SLIDER:
            return pygame_gui.elements.UIHorizontalSlider(
                relative_rect=rect,
                start_value=config.get('default', 0.5),
                value_range=(config.get('min', 0.0), config.get('max', 1.0)),
                manager=self.ui_manager,
                container=self.content_container
            )
        elif field_type == SettingsFieldType.DROPDOWN:
            options = config.get('options', [])
            return pygame_gui.elements.UIDropDownMenu(
                relative_rect=rect,
                options_list=options,
                starting_option=options[0] if options else '',
                manager=self.ui_manager,
                container=self.content_container
            )
        elif field_type == SettingsFieldType.CHECKBOX:
            return pygame_gui.elements.UIButton(
                relative_rect=rect,
                text='☐ ' + config.get('label', ''),
                manager=self.ui_manager,
                container=self.content_container
            )
        elif field_type == SettingsFieldType.TEXT_INPUT:
            return pygame_gui.elements.UITextEntryLine(
                relative_rect=rect,
                manager=self.ui_manager,
                container=self.content_container
            )
        elif field_type == SettingsFieldType.BUTTON:
            return pygame_gui.elements.UIButton(
                relative_rect=rect,
                text=config.get('name', config.get('label', 'Button')),
                manager=self.ui_manager,
                container=self.content_container
            )
        else:
            raise ValueError(f"Unsupported field type: {field_type}")
    
    def _set_ui_element_value(self, ui_element: pygame_gui.core.UIElement, 
                            field_type: SettingsFieldType, value: Any) -> None:
        """UI要素に値を設定"""
        if field_type == SettingsFieldType.SLIDER and hasattr(ui_element, 'set_current_value'):
            ui_element.set_current_value(float(value) if value is not None else 0.5)
        elif field_type == SettingsFieldType.DROPDOWN and hasattr(ui_element, 'selected_option'):
            if value and value in ui_element.options_list:
                ui_element.selected_option = value
        elif field_type == SettingsFieldType.CHECKBOX:
            checked = bool(value) if value is not None else False
            prefix = '☑ ' if checked else '☐ '
            label = ui_element.text.split(' ', 1)[1] if ' ' in ui_element.text else ''
            ui_element.set_text(prefix + label)
        elif field_type == SettingsFieldType.TEXT_INPUT and hasattr(ui_element, 'set_text'):
            ui_element.set_text(str(value) if value is not None else '')
        elif field_type == SettingsFieldType.BUTTON:
            # ボタンは値を設定する必要がない（クリック時のアクションのみ）
            pass
    
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if not self.ui_manager:
            return False
        
        # pygame-guiにイベントを渡す
        self.ui_manager.process_events(event)
        
        # キーボードイベント
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB and event.mod & pygame.KMOD_CTRL:
                self._handle_tab_switch()
                return True
        
        # タブクリック処理
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for i, tab in enumerate(self.tabs):
                if event.ui_element == tab.ui_element:
                    self.switch_tab(i)
                    return True
        
        
        # フィールド値変更処理
        if event.type in [pygame_gui.UI_HORIZONTAL_SLIDER_MOVED, 
                         pygame_gui.UI_DROP_DOWN_MENU_CHANGED,
                         pygame_gui.UI_TEXT_ENTRY_CHANGED]:
            self._handle_field_value_change(event)
            return True
        
        return False
    
    def _handle_tab_switch(self) -> None:
        """Ctrl+Tabでタブ切り替え"""
        next_index = (self.current_tab_index + 1) % len(self.tabs)
        self.switch_tab(next_index)
    
    
    def _handle_field_value_change(self, event) -> None:
        """フィールド値変更を処理"""
        # どのフィールドが変更されたかを特定
        for tab in self.tabs:
            for field in tab.fields:
                if event.ui_element == field.ui_element:
                    new_value = self._get_ui_element_value(field.ui_element, field.field_type)
                    self.set_field_value(field.field_id, new_value)
                    return
    
    def _get_ui_element_value(self, ui_element: pygame_gui.core.UIElement, 
                            field_type: SettingsFieldType) -> Any:
        """UI要素から値を取得"""
        if field_type == SettingsFieldType.SLIDER:
            return ui_element.get_current_value()
        elif field_type == SettingsFieldType.DROPDOWN:
            return ui_element.selected_option
        elif field_type == SettingsFieldType.CHECKBOX:
            return ui_element.text.startswith('☑')
        elif field_type == SettingsFieldType.TEXT_INPUT:
            return ui_element.get_text()
        return None
    
    def switch_tab(self, tab_index: int) -> bool:
        """タブを切り替え"""
        if 0 <= tab_index < len(self.tabs):
            # 現在のタブを非アクティブに
            if self.current_tab_index < len(self.tabs):
                self.tabs[self.current_tab_index].is_active = False
            
            # 新しいタブをアクティブに
            self.tabs[tab_index].is_active = True
            self.current_tab_index = tab_index
            
            # UI要素の表示/非表示を更新
            self._update_tab_display()
            return True
        return False
    
    def _update_tab_display(self) -> None:
        """タブ表示を更新"""
        for i, tab in enumerate(self.tabs):
            # タブボタンの表示を更新
            if hasattr(tab.ui_element, 'set_text'):
                prefix = "* " if tab.is_active else ""
                tab.ui_element.set_text(prefix + tab.label)
            
            # フィールドの表示/非表示を更新
            for field in tab.fields:
                if field.ui_element:
                    field.ui_element.visible = tab.is_active
    
    def set_field_value(self, field_id: str, value: Any) -> bool:
        """フィールドの値を設定"""
        field = self._find_field_by_id(field_id)
        if not field:
            return False
        
        # 検証
        if not self._validate_field_value(field, value):
            return False
        
        # 値を設定
        field.current_value = value
        self.pending_changes[field_id] = value
        
        # UI要素を更新
        self._set_ui_element_value(field.ui_element, field.field_type, value)
        
        return True
    
    def get_field_value(self, field_id: str) -> Any:
        """フィールドの値を取得"""
        field = self._find_field_by_id(field_id)
        return field.current_value if field else None
    
    def _find_field_by_id(self, field_id: str) -> Optional[SettingsField]:
        """IDでフィールドを検索"""
        for tab in self.tabs:
            for field in tab.fields:
                if field.field_id == field_id:
                    return field
        return None
    
    def _validate_field_value(self, field: SettingsField, value: Any) -> bool:
        """フィールド値を検証"""
        # Extract Classパターン適用 - 検証ロジックを専門クラスに委譲
        return self.validator.validate_field_value(field, value)
    
    def _execute_settings_operation(self, operation_type: str) -> bool:
        """設定操作の統一メソッド"""
        if operation_type == 'apply':
            # 変更がある場合は設定を更新
            if len(self.pending_changes) > 0:
                self.current_settings.update(self.pending_changes)
                self.loader.save_settings(self.current_settings)
                self.pending_changes.clear()
                logger.debug("設定変更を適用しました")
            
            # 適用メッセージを送信
            self.send_message('settings_applied', {'settings': self.current_settings})
            return True
            
        elif operation_type == 'cancel':
            # 変更をクリア
            self.pending_changes.clear()
            
            # フィールドを元の値に戻す
            for tab in self.tabs:
                for field in tab.fields:
                    field.current_value = self.current_settings.get(
                        field.field_id, field.default_value
                    )
                    self._set_ui_element_value(
                        field.ui_element, field.field_type, field.current_value
                    )
            
            # キャンセルメッセージを送信
            self.send_message('settings_cancelled')
            logger.debug("設定変更をキャンセルしました")
            return True
            
        elif operation_type == 'reset':
            # デフォルト値にリセット
            for tab in self.tabs:
                for field in tab.fields:
                    if field.default_value is not None:
                        self.set_field_value(field.field_id, field.default_value)
            
            logger.debug("設定をデフォルト値にリセットしました")
            return True
            
        else:
            raise ValueError(f"不正な操作タイプ: {operation_type}")
    
    
    def cancel_changes(self) -> None:
        """変更をキャンセル"""
        self._execute_settings_operation('cancel')
        
        # キャンセル時はウィンドウを非表示にする（破棄しない）
        if self.message_handler:
            self.message_handler('settings_cancelled', {'window_id': self.window_id})
        
        from .window_manager import WindowManager
        window_manager = WindowManager()
        window_manager.hide_window(self, remove_from_stack=True)
    
    
    def handle_escape(self) -> bool:
        """ESCキーの処理"""
        # 変更をキャンセル（ウィンドウのクローズも実行される）
        self.cancel_changes()
        return True
    
    def _load_current_settings(self) -> Dict[str, Any]:
        """現在の設定を読み込み"""
        # Extract Classパターン適用 - 設定読み込みロジックを専門クラスに委譲
        return self.loader.load_settings()
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # タブをクリア
        self.tabs.clear()
        
        # pygame-guiの要素を削除
        if self.ui_manager:
            for element in list(self.ui_manager.get_root_container().elements):
                element.kill()
            self.ui_manager = None
        
        logger.debug(f"SettingsWindow UI要素をクリーンアップ: {self.window_id}")
    
    def hide_ui_elements(self) -> None:
        """UI要素を非表示にする"""
        logger.info(f"SettingsWindow.hide_ui_elements() 開始: {self.window_id}")
        
        if not self.ui_manager:
            logger.warning(f"UIManagerが存在しません: {self.window_id}")
            return
        
        # pygame-guiの展開されたドロップダウンメニューを強制的に閉じる
        logger.info("ドロップダウンメニューの強制クローズを実行")
        self._force_close_dropdowns()
        
        # すべてのUI要素を非表示にする
        if hasattr(self, 'panel') and self.panel:
            self.panel.hide()
            logger.debug("パネルを非表示にしました")
            
        # タブ関連要素を非表示
        if hasattr(self, 'tab_container') and self.tab_container:
            self.tab_container.hide()
            logger.debug("タブコンテナを非表示にしました")
            
        # コンテンツコンテナを非表示
        if hasattr(self, 'content_container') and self.content_container:
            self.content_container.hide()
            logger.debug("コンテンツコンテナを非表示にしました")
            
        # 個別のUI要素を非表示
        for tab in self.tabs:
            if hasattr(tab, 'ui_element') and tab.ui_element:
                tab.ui_element.hide()
            for field in tab.fields:
                if hasattr(field, 'ui_element') and field.ui_element:
                    field.ui_element.hide()
                if hasattr(field, 'label_element') and field.label_element:
                    field.label_element.hide()
        
        logger.info(f"SettingsWindow UI要素の非表示完了: {self.window_id}")
    
    def _force_close_dropdowns(self) -> None:
        """pygame-guiのドロップダウンメニューを強制的に閉じる"""
        if not self.ui_manager:
            return
        
        try:
            dropdown_killed_count = 0
            
            # 方法1: フィールドのドロップダウンを直接チェック
            for tab in self.tabs:
                for field in tab.fields:
                    if hasattr(field, 'ui_element') and field.ui_element:
                        ui_element = field.ui_element
                        
                        # pygame-guiのUIDropDownMenuの場合
                        if hasattr(ui_element, 'drop_down_menu_ui'):
                            if ui_element.drop_down_menu_ui is not None:
                                logger.debug(f"ドロップダウンメニューUI発見: {field.field_id}")
                                ui_element.drop_down_menu_ui.kill()
                                ui_element.drop_down_menu_ui = None
                                dropdown_killed_count += 1
                        
                        # 展開状態をリセット
                        if hasattr(ui_element, 'is_expanded'):
                            ui_element.is_expanded = False
                        if hasattr(ui_element, 'menu_states'):
                            ui_element.menu_states.clear()
            
            # 方法2: UIManagerの全要素をスキャンして孤立したドロップダウンを削除
            if hasattr(self.ui_manager, 'ui_group'):
                all_sprites = list(self.ui_manager.ui_group.sprites())
                for sprite in all_sprites:
                    class_name = sprite.__class__.__name__
                    
                    # ドロップダウン関連クラスを特定
                    if any(keyword in class_name.lower() for keyword in 
                          ['dropdown', 'drop_down', 'menu_ui', 'selection_list']):
                        try:
                            # ウィンドウ所有権チェック: 自分の要素ではない場合はkill
                            owner_belongs_to_settings = False
                            if hasattr(sprite, 'container'):
                                current = sprite.container
                                while current:
                                    if current == self.panel:
                                        owner_belongs_to_settings = True
                                        break
                                    current = getattr(current, 'container', None)
                            
                            if not owner_belongs_to_settings:
                                logger.debug(f"孤立したドロップダウン要素を削除: {class_name}")
                                sprite.kill()
                                dropdown_killed_count += 1
                                
                        except Exception as e:
                            logger.warning(f"ドロップダウンスプライト削除エラー ({class_name}): {e}")
            
            # 方法3: UIManagerの要素コンテナから直接削除
            try:
                root_container = self.ui_manager.get_root_container()
                elements_to_kill = []
                
                def scan_container(container):
                    if hasattr(container, 'elements'):
                        for element in container.elements:
                            class_name = element.__class__.__name__
                            if any(keyword in class_name.lower() for keyword in 
                                  ['dropdown', 'drop_down', 'menu_ui', 'selection_list']):
                                # 自分のパネル配下ではない要素をマーク
                                if not self._is_element_owned_by_settings(element):
                                    elements_to_kill.append(element)
                            
                            # 再帰的にコンテナをスキャン
                            if hasattr(element, 'elements'):
                                scan_container(element)
                
                scan_container(root_container)
                
                for element in elements_to_kill:
                    try:
                        logger.debug(f"ルートコンテナから孤立要素を削除: {element.__class__.__name__}")
                        element.kill()
                        dropdown_killed_count += 1
                    except Exception as e:
                        logger.warning(f"要素削除エラー: {e}")
                        
            except Exception as e:
                logger.warning(f"ルートコンテナスキャンエラー: {e}")
            
            if dropdown_killed_count > 0:
                logger.info(f"ドロップダウン要素を{dropdown_killed_count}個削除しました")
            else:
                logger.debug("削除対象のドロップダウン要素が見つかりませんでした")
                        
        except Exception as e:
            logger.warning(f"ドロップダウンメニュー強制クローズでエラー: {e}")
    
    def _is_element_owned_by_settings(self, element) -> bool:
        """要素が設定ウィンドウに所属するかチェック"""
        try:
            if not hasattr(element, 'container'):
                return False
            
            current = element.container
            while current:
                if current == self.panel:
                    return True
                if hasattr(current, 'container'):
                    current = current.container
                else:
                    break
            return False
        except:
            return False
    
    def show_ui_elements(self) -> None:
        """UI要素を表示する"""
        if not self.ui_manager:
            return
        
        # すべてのUI要素を表示する
        if hasattr(self, 'panel') and self.panel:
            self.panel.show()
            
        # タブ関連要素を表示
        if hasattr(self, 'tab_container') and self.tab_container:
            self.tab_container.show()
            
        # コンテンツコンテナを表示
        if hasattr(self, 'content_container') and self.content_container:
            self.content_container.show()
            
        # 個別のUI要素を表示
        for tab in self.tabs:
            if hasattr(tab, 'ui_element') and tab.ui_element:
                tab.ui_element.show()
            for field in tab.fields:
                if hasattr(field, 'ui_element') and field.ui_element:
                    field.ui_element.show()
                if hasattr(field, 'label_element') and field.label_element:
                    field.label_element.show()
        
        logger.debug(f"SettingsWindow UI要素を表示: {self.window_id}")