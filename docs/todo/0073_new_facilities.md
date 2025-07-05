# 施設システム全面再設計・実装計画

## 背景

以前のWindow System移行時にレガシー処理との互換性を保とうとした結果、以下の問題が発生：
- 5段階の複雑な退出処理チェーン
- メッセージの二重処理（`facility_exit_requested`が実際には処理されない）
- 責任の境界が曖昧な設計
- UI とロジックの密結合

今回はレガシー処理の互換性を考慮せず、クリーンな設計で全面的に再実装する。

## 設計方針

### 基本原則
1. **単一責任の原則**: 各クラスは一つの明確な責任のみ
2. **直接的な制御フロー**: メッセージチェーンを廃止し、直接メソッド呼び出し
3. **UIとロジックの完全分離**: ビジネスロジック層とプレゼンテーション層を分離
4. **設定駆動**: JSONによる施設構成の動的生成

### 削除対象（レガシーコード）
- `BaseFacility` の複雑なメッセージハンドリング
- `FacilityManager` の多層的なコールバック
- 各施設の `_show_main_menu()` 等のレガシーメニューシステム
- `facility_exit_requested` などの未使用メッセージ
- WindowManager経由の複雑な退出処理

## 新アーキテクチャ詳細設計

### 1. コアクラス構造

```
src/facilities/
├── core/
│   ├── facility_service.py          # ビジネスロジックインターフェース
│   ├── facility_controller.py       # 施設制御の中核
│   ├── service_result.py           # 統一結果型
│   └── facility_registry.py        # 施設登録・管理
├── services/
│   ├── guild/
│   │   ├── guild_service.py        # ギルドのビジネスロジック
│   │   ├── character_creation.py   # キャラ作成ロジック
│   │   └── party_formation.py      # パーティ編成ロジック
│   ├── inn/
│   │   ├── inn_service.py          # 宿屋のビジネスロジック
│   │   └── adventure_preparation.py # 冒険準備ロジック
│   └── ...（他施設）
├── ui/
│   ├── facility_window.py          # 統合施設ウィンドウ
│   ├── service_panel.py            # サービス表示パネル
│   ├── wizard_tab.py               # ウィザード型タブ
│   └── navigation_panel.py         # 共通ナビゲーション
└── config/
    └── facilities.json              # 施設設定ファイル
```

### 2. 施設サービスインターフェース

```python
# src/facilities/core/facility_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class MenuItem:
    """メニュー項目"""
    id: str
    label: str
    icon: Optional[str] = None
    enabled: bool = True
    service_type: str = "action"  # action, wizard, list

@dataclass
class ServiceResult:
    """サービス実行結果"""
    success: bool
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def ok(cls, message: str = "", data: Optional[Dict[str, Any]] = None):
        return cls(True, message, data)
    
    @classmethod
    def error(cls, message: str):
        return cls(False, message)

class FacilityService(ABC):
    """施設サービスの基底クラス"""
    
    def __init__(self, facility_id: str):
        self.facility_id = facility_id
        self.party: Optional[Party] = None
    
    @abstractmethod
    def get_menu_items(self) -> List[MenuItem]:
        """利用可能なメニュー項目を取得"""
        pass
    
    @abstractmethod
    def execute_action(self, action_id: str, params: Dict[str, Any]) -> ServiceResult:
        """アクションを実行"""
        pass
    
    @abstractmethod
    def can_execute(self, action_id: str) -> bool:
        """アクション実行可能かチェック"""
        pass
    
    def set_party(self, party: Party) -> None:
        """パーティを設定"""
        self.party = party
```

### 3. 施設コントローラー

