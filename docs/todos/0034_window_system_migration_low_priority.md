# 0034: WindowSystem移行 - 低優先度作業

## 目的
高・中優先度移行完了後、施設・管理機能関連ファイルをUIMenuから新WindowSystemへ移行し、システムの完全統一化を実現する。

## 経緯
- 高・中優先度移行（0032, 0033）完了後の最終段階作業
- 施設システム・管理機能の新WindowSystem統一化
- UIMenuクラスの完全除去に向けた最終工程

## 対象ファイル（低優先度）

### 施設関連ファイル（5ファイル）

#### 1. src/overworld/facilities/guild.py → FacilityMenuWindow
**現状**: UIMenuベースのギルド施設
**移行先**: `src/ui/windows/facility_menu_window.py`使用

**移行作業**:
- `FacilityMenuWindow`への統一移行
- `FacilityMenuManager`, `FacilityMenuUIFactory`の活用
- t-wada式TDDで開発
- ギルド固有機能（冒険者登録、パーティ編成）の統合

#### 2. src/overworld/facilities/inn.py → FacilityMenuWindow  
**現状**: UIMenuベースの宿屋施設
**移行作業**:
- 宿泊、回復機能の`FacilityMenuWindow`統合
- t-wada式TDDで開発
- パーティ情報表示の統一化

#### 3. src/overworld/facilities/shop.py → FacilityMenuWindow
**現状**: UIMenuベースの商店施設  
**移行作業**:
- 売買システムの`FacilityMenuWindow`統合
- t-wada式TDDで開発
- アイテム一覧表示の統一化

#### 4. src/overworld/facilities/magic_guild.py → FacilityMenuWindow
**現状**: UIMenuベースの魔法ギルド施設
**移行作業**:
- 魔法習得システムの`FacilityMenuWindow`統合
- t-wada式TDDで開発
- 魔法スロット管理の統一化

#### 5. src/overworld/facilities/temple.py → FacilityMenuWindow
**現状**: UIMenuベースの神殿施設
**移行作業**:
- 復活・治療システムの`FacilityMenuWindow`統合
- t-wada式TDDで開発
- 祈祷システムの統一化

### 管理機能関連ファイル（6ファイル）

#### 6. src/overworld/overworld_manager_pygame.py
**現状**: UIMenuを使用したオーバーワールド管理
**移行作業**:
- WindowManagerとの統合
- t-wada式TDDで開発
- 施設間遷移の統一化
- Pygame依存部分の新WindowSystem対応

#### 7. src/overworld/overworld_manager.py  
**現状**: UIMenuを使用したオーバーワールド管理（基底）
**移行作業**:
- WindowManager統合による管理統一化
- t-wada式TDDで開発
- 施設管理の抽象化

#### 8. src/overworld/base_facility.py
**現状**: UIMenuを使用した施設基底クラス
**移行作業**:
- `FacilityMenuWindow`を使用する新基底クラスへの移行
- t-wada式TDDで開発
- 全施設の統一インターフェース確立

#### 9. src/ui/menu_stack_manager.py
**現状**: UIMenuスタック管理（レガシー）
**移行作業**:
- WindowStackへの完全移行
- t-wada式TDDで開発
- レガシー管理機能の除去

#### 10. 戦闘UI統合

* ./docs/todos/0039_battle_ui_integration_remaining.md

### 最終クリーンアップ対象

#### 10. src/ui/base_ui_pygame.py  
**現状**: UIMenuクラス定義元（366行目）
**移行作業**:
- UIMenuクラス定義の完全削除
- 関連メソッド（`add_element()`, `add_menu_item()`, `add_back_button()`）の削除
- 他の必要クラスの保持確認
- Fowler式リファクタリングを実施

#### 11. 高優先度作業で発生した残作業

* ./docs/todos/0035_window_system_legacy_cleanup.md
* ./docs/todos/0036_overworld_manager_code_cleanup.md 

#### 12. 中優先度作業で発生した残作業

* ./docs/todos/0040_adapter_removal_and_cleanup.md

#### 11. 全テストの確認修正
**現状**: 全テスト(uv run pytest)で多数のfaildが発生
**作業**: UIMenu関係テストの削除、テストを修正してpassdへ
参考: ./docs/todos/0037_window_system_test_stabilization.md

## 技術仕様

