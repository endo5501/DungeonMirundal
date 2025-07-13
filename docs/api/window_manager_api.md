# WindowManager API リファレンス

**バージョン**: 2.0 (WindowSystem統一化完了版)  
**最終更新**: 2025-06-30

## 概要

WindowManagerは、Dungeon RPGのWindowSystemの中核を成すAPIです。すべてのWindow作成、管理、破棄を担当し、統一されたUIアーキテクチャを提供します。

### 主要機能

- Window生命周期管理（作成・表示・非表示・破棄）
- WindowPool連携によるメモリ効率化
- 統計情報収集・パフォーマンス監視
- 階層管理・フォーカス制御

## WindowManager クラス

### 初期化

```python
class WindowManager:
    """WindowSystem の中央管理クラス"""
    
    def __init__(self):
        """WindowManager初期化
        
        自動的に以下のコンポーネントを初期化:
        - WindowStack: Window階層管理
        - FocusManager: フォーカス制御
        - EventRouter: イベント分配
        - StatisticsManager: 統計収集
        - WindowPool: メモリ効率化
        """
        pass
    
    @classmethod
    def get_instance(cls) -> 'WindowManager':
        """シングルトンインスタンス取得
        
        Returns:
            WindowManager: 唯一のWindowManagerインスタンス
            
        Example:
            >>> manager = WindowManager.get_instance()
            >>> window = manager.create_window(MenuWindow, "main_menu")
        """
        pass
```

### Window作成・管理

#### create_window()

```python
def create_window(self, window_class: Type[Window], 
                 window_id: str = None, **kwargs) -> Window:
    """新しいWindowを作成
    
    WindowPoolから再利用可能なWindowを取得するか、
    新規にWindowを作成します。
    
    Args:
        window_class (Type[Window]): 作成するWindowクラス
        window_id (str, optional): 一意のWindow識別子
                                  未指定時は自動生成
        **kwargs: Window固有の設定パラメータ
        
    Returns:
        Window: 作成されたWindowインスタンス
        
    Raises:
        WindowCreationError: Window作成失敗時
        DuplicateWindowIdError: ID重複時
        InvalidWindowClassError: 無効なWindowクラス指定時
        
    Example:
        >>> # 基本的な使用方法
        >>> window = manager.create_window(
        ...     MenuWindow, 
        ...     'main_menu',
        ...     menu_config={'title': 'Main Menu', 'items': ['Start', 'Quit']}
        ... )
        
        >>> # ダイアログWindow作成
        >>> dialog = manager.create_window(
        ...     DialogWindow,
        ...     'confirm_quit',
        ...     dialog_type=DialogType.YES_NO,
        ...     message='ゲームを終了しますか？',
        ...     callback=self.on_quit_confirmed
        ... )
        
        >>> # 施設WindowをPygame座標で作成
        >>> guild_window = manager.create_window(
        ...     FacilityMenuWindow,
        ...     'guild_main',
        ...     facility_type=FacilityType.GUILD,
        ...     position=(100, 50),
        ...     size=(600, 400)
        ... )
    """
    pass
```

#### show_window()

```python
def show_window(self, window: Window, push_to_stack: bool = True) -> None:
    """Windowを表示してスタックに追加
    
    Args:
        window (Window): 表示するWindow
        push_to_stack (bool): WindowStackにプッシュするか
                             デフォルト: True
        
    Raises:
        WindowNotFoundError: 指定Windowが存在しない
        WindowStateError: Window状態が表示不可
        
    Example:
        >>> window = manager.create_window(MenuWindow, "test_menu")
        >>> manager.show_window(window)  # 通常表示
        >>> manager.show_window(window, push_to_stack=False)  # スタック追加なし
    """
    pass
```

#### hide_window()

```python
def hide_window(self, window: Window, pop_from_stack: bool = True) -> None:
    """Windowを非表示にしてスタックから除去
    
    Args:
        window (Window): 非表示にするWindow
        pop_from_stack (bool): WindowStackからポップするか
                              デフォルト: True
        
    Example:
        >>> manager.hide_window(window)  # 非表示＋スタック除去
        >>> manager.hide_window(window, pop_from_stack=False)  # 非表示のみ
    """
    pass
```

#### destroy_window()