```python
# src/facilities/core/facility_controller.py
from typing import Dict, Optional, Type
import logging

logger = logging.getLogger(__name__)

class FacilityController:
    """施設の統一制御クラス"""
    
    def __init__(self, facility_id: str, service_class: Type[FacilityService]):
        self.facility_id = facility_id
        self.service = service_class(facility_id)
        self.window: Optional[FacilityWindow] = None
        self.is_active = False
    
    def enter(self, party: Party) -> bool:
        """施設に入る"""
        if self.is_active:
            logger.warning(f"Already in facility: {self.facility_id}")
            return False
        
        # サービスにパーティを設定
        self.service.set_party(party)
        
        # ウィンドウを作成・表示
        self.window = FacilityWindow(self)
        self.window.show()
        
        self.is_active = True
        logger.info(f"Entered facility: {self.facility_id}")
        return True
    
    def exit(self) -> bool:
        """施設から出る - シンプルな直接処理"""
        if not self.is_active:
            return False
        
        # ウィンドウを閉じる
        if self.window:
            self.window.close()
            self.window = None
        
        self.is_active = False
        logger.info(f"Exited facility: {self.facility_id}")
        
        # 地上画面に直接戻る
        from src.ui.overworld_ui import OverworldUI
        OverworldUI.show_main_menu()
        return True
    
    def execute_service(self, action_id: str, params: Dict[str, Any]) -> ServiceResult:
        """サービスを実行"""
        if not self.is_active:
            return ServiceResult.error("Facility not active")
        
        if not self.service.can_execute(action_id):
            return ServiceResult.error("Action not available")
        
        # サービス実行
        result = self.service.execute_action(action_id, params)
        
        # UI更新
        if self.window and result.success:
            self.window.refresh_content()
        
        return result
```

### 4. 統合施設ウィンドウ

```python
# src/facilities/ui/facility_window.py
import pygame
import pygame_gui
from typing import Dict, Optional, List

class FacilityWindow:
    """施設の統合ウィンドウ"""
    
    def __init__(self, controller: FacilityController):
        self.controller = controller
        self.ui_manager = self._get_ui_manager()
        self.main_panel: Optional[pygame_gui.UIPanel] = None
        self.service_panels: Dict[str, ServicePanel] = {}
        self.current_service: Optional[str] = None
        self.navigation: Optional[NavigationPanel] = None
        
        self._create_ui()
    
    def _create_ui(self):
        """UI要素を作成"""
        # メインパネル
        self.main_panel = pygame_gui.UIPanel(
            relative_rect=pygame.Rect(50, 50, 900, 600),
            manager=self.ui_manager
        )
        
        # ナビゲーションパネル（上部タブ）
        self.navigation = NavigationPanel(
            parent=self.main_panel,
            menu_items=self.controller.service.get_menu_items(),
            on_select=self._on_service_selected
        )
        
        # 初期サービスを表示
        menu_items = self.controller.service.get_menu_items()
        if menu_items:
            self._show_service(menu_items[0].id)
    
    def _on_service_selected(self, service_id: str):
        """サービスが選択された時"""
        if service_id == "exit":
            self.controller.exit()
        else:
            self._show_service(service_id)
    
    def _show_service(self, service_id: str):
        """サービスを表示"""
        # 現在のサービスを隠す
        if self.current_service and self.current_service in self.service_panels:
            self.service_panels[self.current_service].hide()
        
        # 新しいサービスパネルを作成/表示
        if service_id not in self.service_panels:
            menu_item = self._get_menu_item(service_id)
            if menu_item:
                if menu_item.service_type == "wizard":
                    panel = WizardServicePanel(self.main_panel, self.controller, service_id)
                else:
                    panel = StandardServicePanel(self.main_panel, self.controller, service_id)
                self.service_panels[service_id] = panel
        
        if service_id in self.service_panels:
            self.service_panels[service_id].show()
            self.current_service = service_id
    
    def show(self):
        """ウィンドウを表示"""
        self.main_panel.show()
    
    def close(self):
        """ウィンドウを閉じる"""
        # すべてのUIを破棄
        if self.main_panel:
            self.main_panel.kill()
        self.service_panels.clear()
    
    def refresh_content(self):
        """コンテンツを更新"""
        if self.current_service and self.current_service in self.service_panels:
            self.service_panels[self.current_service].refresh()
```

### 5. ウィザード対応

