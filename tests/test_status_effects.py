"""ステータス効果システムのテスト"""

import pytest
from src.effects.status_effects import (
    StatusEffectType, StatusEffect, StatusEffectManager,
    PoisonEffect, ParalysisEffect, SleepEffect, RegenEffect,
    StrengthUpEffect, DefenseUpEffect, status_effect_manager
)
from src.character.character import Character
from src.character.stats import BaseStats


class TestStatusEffect:
    """ステータス効果基底クラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # テスト用キャラクター作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        self.character = Character.create_character("TestHero", "human", "fighter", stats)
    
    def test_poison_effect_creation(self):
        """毒効果の作成テスト"""
        poison = PoisonEffect(duration=5, strength=2)
        
        assert poison.effect_type == StatusEffectType.POISON
        assert poison.duration == 5
        assert poison.strength == 2
        assert poison.source == "poison"
    
    def test_poison_effect_apply_and_remove(self):
        """毒効果の適用・除去テスト"""
        poison = PoisonEffect(duration=3)
        
        # 適用
        result = poison.apply_effect(self.character)
        assert result['applied'] == True
        assert "毒に冒されました" in result['message']
        
        # 除去
        result = poison.remove_effect(self.character)
        assert result['removed'] == True
        assert "毒が治りました" in result['message']
    
    def test_poison_effect_turn_damage(self):
        """毒効果のターンダメージテスト"""
        poison = PoisonEffect(duration=3, strength=2)
        initial_hp = self.character.derived_stats.current_hp
        
        # ターン処理
        continues, result = poison.tick(self.character)
        
        assert continues == True  # まだ継続
        assert poison.duration == 2  # 減少
        assert result['poison_damage'] > 0
        assert self.character.derived_stats.current_hp < initial_hp
    
    def test_paralysis_effect(self):
        """麻痺効果のテスト"""
        paralysis = ParalysisEffect(duration=2)
        
        # 適用
        result = paralysis.apply_effect(self.character)
        assert result['applied'] == True
        assert "麻痺" in result['message']
        
        # ターン処理（麻痺は継続ダメージなし）
        continues, result = paralysis.tick(self.character)
        assert continues == True
        assert paralysis.duration == 1
    
    def test_regen_effect(self):
        """再生効果のテスト"""
        regen = RegenEffect(duration=3, strength=2)
        
        # HPを減らしてから再生テスト
        self.character.take_damage(20)
        damaged_hp = self.character.derived_stats.current_hp
        
        # ターン処理
        continues, result = regen.tick(self.character)
        
        assert continues == True
        assert result['regen_amount'] > 0
        assert self.character.derived_stats.current_hp > damaged_hp
    
    def test_strength_up_effect(self):
        """筋力強化効果のテスト"""
        strength_up = StrengthUpEffect(duration=5, strength=3)
        
        # 適用
        result = strength_up.apply_effect(self.character)
        assert result['applied'] == True
        assert result['strength_bonus'] == 3
        
        # 除去
        result = strength_up.remove_effect(self.character)
        assert result['removed'] == True
        assert result['strength_bonus'] == -3
    
    def test_effect_serialization(self):
        """ステータス効果のシリアライゼーションテスト"""
        poison = PoisonEffect(duration=5, strength=2, source="test")
        
        # 辞書に変換
        data = poison.to_dict()
        assert data['effect_type'] == 'poison'
        assert data['duration'] == 5
        assert data['strength'] == 2
        assert data['source'] == "test"
        
        # 辞書から復元
        restored = StatusEffect.from_dict(data)
        assert restored.effect_type == StatusEffectType.POISON
        assert restored.duration == 5
        assert restored.strength == 2
        assert restored.source == "test"


class TestStatusEffectManager:
    """ステータス効果管理のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # テスト用キャラクター作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        self.character = Character.create_character("TestHero", "human", "fighter", stats)
        self.manager = StatusEffectManager(self.character.character_id)
        
        # キャラクターオブジェクトをテストで直接渡すため、登録は不要
    
    def test_add_effect(self):
        """効果追加のテスト"""
        poison = PoisonEffect(duration=5)
        
        success, result = self.manager.add_effect(poison, self.character)
        
        assert success == True
        assert self.manager.has_effect(StatusEffectType.POISON)
        assert result['applied'] == True
    
    def test_remove_effect(self):
        """効果除去のテスト"""
        poison = PoisonEffect(duration=5)
        self.manager.add_effect(poison, self.character)
        
        success, result = self.manager.remove_effect(StatusEffectType.POISON, self.character)
        
        assert success == True
        assert not self.manager.has_effect(StatusEffectType.POISON)
        assert result['removed'] == True
    
    def test_effect_override(self):
        """効果の上書きテスト"""
        # 弱い毒効果を追加
        weak_poison = PoisonEffect(duration=3, strength=1)
        self.manager.add_effect(weak_poison, self.character)
        
        # より強い毒効果を追加
        strong_poison = PoisonEffect(duration=5, strength=3)
        success, result = self.manager.add_effect(strong_poison, self.character)
        
        assert success == True
        effect = self.manager.get_effect(StatusEffectType.POISON)
        assert effect.strength == 3
        assert effect.duration == 5
    
    def test_effect_override_rejection(self):
        """弱い効果による上書き拒否テスト"""
        # 強い毒効果を追加
        strong_poison = PoisonEffect(duration=5, strength=3)
        self.manager.add_effect(strong_poison, self.character)
        
        # 弱い毒効果を追加（拒否されるはず）
        weak_poison = PoisonEffect(duration=3, strength=1)
        success, result = self.manager.add_effect(weak_poison, self.character)
        
        assert success == False
        assert "より強い" in result['message']
        effect = self.manager.get_effect(StatusEffectType.POISON)
        assert effect.strength == 3  # 元の強い効果が残る
    
    def test_process_turn(self):
        """ターン処理のテスト"""
        # 複数の効果を追加
        poison = PoisonEffect(duration=2)
        regen = RegenEffect(duration=3)
        paralysis = ParalysisEffect(duration=1)  # 1ターンで終了
        
        self.manager.add_effect(poison, self.character)
        self.manager.add_effect(regen, self.character)
        self.manager.add_effect(paralysis, self.character)
        
        # ターン処理
        results = self.manager.process_turn(self.character)
        
        # 毒・再生・麻痺の処理結果があることを確認
        assert len(results) >= 3
        
        # 麻痺は1ターンで終了するので除去されている
        assert not self.manager.has_effect(StatusEffectType.PARALYSIS)
        # 毒と再生はまだ残っている
        assert self.manager.has_effect(StatusEffectType.POISON)
        assert self.manager.has_effect(StatusEffectType.REGEN)
    
    def test_cure_negative_effects(self):
        """負の効果治療のテスト"""
        # 負の効果と正の効果を追加
        poison = PoisonEffect(duration=5)
        paralysis = ParalysisEffect(duration=3)
        strength_up = StrengthUpEffect(duration=6)
        
        self.manager.add_effect(poison, self.character)
        self.manager.add_effect(paralysis, self.character)
        self.manager.add_effect(strength_up, self.character)
        
        # 負の効果を治療
        results = self.manager.cure_negative_effects(self.character)
        
        # 負の効果は除去され、正の効果は残る
        assert not self.manager.has_effect(StatusEffectType.POISON)
        assert not self.manager.has_effect(StatusEffectType.PARALYSIS)
        assert self.manager.has_effect(StatusEffectType.STRENGTH_UP)
        assert len(results) == 2  # 2つの負の効果が治療された
    
    def test_stat_modifiers(self):
        """ステータス修正値のテスト"""
        strength_up = StrengthUpEffect(duration=5, strength=3)
        defense_up = DefenseUpEffect(duration=4, strength=2)
        
        self.manager.add_effect(strength_up, self.character)
        self.manager.add_effect(defense_up, self.character)
        
        modifiers = self.manager.get_stat_modifiers()
        
        assert modifiers['strength'] == 3
        assert modifiers['attack'] == 3  # 筋力強化は攻撃力も上昇
        assert modifiers['defense'] == 2
        assert modifiers['agility'] == 0  # 影響なし
    
    def test_can_act(self):
        """行動可能性チェックのテスト"""
        # 通常状態では行動可能
        can_act, reason = self.manager.can_act()
        assert can_act == True
        assert reason == ""
        
        # 麻痺状態では行動不可
        paralysis = ParalysisEffect(duration=3)
        self.manager.add_effect(paralysis, self.character)
        
        can_act, reason = self.manager.can_act()
        assert can_act == False
        assert "麻痺" in reason
        
        # 麻痺を治療すると行動可能に
        self.manager.remove_effect(StatusEffectType.PARALYSIS, self.character)
        can_act, reason = self.manager.can_act()
        assert can_act == True
    
    def test_active_effects_summary(self):
        """効果一覧取得のテスト"""
        poison = PoisonEffect(duration=3)
        strength_up = StrengthUpEffect(duration=5)
        
        self.manager.add_effect(poison, self.character)
        self.manager.add_effect(strength_up, self.character)
        
        summary = self.manager.get_active_effects_summary()
        
        assert len(summary) == 2
        assert any('poison' in desc for desc in summary)
        assert any('strength_up' in desc for desc in summary)
    
    def test_manager_serialization(self):
        """管理システムのシリアライゼーションテスト"""
        poison = PoisonEffect(duration=5, strength=2)
        self.manager.add_effect(poison, self.character)
        
        # 辞書に変換
        data = self.manager.to_dict()
        assert data['character_id'] == self.character.character_id
        assert 'poison' in data['active_effects']
        
        # 辞書から復元
        restored = StatusEffectManager.from_dict(data)
        assert restored.character_id == self.character.character_id
        assert restored.has_effect(StatusEffectType.POISON)


