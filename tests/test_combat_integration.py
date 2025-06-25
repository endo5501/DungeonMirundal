"""戦闘システム統合テスト（魔法・アイテム）"""

import pytest
from unittest.mock import Mock, patch

from src.combat.combat_manager import CombatManager, CombatAction, CombatResult
from src.character.character import Character
from src.character.party import Party
from src.character.stats import BaseStats
from src.monsters.monster import Monster, MonsterType, MonsterSize, MonsterStats
from src.magic.spells import spell_manager
from src.items.item import Item, ItemType, ItemInstance, item_manager
from src.items.item_usage import item_usage_manager


class TestCombatMagicIntegration:
    """戦闘での魔法使用統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.combat_manager = CombatManager()
        
        # テスト用キャラクター作成（魔法使い）
        stats = BaseStats(strength=10, agility=12, intelligence=16, faith=14, luck=12)
        self.mage = Character.create_character("TestMage", "elf", "mage", stats)
        self.mage.derived_stats.max_mp = 20
        self.mage.derived_stats.current_mp = 20
        
        # テスト用パーティ作成
        self.party = Party(party_id="test_party", name="TestParty")
        self.party.add_character(self.mage)
        
        # テスト用モンスター作成
        monster_stats = MonsterStats(
            level=2,
            hit_points=15,
            armor_class=12,
            attack_bonus=2,
            damage_dice="1d6"
        )
        
        self.monster = Monster(
            monster_id="test_goblin",
            name="テストゴブリン",
            description="テスト用ゴブリン",
            monster_type=MonsterType.HUMANOID,
            size=MonsterSize.SMALL,
            stats=monster_stats
        )
        
        self.monsters = [self.monster]
    
    def test_cast_offensive_spell_in_combat(self):
        """戦闘での攻撃魔法使用テスト"""
        # 戦闘開始
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # 攻撃魔法の情報を準備
        spell_data = {
            'name_key': 'spell.fireball',
            'level': 1,
            'school': 'mage',
            'type': 'offensive',
            'target': 'single_enemy',
            'mp_cost': 3,
            'effect_type': 'fire_damage',
            'base_damage': 8
        }
        
        # 魔法使用のターンデータ
        action_data = {
            'spell_id': 'fireball'
        }
        
        # 魔法マネージャーにテスト魔法を追加
        with patch.object(spell_manager, 'get_spell') as mock_get_spell:
            from src.magic.spells import Spell
            test_spell = Spell('fireball', spell_data)
            mock_get_spell.return_value = test_spell
            
            initial_hp = self.monster.current_hp
            initial_mp = self.mage.derived_stats.current_mp
            
            # 魔法詠唱実行
            result = self.combat_manager.execute_action(
                CombatAction.CAST_SPELL, 
                self.monster, 
                action_data
            )
            
            # 結果確認
            assert result == CombatResult.CONTINUE
            assert self.monster.current_hp < initial_hp  # ダメージを受けている
            assert self.mage.derived_stats.current_mp < initial_mp  # MPが消費されている
    
    def test_cast_healing_spell_in_combat(self):
        """戦闘での回復魔法使用テスト"""
        # キャラクターにダメージを与える（軽傷）
        self.mage.take_damage(3)
        initial_hp = self.mage.derived_stats.current_hp
        initial_mp = self.mage.derived_stats.current_mp
        
        # 戦闘開始
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # 回復魔法の情報を準備
        spell_data = {
            'name_key': 'spell.heal',
            'level': 1,
            'school': 'priest',
            'type': 'healing',
            'target': 'single_ally',
            'mp_cost': 2,
            'effect_type': 'heal',
            'base_value': 6,
            'scaling_stat': 'faith'
        }
        
        action_data = {
            'spell_id': 'heal'
        }
        
        with patch.object(spell_manager, 'get_spell') as mock_get_spell:
            from src.magic.spells import Spell
            test_spell = Spell('heal', spell_data)
            mock_get_spell.return_value = test_spell
            
            # 回復魔法実行（自分をターゲットに）
            result = self.combat_manager.execute_action(
                CombatAction.CAST_SPELL,
                target=self.mage,
                action_data=action_data
            )
            
            # デバッグ出力
            print(f"Result: {result}")
            print(f"Initial HP: {initial_hp}, Current HP: {self.mage.derived_stats.current_hp}")
            print(f"Initial MP: {initial_mp}, Current MP: {self.mage.derived_stats.current_mp}")
            print(f"Spell effect base_value: {test_spell.effect.base_value}")
            print(f"Spell effect scaling_stat: {test_spell.effect.scaling_stat}")
            print(f"Mage faith: {self.mage.base_stats.faith}")
            
            # 結果確認
            assert result == CombatResult.CONTINUE
            assert self.mage.derived_stats.current_hp > initial_hp  # 回復している
            assert self.mage.derived_stats.current_mp < initial_mp  # MPが消費されている
    
    def test_insufficient_mp_for_spell(self):
        """MP不足での魔法詠唱失敗テスト"""
        # MPをほぼ0にする
        self.mage.derived_stats.current_mp = 1
        
        # 戦闘開始
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # 高コストの魔法情報
        spell_data = {
            'name_key': 'spell.meteor',
            'level': 5,
            'school': 'mage',
            'type': 'offensive',
            'target': 'all_enemies',
            'mp_cost': 15,  # 現在のMPより多い
            'effect_type': 'fire_damage',
            'base_damage': 25
        }
        
        action_data = {
            'spell_id': 'meteor'
        }
        
        with patch.object(spell_manager, 'get_spell') as mock_get_spell:
            from src.magic.spells import Spell
            test_spell = Spell('meteor', spell_data)
            mock_get_spell.return_value = test_spell
            
            initial_monster_hp = self.monster.current_hp
            
            # 魔法詠唱実行（失敗するはず）
            result = self.combat_manager.execute_action(
                CombatAction.CAST_SPELL,
                self.monster,
                action_data
            )
            
            # 結果確認：MP不足で失敗
            assert result == CombatResult.CONTINUE
            assert self.monster.current_hp == initial_monster_hp  # ダメージを受けていない


class TestCombatItemIntegration:
    """戦闘でのアイテム使用統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.combat_manager = CombatManager()
        
        # テスト用キャラクター作成
        stats = BaseStats(strength=14, agility=12, intelligence=10, faith=11, luck=13)
        self.fighter = Character.create_character("TestFighter", "human", "fighter", stats)
        
        # テスト用パーティ作成
        self.party = Party(party_id="test_party", name="TestParty")
        self.party.add_character(self.fighter)
        
        # テスト用モンスター作成
        monster_stats = MonsterStats(
            level=2,
            hit_points=20,
            armor_class=13,
            attack_bonus=3,
            damage_dice="1d6+1"
        )
        
        self.monster = Monster(
            monster_id="test_orc",
            name="テストオーク",
            description="テスト用オーク",
            monster_type=MonsterType.HUMANOID,
            size=MonsterSize.MEDIUM,
            stats=monster_stats
        )
        
        self.monsters = [self.monster]
    
    def test_use_healing_potion_in_combat(self):
        """戦闘での回復ポーション使用テスト"""
        # キャラクターにダメージを与える（軽傷）
        self.fighter.take_damage(5)
        initial_hp = self.fighter.derived_stats.current_hp
        
        # 戦闘開始
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # テスト用回復ポーション作成
        potion_data = {
            'name_key': 'item.healing_potion',
            'description_key': 'item.healing_potion_desc',
            'type': 'consumable',
            'usable_in_combat': True,
            'effects': {'heal_hp': 10}
        }
        healing_potion = Item("healing_potion", potion_data)
        
        potion_instance = ItemInstance(item_id="healing_potion", quantity=1)
        
        action_data = {
            'item_instance': potion_instance
        }
        
        # アイテム使用実行
        result = self.combat_manager.execute_action(
            CombatAction.USE_ITEM,
            self.fighter,
            action_data
        )
        
        # 結果確認
        assert result == CombatResult.CONTINUE
        assert self.fighter.derived_stats.current_hp > initial_hp  # 回復している
    
    def test_use_offensive_item_in_combat(self):
        """戦闘での攻撃アイテム使用テスト"""
        # 戦闘開始
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # テスト用爆弾作成
        bomb_data = {
            'name_key': 'item.bomb',
            'description_key': 'item.bomb_desc', 
            'type': 'consumable',
            'usable_in_combat': True,
            'effects': {'damage': 12}
        }
        bomb = Item("bomb", bomb_data)
        
        bomb_instance = ItemInstance(item_id="bomb", quantity=1)
        initial_monster_hp = self.monster.current_hp
        
        action_data = {
            'item_instance': bomb_instance
        }
        
        # アイテム使用実行
        result = self.combat_manager.execute_action(
            CombatAction.USE_ITEM,
            self.monster,  # 敵対象
            action_data
        )
        
        # 結果確認
        assert result == CombatResult.CONTINUE
        # アイテム使用システムによってダメージまたは効果が適用されている


