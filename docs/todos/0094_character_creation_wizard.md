# CharacterCreationWizard UIElementManager移行計画

## 概要

CharacterCreationWizardは600行以上の複雑なウィザード形式のパネルで、既にWizardServicePanelを継承しているが、UIElementManager統合が未完了。Phase 5での対応を予定。

## 現在の状況

### ✅ 完了済み
- **WizardServicePanel継承**: 既に適切なベースクラスを使用
- **ウィザードステップ管理**: 5段階のステップフロー実装済み
- **基本アーキテクチャ**: ステップベースのUI構造確立

### ❌ 未対応（要移行）
- **UIElementManager統合**: 直接pygame_gui要素作成を使用
- **フォールバック機能**: UIElementManager障害時の対応なし
- **要素ID管理**: 統一された要素識別システム未適用

## 📋 移行作業計画

### Phase 5-A: 分析・設計 (1-2時間)

#### 1. コード構造分析
```bash
# ファイル構造確認
wc -l src/facilities/ui/guild/character_creation_wizard.py
grep -n "pygame_gui.elements" src/facilities/ui/guild/character_creation_wizard.py | wc -l

# UI要素の種類と数量調査
grep -E "(UIButton|UILabel|UITextEntryLine|UISelectionList|UIDropDownMenu)" \
  src/facilities/ui/guild/character_creation_wizard.py
```

#### 2. ステップ別UI要素マッピング
| ステップ | 推定UI要素数 | 主要要素タイプ |
|----------|--------------|----------------|
| name | 2-3 | UITextEntryLine, UILabel |
| race | 10+ | UIButton（種族ボタン群） |
| stats | 15+ | UILabel（ステータス表示） |
| class | 10+ | UIButton（職業ボタン群） |
| confirm | 5+ | UILabel（確認表示） |

#### 3. 移行優先度設定
1. **高優先度**: name, confirmステップ（シンプル）
2. **中優先度**: raceステップ（ボタン群）
3. **低優先度**: stats, classステップ（複雑なロジック）

### Phase 5-B: 段階的移行 (3-4時間)

#### ステップ1: 基盤準備
```python
def _create_step_content(self, step: WizardStep, panel: pygame_gui.elements.UIPanel) -> None:
    """ステップ固有のコンテンツを作成"""
    if step.id == "name":
        self._create_name_input_content_managed(panel)  # UIElementManager版
    elif step.id == "race":
        self._create_race_selection_content_managed(panel)  # UIElementManager版
    # ... 他のステップ
```

#### ステップ2: 名前入力ステップ移行
```python
def _create_name_input_content_managed(self, panel: pygame_gui.elements.UIPanel) -> None:
    """名前入力コンテンツを作成（UIElementManager版）"""
    input_rect = pygame.Rect(10, 60, 300, 40)
    
    if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
        self.name_input = self.ui_element_manager.create_text_entry(
            "character_name_input", "", input_rect, placeholder_text="キャラクター名を入力"
        )
    else:
        # フォールバック: 既存実装
        self.name_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=input_rect,
            manager=self.ui_manager,
            container=panel,
            placeholder_text="キャラクター名を入力",
            object_id="#character_name_input"
        )
        self.ui_elements.append(self.name_input)
```

#### ステップ3: ボタン群ステップ移行
```python
def _create_race_selection_content_managed(self, panel: pygame_gui.elements.UIPanel) -> None:
    """種族選択コンテンツを作成（UIElementManager版）"""
    races = ["human", "elf", "dwarf", "gnome", "hobbit"]
    
    for i, race in enumerate(races):
        x = 50 + (i % 3) * 120
        y = 100 + (i // 3) * 60
        button_rect = pygame.Rect(x, y, 100, 50)
        
        button_id = f"race_button_{race}"
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            button = self.ui_element_manager.create_button(
                button_id, race.capitalize(), button_rect
            )
        else:
            # フォールバック
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=race.capitalize(),
                manager=self.ui_manager,
                container=panel,
                object_id=f"#{button_id}"
            )
            self.ui_elements.append(button)
        
        self.race_buttons[race] = button
```

### Phase 5-C: テスト更新 (1-2時間)

#### 既存テスト分析
```bash
# テストファイル確認
find tests -name "*character_creation*" -type f
grep -r "CharacterCreationWizard" tests/
```

#### テスト更新方針
1. **UIElementManager機能テスト**: 要素作成・破棄
2. **フォールバックテスト**: UIElementManager無効時の動作
3. **ステップ遷移テスト**: ウィザードフロー維持確認
4. **イベント処理テスト**: ボタンクリック・入力処理