### 施設統一パターン
```python
# 変更前（各施設個別UIMenu）
class Guild(BaseFacility):
    def show_menu(self):
        menu = UIMenu("guild_menu", "冒険者ギルド")
        menu.add_element(...)

# 変更後（FacilityMenuWindow統一）
class Guild(BaseFacility):  
    def show_menu(self):
        window = WindowManager.instance.create_window(
            FacilityMenuWindow,
            facility_type="guild",
            window_id="guild_menu",
            title="冒険者ギルド"
        )
        WindowManager.instance.show_window(window)
```

### 管理機能統一パターン
```python
# 変更前（MenuStackManager使用）
class OverworldManager:
    def __init__(self):
        self.menu_stack = MenuStackManager()
    
    def handle_menu(self):
        self.menu_stack.push_menu(...)

# 変更後（WindowManager統一）
class OverworldManager:
    def __init__(self):
        self.window_manager = WindowManager.instance
    
    def handle_menu(self):
        self.window_manager.show_window(...)
```

## 特殊考慮事項

### 施設間データ共有
- パーティ情報の一元管理
- 所持金・アイテムの同期
- 施設利用履歴の統合

### レガシーコード除去
- UIMenu完全削除前の依存関係確認
- 他コンポーネントへの影響調査
- 段階的削除による安全性確保

### 互換性保持
- セーブデータ形式の維持
- 設定ファイルとの整合性
- API互換性の確保

## 依存関係・影響範囲

### 上流依存
- WindowManager, FocusManagerの完全安定化
- 高・中優先度移行（0032, 0033）の完了
- 新WindowSystemクラスの実装完了

### 下流影響
- ゲーム全体のUI統一化完成
- レガシーコードの完全除去
- 保守性・拡張性の大幅向上

### 横断的影響
- 全施設システムの動作変更
- テストケースの全面修正
- ドキュメント更新

## テスト要件

### 施設機能テスト
- 各施設の基本機能確認
- 施設間遷移の確認
- データ保存・読み込みの確認

### 統合テスト
- オーバーワールド全体の動作確認
- メモリ使用量の最適化確認
- パフォーマンス劣化なし確認

### レグレッションテスト
- 既存機能の完全動作確認
- セーブデータ互換性確認
- 設定システムの整合性確認

## 期待される効果

### システム統一化
- 単一WindowSystemによる一貫した操作
- フォーカス管理の完全解決
- メニュー階層の確実な管理

### 保守性向上
- レガシーコード完全除去
- シンプルな構造による保守容易性
- 新機能追加の高い効率性

### パフォーマンス向上
- 不要なコード除去による軽量化
- 統一管理による効率化
- メモリ使用量の最適化

## リスク・制約事項

### 技術的リスク
- 施設システム全体への影響
- セーブデータ互換性の問題
- 想定外の依存関係発覚

### 業務リスク
- 最終段階での重大バグ発生
- テスト工数の予想以上の増大
- リリーススケジュールへの影響

### 軽減策
- 段階的移行による影響分散
- 豊富なテストケース実施
- ロールバック計画の詳細化

## 作業スケジュール
- **期間**: 3-4週間以内
- **第1段階（1-2週間）**: 施設関連5ファイルの移行
- **第2段階（1-1.5週間）**: 管理機能4ファイルの移行  
- **第3段階（0.5-1週間）**: UIMenuクラス削除・最終クリーンアップ
- **マイルストーン**:
  - 週次での進捗確認
  - 段階毎の統合テスト実施

## 完了条件
- [ ] 施設関連5ファイルの完全移行
- [ ] 管理機能4ファイルの完全移行
- [ ] UIMenuクラスの完全削除
- [ ] レガシーコードの完全除去
- [ ] 全機能の動作確認完了
- [ ] レグレッションテスト通過
- [ ] パフォーマンス劣化なし確認
- [ ] ドキュメント更新完了

## プロジェクト完了時の成果
- UIMenuシステムの完全除去
- 単一WindowSystemによる統一UI
- 保守性・拡張性の大幅向上
- フォーカス管理問題の根絶
- レガシーコード完全クリーンアップ

## 関連ドキュメント
- `docs/todos/0031_change_window_system.md`: 調査結果
- `docs/todos/0032_window_system_migration_high_priority.md`: 高優先度移行
- `docs/todos/0033_window_system_migration_medium_priority.md`: 中優先度移行
- `docs/window_system.md`: WindowSystem設計書