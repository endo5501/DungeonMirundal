"""
インターフェース定義モジュール

このモジュールでは、型安全性を向上させるためのProtocolベースの
インターフェース定義を提供します。
"""

from .core_protocols import (
    Cleanupable,
    MessageSender,
    MessageReceiver,
    Renderable,
    Updatable,
)

from .battle_protocols import (
    BattleWindow,
    BattleManager,
    WindowMessageHandler,
)

from .ui_lifecycle_protocols import (
    UIDestructible,
    UIContainer,
    UIRefreshable,
    UISelectable,
    ServicePanel,
    NavigationPanel,
    ManagedUIElement,
    InteractiveUIElement,
    UIElementContainer,
)

from .facility_protocols import (
    FacilityController,
    FacilityService,
    StorageService,
    GuildService,
    InnService,
    ShopService,
    TempleService,
    FullServiceFacility,
    TradingFacility,
    HealingFacility,
)

from .game_data_protocols import (
    PartyAccessible,
    GameManagerAccessible,
    InventoryAccessible,
    CharacterDataAccessible,
    PartyMember,
    SaveableData,
    PersistentGameManager,
    FullGameDataAccess,
    PartyManagement,
)

from .equipment_protocols import (
    EquippableItem,
    ConsumableItem,
    EnchantableItem,
    ItemContainer,
    EquipmentSlots,
    EquipmentManager,
    WeaponItem,
    ArmorItem,
    MagicalItem,
)

from .dungeon_protocols import (
    DungeonCell,
    DungeonLevel,
    DungeonManager,
    TreasureSystem,
    MonsterEncounter,
    DungeonNavigation,
    DungeonRenderer,
    CompleteDungeonSystem,
    InteractiveDungeonCell,
)

__all__ = [
    # Core protocols
    "Cleanupable",
    "MessageSender", 
    "MessageReceiver",
    "Renderable",
    "Updatable",
    
    # Battle protocols
    "BattleWindow",
    "BattleManager",
    "WindowMessageHandler",
    
    # UI lifecycle protocols
    "UIDestructible",
    "UIContainer", 
    "UIRefreshable",
    "UISelectable",
    "ServicePanel",
    "NavigationPanel",
    "ManagedUIElement",
    "InteractiveUIElement",
    "UIElementContainer",
    
    # Facility protocols
    "FacilityController",
    "FacilityService",
    "StorageService",
    "GuildService",
    "InnService",
    "ShopService",
    "TempleService",
    "FullServiceFacility",
    "TradingFacility",
    "HealingFacility",
    
    # Game data protocols
    "PartyAccessible",
    "GameManagerAccessible",
    "InventoryAccessible",
    "CharacterDataAccessible",
    "PartyMember",
    "SaveableData",
    "PersistentGameManager",
    "FullGameDataAccess",
    "PartyManagement",
    
    # Equipment protocols
    "EquippableItem",
    "ConsumableItem",
    "EnchantableItem",
    "ItemContainer",
    "EquipmentSlots",
    "EquipmentManager",
    "WeaponItem",
    "ArmorItem",
    "MagicalItem",
    
    # Dungeon protocols
    "DungeonCell",
    "DungeonLevel",
    "DungeonManager",
    "TreasureSystem",
    "MonsterEncounter",
    "DungeonNavigation",
    "DungeonRenderer",
    "CompleteDungeonSystem",
    "InteractiveDungeonCell",
]