```python
# src/facilities/ui/wizard_tab.py
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

@dataclass
class WizardStep:
    """ウィザードステップ"""
    id: str
    name: str
    validator: Optional[Callable[[Dict[str, Any]], bool]] = None

class WizardServicePanel(ServicePanel):
    """ウィザード型サービスパネル"""
    
    def __init__(self, parent, controller, service_id):
        super().__init__(parent, controller, service_id)
        self.wizard_data: Dict[str, Any] = {}
        self.steps: List[WizardStep] = self._get_wizard_steps()
        self.current_step_index = 0
        self.step_panels: Dict[str, pygame_gui.UIPanel] = {}
        
        self._create_wizard_ui()
    
    def _create_wizard_ui(self):
        """ウィザードUIを作成"""
        # ステップインジケーター（上部）
        self._create_step_indicator()
        
        # コンテンツエリア
        self.content_area = pygame_gui.UIPanel(
            relative_rect=pygame.Rect(10, 80, 880, 400),
            manager=self.ui_manager,
            container=self.container
        )
        
        # ナビゲーションボタン（下部）
        self._create_navigation_buttons()
        
        # 最初のステップを表示
        self._show_step(0)
    
    def _create_step_indicator(self):
        """ステップインジケーターを作成"""
        indicator_panel = pygame_gui.UIPanel(
            relative_rect=pygame.Rect(10, 10, 880, 60),
            manager=self.ui_manager,
            container=self.container
        )
        
        step_width = 880 // len(self.steps)
        for i, step in enumerate(self.steps):
            # ステップ状態に応じた表示
            if i < self.current_step_index:
                text = f"✓ {step.name}"
                color = "#28a745"  # 完了済み - 緑
            elif i == self.current_step_index:
                text = f"▶ {step.name}"
                color = "#007bff"  # 現在 - 青
            else:
                text = f"○ {step.name}"
                color = "#6c757d"  # 未完了 - グレー
            
            label = pygame_gui.UILabel(
                relative_rect=pygame.Rect(i * step_width, 0, step_width, 60),
                text=text,
                manager=self.ui_manager,
                container=indicator_panel
            )
    
    def next_step(self):
        """次のステップへ"""
        if self.current_step_index < len(self.steps) - 1:
            # 現在のステップを検証
            current_step = self.steps[self.current_step_index]
            if current_step.validator and not current_step.validator(self.wizard_data):
                self._show_validation_error()
                return
            
            # 次のステップへ
            self.current_step_index += 1
            self._show_step(self.current_step_index)
            self._update_navigation_buttons()
        else:
            # 最後のステップの場合は完了処理
            self._complete_wizard()
    
    def _complete_wizard(self):
        """ウィザード完了処理"""
        result = self.controller.execute_service(
            f"{self.service_id}_complete",
            self.wizard_data
        )
        
        if result.success:
            # 成功メッセージを表示して閉じる
            self._show_success_message(result.message)
            # メインサービス一覧に戻る
            self.controller.window.navigation.reset_to_main()
```

### 6. 具体的な施設実装例（ギルド）

```python
# src/facilities/services/guild/guild_service.py
from typing import List, Dict, Any
from src.facilities.core import FacilityService, MenuItem, ServiceResult

class GuildService(FacilityService):
    """ギルドのサービス実装"""
    
    def get_menu_items(self) -> List[MenuItem]:
        """ギルドのメニュー項目"""
        return [
            MenuItem(
                id="character_creation",
                label="キャラクター作成",
                icon="character_icon.png",
                service_type="wizard"
            ),
            MenuItem(
                id="party_formation", 
                label="パーティ編成",
                icon="party_icon.png",
                enabled=self.party is not None
            ),
            MenuItem(
                id="class_change",
                label="クラス変更", 
                icon="class_icon.png",
                enabled=self._has_eligible_characters()
            ),
            MenuItem(
                id="character_list",
                label="冒険者一覧",
                icon="list_icon.png",
                service_type="list"
            ),
            MenuItem(
                id="exit",
                label="ギルドを出る",
                icon="exit_icon.png"
            )
        ]
    
    def execute_action(self, action_id: str, params: Dict[str, Any]) -> ServiceResult:
        """アクションを実行"""
        if action_id == "character_creation_complete":
            return self._create_character(params)
        elif action_id == "party_formation":
            return self._manage_party_formation(params)
        elif action_id == "class_change":
            return self._change_character_class(params)
        elif action_id == "character_list":
            return self._show_character_list()
        else:
            return ServiceResult.error(f"Unknown action: {action_id}")
    
    def _create_character(self, char_data: Dict[str, Any]) -> ServiceResult:
        """キャラクターを作成"""
        try:
            # キャラクター作成ロジック
            from src.character.character import Character
            character = Character.create(
                name=char_data['name'],
                race=char_data['race'],
                character_class=char_data['class'],
                stats=char_data['stats']
            )
            
            # キャラクターを保存
            from src.character.character_manager import character_manager
            character_manager.add_character(character)
            
            return ServiceResult.ok(
                f"キャラクター「{character.name}」を作成しました",
                {"character": character}
            )
        except Exception as e:
            return ServiceResult.error(f"作成失敗: {str(e)}")
```

