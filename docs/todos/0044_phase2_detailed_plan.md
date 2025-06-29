# 0044 Phase 2: 中リスク削除 詳細実行計画

## 実行概要
WindowSystem移行完了後のPhase 2として、施設サブメニュー25箇所のUIMenu削除とMenuStackManager統合を実施。

## 移行対象詳細

### 1. Inn（宿屋）- 12箇所（最高複雑度）
**対象メニュー**: 
- 冒険準備メニュー: `adventure_prep_menu`
- アイテム管理: `new_item_mgmt_menu`, `character_item_menu`
- 魔法管理: `spell_mgmt_menu`, `prayer_mgmt_menu`, `character_spell_menu`, `character_prayer_menu`
- 装備管理: `party_equipment_menu`
- 高度魔法管理: `spell_equip_menu`, `character_spell_slot_detail`, `spell_user_selection`, `spell_slot_selection`

**複雑度**: 4階層のネストメニュー、コンテキスト管理、23回のshow_submenu呼び出し

### 2. MagicGuild（魔術協会）- 6箇所（中複雑度）
**対象メニュー**:
- 魔術書店: `spellbook_category_menu`
- 魔法習得: `available_spells_menu`
- サービス: `identification_menu`, `analysis_menu`
- キャラクター分析: `character_analysis_menu`, `spell_usage_menu`

### 3. Shop（商店）- 4箇所（中複雑度）
**対象メニュー**:
- カテゴリメニュー: 動的カテゴリベース
- 売却メニュー: `character_sell_menu`, `storage_sell_menu`
- 数量選択: `sell_quantity_menu`

### 4. Temple（教会）- 3箇所（低複雑度）
**対象メニュー**:
- 蘇生サービス: `resurrection_menu`
- 状態異常治療: `status_cure_menu`, `char_status_cure`

## Phase 2実装戦略

### Step 1: 新Window実装（2-3週間）
TDDアプローチで新しいWindow実装を作成

#### 1.1 基盤Windowクラス
```python
class FacilitySubWindow(Window):
    """施設サブメニュー専用基底クラス"""
    
    def __init__(self, window_id: str, facility_config: Dict[str, Any]):
        super().__init__(window_id)
        self.facility_config = facility_config
        self.parent_facility = facility_config.get('parent_facility')
        self.context_data = facility_config.get('context', {})
        
    def handle_back_navigation(self):
        """共通の戻り処理"""
        if self.parent_facility:
            self.parent_facility._show_main_menu()
        else:
            self.close()
```

#### 1.2 専用Windowクラス
```python
class InnServiceWindow(FacilitySubWindow):
    """宿屋サービス専用ウィンドウ"""
    # 冒険準備、アイテム管理、魔法管理、装備管理の統合
    
class ShopTransactionWindow(FacilitySubWindow):
    """商店取引専用ウィンドウ"""
    # 購入・売却・数量選択の統合
    
class MagicGuildServiceWindow(FacilitySubWindow):
    """魔術協会サービス専用ウィンドウ"""
    # 魔法習得・鑑定・分析の統合
    
class TempleServiceWindow(FacilitySubWindow):
    """神殿サービス専用ウィンドウ"""
    # 蘇生・治療サービスの統合

class ListWindow(Window):
    """リスト表示専用ウィンドウ（UISelectionList代替）"""
    # MenuStackManagerのリスト機能代替
```

### Step 2: 段階的移行（3-4週間）

#### 2.1 Temple移行（1週間）- 最低複雑度から開始
- 3箇所のUIMenuをTempleServiceWindowに統合
- 蘇生・治療サービスの単純なWindow化

#### 2.2 Shop移行（1週間）
- 4箇所のUIMenuをShopTransactionWindowに統合
- 購入・売却フローのWindow化

#### 2.3 MagicGuild移行（1週間）
- 6箇所のUIMenuをMagicGuildServiceWindowに統合
- 魔法関連サービスの統合Window化

#### 2.4 Inn移行（2週間）- 最高複雑度
- 12箇所のUIMenuをInnServiceWindowに統合
- 複雑なネスト構造の平坦化
- コンテキスト管理の新Window対応

### Step 3: MenuStackManager統合削除（1-2週間）

