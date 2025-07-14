# 改善されたテストシステム利用ガイド

## 概要

`docs/todos/0092_improve_test.md` の改善提案を実装した、改善されたテストシステムの利用方法を説明します。

## 🏗️ 実装済み改善点

### 1. 手動テストの自動化

**実装内容**:
- `tests/manual/test_esc_fix.py` → `tests/ui/test_esc_behavior_integration.py`
- `tests/manual/test_facility_integration.py` → `tests/facilities/test_facility_system_integration.py`

**新機能**:
- pytest統合による自動実行
- CI/CDでの実行可能
- 詳細なアサーションとエラーレポート

### 2. 古いテストファイルの整理

**アーカイブ済みファイル**:
```bash
tests/archive/
├── test_raycast_debug.py
├── test_detailed_wall_logic.py  
├── test_dungeon_view_debug.py
└── test_background_display_fix.py
```

これらは特定のバグ修正目的のデバッグテストで、現在は不要と判断されました。

### 3. テストマークシステムの導入

**利用可能なマーク**:
- `@pytest.mark.integration`: 統合テスト（ゲーム起動が必要）
- `@pytest.mark.slow`: 実行時間が長いテスト
- `@pytest.mark.manual`: 手動で確認が必要なテスト
- `@pytest.mark.unit`: 単体テスト（依存関係なし）
- `@pytest.mark.ui`: UIコンポーネントのテスト
- `@pytest.mark.facility`: 施設システムのテスト

### 4. 共通フィクスチャの拡張

**新しいフィクスチャ**:
- `mock_character`: テスト用キャラクターモック
- `mock_party`: テスト用パーティモック
- `temp_config_file`: 一時的な設定ファイル
- `game_api_client`: ゲームAPIクライアント（統合テスト用）

## 🚀 使用方法

### テストの実行

```bash
# 全テスト実行
uv run pytest

# 単体テストのみ実行
uv run pytest -m unit

# 統合テストのみ実行（ゲーム起動が必要）
uv run pytest -m integration

# 施設システムテストのみ実行
uv run pytest -m facility

# 高速テストのみ実行（slowマークを除外）
uv run pytest -m "not slow"

# UIテストのみ実行
uv run pytest -m ui

# 特定のディレクトリのテスト実行
uv run pytest tests/facilities/

# 詳細ログ付きで実行
uv run pytest -v -s
```

### テストの作成例

#### 単体テスト

```python
import pytest

@pytest.mark.unit
class TestMyClass:
    def test_basic_functionality(self):
        # 依存関係のない単純なテスト
        assert True
```

#### 統合テスト

```python
import pytest

@pytest.mark.integration
@pytest.mark.ui
class TestUIIntegration:
    def test_ui_behavior(self, game_api_client):
        # ゲームAPIを使用したテスト
        hierarchy = game_api_client.get_ui_hierarchy()
        assert hierarchy is not None
```

#### 施設テスト

```python
import pytest

@pytest.mark.facility
class TestFacilityService:
    def test_service_registration(self, mock_party):
        # 施設サービスのテスト
        assert mock_party.name == "テストパーティ"
```

### モックフィクスチャの活用

```python
def test_character_operations(mock_character, mock_party):
    """モックを使用したテスト例"""
    # キャラクターがパーティに追加されることをテスト
    mock_party.members.append(mock_character)
    assert len(mock_party.members) == 1
    assert mock_party.members[0].name == "テストキャラクター"
```

### 設定ファイルを使用するテスト

```python
def test_config_loading(temp_config_file):
    """一時設定ファイルを使用したテスト"""
    from src.core.config_manager import ConfigManager
    config_manager = ConfigManager(str(temp_config_file))
    
    races = config_manager.get_character_races()
    assert 'human' in races
    assert races['human']['name'] == '人間'
```

## 📊 テスト戦略

### テストピラミッド

```
     /\     統合テスト (少数)
    /  \    - ESCキー動作テスト  
   /    \   - 施設システム統合テスト
  /______\  
 / 単体   \  単体テスト (多数)
/_________\  - キャラクター作成テスト
            - ステータス計算テスト
            - 設定管理テスト
```

### テスト種別の使い分け

| テスト種別 | 実行頻度 | 実行タイミング | 目的 |
|-----------|---------|---------------|------|
| 単体テスト | 毎回 | 開発中・CI | 基本機能の確認 |
| 統合テスト | 定期的 | CI・リリース前 | システム全体の動作確認 |
| 手動テスト | 必要時 | 重要な変更後 | 複雑なシナリオの確認 |

## 🔧 開発ワークフロー

### 新機能開発時

1. **TDDアプローチ**:
   ```bash
   # まず失敗するテストを作成
   uv run pytest tests/new_feature/test_my_feature.py::test_new_functionality
   
   # 機能を実装
   # ... コーディング ...
   
   # テストが通ることを確認
   uv run pytest tests/new_feature/test_my_feature.py::test_new_functionality
   ```

2. **統合テストで確認**:
   ```bash
   # 関連する統合テストを実行
   uv run pytest -m integration -k "my_feature"
   ```

### リファクタリング時

1. **既存テストの実行**:
   ```bash
   # 変更前にすべてのテストが通ることを確認
   uv run pytest
   ```

2. **リファクタリング実行**

3. **回帰テストの実行**:
   ```bash
   # リファクタリング後もテストが通ることを確認
   uv run pytest
   ```

## 🚨 注意事項

### 統合テストの実行

統合テストはゲームが起動している必要があります：

```bash
# ターミナル1: ゲーム起動
./scripts/start_game_for_debug.sh

# ターミナル2: 統合テスト実行
uv run pytest -m integration
```

### パフォーマンス考慮

- `@pytest.mark.slow` のついたテストは通常実行時に除外
- 統合テストは必要な場合のみ実行
- CIでは単体テストを優先実行

## 📝 今後の拡張予定

- [ ] E2Eテストフレームワークの導入
- [ ] パフォーマンステストの自動化
- [ ] ビジュアルリグレッションテストの導入
- [ ] テストカバレッジレポートの統合

---

**作成**: 2025年7月13日  
**対応課題**: docs/todos/0092_improve_test.md  
**関連ファイル**: 
- `tests/conftest.py` - 共通設定とフィクスチャ
- `tests/ui/test_esc_behavior_integration.py` - ESC動作統合テスト
- `tests/facilities/test_facility_system_integration.py` - 施設統合テスト