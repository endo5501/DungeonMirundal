"""エンカウンター管理システムのテスト"""

import pytest
from unittest.mock import Mock, patch

from src.encounter.encounter_manager import (
    EncounterManager, EncounterType, EncounterResult, MonsterRank, 
    MonsterGroup, EncounterEvent
)
from src.dungeon.dungeon_manager import DungeonState
from src.dungeon.dungeon_generator import DungeonAttribute
from src.character.party import Party
from src.character.character import Character
from src.character.stats import BaseStats


class TestEncounterManager:
    """エンカウンター管理システムのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.encounter_manager = EncounterManager()
        
        # テスト用パーティ作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("EncounterHero", "human", "fighter", stats)
        self.party = Party(party_id="encounter_party", name="EncounterParty")
        self.party.add_character(character)
        self.encounter_manager.set_party(self.party)
        
        # テスト用ダンジョン状態
        self.dungeon_state = Mock(spec=DungeonState)
        self.dungeon_state.dungeon_id = "test_dungeon"
        self.encounter_manager.set_dungeon(self.dungeon_state)
    
    def test_encounter_manager_initialization(self):
        """エンカウンターマネージャー初期化テスト"""
        em = EncounterManager()
        
        assert em.current_party is None
        assert em.current_dungeon is None
        assert len(em.encounter_tables) > 0  # エンカウンターテーブルが初期化される
        assert em.encounter_statistics['total_encounters'] == 0
    
    def test_set_party(self):
        """パーティ設定テスト"""
        em = EncounterManager()
        em.set_party(self.party)
        
        assert em.current_party == self.party
    
    def test_set_dungeon(self):
        """ダンジョン設定テスト"""
        em = EncounterManager()
        em.set_dungeon(self.dungeon_state)
        
        assert em.current_dungeon == self.dungeon_state
    
    def test_encounter_table_initialization(self):
        """エンカウンターテーブル初期化テスト"""
        # 各属性のテーブルが存在することを確認
        for attribute in DungeonAttribute:
            assert attribute in self.encounter_manager.encounter_tables
            
            # レベル1-20のテーブルが存在することを確認
            for level in range(1, 21):
                assert level in self.encounter_manager.encounter_tables[attribute]
                assert len(self.encounter_manager.encounter_tables[attribute][level]) > 0
    
    def test_generate_normal_encounter(self):
        """通常エンカウンター生成テスト"""
        encounter = self.encounter_manager.generate_encounter(
            encounter_type="normal",
            level=3,
            dungeon_attribute=DungeonAttribute.FIRE,
            location=(5, 5, 3)
        )
        
        assert encounter.encounter_type == EncounterType.NORMAL
        assert encounter.dungeon_attribute == DungeonAttribute.FIRE
        assert encounter.location == (5, 5, 3)
        assert encounter.monster_group is not None
        assert len(encounter.monster_group.monster_ids) >= 1
        assert encounter.can_flee == True
        assert encounter.description != ""
    
    def test_generate_ambush_encounter(self):
        """奇襲エンカウンター生成テスト"""
        encounter = self.encounter_manager.generate_encounter(
            encounter_type="ambush",
            level=5,
            dungeon_attribute=DungeonAttribute.DARK,
            location=(10, 8, 5)
        )
        
        assert encounter.encounter_type == EncounterType.AMBUSH
        assert encounter.can_flee == False  # 奇襲時は最初のターンで逃走不可
        assert "surprise_round" in encounter.special_conditions
        assert "突然" in encounter.description
    
    def test_generate_treasure_guardian_encounter(self):
        """宝箱守護者エンカウンター生成テスト"""
        encounter = self.encounter_manager.generate_encounter(
            encounter_type="treasure_guardian",
            level=7,
            dungeon_attribute=DungeonAttribute.LIGHT,
            location=(3, 12, 7)
        )
        
        assert encounter.encounter_type == EncounterType.TREASURE_GUARDIAN
        assert encounter.can_negotiate == True
        assert "guarding_treasure" in encounter.special_conditions
        assert "宝箱を守る" in encounter.description
    
    def test_monster_group_generation(self):
        """モンスターグループ生成テスト"""
        encounter = self.encounter_manager.generate_encounter(
            encounter_type="normal",
            level=4,
            dungeon_attribute=DungeonAttribute.ICE,
            location=(7, 3, 4)
        )
        
        group = encounter.monster_group
        assert group is not None
        assert len(group.monster_ids) >= 1
        assert len(group.monster_ids) <= 4  # 通常エンカウンターの最大グループサイズ
        assert group.total_level > 0
        assert group.rank in MonsterRank
        assert group.treasure_modifier > 0
        assert group.experience_modifier > 0
    
    def test_attribute_monster_variation(self):
        """属性によるモンスター変化テスト"""
        # 炎属性ダンジョンのモンスターテーブル
        fire_monsters = self.encounter_manager.encounter_tables[DungeonAttribute.FIRE][1]
        # 物理属性ダンジョンのモンスターテーブル
        physical_monsters = self.encounter_manager.encounter_tables[DungeonAttribute.PHYSICAL][1]
        
        # 炎属性には flame_ プレフィックスのモンスターが含まれる
        flame_monsters = [m for m in fire_monsters if m.startswith("flame_")]
        assert len(flame_monsters) > 0
        
        # 物理属性にはプレフィックスモンスターが含まれない
        physical_prefixed = [m for m in physical_monsters if "_" in m and not m.startswith("dire_")]
        assert len(physical_prefixed) == 0
    
    def test_encounter_location_consistency(self):
        """エンカウンター位置の一貫性テスト"""
        location = (15, 20, 8)
        
        # 同じ位置で複数回生成すると同じモンスターグループになる
        encounter1 = self.encounter_manager.generate_encounter(
            encounter_type="normal",
            level=8,
            dungeon_attribute=DungeonAttribute.LIGHTNING,
            location=location
        )
        
        encounter2 = self.encounter_manager.generate_encounter(
            encounter_type="normal",
            level=8,
            dungeon_attribute=DungeonAttribute.LIGHTNING,
            location=location
        )
        
        # 同じ位置なので同じモンスターIDになる
        assert encounter1.monster_group.monster_ids == encounter2.monster_group.monster_ids
    
    def test_resolve_encounter_fight(self):
        """戦闘選択解決テスト"""
        encounter = EncounterEvent(
            encounter_type=EncounterType.NORMAL,
            monster_group=MonsterGroup(monster_ids=["goblin"]),
            location=(5, 5, 1),
            dungeon_attribute=DungeonAttribute.PHYSICAL
        )
        
        result, message = self.encounter_manager.resolve_encounter_attempt("fight", encounter)
        
        assert result == EncounterResult.COMBAT_START
        assert "戦闘を開始します" in message
    
    def test_resolve_encounter_flee_success(self):
        """逃走成功解決テスト"""
        encounter = EncounterEvent(
            encounter_type=EncounterType.NORMAL,
            monster_group=MonsterGroup(monster_ids=["weak_goblin"], rank=MonsterRank.WEAK),
            location=(5, 5, 1),
            dungeon_attribute=DungeonAttribute.PHYSICAL,
            can_flee=True
        )
        
        # 逃走成功するように高い敏捷性パーティを設定
        high_agi_stats = BaseStats(strength=15, agility=18, intelligence=12, faith=12, luck=12)
        high_agi_char = Character.create_character("FastRunner", "elf", "fighter", high_agi_stats)
        fast_party = Party(party_id="fast_party", name="FastParty")
        fast_party.add_character(high_agi_char)
        self.encounter_manager.set_party(fast_party)
        
        # 複数回試行して少なくとも1回は成功することを確認
        success_count = 0
        for _ in range(20):
            result, message = self.encounter_manager.resolve_encounter_attempt("flee", encounter)
            if result == EncounterResult.FLED:
                success_count += 1
        
        assert success_count > 0  # 少なくとも1回は逃走成功
    
    def test_resolve_encounter_flee_blocked(self):
        """逃走阻止解決テスト"""
        encounter = EncounterEvent(
            encounter_type=EncounterType.AMBUSH,
            monster_group=MonsterGroup(monster_ids=["orc"]),
            location=(5, 5, 1),
            dungeon_attribute=DungeonAttribute.PHYSICAL,
            can_flee=False  # 奇襲なので逃走不可
        )
        
        result, message = self.encounter_manager.resolve_encounter_attempt("flee", encounter)
        
        assert result == EncounterResult.COMBAT_START
        assert "逃げることができません" in message
    
    def test_resolve_encounter_negotiate_success(self):
        """交渉成功解決テスト"""
        encounter = EncounterEvent(
            encounter_type=EncounterType.TREASURE_GUARDIAN,
            monster_group=MonsterGroup(monster_ids=["guardian"]),
            location=(5, 5, 1),
            dungeon_attribute=DungeonAttribute.LIGHT,
            can_negotiate=True
        )
        
        # 交渉成功するように高い知力パーティを設定
        high_int_stats = BaseStats(strength=12, agility=12, intelligence=18, faith=12, luck=12)
        smart_char = Character.create_character("Negotiator", "human", "mage", high_int_stats)
        smart_party = Party(party_id="smart_party", name="SmartParty")
        smart_party.add_character(smart_char)
        self.encounter_manager.set_party(smart_party)
        
        # 複数回試行して少なくとも1回は成功することを確認
        success_count = 0
        for _ in range(20):
            result, message = self.encounter_manager.resolve_encounter_attempt("negotiate", encounter)
            if result == EncounterResult.NEGOTIATED:
                success_count += 1
        
        assert success_count > 0  # 少なくとも1回は交渉成功
    
    def test_resolve_encounter_negotiate_blocked(self):
        """交渉阻止解決テスト"""
        encounter = EncounterEvent(
            encounter_type=EncounterType.NORMAL,
            monster_group=MonsterGroup(monster_ids=["aggressive_orc"]),
            location=(5, 5, 1),
            dungeon_attribute=DungeonAttribute.PHYSICAL,
            can_negotiate=False  # 通常エンカウンターなので交渉不可
        )
        
        result, message = self.encounter_manager.resolve_encounter_attempt("negotiate", encounter)
        
        assert result == EncounterResult.COMBAT_START
        assert "交渉はできません" in message
    
    def test_resolve_encounter_invalid_action(self):
        """無効行動解決テスト"""
        encounter = EncounterEvent(
            encounter_type=EncounterType.NORMAL,
            monster_group=MonsterGroup(monster_ids=["goblin"]),
            location=(5, 5, 1),
            dungeon_attribute=DungeonAttribute.PHYSICAL
        )
        
        result, message = self.encounter_manager.resolve_encounter_attempt("invalid", encounter)
        
        assert result == EncounterResult.COMBAT_START
        assert "無効な行動" in message
    
    def test_calculate_flee_chance_factors(self):
        """逃走成功率計算要因テスト"""
        # 基本エンカウンター
        basic_encounter = EncounterEvent(
            encounter_type=EncounterType.NORMAL,
            monster_group=MonsterGroup(monster_ids=["goblin"], rank=MonsterRank.NORMAL),
            location=(5, 5, 1),
            dungeon_attribute=DungeonAttribute.PHYSICAL
        )
        
        basic_chance = self.encounter_manager._calculate_flee_chance(basic_encounter)
        
        # ボスエンカウンター（逃走困難）
        boss_encounter = EncounterEvent(
            encounter_type=EncounterType.BOSS,
            monster_group=MonsterGroup(monster_ids=["dragon"], rank=MonsterRank.BOSS),
            location=(5, 5, 1),
            dungeon_attribute=DungeonAttribute.FIRE
        )
        
        boss_chance = self.encounter_manager._calculate_flee_chance(boss_encounter)
        
        # ボスの方が逃走困難
        assert boss_chance < basic_chance
        
        # 弱いモンスター（逃走容易）
        weak_encounter = EncounterEvent(
            encounter_type=EncounterType.NORMAL,
            monster_group=MonsterGroup(monster_ids=["rat"], rank=MonsterRank.WEAK),
            location=(5, 5, 1),
            dungeon_attribute=DungeonAttribute.PHYSICAL
        )
        
        weak_chance = self.encounter_manager._calculate_flee_chance(weak_encounter)
        
        # 弱いモンスターの方が逃走容易
        assert weak_chance > basic_chance
    
    def test_calculate_negotiation_chance_factors(self):
        """交渉成功率計算要因テスト"""
        # 宝箱守護者（交渉しやすい）
        guardian_encounter = EncounterEvent(
            encounter_type=EncounterType.TREASURE_GUARDIAN,
            monster_group=MonsterGroup(monster_ids=["guardian"]),
            location=(5, 5, 1),
            dungeon_attribute=DungeonAttribute.LIGHT
        )
        
        guardian_chance = self.encounter_manager._calculate_negotiation_chance(guardian_encounter)
        
        # 通常エンカウンター
        normal_encounter = EncounterEvent(
            encounter_type=EncounterType.NORMAL,
            monster_group=MonsterGroup(monster_ids=["orc"]),
            location=(5, 5, 1),
            dungeon_attribute=DungeonAttribute.PHYSICAL
        )
        
        normal_chance = self.encounter_manager._calculate_negotiation_chance(normal_encounter)
        
        # 宝箱守護者の方が交渉しやすい
        assert guardian_chance > normal_chance
    
    def test_encounter_statistics_tracking(self):
        """エンカウンター統計追跡テスト"""
        initial_stats = self.encounter_manager.get_encounter_statistics()
        initial_total = initial_stats['total_encounters']
        
        # エンカウンター生成（統計が更新される）
        self.encounter_manager.generate_encounter(
            encounter_type="normal",
            level=1,
            dungeon_attribute=DungeonAttribute.PHYSICAL,
            location=(1, 1, 1)
        )
        
        updated_stats = self.encounter_manager.get_encounter_statistics()
        
        assert updated_stats['total_encounters'] == initial_total + 1
        assert 'flee_rate' in updated_stats
        assert 'combat_victory_rate' in updated_stats
    
    def test_special_conditions_application(self):
        """特殊条件適用テスト"""
        # 深階層でのエンカウンター
        deep_encounter = self.encounter_manager.generate_encounter(
            encounter_type="normal",
            level=18,  # 深い階層
            dungeon_attribute=DungeonAttribute.DARK,
            location=(5, 5, 18)
        )
        
        # 深階層特殊条件が適用される
        assert "deep_dungeon" in deep_encounter.special_conditions
    
    def test_monster_rank_distribution(self):
        """モンスターランク分布テスト"""
        ranks = []
        
        # 複数回生成してランク分布を確認
        for i in range(50):
            encounter = self.encounter_manager.generate_encounter(
                encounter_type="normal",
                level=5,
                dungeon_attribute=DungeonAttribute.PHYSICAL,
                location=(i, i, 5)  # 位置を変えて異なるモンスターを生成
            )
            ranks.append(encounter.monster_group.rank)
        
        # 各ランクが最低1回は出現する（確率的テスト）
        unique_ranks = set(ranks)
        assert MonsterRank.WEAK in unique_ranks or MonsterRank.NORMAL in unique_ranks
        assert len(unique_ranks) >= 2  # 少なくとも2種類のランクが出現
    
    def test_encounter_no_party(self):
        """パーティなしでのエンカウンター解決テスト"""
        encounter = EncounterEvent(
            encounter_type=EncounterType.NORMAL,
            monster_group=MonsterGroup(monster_ids=["goblin"]),
            location=(5, 5, 1),
            dungeon_attribute=DungeonAttribute.PHYSICAL
        )
        
        # パーティを削除
        em = EncounterManager()
        em.current_party = None
        
        result, message = em.resolve_encounter_attempt("flee", encounter)
        
        # パーティがなくても基本的な処理は動作する
        assert result in [EncounterResult.COMBAT_START, EncounterResult.FLED]