class TestCharacterStatusEffectIntegration:
    """キャラクターとステータス効果の統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        self.character = Character.create_character("TestHero", "human", "fighter", stats)
        
        # キャラクターオブジェクトをテストで直接渡すため、登録は不要
    
    def test_character_status_effects_initialization(self):
        """キャラクターのステータス効果初期化テスト"""
        status_effects = self.character.get_status_effects()
        
        assert status_effects is not None
        assert status_effects.character_id == self.character.character_id
        assert self.character._status_effects_initialized == True
    
    def test_character_effective_stats_with_status_effects(self):
        """ステータス効果を含む実効能力値テスト"""
        base_strength = self.character.base_stats.strength
        
        # 筋力強化効果を追加
        status_effects = self.character.get_status_effects()
        strength_up = StrengthUpEffect(duration=5, strength=3)
        status_effects.add_effect(strength_up, self.character)
        
        # 実効能力値にボーナスが反映されることを確認
        effective_stats = self.character.get_effective_stats()
        assert effective_stats.strength == base_strength + 3
    
    def test_character_attack_power_with_status_effects(self):
        """ステータス効果を含む攻撃力テスト"""
        base_attack = self.character.get_attack_power()
        
        # 筋力強化効果を追加
        status_effects = self.character.get_status_effects()
        strength_up = StrengthUpEffect(duration=5, strength=3)
        status_effects.add_effect(strength_up, self.character)
        
        # 攻撃力にボーナスが反映されることを確認
        enhanced_attack = self.character.get_attack_power()
        assert enhanced_attack == base_attack + 3
    
    def test_character_defense_with_status_effects(self):
        """ステータス効果を含む防御力テスト"""
        base_defense = self.character.get_defense()
        
        # 防御強化効果を追加
        status_effects = self.character.get_status_effects()
        defense_up = DefenseUpEffect(duration=5, strength=2)
        status_effects.add_effect(defense_up, self.character)
        
        # 防御力にボーナスが反映されることを確認
        enhanced_defense = self.character.get_defense()
        assert enhanced_defense == base_defense + 2


class TestGlobalStatusEffectManager:
    """グローバルステータス効果管理のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        self.character1 = Character.create_character("Hero1", "human", "fighter", stats)
        self.character2 = Character.create_character("Hero2", "elf", "mage", stats)
        
        # キャラクターオブジェクトをテストで直接渡すため、登録は不要
    
    def test_get_character_effects(self):
        """キャラクター効果管理取得のテスト"""
        manager1 = status_effect_manager.get_character_effects(self.character1.character_id)
        manager2 = status_effect_manager.get_character_effects(self.character2.character_id)
        
        assert manager1.character_id == self.character1.character_id
        assert manager2.character_id == self.character2.character_id
        assert manager1 != manager2
    
    def test_process_party_turn(self):
        """パーティターン処理のテスト"""
        # 各キャラクターに効果を追加
        manager1 = status_effect_manager.get_character_effects(self.character1.character_id)
        manager2 = status_effect_manager.get_character_effects(self.character2.character_id)
        
        poison1 = PoisonEffect(duration=2)
        poison2 = PoisonEffect(duration=3)
        manager1.add_effect(poison1, self.character1)
        manager2.add_effect(poison2, self.character2)
        
        # パーティターン処理
        characters = [self.character1, self.character2]
        results = status_effect_manager.process_party_turn(characters)
        
        assert len(results) == 2
        assert self.character1.character_id in results
        assert self.character2.character_id in results
    
    def test_global_manager_serialization(self):
        """グローバル管理のシリアライゼーションテスト"""
        # 効果を追加
        manager = status_effect_manager.get_character_effects(self.character1.character_id)
        poison = PoisonEffect(duration=5)
        manager.add_effect(poison, self.character1)
        
        # シリアライゼーション
        data = status_effect_manager.to_dict()
        assert self.character1.character_id in data['character_managers']
        
        # 復元
        restored = status_effect_manager.from_dict(data)
        restored_manager = restored.get_character_effects(self.character1.character_id)
        assert restored_manager.has_effect(StatusEffectType.POISON)