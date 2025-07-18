# Phase 4: Pygame版OverworldManager WindowSystem移行計画

**ステータス**: ✅ **完了** (2025-06-29)

## 目標
実際に使用されている`overworld_manager_pygame.py`をWindowSystemに移行し、UIMenuへの依存を除去する。

## 完了報告
✅ **Phase 4の全ステップが正常に完了しました** (2025-06-29)

## 戦略: ハイブリッドアプローチ

既存のPygame版に段階的にWindowSystem機能を統合し、最終的にUIMenuを置き換える。

### ステップ1: WindowSystem統合の準備
**目標**: Pygame版にWindowManagerサポートを追加

#### 1.1 OverworldMainWindow統合
```python
# overworld_manager_pygame.py に追加
from src.ui.window_system.overworld_main_window import OverworldMainWindow

def _show_main_menu_window(self):
    """WindowSystemベースのメインメニュー表示"""
    try:
        menu_config = self._create_main_menu_config()
        self.main_window = OverworldMainWindow('overworld_main', menu_config)
        self.main_window.message_handler = self.handle_main_menu_message
        self.window_manager.show_window(self.main_window)
        return True
    except Exception as e:
        logger.warning(f"WindowSystem未対応、レガシーUIMenuを使用: {e}")
        self._create_main_menu()  # フォールバック
        return False
```

#### 1.2 デュアルモード実装
- レガシーUIMenu機能を保持
- WindowSystem機能を並行して実装
- 設定またはフラグでの切り替え機能

### ステップ2: メソッド統合
**目標**: 標準版で実装済みのWindowSystemメソッドをPygame版に移植

#### 2.1 設定作成メソッド移植
```python
def _create_main_menu_config(self):
    """標準版からの移植"""
    # overworld_manager.pyの実装をコピー
    
def _create_settings_menu_config(self):
    """標準版からの移植"""
    # overworld_manager.pyの実装をコピー
```

#### 2.2 メッセージハンドラー移植
```python
def handle_main_menu_message(self, message_type: str, data: dict) -> bool:
    """標準版からの移植"""
    # overworld_manager.pyの実装をコピー
```

### ステップ3: 段階的切り替え
**目標**: UIMenuからWindowSystemへの段階的移行

#### 3.1 メインメニュー移行
1. `_show_main_menu()`でWindowSystem版を試行
2. 失敗時はUIMenu版にフォールバック
3. テスト完了後、UIMenu版を削除

#### 3.2 設定メニュー移行
1. ESCキー処理でWindowSystem版を使用
2. MenuStackManagerからWindowManagerへの移行
3. フォールバック機構の削除

### ステップ4: 依存関係除去
**目標**: UIMenuとMenuStackManagerの完全除去

#### 4.1 MenuStackManager除去
```python
# 削除対象
self.menu_stack_manager = MenuStackManager(ui_manager)

# 置き換え
# WindowManagerの機能で代替
```

#### 4.2 UIMenuインポート除去
```python
# 削除対象
from src.ui.base_ui_pygame import UIMenu, UIButton, UIText

# 置き換え
# WindowSystemコンポーネントのみ使用
```

## 実装順序

### Phase 4.1: 基盤準備 (1週間)
1. Pygame版にWindowManagerサポート追加
2. 標準版からの設定作成メソッド移植
3. デュアルモード実装とテスト

### Phase 4.2: 主要機能移行 (2週間)
1. メインメニューのWindowSystem移行
2. 設定メニューのWindowSystem移行
3. セーブ・ロード機能の移行

### Phase 4.3: 依存除去 (1週間)
1. MenuStackManager除去
2. UIMenuフォールバック削除
3. 最終テストと統合確認

## リスク軽減策

### 後方互換性保持
- すべての段階でレガシー機能を保持
- 段階的な有効化によるリスク分散
- 詳細なテストスイート整備

### ロールバック計画
- 各ステップでのgit tagによる復旧点設定
- フィーチャーフラグによる機能切り替え
- 継続的テスト実行

## 成功指標

### 技術指標
- [x] WindowSystem版メニューの正常動作 ✅
- [x] UIMenuインポートの完全除去 ✅
- [x] MenuStackManager使用箇所の除去 ✅
- [x] すべてのテストの合格 ✅

### 機能指標
- [x] 既存の全機能が正常動作 ✅
- [x] パフォーマンスの維持または向上 ✅
- [x] ユーザーエクスペリエンスの維持 ✅

## 完了した作業

### Phase 4.1: 基盤準備 ✅
- [x] Pygame版にWindowManagerサポート追加
- [x] 標準版からの設定作成メソッド移植
- [x] デュアルモード実装とテスト

### Phase 4.2: 主要機能移行 ✅
- [x] メインメニューのWindowSystem移行
- [x] 設定メニューのWindowSystem移行
- [x] セーブ・ロード機能の移行

### Phase 4.3: 依存除去 ✅
- [x] MenuStackManager除去
- [x] UIMenuフォールバック削除
- [x] 最終テストと統合確認

### Phase 4.4: base_facility.py移行 ✅
- [x] base_facility.pyのWindowSystem完全移行
- [x] MenuStackManager依存関係の完全除去

### Phase 4.5: UIMenuクラス削除 ✅
- [x] UIDialogクラスの独立化
- [x] 全実装ファイルからのUIMenu参照除去
- [x] UIManagerの型ヒント修正
- [x] UIMenuクラス本体の削除

## 実績工数
- **Phase 4全体**: 1日で完了（効率的な段階的実施により予定より大幅短縮）

## 達成された成果
✅ **完全なWindowSystem統一**: 実際に使用されているPygame版OverworldManagerが安全かつ完全にWindowSystemに移行されました。

### 技術的成果
- UIMenuクラスの完全削除
- MenuStackManagerの除去
- WindowSystemベースの統一アーキテクチャ
- レガシーコードの完全除去

### 代替システム
- **OverworldMainWindow**: 地上部メニュー機能
- **FacilityMenuWindow**: 施設メニュー機能
- **DialogWindow**: ダイアログ機能