### 7. 施設設定ファイル

```json
// src/facilities/config/facilities.json
{
  "facilities": {
    "guild": {
      "id": "guild",
      "name": "冒険者ギルド",
      "service_class": "GuildService",
      "icon": "guild_icon.png",
      "welcome_message": "冒険者ギルドへようこそ！",
      "services": {
        "character_creation": {
          "type": "wizard",
          "steps": [
            {"id": "name", "label": "名前入力"},
            {"id": "race", "label": "種族選択"},
            {"id": "stats", "label": "能力値決定"},
            {"id": "class", "label": "職業選択"},
            {"id": "confirm", "label": "確認"}
          ]
        }
      }
    },
    "inn": {
      "id": "inn",
      "name": "宿屋",
      "service_class": "InnService",
      "icon": "inn_icon.png",
      "services": {
        "rest": {"type": "action", "cost": 10},
        "adventure_prep": {"type": "panel", "sub_services": ["items", "spells", "equipment"]}
      }
    }
  }
}
```

### 8. 施設レジストリ（グローバル管理）

```python
# src/facilities/core/facility_registry.py
from typing import Dict, Type, Optional
import json
import logging

logger = logging.getLogger(__name__)

class FacilityRegistry:
    """施設のグローバル登録・管理"""
    
    _instance = None
    
    def __init__(self):
        self.facilities: Dict[str, FacilityController] = {}
        self.service_classes: Dict[str, Type[FacilityService]] = {}
        self.config = self._load_config()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _load_config(self) -> Dict:
        """施設設定を読み込み"""
        with open("src/facilities/config/facilities.json", "r", encoding="utf-8") as f:
            return json.load(f)
    
    def register_service_class(self, facility_id: str, service_class: Type[FacilityService]):
        """サービスクラスを登録"""
        self.service_classes[facility_id] = service_class
    
    def enter_facility(self, facility_id: str, party: Party) -> bool:
        """施設に入る"""
        # 既存の施設から退出
        self.exit_current_facility()
        
        # 施設コントローラーを取得/作成
        if facility_id not in self.facilities:
            service_class = self.service_classes.get(facility_id)
            if not service_class:
                logger.error(f"Service class not found for: {facility_id}")
                return False
            
            self.facilities[facility_id] = FacilityController(facility_id, service_class)
        
        # 施設に入る
        return self.facilities[facility_id].enter(party)
    
    def exit_current_facility(self):
        """現在の施設から退出"""
        for facility in self.facilities.values():
            if facility.is_active:
                facility.exit()
                break

# グローバルインスタンス
facility_registry = FacilityRegistry.get_instance()
```

## 実装計画

### Phase 1: 基盤構築（5日間）

**Day 1-2: コア実装**
- [x] `FacilityService` 基底クラス
- [x] `ServiceResult` 統一結果型
- [x] `FacilityController` 制御クラス
- [x] `FacilityRegistry` グローバル管理

**Day 3-4: UI基盤**
- [x] `FacilityWindow` 統合ウィンドウ
- [x] `ServicePanel` 基底パネル
- [x] `NavigationPanel` ナビゲーション
- [x] `WizardServicePanel` ウィザード対応

**Day 5: 設定システム**
- [x] 施設設定JSONスキーマ定義
- [x] 設定ローダー実装
- [x] 動的UI生成システム

### Phase 2: ギルド実装（4日間）

**Day 6-7: ギルドサービス**
- [x] `GuildService` 実装
- [x] キャラクター作成ロジック分離
- [x] パーティ編成ロジック実装
- [x] クラス変更ロジック実装

**Day 8-9: ギルドUI統合**
- [x] キャラクター作成ウィザード（新設計）
- [x] パーティ編成パネル
- [x] 冒険者一覧表示
- [x] 統合テスト

### Phase 3: 他施設実装（8日間）

