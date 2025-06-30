# Window実装ガイド

**バージョン**: 2.0 (WindowSystem統一化完了版)  
**最終更新**: 2025-06-30

## 概要

このガイドでは、Dungeon RPGのWindowSystemにおける新しいWindow実装方法について、具体的なコード例とベストプラクティスを示します。WindowSystem統一化完了後の最新アーキテクチャに基づいています。

### このガイドの対象者
- 新しいWindow機能を実装する開発者
- 既存Windowの拡張・修正を行う開発者
- WindowSystemの動作原理を理解したい開発者

## 基本Window実装

### 1. Window基底クラスの理解

すべてのWindowは`Window`基底クラスを継承します。

```python
from abc import abstractmethod
from typing import Optional, Dict, Any, List
import pygame
from src.ui.window_system.window_base import Window, WindowState

class Window:
    """全Windowの基底クラス"""
    
    def __init__(self, window_id: str):
        """Window初期化
        
        Args:
            window_id (str): 一意のWindow識別子
        """
        self.window_id = window_id
        self.state = WindowState.CREATED
        self.visible = False
        self.focused = False
        self.parent_window: Optional[Window] = None
        self.child_windows: List[Window] = []
        self.ui_elements: List[UIElement] = []
        
    @abstractmethod
    def create(self) -> None:
        """UI要素作成（必須実装）
        
        このメソッドで、Windowに表示される
        すべてのUI要素を作成・配置します。
        """
        pass
        
    @abstractmethod
    def handle_event(self, event: pygame.Event) -> bool:
        """イベント処理（必須実装）
        
        Args:
            event: 処理するPygameイベント
            
        Returns:
            bool: イベントを処理した場合True、
                 しなかった場合False
        """
        pass
        
    def update(self, time_delta: float) -> None:
        """更新処理（オプション実装）
        
        Args:
            time_delta: 前フレームからの経過時間（秒）
        """
        for element in self.ui_elements:
            element.update(time_delta)
            
    def render(self, surface: pygame.Surface) -> None:
        """描画処理（オプション実装）
        
        Args:
            surface: 描画対象のPygameサーフェス
        """
        for element in self.ui_elements:
            element.render(surface)
```

### 2. 基本Window実装例

```python
class SimpleMenuWindow(Window):
    """シンプルなメニューWindow実装例"""
    
    def __init__(self, window_id: str, menu_config: Dict[str, Any]):
        super().__init__(window_id)
        self.menu_config = menu_config
        self.buttons: List[UIButton] = []
        self.title_text: Optional[UIText] = None
        self.selected_index = 0
        
    def create(self) -> None:
        """UI要素作成"""
        # タイトルテキスト作成
        title = self.menu_config.get('title', 'Menu')
        self.title_text = UIText(
            'title',
            title,
            position=(400, 100),  # 画面中央上部
            font_size=32,
            color=(255, 255, 255)
        )
        self.ui_elements.append(self.title_text)
        
        # メニューボタン作成
        items = self.menu_config.get('items', [])
        button_y = 200
        
        for i, item_text in enumerate(items):
            button = UIButton(
                f'button_{i}',
                item_text,
                position=(300, button_y + i * 60),
                size=(200, 40),
                callback=lambda idx=i: self.on_button_click(idx)
            )
            self.buttons.append(button)
            self.ui_elements.append(button)
    
    def handle_event(self, event: pygame.Event) -> bool:
        """イベント処理"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
                self.update_selection()
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.buttons) - 1, 
                                        self.selected_index + 1)
                self.update_selection()
                return True
            elif event.key == pygame.K_RETURN:
                self.on_button_click(self.selected_index)
                return True
            elif event.key == pygame.K_ESCAPE:
                self.close()
                return True
        
        # マウス・その他のイベントはUI要素に委譲
        for element in self.ui_elements:
            if element.handle_event(event):
                return True
                
        return False
    
    def update_selection(self) -> None:
        """選択状態更新"""
        for i, button in enumerate(self.buttons):
            button.set_selected(i == self.selected_index)
    
    def on_button_click(self, index: int) -> None:
        """ボタンクリック処理"""
        callback = self.menu_config.get('callbacks', {}).get(index)
        if callback:
            callback()
        else:
            print(f"Button {index} clicked: {self.buttons[index].text}")
    
    def close(self) -> None:
        """Window閉鎖処理"""
        from src.ui.window_system.window_manager import WindowManager
        manager = WindowManager.get_instance()
        manager.hide_window(self)
        manager.destroy_window(self)
```