```python
def destroy_window(self, window: Window) -> None:
    """Windowを破棄
    
    WindowPoolに返却可能な場合は返却、
    そうでなければ完全削除。
    
    Args:
        window (Window): 破棄するWindow
        
    Raises:
        WindowNotFoundError: 指定Windowが存在しない
        
    Example:
        >>> manager.destroy_window(window)
        >>> # window は使用不可になります
    """
    pass
```

### Window検索・取得

#### get_window()

```python
def get_window(self, window_id: str) -> Optional[Window]:
    """Window IDでWindow取得
    
    O(1)ハッシュテーブル検索で高速取得。
    
    Args:
        window_id (str): Window識別子
        
    Returns:
        Optional[Window]: 見つかったWindow、存在しない場合はNone
        
    Example:
        >>> window = manager.get_window("main_menu")
        >>> if window:
        ...     print(f"Found window: {window.window_id}")
        ... else:
        ...     print("Window not found")
    """
    pass
```

#### get_all_windows()

```python
def get_all_windows(self) -> List[Window]:
    """すべてのWindowを取得
    
    Returns:
        List[Window]: 現在管理中の全Window
        
    Example:
        >>> all_windows = manager.get_all_windows()
        >>> print(f"Total windows: {len(all_windows)}")
        >>> for window in all_windows:
        ...     print(f"- {window.window_id}: {window.state}")
    """
    pass
```

#### get_visible_windows()

```python
def get_visible_windows(self) -> List[Window]:
    """表示中のWindowを取得
    
    Returns:
        List[Window]: 現在表示中のWindow（Z順序順）
        
    Example:
        >>> visible = manager.get_visible_windows()
        >>> if visible:
        ...     print(f"Top window: {visible[0].window_id}")
    """
    pass
```

### WindowStack操作

#### get_window_stack()

```python
def get_window_stack(self) -> WindowStack:
    """WindowStackインスタンス取得
    
    Returns:
        WindowStack: 現在のWindowStack
        
    Example:
        >>> stack = manager.get_window_stack()
        >>> top_window = stack.peek()
        >>> if top_window:
        ...     print(f"Current top: {top_window.window_id}")
    """
    pass
```

#### push_window()

```python
def push_window(self, window: Window) -> None:
    """WindowをスタックにプッシュT
    
    Args:
        window (Window): プッシュするWindow
        
    Example:
        >>> manager.push_window(window)  # 最前面に移動
    """
    pass
```

#### pop_window()

```python
def pop_window(self) -> Optional[Window]:
    """最上位Windowをポップ
    
    Returns:
        Optional[Window]: ポップされたWindow、空の場合はNone
        
    Example:
        >>> top_window = manager.pop_window()
        >>> if top_window:
        ...     print(f"Popped: {top_window.window_id}")
    """
    pass
```

### フォーカス管理

#### get_focus_manager()

```python
def get_focus_manager(self) -> FocusManager:
    """FocusManagerインスタンス取得
    
    Returns:
        FocusManager: フォーカス管理インスタンス
        
    Example:
        >>> focus_mgr = manager.get_focus_manager()
        >>> focused = focus_mgr.get_focused_window()
    """
    pass
```

#### set_focus()

```python
def set_focus(self, window: Optional[Window]) -> bool:
    """指定Windowにフォーカス設定
    
    Args:
        window (Optional[Window]): フォーカスするWindow
                                  Noneでフォーカス解除
    
    Returns:
        bool: フォーカス設定成功時True
        
    Example:
        >>> success = manager.set_focus(window)
        >>> if success:
        ...     print("Focus set successfully")
    """
    pass
```

#### get_focused_window()

```python
def get_focused_window(self) -> Optional[Window]:
    """現在フォーカス中のWindow取得
    
    Returns:
        Optional[Window]: フォーカス中のWindow
        
    Example:
        >>> focused = manager.get_focused_window()
        >>> if focused:
        ...     print(f"Focused: {focused.window_id}")
    """
    pass
```

### イベント処理

#### get_event_router()

```python
def get_event_router(self) -> EventRouter:
    """EventRouterインスタンス取得
    
    Returns:
        EventRouter: イベントルーティングインスタンス
        
    Example:
        >>> router = manager.get_event_router()
        >>> router.route_event(event, target_window)
    """
    pass
```

#### route_event()