**Day 10-11: 宿屋**
- [x] `InnService` 実装
- [x] 休息・回復ロジック
- [x] 冒険準備統合パネル
- [x] アイテム/装備/魔法管理

**Day 12-13: 商店**
- [x] `ShopService` 実装
- [x] 売買ロジック分離
- [x] 商品リスト表示
- [x] 取引確認UI

**Day 14-15: 教会**
- [x] `TempleService` 実装
- [x] 治療・蘇生ロジック
- [x] サービス選択UI
- [x] 料金計算・表示

**Day 16-17: 魔法ギルド**
- [x] `MagicGuildService` 実装
- [x] 魔法学習ロジック
- [x] 鑑定サービス
- [x] 魔法分析UI

### Phase 4: 統合・移行（3日間）

**Day 18: レガシーコード削除** ✅ **完了**
- [x] 旧 `BaseFacility` 関連コード削除（936行）
- [x] 旧メニューシステム削除（facility_menu_*.py 全削除）
- [x] 未使用メッセージハンドラー削除
- [x] 旧UI要素の完全削除（約11,460行削除）
- [x] 削除対象レガシーファイル：
  - `src/overworld/base_facility.py`
  - `src/overworld/facilities/*.py` (guild.py, inn.py, shop.py, temple.py, magic_guild.py)
  - `src/overworld/facilities/*_handler.py`
  - `src/ui/window_system/facility_*.py`
  - `src/ui/window_system/*_service_window.py`
- [x] レガシーテストファイルをアーカイブに移動
- [x] 機能再現性確認完了（docs/phase4_legacy_functionality_migration_analysis.md）

**Day 19: 最終統合** 🔄 **進行中**
- [x] `OverworldManager` との統合（新施設システムに移行済み）
- [x] game_manager.pyで新システム使用に変更
- [ ] 地上画面からの施設入場処理の動作確認
- [ ] ESCキー/退出処理の統一確認
- [ ] セーブ/ロード対応確認
- [ ] 残存インポートエラー修正
- [ ] UIDialog呼び出しの新システム移行

**Day 20: 最終確認**
- [ ] 全施設の動作確認
- [ ] パフォーマンステスト
- [ ] メモリリーク確認
- [ ] ドキュメント更新

## 削除ファイル一覧

以下のファイルは新実装完了後に削除：

```
src/overworld/base_facility.py          # レガシー基底クラス
src/overworld/facilities/*.py           # 旧施設実装（新実装で置換後）
src/ui/window_system/facility_menu_window.py  # 旧メニューウィンドウ
src/ui/window_system/facility_sub_window.py   # 旧サブウィンドウ基底
src/ui/window_system/*_service_window.py      # 各種サービスウィンドウ
```

## 実装状況

### 完了した施設
1. **ギルド** (Phase 2): キャラクター作成、パーティ編成、クラス変更、冒険者一覧
2. **宿屋** (Phase 3 Day 10-11): 休息、冒険準備、保管、パーティ名変更
3. **商店** (Phase 3 Day 12-13): 購入、売却、鑑定
4. **教会** (Phase 3 Day 14-15): 治療、蘇生、状態回復、祝福、寄付
5. **魔法ギルド** (Phase 3 Day 16-17): 魔法学習、魔法鑑定、魔法分析、魔法研究

### 残りの作業
1. **Phase 4: 統合・移行** (Day 18-20): レガシーコード削除、最終統合、動作確認

## 成功指標

1. **コード削減**: 施設関連コード50%以上削減
2. **複雑度低減**: 施設退出が2ステップ以内で完了
3. **テスト容易性**: ビジネスロジックの単体テスト可能
4. **開発効率**: 新施設追加が1日で可能
5. **パフォーマンス**: 施設切り替え100ms以内

## リスクと対策

### リスク1: 大規模な変更による不具合
**対策**: 施設ごとに段階的に移行し、各段階で動作確認

### リスク2: 保存データの互換性
**対策**: セーブデータのマイグレーション処理を実装

### リスク3: UI/UXの大幅な変更
**対策**: 基本的な操作フローは維持しつつ内部実装のみ変更

## 備考

- ゲーム起動は行わないため、実装中の動作確認は単体テストで実施
- レガシーコードとの互換性は一切考慮しない
- 新設計は将来の拡張性を重視し、プラグイン的な施設追加を可能にする