## 高度なWindow実装

### 1. データ表示Window

```python
class DataDisplayWindow(Window):
    """データ表示特化Window"""
    
    def __init__(self, window_id: str, data_source: Any, 
                 display_config: Dict[str, Any]):
        super().__init__(window_id)
        self.data_source = data_source
        self.display_config = display_config
        self.data_list: Optional[UIList] = None
        self.detail_panel: Optional[UIPanel] = None
        self.selected_item = None
        
    def create(self) -> None:
        """データ表示UI作成"""
        # データリスト作成
        self.data_list = UIList(
            'data_list',
            position=(50, 100),
            size=(300, 400),
            on_selection_change=self.on_item_selected
        )
        
        # データ詳細パネル作成
        self.detail_panel = UIPanel(
            'detail_panel',
            position=(400, 100),
            size=(350, 400),
            background_color=(50, 50, 50)
        )
        
        self.ui_elements.extend([self.data_list, self.detail_panel])
        self.load_data()
    
    def load_data(self) -> None:
        """データ読み込み"""
        data_items = self.data_source.get_items()
        for item in data_items:
            display_text = self.format_item(item)
            self.data_list.add_item(display_text, item)
    
    def format_item(self, item: Any) -> str:
        """アイテム表示フォーマット"""
        formatter = self.display_config.get('formatter')
        if formatter:
            return formatter(item)
        return str(item)
    
    def on_item_selected(self, item: Any) -> None:
        """アイテム選択処理"""
        self.selected_item = item
        self.update_detail_panel()
    
    def update_detail_panel(self) -> None:
        """詳細パネル更新"""
        self.detail_panel.clear()
        
        if self.selected_item:
            details = self.get_item_details(self.selected_item)
            for detail in details:
                self.detail_panel.add_text(detail)
    
    def get_item_details(self, item: Any) -> List[str]:
        """アイテム詳細取得"""
        detail_provider = self.display_config.get('detail_provider')
        if detail_provider:
            return detail_provider(item)
        return [f"Item: {item}"]
    
    def handle_event(self, event: pygame.Event) -> bool:
        """イベント処理"""
        # データ操作キーボード操作
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F5:
                self.refresh_data()
                return True
            elif event.key == pygame.K_DELETE and self.selected_item:
                self.delete_selected_item()
                return True
        
        # 基本のイベント委譲
        return super().handle_event(event)
    
    def refresh_data(self) -> None:
        """データ再読み込み"""
        self.data_list.clear()
        self.load_data()
    
    def delete_selected_item(self) -> None:
        """選択アイテム削除"""
        if self.selected_item and hasattr(self.data_source, 'delete_item'):
            self.data_source.delete_item(self.selected_item)
            self.refresh_data()
```

### 2. フォーム入力Window