```python
def route_event(self, event: pygame.event.Event, 
               target_window: Optional[Window] = None) -> bool:
    """イベントを適切なWindowにルーティング
    
    Args:
        event (pygame.event.Event): 処理するイベント
        target_window (Optional[Window]): 対象Window
                                        未指定時はフォーカス中Windowに配信
    
    Returns:
        bool: イベント処理成功時True
        
    Example:
        >>> # フォーカス中Windowに配信
        >>> handled = manager.route_event(event)
        
        >>> # 特定Windowに配信
        >>> handled = manager.route_event(event, specific_window)
    """
    pass
```

#### broadcast_message()

```python
def broadcast_message(self, message_type: str, data: Dict[str, Any]) -> None:
    """全Windowにメッセージブロードキャスト
    
    Args:
        message_type (str): メッセージ種別
        data (Dict[str, Any]): メッセージデータ
        
    Example:
        >>> # 言語変更通知
        >>> manager.broadcast_message("language_changed", {
        ...     "new_language": "japanese",
        ...     "old_language": "english"
        ... })
        
        >>> # システム設定変更通知
        >>> manager.broadcast_message("settings_updated", {
        ...     "category": "graphics",
        ...     "changes": {"fullscreen": True}
        ... })
    """
    pass
```

### 統計・監視

#### get_statistics_manager()

```python
def get_statistics_manager(self) -> StatisticsManager:
    """StatisticsManagerインスタンス取得
    
    Returns:
        StatisticsManager: 統計管理インスタンス
        
    Example:
        >>> stats_mgr = manager.get_statistics_manager()
        >>> stats = stats_mgr.get_statistics()
    """
    pass
```

#### get_statistics()

```python
def get_statistics(self) -> Dict[str, Any]:
    """WindowSystem統計情報取得
    
    Returns:
        Dict[str, Any]: 統計情報
            - window_count: 現在のWindow数
            - total_created: 総作成Window数
            - total_destroyed: 総破棄Window数
            - pool_stats: WindowPool統計
            - performance_metrics: 性能指標
        
    Example:
        >>> stats = manager.get_statistics()
        >>> print(f"Active windows: {stats['window_count']}")
        >>> print(f"Pool hit rate: {stats['pool_stats']['hit_rate']:.1%}")
    """
    pass
```

### WindowPool連携

#### get_window_pool()

```python
def get_window_pool(self) -> WindowPool:
    """WindowPoolインスタンス取得
    
    Returns:
        WindowPool: Window再利用プールインスタンス
        
    Example:
        >>> pool = manager.get_window_pool()
        >>> pool_stats = pool.get_pool_statistics()
    """
    pass
```

#### optimize_pools()

```python
def optimize_pools(self) -> None:
    """WindowPool最適化実行
    
    不要なプールエントリの削除や、
    メモリ使用量の最適化を実行。
    
    Example:
        >>> manager.optimize_pools()  # 定期的に実行推奨
    """
    pass
```

### システム制御

#### shutdown()

```python
def shutdown(self) -> None:
    """WindowManager終了処理
    
    すべてのWindowを適切に破棄し、
    リソースをクリーンアップ。
    
    Example:
        >>> manager.shutdown()  # ゲーム終了時に実行
    """
    pass
```

#### reset()

```python
def reset(self) -> None:
    """WindowManagerリセット
    
    すべてのWindowを破棄し、
    初期状態に戻す。
    
    Example:
        >>> manager.reset()  # 新規ゲーム開始時などに使用
    """
    pass
```

## 使用例

### 基本的な使用パターン

```python
# WindowManager取得
manager = WindowManager.get_instance()

# メインメニューWindow作成・表示
main_menu = manager.create_window(
    MenuWindow,
    "main_menu",
    menu_config={
        "title": "Dungeon RPG",
        "items": ["New Game", "Load Game", "Settings", "Quit"],
        "position": (400, 300)
    }
)
manager.show_window(main_menu)

# 設定ダイアログ表示
settings_dialog = manager.create_window(
    DialogWindow,
    "settings",
    dialog_type=DialogType.SETTINGS,
    parent_window=main_menu
)
manager.show_window(settings_dialog)

# フォーカス管理
manager.set_focus(settings_dialog)

# イベント処理
for event in pygame.event.get():
    handled = manager.route_event(event)
    if not handled:
        # WindowSystemで処理されなかった場合の処理
        pass
```

### 施設システム統合例

