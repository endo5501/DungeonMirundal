"""キャラクターコンポーネントシステム基底クラス

Fowlerの「Replace Data Value with Object」と「Extract Class」パターンを適用し、
Characterクラスの複雑な責務をコンポーネントに分離。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from src.character.character import Character


class ComponentType(Enum):
    """コンポーネントタイプ"""
    EQUIPMENT = "equipment"
    INVENTORY = "inventory"
    SPELLBOOK = "spellbook"
    STATUS_EFFECTS = "status_effects"
    COMBAT_STATS = "combat_stats"
    PROFESSION = "profession"


@dataclass
class ComponentData:
    """コンポーネントデータの基底クラス"""
    component_type: ComponentType
    initialized: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式にシリアライズ"""
        return {
            'component_type': self.component_type.value,
            'initialized': self.initialized
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComponentData':
        """辞書からデシリアライズ"""
        return cls(
            component_type=ComponentType(data.get('component_type')),
            initialized=data.get('initialized', False)
        )


class CharacterComponent(ABC):
    """キャラクターコンポーネントの基底クラス
    
    Strategyパターンの要素も含み、キャラクターの特定の機能を
    独立したオブジェクトとして実装する。
    """
    
    def __init__(self, owner: 'Character', component_type: ComponentType):
        self.owner = owner
        self.component_type = component_type
        self.initialized = False
        self._data: Optional[ComponentData] = None
    
    @abstractmethod
    def initialize(self) -> bool:
        """コンポーネントを初期化"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """コンポーネントのクリーンアップ"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        pass
    
    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> bool:
        """辞書からデシリアライズ"""
        pass
    
    def get_data(self) -> Optional[ComponentData]:
        """コンポーネントデータを取得"""
        return self._data
    
    def set_data(self, data: ComponentData):
        """コンポーネントデータを設定"""
        self._data = data
        self.initialized = data.initialized
    
    def ensure_initialized(self) -> bool:
        """初期化されていることを確認"""
        if not self.initialized:
            return self.initialize()
        return True
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.component_type.value}, initialized={self.initialized})"


class ComponentManager:
    """キャラクターコンポーネントマネージャー
    
    複数のコンポーネントを統一的に管理し、Characterクラスの責務を軽減。
    """
    
    def __init__(self, character: 'Character'):
        self.character = character
        self._components: Dict[ComponentType, CharacterComponent] = {}
    
    def add_component(self, component: CharacterComponent) -> bool:
        """コンポーネントを追加"""
        if component.component_type in self._components:
            # 既存のコンポーネントをクリーンアップ
            self._components[component.component_type].cleanup()
        
        self._components[component.component_type] = component
        return True
    
    def get_component(self, component_type: ComponentType) -> Optional[CharacterComponent]:
        """コンポーネントを取得"""
        return self._components.get(component_type)
    
    def remove_component(self, component_type: ComponentType) -> bool:
        """コンポーネントを削除"""
        if component_type in self._components:
            self._components[component_type].cleanup()
            del self._components[component_type]
            return True
        return False
    
    def has_component(self, component_type: ComponentType) -> bool:
        """コンポーネントが存在するかチェック"""
        return component_type in self._components
    
    def ensure_component_initialized(self, component_type: ComponentType) -> bool:
        """コンポーネントが初期化されていることを確認"""
        component = self.get_component(component_type)
        if component:
            return component.ensure_initialized()
        return False
    
    def get_all_components(self) -> Dict[ComponentType, CharacterComponent]:
        """全コンポーネントを取得"""
        return self._components.copy()
    
    def initialize_all_components(self) -> bool:
        """全コンポーネントを初期化"""
        success = True
        for component in self._components.values():
            if not component.ensure_initialized():
                success = False
        return success
    
    def cleanup_all_components(self):
        """全コンポーネントをクリーンアップ"""
        for component in self._components.values():
            component.cleanup()
        self._components.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """全コンポーネントを辞書形式でシリアライズ"""
        components_data = {}
        for comp_type, component in self._components.items():
            components_data[comp_type.value] = component.to_dict()
        
        return {
            'components': components_data
        }
    
    def from_dict(self, data: Dict[str, Any]) -> bool:
        """辞書から全コンポーネントをデシリアライズ"""
        components_data = data.get('components', {})
        
        success = True
        for comp_type_str, comp_data in components_data.items():
            try:
                comp_type = ComponentType(comp_type_str)
                component = self.get_component(comp_type)
                
                if component:
                    if not component.from_dict(comp_data):
                        success = False
                else:
                    # コンポーネントが存在しない場合の処理
                    # 必要に応じてコンポーネントを動的作成
                    pass
                    
            except Exception as e:
                from src.utils.logger import logger
                logger.error(f"コンポーネントデシリアライズエラー: {comp_type_str}: {e}")
                success = False
        
        return success


# === ユーティリティ関数 ===

def create_component_manager(character: 'Character') -> ComponentManager:
    """コンポーネントマネージャーを作成"""
    return ComponentManager(character)


def ensure_component(character: 'Character', component_type: ComponentType) -> Optional[CharacterComponent]:
    """キャラクターに指定されたコンポーネントが存在することを確認"""
    if not hasattr(character, '_component_manager'):
        character._component_manager = create_component_manager(character)
    
    return character._component_manager.get_component(component_type)