```python
class FormInputWindow(Window):
    """フォーム入力特化Window"""
    
    def __init__(self, window_id: str, form_schema: Dict[str, Any],
                 on_submit: Callable = None):
        super().__init__(window_id)
        self.form_schema = form_schema
        self.on_submit = on_submit
        self.form_fields: Dict[str, UIElement] = {}
        self.submit_button: Optional[UIButton] = None
        self.cancel_button: Optional[UIButton] = None
        
    def create(self) -> None:
        """フォームUI作成"""
        y_offset = 100
        
        # フォームフィールド作成
        for field_name, field_config in self.form_schema.items():
            field_type = field_config.get('type', 'text')
            label = field_config.get('label', field_name)
            
            # ラベル作成
            label_element = UIText(
                f'label_{field_name}',
                label,
                position=(100, y_offset),
                font_size=16
            )
            self.ui_elements.append(label_element)
            
            # 入力フィールド作成
            if field_type == 'text':
                field = UITextInput(
                    f'input_{field_name}',
                    position=(250, y_offset),
                    size=(200, 30),
                    placeholder=field_config.get('placeholder', '')
                )
            elif field_type == 'number':
                field = UINumberInput(
                    f'input_{field_name}',
                    position=(250, y_offset),
                    size=(200, 30),
                    min_value=field_config.get('min', 0),
                    max_value=field_config.get('max', 100)
                )
            elif field_type == 'choice':
                field = UIDropdown(
                    f'input_{field_name}',
                    position=(250, y_offset),
                    size=(200, 30),
                    choices=field_config.get('choices', [])
                )
            else:
                raise ValueError(f"Unsupported field type: {field_type}")
            
            self.form_fields[field_name] = field
            self.ui_elements.append(field)
            y_offset += 50
        
        # ボタン作成
        y_offset += 20
        self.submit_button = UIButton(
            'submit',
            'OK',
            position=(200, y_offset),
            size=(80, 35),
            callback=self.on_submit_click
        )
        
        self.cancel_button = UIButton(
            'cancel',
            'Cancel',
            position=(300, y_offset),
            size=(80, 35),
            callback=self.on_cancel_click
        )
        
        self.ui_elements.extend([self.submit_button, self.cancel_button])
    
    def handle_event(self, event: pygame.Event) -> bool:
        """イベント処理"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.on_submit_click()
                return True
            elif event.key == pygame.K_ESCAPE:
                self.on_cancel_click()
                return True
        
        return super().handle_event(event)
    
    def get_form_data(self) -> Dict[str, Any]:
        """フォームデータ取得"""
        data = {}
        for field_name, field in self.form_fields.items():
            data[field_name] = field.get_value()
        return data
    
    def validate_form(self) -> List[str]:
        """フォーム検証"""
        errors = []
        data = self.get_form_data()
        
        for field_name, field_config in self.form_schema.items():
            value = data.get(field_name)
            
            # 必須チェック
            if field_config.get('required', False) and not value:
                errors.append(f"{field_config.get('label', field_name)} is required")
            
            # 値範囲チェック
            if field_config.get('type') == 'number' and value is not None:
                min_val = field_config.get('min')
                max_val = field_config.get('max')
                if min_val is not None and value < min_val:
                    errors.append(f"{field_config.get('label', field_name)} must be >= {min_val}")
                if max_val is not None and value > max_val:
                    errors.append(f"{field_config.get('label', field_name)} must be <= {max_val}")
        
        return errors
    
    def on_submit_click(self) -> None:
        """送信ボタンクリック"""
        errors = self.validate_form()
        if errors:
            self.show_validation_errors(errors)
        else:
            data = self.get_form_data()
            if self.on_submit:
                self.on_submit(data)
            self.close()
    
    def on_cancel_click(self) -> None:
        """キャンセルボタンクリック"""
        self.close()
    
    def show_validation_errors(self, errors: List[str]) -> None:
        """検証エラー表示"""
        from src.ui.window_system.window_manager import WindowManager
        manager = WindowManager.get_instance()
        
        error_dialog = manager.create_window(
            DialogWindow,
            'validation_error',
            dialog_type=DialogType.ERROR,
            message='\n'.join(errors)
        )
        manager.show_window(error_dialog)
```

### 3. ダイアログWindow

