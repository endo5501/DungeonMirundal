"""状態異常コンポーネント

キャラクターの状態異常管理機能を独立したコンポーネントとして実装。
Fowlerの「Extract Class」パターンを適用。
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from src.character.components.base_component import CharacterComponent, ComponentType, ComponentData
from src.utils.logger import logger


class StatusEffectType(Enum):
    """状態異常タイプ"""
    # 有益な効果
    BLESSED = "blessed"         # 祝福
    HASTE = "haste"            # 加速
    STRENGTH_UP = "strength_up" # 筋力強化
    PROTECTION = "protection"   # 防護
    REGENERATION = "regen"     # 再生
    
    # 有害な効果
    POISONED = "poisoned"      # 毒
    PARALYZED = "paralyzed"    # 麻痺
    CONFUSED = "confused"      # 混乱
    CURSED = "cursed"          # 呪い
    WEAKENED = "weakened"      # 弱体化
    BLEEDING = "bleeding"      # 出血
    
    # 特殊状態
    UNCONSCIOUS = "unconscious" # 意識不明
    PETRIFIED = "petrified"    # 石化
    CHARMED = "charmed"        # 魅了
    FEARED = "feared"          # 恐怖


@dataclass
class StatusEffect:
    """状態異常効果"""
    effect_type: StatusEffectType
    name: str
    description: str
    duration: int = -1  # -1は永続、0以上はターン数
    intensity: int = 1  # 効果の強度
    source: str = "unknown"  # 効果の発生源
    applied_at: Optional[str] = None
    
    def is_permanent(self) -> bool:
        """永続効果かどうか"""
        return self.duration == -1
    
    def is_expired(self) -> bool:
        """効果が切れているかどうか"""
        return self.duration == 0
    
    def tick(self) -> bool:
        """ターン経過処理。効果が切れた場合Trueを返す"""
        if self.duration > 0:
            self.duration -= 1
        return self.is_expired()
    
    def is_beneficial(self) -> bool:
        """有益な効果かどうか"""
        beneficial_effects = {
            StatusEffectType.BLESSED,
            StatusEffectType.HASTE,
            StatusEffectType.STRENGTH_UP,
            StatusEffectType.PROTECTION,
            StatusEffectType.REGENERATION
        }
        return self.effect_type in beneficial_effects
    
    def is_harmful(self) -> bool:
        """有害な効果かどうか"""
        return not self.is_beneficial()


@dataclass
class StatusEffectsData(ComponentData):
    """状態異常データ"""
    active_effects: Dict[str, StatusEffect] = field(default_factory=dict)
    effect_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        self.component_type = ComponentType.STATUS_EFFECTS
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            'active_effects': {
                effect_id: {
                    'effect_type': effect.effect_type.value,
                    'name': effect.name,
                    'description': effect.description,
                    'duration': effect.duration,
                    'intensity': effect.intensity,
                    'source': effect.source,
                    'applied_at': effect.applied_at
                }
                for effect_id, effect in self.active_effects.items()
            },
            'effect_history': self.effect_history
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatusEffectsData':
        active_effects = {}
        effects_data = data.get('active_effects', {})
        
        for effect_id, effect_data in effects_data.items():
            active_effects[effect_id] = StatusEffect(
                effect_type=StatusEffectType(effect_data.get('effect_type')),
                name=effect_data.get('name', ''),
                description=effect_data.get('description', ''),
                duration=effect_data.get('duration', -1),
                intensity=effect_data.get('intensity', 1),
                source=effect_data.get('source', 'unknown'),
                applied_at=effect_data.get('applied_at')
            )
        
        return cls(
            component_type=ComponentType.STATUS_EFFECTS,
            initialized=data.get('initialized', False),
            active_effects=active_effects,
            effect_history=data.get('effect_history', [])
        )


class StatusEffectsComponent(CharacterComponent):
    """状態異常管理コンポーネント"""
    
    def __init__(self, owner):
        super().__init__(owner, ComponentType.STATUS_EFFECTS)
        self._status_data: Optional[StatusEffectsData] = None
    
    def initialize(self) -> bool:
        """状態異常システムを初期化"""
        try:
            if self.initialized:
                return True
            
            self._status_data = StatusEffectsData(initialized=True)
            
            self.initialized = True
            self.set_data(self._status_data)
            
            logger.info(f"状態異常システム初期化完了: {self.owner.name}")
            return True
            
        except Exception as e:
            logger.error(f"状態異常システム初期化エラー ({self.owner.name}): {e}")
            return False
    
    def cleanup(self):
        """状態異常システムのクリーンアップ"""
        self._status_data = None
        self.initialized = False
    
    def apply_status_effect(self, effect_type: StatusEffectType, duration: int = -1, 
                          intensity: int = 1, source: str = "unknown") -> bool:
        """状態異常を適用"""
        if not self.ensure_initialized():
            return False
        
        # 効果情報を取得
        effect_info = self._get_status_effect_info(effect_type)
        
        effect_id = f"{effect_type.value}_{len(self._status_data.active_effects)}"
        
        from datetime import datetime
        new_effect = StatusEffect(
            effect_type=effect_type,
            name=effect_info['name'],
            description=effect_info['description'],
            duration=duration,
            intensity=intensity,
            source=source,
            applied_at=datetime.now().isoformat()
        )
        
        # 既存の同じ効果をチェック
        existing_effect_id = self._find_existing_effect(effect_type)
        if existing_effect_id:
            # 既存効果を更新または延長
            existing_effect = self._status_data.active_effects[existing_effect_id]
            if duration > existing_effect.duration or duration == -1:
                existing_effect.duration = duration
                existing_effect.intensity = max(existing_effect.intensity, intensity)
                logger.info(f"状態異常更新: {self.owner.name} - {new_effect.name}")
            else:
                logger.info(f"状態異常適用失敗（既存効果が強い）: {self.owner.name} - {new_effect.name}")
                return False
        else:
            # 新しい効果を追加
            self._status_data.active_effects[effect_id] = new_effect
            logger.info(f"状態異常適用: {self.owner.name} - {new_effect.name} (期間: {duration})")
        
        # キャラクター状態の更新
        self._update_character_status()
        
        # 状態変更イベントを発行
        self._publish_status_changed_event(effect_type, True)
        
        return True
    
    def remove_status_effect(self, effect_type: StatusEffectType) -> bool:
        """状態異常を除去"""
        if not self.ensure_initialized():
            return False
        
        effect_id = self._find_existing_effect(effect_type)
        if not effect_id:
            return False
        
        effect = self._status_data.active_effects[effect_id]
        del self._status_data.active_effects[effect_id]
        
        logger.info(f"状態異常除去: {self.owner.name} - {effect.name}")
        
        # キャラクター状態の更新
        self._update_character_status()
        
        # 状態変更イベントを発行
        self._publish_status_changed_event(effect_type, False)
        
        return True
    
    def has_status_effect(self, effect_type: StatusEffectType) -> bool:
        """指定された状態異常を持っているかチェック"""
        if not self.ensure_initialized():
            return False
        
        return self._find_existing_effect(effect_type) is not None
    
    def get_status_effect(self, effect_type: StatusEffectType) -> Optional[StatusEffect]:
        """指定された状態異常の詳細を取得"""
        if not self.ensure_initialized():
            return None
        
        effect_id = self._find_existing_effect(effect_type)
        if effect_id:
            return self._status_data.active_effects[effect_id]
        return None
    
    def get_all_status_effects(self) -> List[StatusEffect]:
        """全ての状態異常を取得"""
        if not self.ensure_initialized():
            return []
        
        return list(self._status_data.active_effects.values())
    
    def get_beneficial_effects(self) -> List[StatusEffect]:
        """有益な効果のみを取得"""
        return [effect for effect in self.get_all_status_effects() if effect.is_beneficial()]
    
    def get_harmful_effects(self) -> List[StatusEffect]:
        """有害な効果のみを取得"""
        return [effect for effect in self.get_all_status_effects() if effect.is_harmful()]
    
    def process_turn_effects(self) -> List[StatusEffect]:
        """ターン経過処理を行い、切れた効果を返す"""
        if not self.ensure_initialized():
            return []
        
        expired_effects = []
        effects_to_remove = []
        
        for effect_id, effect in self._status_data.active_effects.items():
            if effect.tick():  # ターン経過
                expired_effects.append(effect)
                effects_to_remove.append(effect_id)
        
        # 切れた効果を削除
        for effect_id in effects_to_remove:
            del self._status_data.active_effects[effect_id]
            logger.info(f"状態異常期限切れ: {self.owner.name} - {expired_effects[-1].name}")
        
        if effects_to_remove:
            self._update_character_status()
        
        return expired_effects
    
    def _find_existing_effect(self, effect_type: StatusEffectType) -> Optional[str]:
        """既存の同じタイプの効果を検索"""
        for effect_id, effect in self._status_data.active_effects.items():
            if effect.effect_type == effect_type:
                return effect_id
        return None
    
    def _get_status_effect_info(self, effect_type: StatusEffectType) -> Dict[str, str]:
        """状態異常の情報を取得"""
        effect_info = {
            StatusEffectType.BLESSED: {'name': '祝福', 'description': '全ての行動が成功しやすくなる'},
            StatusEffectType.HASTE: {'name': '加速', 'description': '行動速度が上昇する'},
            StatusEffectType.STRENGTH_UP: {'name': '筋力強化', 'description': '物理攻撃力が上昇する'},
            StatusEffectType.PROTECTION: {'name': '防護', 'description': '受けるダメージが軽減される'},
            StatusEffectType.REGENERATION: {'name': '再生', 'description': 'ターン毎にHPが回復する'},
            
            StatusEffectType.POISONED: {'name': '毒', 'description': 'ターン毎にダメージを受ける'},
            StatusEffectType.PARALYZED: {'name': '麻痺', 'description': '行動できない'},
            StatusEffectType.CONFUSED: {'name': '混乱', 'description': '行動が制御できない'},
            StatusEffectType.CURSED: {'name': '呪い', 'description': '全ての行動が失敗しやすくなる'},
            StatusEffectType.WEAKENED: {'name': '弱体化', 'description': '攻撃力と防御力が低下する'},
            StatusEffectType.BLEEDING: {'name': '出血', 'description': 'ターン毎にダメージを受ける'},
            
            StatusEffectType.UNCONSCIOUS: {'name': '意識不明', 'description': '行動不能状態'},
            StatusEffectType.PETRIFIED: {'name': '石化', 'description': '完全に行動不能'},
            StatusEffectType.CHARMED: {'name': '魅了', 'description': '敵の味方になる'},
            StatusEffectType.FEARED: {'name': '恐怖', 'description': '逃走しようとする'}
        }
        
        return effect_info.get(effect_type, {'name': str(effect_type.value), 'description': '不明な効果'})
    
    def _update_character_status(self):
        """キャラクターの状態を更新"""
        # 重篤な状態異常をチェック
        if self.has_status_effect(StatusEffectType.UNCONSCIOUS):
            from src.character.character import CharacterStatus
            self.owner.status = CharacterStatus.UNCONSCIOUS
        elif self.has_status_effect(StatusEffectType.PETRIFIED):
            from src.character.character import CharacterStatus
            self.owner.status = CharacterStatus.UNCONSCIOUS  # 石化も意識不明扱い
        else:
            # HPに基づいた状態判定
            if hasattr(self.owner, 'derived_stats') and self.owner.derived_stats:
                hp_ratio = self.owner.derived_stats.current_hp / max(self.owner.derived_stats.max_hp, 1)
                
                if hp_ratio <= 0:
                    from src.character.character import CharacterStatus
                    self.owner.status = CharacterStatus.DEAD
                elif hp_ratio <= 0.25:
                    from src.character.character import CharacterStatus
                    self.owner.status = CharacterStatus.INJURED
                else:
                    from src.character.character import CharacterStatus
                    self.owner.status = CharacterStatus.GOOD
    
    def _publish_status_changed_event(self, effect_type: StatusEffectType, applied: bool):
        """状態変更イベントを発行"""
        try:
            from src.core.event_bus import publish_event, EventType
            
            publish_event(
                EventType.CHARACTER_STATUS_CHANGED,
                f"character_{self.owner.character_id}",
                {
                    'character_id': self.owner.character_id,
                    'character_name': self.owner.name,
                    'effect_type': effect_type.value,
                    'applied': applied,
                    'character_status': self.owner.status.value if hasattr(self.owner.status, 'value') else str(self.owner.status)
                }
            )
        except Exception as e:
            logger.warning(f"状態変更イベント発行エラー: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        if not self._status_data:
            return {'initialized': False}
        
        return self._status_data.to_dict()
    
    def from_dict(self, data: Dict[str, Any]) -> bool:
        """辞書からデシリアライズ"""
        try:
            self._status_data = StatusEffectsData.from_dict(data)
            self.initialized = self._status_data.initialized
            self.set_data(self._status_data)
            return True
        except Exception as e:
            logger.error(f"状態異常データデシリアライズエラー: {e}")
            return False
    
    def __repr__(self) -> str:
        if self.initialized and self._status_data:
            effect_count = len(self._status_data.active_effects)
            return f"StatusEffectsComponent(owner={self.owner.name}, effects={effect_count})"
        return f"StatusEffectsComponent(owner={self.owner.name}, uninitialized)"