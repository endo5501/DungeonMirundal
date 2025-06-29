# メニューアーキテクチャ仕様書

~~このドキュメントは、ダンジョンRPGにおける統一されたメニューナビゲーションシステムの設計仕様を定義します。~~

**注意** ：このアーキテクチャは旧式です。 最新の仕組みについては @docs/window_system.md を参照してください

## 1. アーキテクチャ概要

### 1.1 設計思想
- **統一性**: 全施設で一貫したメニュー操作体験を提供
- **予測可能性**: ユーザーが直感的にナビゲーションできる構造
- **拡張性**: 新しい施設や機能を簡単に追加できる設計
- **保守性**: メニュー関連の不具合を体系的に防止・修正

### 1.2 主要コンポーネント
1. **MenuStackManager**: メニュー階層の管理
2. **DialogTemplate**: 標準化されたダイアログテンプレート
3. **NavigationHandler**: 戻る・ESCキー処理の統一
4. **FacilityMenuBase**: 施設メニューの基底クラス

## 2. MenuStackManager

### 2.1 責務
- メニュー階層のスタック管理
- 戻る処理の標準化
- ESCキー処理の統一
- メニュー遷移履歴の追跡

### 2.2 メニュー階層構造
```
地上マップ (OverworldMenu) [ROOT]
├── 冒険者ギルド (GuildMainMenu)
│   ├── キャラクター作成 (CharacterCreationFlow)
│   ├── パーティ編成 (PartyFormationMenu)
│   │   ├── 現在の編成確認 (PartyStatusDialog)
│   │   ├── 位置変更 (PositionChangeDialog)
│   │   └── キャラクター削除 (RemoveCharacterDialog)
│   └── キャラクター一覧 (CharacterListDialog)
├── 宿屋 (InnMainMenu)
│   ├── 冒険の準備 (AdventurePreparationMenu)
│   │   ├── アイテム整理 (ItemOrganizationMenu)
│   │   ├── 魔術スロット設定 (SpellSlotMenu)
│   │   └── 祈祷スロット設定 (PrayerSlotMenu)
│   ├── 旅の情報を聞く (TravelInfoDialog)
│   └── 酒場の噂話 (TavernRumorsDialog)
├── 商店 (ShopMainMenu)
├── 教会 (TempleMainMenu)
├── 魔術師ギルド (MagicGuildMainMenu)
└── 設定画面 (SettingsMenu) [ESC]
```

### 2.3 API設計
```python
class MenuStackManager:
    def push_menu(self, menu: UIMenu) -> None
    def pop_menu(self) -> Optional[UIMenu]
    def peek_current_menu(self) -> Optional[UIMenu]
    def back_to_previous(self) -> bool
    def back_to_root(self) -> bool
    def clear_stack(self) -> None
    def handle_escape_key(self) -> bool
```

## 3. DialogTemplate

### 3.1 標準ダイアログタイプ
1. **InformationDialog**: 情報表示 + [OK]ボタン
2. **ConfirmationDialog**: 確認 + [はい]/[いいえ]ボタン
3. **SelectionDialog**: 選択肢 + [選択]/[戻る]ボタン
4. **InputDialog**: 入力 + [確定]/[キャンセル]ボタン
5. **ErrorDialog**: エラー表示 + [OK]ボタン

### 3.2 必須要素
- **戻るボタン**: 全てのダイアログに統一された戻る手段を提供
- **タイトルバー**: 現在の位置を明示
- **ナビゲーションヒント**: ユーザーが次に何をすべきかを示す

### 3.3 ButtonTemplate
```python
class ButtonTemplate:
    OK = {"text": "OK", "action": "close_dialog"}
    CANCEL = {"text": "キャンセル", "action": "close_dialog"}
    BACK = {"text": "戻る", "action": "go_back"}
    YES = {"text": "はい", "action": "confirm_and_close"}
    NO = {"text": "いいえ", "action": "cancel_and_close"}
```

## 4. NavigationHandler

### 4.1 キー処理統一
- **ESCキー**: 常に一つ前のメニューレベルに戻る
- **Enterキー**: 現在選択中の項目を実行
- **方向キー**: メニュー項目間の移動

### 4.2 戻る処理フロー
```
1. 現在のダイアログを閉じる
2. MenuStackから前のメニューを取得
3. 前のメニューを表示（modal=Trueで）
4. 必要に応じてUIクリーンアップを実行
```

### 4.3 エラーハンドリング
- メニューが見つからない場合は最上位（地上マップ）に戻る
- UI要素の初期化エラー時は適切なエラーメッセージを表示
- スタックが空の場合は安全にメインメニューを表示

## 5. FacilityMenuBase

### 5.1 統一インターフェース
```python
class FacilityMenuBase(BaseFacility):
    def __init__(self):
        self.menu_stack_manager = MenuStackManager()
        self.dialog_template = DialogTemplate()
    
    def show_submenu(self, menu: UIMenu) -> None
    def show_dialog(self, dialog_type: str, **kwargs) -> None
    def handle_back_action(self) -> bool
    def cleanup_ui(self) -> None
```

### 5.2 メニュー表示標準フロー
```
1. 現在のメニューをスタックにプッシュ
2. 新しいメニューを作成・設定
3. UIManagerに追加（modal=True）
4. 表示完了をログ出力
```

### 5.3 ダイアログ表示標準フロー
```
1. テンプレートから適切なダイアログを作成
2. 必要なボタンを自動追加
3. メニュースタックに現在の状態を保存
4. モーダルダイアログとして表示
```

## 6. エラー状況別対応

### 6.1 メニューが応答しない場合
- MenuStackManagerのstatus確認
- UI要素の初期化状態確認
- 強制的なクリーンアップ＋メインメニュー復帰

### 6.2 ダイアログが閉じられない場合
- 明示的なダイアログID管理
- タイムアウト処理
- ESCキーによる強制クローズ

### 6.3 画面遷移が途中で止まる場合
- 前の状態への自動復帰機能
- ログベースのデバッグ情報
- ユーザーへの適切なフィードバック

## 7. 実装方針

### 7.1 Phase 1: 基盤クラス作成
- MenuStackManager実装
- DialogTemplate実装
- NavigationHandler実装

### 7.2 Phase 2: BaseFacility統合
- 既存BaseFacilityに新システム統合
- 後方互換性の確保
- テスト用の簡単な施設で動作確認

### 7.3 Phase 3: 全施設対応
- 宿屋から順次新システムに移行
- 各施設の個別実装を標準テンプレートに置換
- 不具合の逐次修正

### 7.4 Phase 4: テスト・最適化
- 全不具合項目の動作確認
- パフォーマンステスト
- ユーザビリティ改善

## 8. 期待効果

### 8.1 不具合解決
- 全ての既知メニューナビゲーション不具合の解決
- 新機能追加時の不具合予防
- 保守性の向上

### 8.2 ユーザーエクスペリエンス向上
- 一貫した操作体験
- 直感的なナビゲーション
- エラー時の適切なフィードバック

### 8.3 開発効率向上
- 新施設追加の簡素化
- メニュー関連のコード重複削除
- デバッグの効率化