```python
class CustomDialogWindow(Window):
    """カスタムダイアログWindow"""
    
    def __init__(self, window_id: str, dialog_config: Dict[str, Any]):
        super().__init__(window_id)
        self.dialog_config = dialog_config
        self.result = None
        self.callback = dialog_config.get('callback')
        self.message_text: Optional[UIText] = None
        self.buttons: List[UIButton] = []
        
    def create(self) -> None:
        """ダイアログUI作成"""
        # 背景パネル
        bg_panel = UIPanel(
            'background',
            position=(200, 150),
            size=(400, 200),
            background_color=(80, 80, 80),
            border_color=(200, 200, 200),
            border_width=2
        )
        self.ui_elements.append(bg_panel)
        
        # メッセージテキスト
        message = self.dialog_config.get('message', '')
        self.message_text = UIText(
            'message',
            message,
            position=(400, 200),  # 中央
            font_size=18,
            color=(255, 255, 255),
            align='center'
        )
        self.ui_elements.append(self.message_text)
        
        # ボタン作成
        button_configs = self.dialog_config.get('buttons', [
            {'text': 'OK', 'result': 'ok'},
            {'text': 'Cancel', 'result': 'cancel'}
        ])
        
        button_width = 80
        button_spacing = 100
        total_width = len(button_configs) * button_width + (len(button_configs) - 1) * (button_spacing - button_width)
        start_x = 400 - total_width // 2
        
        for i, btn_config in enumerate(button_configs):
            button = UIButton(
                f'button_{i}',
                btn_config['text'],
                position=(start_x + i * button_spacing, 280),
                size=(button_width, 35),
                callback=lambda result=btn_config['result']: self.on_button_click(result)
            )
            self.buttons.append(button)
            self.ui_elements.append(button)
    
    def handle_event(self, event: pygame.Event) -> bool:
        """イベント処理"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.on_button_click('ok')
                return True
            elif event.key == pygame.K_ESCAPE:
                self.on_button_click('cancel')
                return True
        
        return super().handle_event(event)
    
    def on_button_click(self, result: str) -> None:
        """ボタンクリック処理"""
        self.result = result
        if self.callback:
            self.callback(result)
        self.close()
    
    def get_result(self) -> Optional[str]:
        """ダイアログ結果取得"""
        return self.result
```

## Window登録・使用

### 1. WindowManagerへの登録

```python
# window_factory.py
from src.ui.window_system.window_manager import WindowManager

def register_custom_windows():
    """カスタムWindowの登録"""
    manager = WindowManager.get_instance()
    
    # Window種別の登録
    manager.register_window_type('simple_menu', SimpleMenuWindow)
    manager.register_window_type('data_display', DataDisplayWindow)
    manager.register_window_type('form_input', FormInputWindow)
    manager.register_window_type('custom_dialog', CustomDialogWindow)

# main.py などで初期化時に呼び出し
register_custom_windows()
```

### 2. Window使用例

```python
def show_character_selection():
    """キャラクター選択Windowの表示例"""
    manager = WindowManager.get_instance()
    
    # キャラクターデータ取得
    character_data = get_character_data()
    
    # データ表示Window作成
    char_window = manager.create_window(
        DataDisplayWindow,
        'character_selection',
        data_source=character_data,
        display_config={
            'formatter': lambda char: f"{char.name} (Lv.{char.level})",
            'detail_provider': lambda char: [
                f"Name: {char.name}",
                f"Level: {char.level}",
                f"Class: {char.character_class}",
                f"HP: {char.hp}/{char.max_hp}"
            ]
        }
    )
    
    manager.show_window(char_window)

def show_character_creation():
    """キャラクター作成フォームの表示例"""
    manager = WindowManager.get_instance()
    
    form_schema = {
        'name': {
            'type': 'text',
            'label': 'Character Name',
            'required': True,
            'placeholder': 'Enter name...'
        },
        'race': {
            'type': 'choice',
            'label': 'Race',
            'choices': ['Human', 'Elf', 'Dwarf', 'Halfling'],
            'required': True
        },
        'class': {
            'type': 'choice',
            'label': 'Class',
            'choices': ['Fighter', 'Mage', 'Priest', 'Thief'],
            'required': True
        },
        'bonus_points': {
            'type': 'number',
            'label': 'Bonus Points',
            'min': 0,
            'max': 50,
            'required': False
        }
    }
    
    creation_window = manager.create_window(
        FormInputWindow,
        'character_creation',
        form_schema=form_schema,
        on_submit=on_character_created
    )
    
    manager.show_window(creation_window)

def on_character_created(data: Dict[str, Any]):
    """キャラクター作成完了処理"""
    print(f"Character created: {data}")
    # キャラクター作成処理...
```

## ベストプラクティス

### 1. Windowライフサイクル管理

