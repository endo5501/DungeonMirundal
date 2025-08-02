---
priority: 2
tags: ["architecture", "refactoring", "type-safety", "design-patterns"]
description: "hasattr/getattr使用箇所をインターフェース設計で置き換え、型安全性を向上"
created_at: "2025-08-02T10:39:32Z"
started_at: 2025-08-02T10:54:40Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# インターフェース設計見直し

## 現状の問題

pyrightエラー修正で大量のhasattr/getattr使用によるランタイムチェックが導入されており、型安全性の根本的な解決になっていない。

### 影響範囲の詳細調査結果
- **戦闘関連**: battle_integration_manager.py（5箇所）- ✅ 完了
- **施設関連**: facilities/（150+箇所）- 宿屋、商店、神殿、ギルド等
- **UI関連**: ui/（200+箇所）- パネル管理、ライフサイクル、イベント処理
- **装備関連**: equipment/（15箇所）- アイテム特性、装備管理
- **ダンジョン関連**: dungeon/（15箇所）- セル情報、レベル管理
- **ゲームデータアクセス**: 全体（100+箇所）- パーティ、キャラクター、インベントリ

**総計**: 約400+箇所のhasattr/getattr使用が確認されており、現在の実装（戦闘関連のみ）では全体の1.3%しかカバーできていない。

## 目的

- Protocol/ABC（抽象基底クラス）を使用した型安全なインターフェース定義
- ランタイムチェックから静的型チェックへの移行
- 保守性と可読性の向上

## 実施内容

### Phase 1: 基盤Protocol定義 ✅ **完了**
- [x] **コアProtocol定義** (src/interfaces/core_protocols.py)
  - [x] Cleanupable Protocol の定義
  - [x] MessageSender/MessageReceiver Protocol の定義
  - [x] Renderable Protocol の定義
  - [x] Updatable Protocol の定義
  - [x] UIComponent, GameComponent, WindowComponent Protocol の定義

- [x] **戦闘関連Protocol定義** (src/interfaces/battle_protocols.py)
  - [x] BattleWindow Protocol の定義
  - [x] BattleManager Protocol の定義
  - [x] WindowMessageHandler Protocol の定義

- [x] **概念実証実装**
  - [x] BattleIntegrationManager でのProtocol適用実証
  - [x] BattleUIWindow でのProtocol実装
  - [x] Window.send_message での型安全化

### Phase 2: 包括的Protocol体系設計 🔄 **進行中**

#### 2.1 影響度分析とProtocol設計完了
**調査完了**: 全ゲーム領域（400+箇所）のhasattr/getattr使用パターンを特定

**設計済み領域別Protocol**:

1. **UIライフサイクルProtocol** (ui_lifecycle_protocols.py) - 優先度: HIGHEST
   - 対象: 200+箇所
   - UIDestructible, UIRefreshable, UIContainer
   - ServicePanel, NavigationPanel, UISelectable

2. **施設サービスProtocol** (facility_protocols.py) - 優先度: HIGH  
   - 対象: 150+箇所
   - FacilityService, GuildService, InnService, ShopService, TempleService

3. **ゲームデータアクセスProtocol** (game_data_protocols.py) - 優先度: HIGH
   - 対象: 100+箇所
   - PartyMember, PartyAccessible, InventoryAccessible, GameManagerAccessible

4. **装備システムProtocol** (equipment_protocols.py) - 優先度: MEDIUM
   - 対象: 15箇所
   - EquippableItem, ConsumableItem, EquipmentSlots, EquipmentManager

5. **ダンジョンシステムProtocol** (dungeon_protocols.py) - 優先度: MEDIUM
   - 対象: 15箇所  
   - DungeonCell, DungeonLevel, DungeonManager, TreasureSystem

#### 2.2 実装優先順位策定
1. **Week 1**: UIライフサイクル（200+箇所、最多影響）
2. **Week 2**: ゲームデータアクセス（100+箇所、核心機能）
3. **Week 3**: 施設サービス（150+箇所、高複雑度）
4. **Week 4**: 装備・ダンジョン（30箇所、特定領域）

### Phase 3: 今回のチケット範囲確定 ⚠️ **要決定**

**選択肢A**: 基盤実証のみ（現在完了分）
- 戦闘関連Protocol適用完了
- 概念実証として次チケットに引き継ぎ

**選択肢B**: 包括的Protocol体系実装
- 全5領域のProtocol実装  
- 400+箇所の段階的移行
- 本格的な型安全化実現

## 成果と進捗

### ✅ 達成済み成果（Phase 1完了）
- **Protocol基盤確立**: 型安全なインターフェース設計の基盤を構築
- **戦闘システム実証**: BattleIntegrationManagerで5箇所のhasattr/getattr を型安全化
- **pyrightエラー解決**: Protocol関連の型エラーを全て解決
- **IDEサポート改善**: 戦闘関連コードでの補完・リファクタリング機能向上

### 📊 影響度評価
- **現在カバー率**: 5/400+ = 1.3%（戦闘関連のみ）
- **次ステップ対象**: 395箇所のhasattr/getattr使用が残存
- **高優先領域**: UIライフサイクル（200+）、施設サービス（150+）、ゲームデータ（100+）

### 🔄 継続課題の整理
1. **包括的Protocol体系の実装**が必要
2. **次チケット** `250802-104527-eliminate-hasattr-getattr-pattern.md` で継続
3. **段階的移行戦略**により400+箇所を型安全化

## 技術的詳細

### 実装済みProtocol例
```python
# src/interfaces/core_protocols.py
class Cleanupable(Protocol):
    def cleanup(self) -> None: ...

class MessageSender(Protocol):
    def send_message(self, message_type: str, data: Dict[str, Any] = None) -> None: ...

# src/interfaces/battle_protocols.py
class BattleWindow(MessageSender, Cleanupable, Protocol):
    def cleanup_ui(self) -> None: ...

# 使用例 (BattleIntegrationManager)
def cleanup_battle_window(self):
    if self.current_battle_window:
        self.current_battle_window.cleanup()  # 型安全アクセス
```

### 設計済み次期Protocol概要
```python
# 今後実装予定の主要Protocol
class UIDestructible(Protocol):
    def kill(self) -> None: ...
    def destroy(self) -> None: ...

class FacilityService(Protocol):
    def set_controller(self, controller: Any) -> None: ...
    def execute_action(self, action: str, params: Dict[str, Any]) -> ServiceResult: ...

class PartyMember(Protocol):
    def is_alive(self) -> bool: ...
    def get_inventory(self) -> Optional[Inventory]: ...
```

## 参考資料
- [PEP 544 – Protocols](https://www.python.org/dev/peps/pep-0544/)
- [次チケット: hasattr/getattr パターンの排除](./250802-104527-eliminate-hasattr-getattr-pattern.md)
- 包括的hasattr/getattr使用状況分析（400+箇所特定済み）