## ⚠️ 重要な注意事項

### 1. ウィザードステップの複雑性
```python
# 現在のステップ管理構造を破損させないよう注意
def _load_wizard_steps(self) -> None:
    # 既存のsteps配列を保持
    if self.steps:  # 重複初期化防止
        return
```

### 2. 動的UI要素の管理
```python
# race_buttons, class_buttons等の辞書構造を維持
self.race_buttons: Dict[str, pygame_gui.elements.UIButton] = {}
self.class_buttons: Dict[str, pygame_gui.elements.UIButton] = {}
```

### 3. ステップ間データ保持
```python
# ウィザードのstate管理を破損させない
self.character_data: Dict[str, Any] = {}  # ステップ間でのデータ保持
```

### 4. WizardServicePanelとの互換性
```python
# 親クラスのメソッドを適切にオーバーライド
def _create_step_content(self, step: WizardStep, panel: pygame_gui.elements.UIPanel) -> None:
    """親クラスの抽象メソッドを実装"""
    # UIElementManager統合版の実装
```

## 🧪 テスト戦略

### 1. 段階的テスト
```python
class TestCharacterCreationWizardMigration:
    """移行段階でのテスト"""
    
    def test_uielement_manager_integration(self):
        """UIElementManager統合テスト"""
        # UIElementManager有効時の動作確認
        
    def test_fallback_functionality(self):
        """フォールバック機能テスト"""
        # UIElementManager無効時の動作確認
        
    def test_wizard_step_progression(self):
        """ウィザードステップ進行テスト"""
        # 既存のステップフローが正常動作することを確認
```

### 2. 回帰テスト
```python
def test_character_creation_complete_flow(self):
    """キャラクター作成完全フローテスト"""
    # 既存機能が全て動作することを確認
    # name -> race -> stats -> class -> confirm -> 作成完了
```

## 📈 期待される効果

### 1. 保守性向上
- **統一されたUI管理**: 他パネルと同じUIElementManagerパターン
- **デバッグ支援**: 要素ID によるトレーサビリティ
- **エラー処理**: 安全な要素作成・破棄

### 2. 開発効率向上
- **一貫性**: 全パネルで統一されたAPI使用
- **再利用性**: UIElementManagerの機能フル活用
- **拡張性**: 新機能追加時の実装容易化

### 3. 品質向上
- **フォールバック機能**: UIElementManager障害時の安定動作
- **メモリ管理**: 適切な要素ライフサイクル管理
- **テストカバレッジ**: 包括的なテスト実装

## 🚀 実装推奨順序

### 第1段階: 準備・分析
1. **現状分析**: UI要素数・種類の詳細調査
2. **要素ID設計**: 統一された命名規則策定
3. **テスト計画**: 既存機能の回帰テスト設計

### 第2段階: 基盤実装
1. **フォールバック基盤**: UIElementManager統合パターン確立
2. **要素作成ヘルパー**: 共通UI要素作成メソッド実装
3. **基本テスト**: UIElementManager統合テスト実装

### 第3段階: ステップ別移行
1. **nameステップ**: 最もシンプルなステップから開始
2. **confirmステップ**: 表示のみのステップで検証
3. **race/classステップ**: ボタン群の複雑なステップ
4. **statsステップ**: 最も複雑なロジックを持つステップ

### 第4段階: 完成・検証
1. **統合テスト**: 全ステップでの動作確認
2. **回帰テスト**: 既存機能の完全動作確認
3. **パフォーマンステスト**: メモリ・レスポンス時間確認

## 📚 参考情報

### 成功例
- **NavigationPanel**: 初期化順序の重要性
- **ItemDetailPanel**: 表示専用パネルのシンプルな移行
- **SpellAnalysisPanel**: 複雑な双方向パネルの移行成功例

### 技術的参考
- **ServicePanel**: `src/facilities/ui/service_panel.py`
- **WizardServicePanel**: `src/facilities/ui/wizard_service_panel.py`
- **UIElementManager**: `src/ui/ui_element_manager.py`

### テスト参考
- **NavigationPanel**: `tests/facilities/test_navigation_panel.py`
- **ItemDetailPanel**: `tests/facilities/test_item_detail_panel.py`
- **SpellAnalysisPanel**: `tests/facilities/test_spell_analysis_panel.py`

---

**作成日**: 2025年7月19日  
**対象**: Phase 5 開発チーム  
**優先度**: Medium  
**推定工数**: 6-8時間  
**前提条件**: Phase 4-B完了（ServicePanel + UIElementManager基盤）