```python
class WindowLifecycleExample:
    """Windowライフサイクル管理例"""
    
    def __init__(self):
        self.manager = WindowManager.get_instance()
        self.active_windows: List[Window] = []
    
    def create_window_safely(self, window_class, window_id, **kwargs):
        """安全なWindow作成"""
        try:
            window = self.manager.create_window(window_class, window_id, **kwargs)
            self.active_windows.append(window)
            return window
        except Exception as e:
            logger.error(f"Window作成失敗: {window_id}, {e}")
            return None
    
    def cleanup_all_windows(self):
        """すべてのWindowクリーンアップ"""
        for window in self.active_windows[:]:  # コピーしてイテレート
            try:
                self.manager.destroy_window(window)
                self.active_windows.remove(window)
            except Exception as e:
                logger.error(f"Window破棄エラー: {e}")
```

### 2. イベント処理パターン

```python
class EventHandlingPatterns:
    """イベント処理パターン例"""
    
    def handle_event_with_priority(self, event: pygame.Event) -> bool:
        """優先度付きイベント処理"""
        # 1. 高優先度イベント（システムレベル）
        if self.handle_system_events(event):
            return True
        
        # 2. 中優先度イベント（UIレベル）
        if self.handle_ui_events(event):
            return True
        
        # 3. 低優先度イベント（ゲームレベル）
        if self.handle_game_events(event):
            return True
        
        return False
    
    def handle_event_with_state(self, event: pygame.Event) -> bool:
        """状態依存イベント処理"""
        if self.state == WindowState.SHOWN:
            return self.handle_active_events(event)
        elif self.state == WindowState.HIDDEN:
            return self.handle_passive_events(event)
        else:
            return False
    
    def handle_event_with_delegation(self, event: pygame.Event) -> bool:
        """委譲パターンイベント処理"""
        # 子Windowに先に委譲
        for child in self.child_windows:
            if child.visible and child.handle_event(event):
                return True
        
        # UI要素に委譲
        for element in self.ui_elements:
            if element.visible and element.handle_event(event):
                return True
        
        # 自分で処理
        return self.handle_own_events(event)
```

### 3. パフォーマンス最適化

```python
class PerformanceOptimizedWindow(Window):
    """パフォーマンス最適化Window例"""
    
    def __init__(self, window_id: str):
        super().__init__(window_id)
        self.dirty_regions: Set[pygame.Rect] = set()
        self.last_render_time = 0
        self.render_throttle = 1.0 / 60  # 60FPS制限
    
    def mark_dirty(self, rect: pygame.Rect) -> None:
        """描画更新領域マーク"""
        self.dirty_regions.add(rect)
    
    def render(self, surface: pygame.Surface) -> None:
        """最適化された描画"""
        current_time = time.time()
        if current_time - self.last_render_time < self.render_throttle:
            return  # FPS制限
        
        if not self.dirty_regions:
            return  # 更新不要
        
        # 差分描画実行
        for region in self.dirty_regions:
            self.render_region(surface, region)
        
        self.dirty_regions.clear()
        self.last_render_time = current_time
    
    def update_efficiently(self, time_delta: float) -> None:
        """効率的な更新処理"""
        # 表示中の要素のみ更新
        visible_elements = [e for e in self.ui_elements if e.visible]
        for element in visible_elements:
            element.update(time_delta)
```

### 4. エラーハンドリング

```python
class RobustWindow(Window):
    """堅牢なWindow実装例"""
    
    def create(self) -> None:
        """安全なUI作成"""
        try:
            self.create_ui_elements()
        except Exception as e:
            logger.error(f"UI作成エラー: {self.window_id}, {e}")
            self.create_fallback_ui()
    
    def create_fallback_ui(self) -> None:
        """フォールバックUI作成"""
        # 最小限のUI要素作成
        error_text = UIText(
            'error',
            'UI作成エラーが発生しました',
            position=(400, 300),
            color=(255, 0, 0)
        )
        self.ui_elements = [error_text]
    
    def handle_event(self, event: pygame.Event) -> bool:
        """安全なイベント処理"""
        try:
            return self.handle_event_impl(event)
        except Exception as e:
            logger.error(f"イベント処理エラー: {self.window_id}, {e}")
            return False
    
    def safe_close(self) -> None:
        """安全なWindow閉鎖"""
        try:
            self.cleanup_resources()
        except Exception as e:
            logger.error(f"リソースクリーンアップエラー: {e}")
        finally:
            super().close()
```