```python
# ギルドWindow作成
guild_window = manager.create_window(
    FacilityMenuWindow,
    "guild_main",
    facility_type=FacilityType.GUILD,
    facility_data=guild_data,
    size=(800, 600)
)

# サブWindowチェーン作成
character_creation = manager.create_window(
    CharacterCreationWindow,
    "char_creation",
    parent_window=guild_window
)

# Window階層管理
manager.show_window(guild_window)
manager.show_window(character_creation)  # 自動的に前面表示

# 階層的終了
manager.hide_window(character_creation)  # ギルドに戻る
manager.destroy_window(character_creation)  # メモリ解放
```

### パフォーマンス監視例

```python
# 統計情報取得
stats = manager.get_statistics()
print(f"Window数: {stats['window_count']}")
print(f"プール効率: {stats['pool_stats']['hit_rate']:.1%}")

# パフォーマンス問題検出
if stats['window_count'] > 20:
    print("警告: Window数が多すぎます")
    manager.optimize_pools()

if stats['pool_stats']['hit_rate'] < 0.3:
    print("情報: プール効率が低下しています")
```

## エラーハンドリング

### 標準例外

```python
# Window作成エラー
try:
    window = manager.create_window(MenuWindow, "test")
except WindowCreationError as e:
    print(f"Window作成失敗: {e}")
except DuplicateWindowIdError as e:
    print(f"ID重複エラー: {e}")
except InvalidWindowClassError as e:
    print(f"無効なWindowクラス: {e}")

# Window操作エラー
try:
    manager.show_window(window)
except WindowNotFoundError as e:
    print(f"Window未発見: {e}")
except WindowStateError as e:
    print(f"Window状態エラー: {e}")
```

### 推奨エラー処理パターン

```python
def safe_create_window(manager, window_class, window_id, **kwargs):
    """安全なWindow作成ヘルパー"""
    try:
        return manager.create_window(window_class, window_id, **kwargs)
    except (WindowCreationError, DuplicateWindowIdError) as e:
        logger.error(f"Window作成失敗: {window_id}, {e}")
        return None
    except Exception as e:
        logger.critical(f"予期しないエラー: {window_id}, {e}")
        return None

def safe_destroy_window(manager, window):
    """安全なWindow破棄ヘルパー"""
    if window is None:
        return
    
    try:
        manager.destroy_window(window)
    except WindowNotFoundError:
        pass  # 既に削除済み
    except Exception as e:
        logger.error(f"Window破棄エラー: {e}")
```

## パフォーマンス考慮事項

### 最適な使用方法

1. **Window再利用の活用**
   ```python
   # Good: 同じWindowクラスの再利用
   window = manager.create_window(DialogWindow, "confirm")
   manager.destroy_window(window)  # プールに返却
   window2 = manager.create_window(DialogWindow, "info")  # プールから再利用
   ```

2. **適切なWindow破棄**
   ```python
   # Good: 使用後は必ず破棄
   temp_window = manager.create_window(MenuWindow, "temp")
   # ... 使用 ...
   manager.destroy_window(temp_window)
   ```

3. **統計監視の活用**
   ```python
   # Good: 定期的な最適化
   if manager.get_statistics()['window_count'] > threshold:
       manager.optimize_pools()
   ```

### 避けるべきパターン

1. **過度なWindow作成**
   ```python
   # Bad: 大量Window作成
   for i in range(100):
       manager.create_window(MenuWindow, f"menu_{i}")
   ```

2. **Window破棄の忘れ**
   ```python
   # Bad: 破棄を忘れる
   temp_window = manager.create_window(MenuWindow, "temp")
   # manager.destroy_window(temp_window)  # <- 忘れやすい
   ```

## 関連クラス・API

- [Window基底クラス](window_base_api.md)
- [WindowStack API](window_stack_api.md)
- [FocusManager API](focus_manager_api.md)
- [EventRouter API](event_router_api.md)
- [StatisticsManager API](statistics_manager_api.md)
- [WindowPool API](window_pool_api.md)

## 更新履歴

- **2.0 (2025-06-30)**: WindowSystem統一化完了版
  - UIMenu完全除去後の最終API
  - WindowPool統合
  - パフォーマンス最適化完了
  
- **1.9 (2025-06-29)**: 移行過渡期版
  - UIMenuとの並行運用版
  
- **1.0 (2025-06-01)**: 初期版
  - 基本WindowManager機能

---

**ドキュメント管理**:

- **作成者**: Claude Code
- **レビュー**: WindowSystemチーム
- **承認**: プロジェクトリーダー
- **次回更新**: API変更時