#### 3.1 DialogTemplate移行
```python
class WindowManagerDialogTemplate:
    """WindowManagerベースのダイアログテンプレート"""
    
    def __init__(self, window_manager: WindowManager):
        self.window_manager = window_manager
        
    def create_information_dialog(self, dialog_id: str, title: str, message: str):
        # DialogWindowベースの実装
        pass
```

#### 3.2 UISelectionList → ListWindow移行
- MenuStackManagerのリスト機能をListWindowに移行
- 選択リストの新Window実装

#### 3.3 MenuStackManager削除
- 全施設からMenuStackManager依存を除去
- WindowManagerへの完全統一

## 技術的実装詳細

### メニュー階層の平坦化戦略
```python
# 変更前: 4階層ネストメニュー
# Main → Adventure Prep → Character Selection → Spell Management → Slot Selection

# 変更後: タブベース統合ウィンドウ
class InnServiceWindow(FacilitySubWindow):
    def create(self):
        self.tab_container = TabContainer([
            ('preparation', '冒険準備'),
            ('items', 'アイテム管理'),
            ('magic', '魔法管理'),
            ('equipment', '装備管理')
        ])
        
        for tab_id, tab_name in self.tabs:
            self.create_tab_content(tab_id)
```

### コンテキスト管理の改善
```python
@dataclass
class FacilityContext:
    """施設コンテキスト管理"""
    current_party: Party
    selected_character: Optional[Character] = None
    selected_item: Optional[Item] = None
    service_type: str = ""
    navigation_history: List[str] = field(default_factory=list)
    
class FacilitySubWindow(Window):
    def __init__(self, window_id: str, context: FacilityContext):
        super().__init__(window_id)
        self.context = context
```

### UIMenu → Window移行パターン
```python
# UIMenuパターン（削除対象）
def _show_character_spell_menu(self, character):
    spell_menu = UIMenu("character_spell_menu", f"{character.name} - 魔術管理")
    spell_menu.add_menu_item("スロット設定", self._manage_spell_slots, character)
    self.show_submenu(spell_menu, {'character': character})

# Windowパターン（新実装）
def _show_character_spell_window(self, character):
    context = FacilityContext(
        current_party=self.current_party,
        selected_character=character,
        service_type='spell_management'
    )
    
    window = InnServiceWindow(f"inn_spell_{character.id}", context)
    window.set_initial_tab('magic')
    self.window_manager.show_window(window, push_to_stack=True)
```

## テスト戦略

### TDDアプローチ
```python
class TestPhase2Migration:
    """Phase 2移行のTDDテスト"""
    
    def test_temple_service_window_creation(self):
        """TempleServiceWindow作成テスト"""
        # Given: 神殿サービスコンテキスト
        # When: TempleServiceWindowを作成
        # Then: 適切なサービスオプションが表示される
        
    def test_complex_inn_menu_navigation(self):
        """Inn複雑メニューナビゲーションテスト"""
        # Given: キャラクター選択状態
        # When: 魔法管理タブに遷移
        # Then: キャラクター魔法設定が表示される
        
    def test_menustack_manager_removal(self):
        """MenuStackManager削除後の動作テスト"""
        # Given: MenuStackManager削除後
        # When: 施設メニューナビゲーション
        # Then: WindowManagerのみで正常動作する
```

## リスク軽減策

### 1. 段階的移行
- 複雑度の低い施設から開始（Temple → Shop → MagicGuild → Inn）
- 各段階でテスト・検証を実施

### 2. 並行稼働期間
- 新Window実装完了後、UIMenuと並行稼働
- フォールバック機能で安全性確保

### 3. ロールバック計画
- UIMenu削除前のコミットポイント保持
- 問題発生時の迅速な復旧手順

## 完了条件

### 機能完了条件
- [ ] 4つの新Window実装完了
- [ ] 25箇所のUIMenu削除完了
- [ ] MenuStackManager削除完了
- [ ] DialogTemplateのWindowManager移行完了

### 品質完了条件
- [ ] 全施設の機能動作確認
- [ ] 統合テスト通過
- [ ] パフォーマンス劣化なし
- [ ] ユーザビリティ維持

### スケジュール目標
- **全体期間**: 6-8週間
- **新Window実装**: 2-3週間
- **段階的移行**: 3-4週間
- **統合・検証**: 1-2週間

Phase 2完了により、施設システムの完全WindowSystem化とMenuStackManagerの除去を実現し、UIMenu段階的削除の中核部分を完了します。