## テスト実装

### 1. Window単体テスト

```python
import pytest
from unittest.mock import Mock, patch
from src.ui.window_system.window_manager import WindowManager

class TestCustomWindow:
    """カスタムWindowテストクラス"""
    
    def test_window_creation(self):
        """Window作成テスト"""
        config = {'title': 'Test Window', 'items': ['Item1', 'Item2']}
        window = SimpleMenuWindow('test_window', config)
        
        assert window.window_id == 'test_window'
        assert window.menu_config == config
        assert window.state == WindowState.CREATED
    
    def test_window_ui_creation(self):
        """UI作成テスト"""
        config = {'title': 'Test', 'items': ['A', 'B']}
        window = SimpleMenuWindow('test', config)
        window.create()
        
        assert window.title_text is not None
        assert len(window.buttons) == 2
        assert len(window.ui_elements) == 3  # title + 2 buttons
    
    def test_keyboard_navigation(self):
        """キーボードナビゲーションテスト"""
        window = SimpleMenuWindow('test', {'items': ['A', 'B', 'C']})
        window.create()
        
        # 下キー押下
        down_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        assert window.handle_event(down_event) == True
        assert window.selected_index == 1
        
        # 上キー押下
        up_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        assert window.handle_event(up_event) == True
        assert window.selected_index == 0
    
    @patch('src.ui.window_system.window_manager.WindowManager.get_instance')
    def test_window_close(self, mock_manager):
        """Window閉鎖テスト"""
        manager_instance = Mock()
        mock_manager.return_value = manager_instance
        
        window = SimpleMenuWindow('test', {})
        escape_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        
        window.handle_event(escape_event)
        
        manager_instance.hide_window.assert_called_once_with(window)
        manager_instance.destroy_window.assert_called_once_with(window)
```

### 2. 統合テスト

```python
class TestWindowIntegration:
    """Window統合テストクラス"""
    
    def test_window_manager_integration(self):
        """WindowManager統合テスト"""
        manager = WindowManager.get_instance()
        
        # Window作成
        window = manager.create_window(
            SimpleMenuWindow,
            'integration_test',
            menu_config={'title': 'Test', 'items': ['A']}
        )
        
        assert window is not None
        assert manager.get_window('integration_test') == window
        
        # Window表示
        manager.show_window(window)
        assert window.state == WindowState.SHOWN
        assert window in manager.get_visible_windows()
        
        # Window破棄
        manager.destroy_window(window)
        assert manager.get_window('integration_test') is None
    
    def test_focus_management_integration(self):
        """フォーカス管理統合テスト"""
        manager = WindowManager.get_instance()
        
        window1 = manager.create_window(SimpleMenuWindow, 'window1', {})
        window2 = manager.create_window(SimpleMenuWindow, 'window2', {})
        
        manager.show_window(window1)
        manager.show_window(window2)
        
        # フォーカステスト
        assert manager.get_focused_window() == window2  # 最新が自動フォーカス
        
        manager.set_focus(window1)
        assert manager.get_focused_window() == window1
        
        # クリーンアップ
        manager.destroy_window(window1)
        manager.destroy_window(window2)
```

## 関連ドキュメント

- [WindowManager API リファレンス](../api/window_manager_api.md)
- [Window基底クラス API](../api/window_base_api.md)
- [UI要素実装ガイド](ui_elements_guide.md)
- [テスト戦略](../testing/testing_strategy.md)
- [パフォーマンス最適化ガイド](../performance/optimization_guide.md)

## 更新履歴

- **2.0 (2025-06-30)**: WindowSystem統一化完了版
  - UIMenu完全除去後の実装ガイド
  - WindowPool統合対応
  - パフォーマンス最適化例追加
  
- **1.9 (2025-06-29)**: 移行過渡期版
  - UIMenuとの並行運用対応
  
- **1.0 (2025-06-01)**: 初期版
  - 基本Window実装ガイド

---

**ドキュメント管理**:
- **作成者**: Claude Code
- **レビュー**: WindowSystemチーム
- **承認**: プロジェクトリーダー
- **次回更新**: 実装パターン追加時