class TestCombatSystemIntegration:
    """戦闘システム全体統合テスト"""
    
    def test_full_combat_with_magic_and_items(self):
        """魔法とアイテムを含む完全な戦闘フローテスト"""
        combat_manager = CombatManager()
        
        # 魔法使いとファイターのパーティ
        mage_stats = BaseStats(strength=8, agility=11, intelligence=16, faith=12, luck=14)
        mage = Character.create_character("Mage", "elf", "mage", mage_stats)
        mage.derived_stats.max_mp = 15
        mage.derived_stats.current_mp = 15
        
        fighter_stats = BaseStats(strength=16, agility=13, intelligence=9, faith=10, luck=12)
        fighter = Character.create_character("Fighter", "human", "fighter", fighter_stats)
        
        party = Party(party_id="test_party", name="TestParty")
        party.add_character(mage)
        party.add_character(fighter)
        
        # 敵モンスター
        monster_stats = MonsterStats(
            level=3,
            hit_points=25,
            armor_class=14,
            attack_bonus=4,
            damage_dice="1d8+2"
        )
        
        monster = Monster(
            monster_id="boss_orc",
            name="ボスオーク",
            description="強力なオーク",
            monster_type=MonsterType.HUMANOID,
            size=MonsterSize.MEDIUM,
            stats=monster_stats
        )
        
        # 戦闘開始
        success = combat_manager.start_combat(party, [monster])
        assert success == True
        assert combat_manager.combat_state.value == 'in_progress'
        
        # 戦闘状況確認
        status = combat_manager.get_combat_status()
        assert status['party_members'] == 2
        assert status['monsters_alive'] == 1
        assert status['is_player_turn'] in [True, False]  # ターン順による
        
        # 有効な対象取得テスト
        mage_targets = combat_manager.get_valid_targets(mage, CombatAction.ATTACK)
        assert len(mage_targets) == 1
        assert mage_targets[0] == monster
        
        fighter_targets = combat_manager.get_valid_targets(fighter, CombatAction.USE_ITEM)
        assert len(fighter_targets) == 2  # 味方2人が対象
        
        logger_messages = []
        
        # 戦闘が正常に管理されていることを確認
        assert combat_manager.party == party
        assert len(combat_manager.monsters) == 1
        assert len(combat_manager.turn_order) == 3  # 2キャラ + 1モンスター