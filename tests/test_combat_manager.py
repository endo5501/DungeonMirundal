"""戦闘管理システムのテスト"""

import pytest
from unittest.mock import Mock, patch

from src.combat.combat_manager import (
    CombatManager, CombatState, CombatAction, CombatResult, 
    CombatTurn, CombatStats, combat_manager
)
from src.character.character import Character
from src.character.party import Party
from src.character.stats import BaseStats
from src.monsters.monster import Monster, MonsterType, MonsterSize, MonsterStats


class TestCombatManager:
    """戦闘管理システムのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.combat_manager = CombatManager()
        
        # テスト用パーティ作成
        stats1 = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        stats2 = BaseStats(strength=12, agility=14, intelligence=16, faith=12, luck=11)
        
        self.character1 = Character.create_character("Fighter", "human", "fighter", stats1)
        self.character2 = Character.create_character("Mage", "elf", "mage", stats2)
        
        self.party = Party(party_id="test_party", name="TestParty")
        self.party.add_character(self.character1)
        self.party.add_character(self.character2)
        
        # テスト用モンスター作成
        monster_stats = MonsterStats(
            level=3,
            hit_points=20,
            armor_class=12,
            attack_bonus=3,
            damage_dice="1d6+1",
            strength=14,
            agility=10
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
    
    def test_combat_manager_initialization(self):
        """戦闘マネージャー初期化テスト"""
        assert self.combat_manager.combat_state == CombatState.PREPARATION
        assert self.combat_manager.party is None
        assert len(self.combat_manager.monsters) == 0
        assert len(self.combat_manager.turn_order) == 0
        assert self.combat_manager.turn_number == 1
    
    def test_start_combat_success(self):
        """戦闘開始成功テスト"""
        success = self.combat_manager.start_combat(self.party, self.monsters)
        
        assert success == True
        assert self.combat_manager.combat_state == CombatState.IN_PROGRESS
        assert self.combat_manager.party == self.party
        assert self.combat_manager.monsters == self.monsters
        assert len(self.combat_manager.turn_order) == 3  # 2キャラ + 1モンスター
    
    def test_start_combat_no_living_characters(self):
        """生存キャラクターなしでの戦闘開始テスト"""
        # キャラクターを全員死亡させる
        self.character1.take_damage(1000)
        self.character2.take_damage(1000)
        
        success = self.combat_manager.start_combat(self.party, self.monsters)
        
        assert success == False
        assert self.combat_manager.combat_state == CombatState.PREPARATION
    
    def test_start_combat_no_living_monsters(self):
        """生存モンスターなしでの戦闘開始テスト"""
        # モンスターを死亡させる
        self.monster.take_damage(1000)
        
        success = self.combat_manager.start_combat(self.party, self.monsters)
        
        assert success == False
        assert self.combat_manager.combat_state == CombatState.PREPARATION
    
    def test_start_combat_already_in_progress(self):
        """既に戦闘中での戦闘開始テスト"""
        # 最初の戦闘開始
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # 2回目の戦闘開始（失敗すべき）
        success = self.combat_manager.start_combat(self.party, self.monsters)
        
        assert success == False
    
    def test_turn_order_determination(self):
        """ターン順序決定テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # ターン順序が敏捷性順になっているかチェック
        turn_order = self.combat_manager.turn_order
        agilities = [self.combat_manager._get_agility(actor) for actor in turn_order]
        
        # 敏捷性が降順になっていることを確認
        assert agilities == sorted(agilities, reverse=True)
    
    def test_get_current_actor(self):
        """現在のアクター取得テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        current_actor = self.combat_manager.get_current_actor()
        assert current_actor is not None
        assert current_actor in self.combat_manager.turn_order
    
    def test_is_player_turn(self):
        """プレイヤーターン判定テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # 最初のアクターがキャラクターかモンスターかで判定
        is_player = self.combat_manager.is_player_turn()
        current_actor = self.combat_manager.get_current_actor()
        
        expected = isinstance(current_actor, Character)
        assert is_player == expected
    
    @patch('random.random')
    def test_execute_attack_hit(self, mock_random):
        """攻撃実行（命中）テスト"""
        # 必ず命中するように設定
        mock_random.return_value = 0.1  # 命中率より低い値
        
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # 攻撃対象を設定
        attacker = self.combat_manager.get_current_actor()
        if isinstance(attacker, Character):
            target = self.monster
        else:
            target = self.character1
        
        initial_hp = target.current_hp if hasattr(target, 'current_hp') else target.derived_stats.current_hp
        
        # 攻撃実行
        result = self.combat_manager.execute_action(CombatAction.ATTACK, target)
        
        # HPが減少していることを確認
        final_hp = target.current_hp if hasattr(target, 'current_hp') else target.derived_stats.current_hp
        assert final_hp < initial_hp
        assert result == CombatResult.CONTINUE
    
    @patch('random.random')
    def test_execute_attack_miss(self, mock_random):
        """攻撃実行（外れ）テスト"""
        # 必ず外れるように設定
        mock_random.return_value = 0.99  # 命中率より高い値
        
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # 攻撃対象を設定
        attacker = self.combat_manager.get_current_actor()
        if isinstance(attacker, Character):
            target = self.monster
        else:
            target = self.character1
        
        initial_hp = target.current_hp if hasattr(target, 'current_hp') else target.derived_stats.current_hp
        
        # 攻撃実行
        result = self.combat_manager.execute_action(CombatAction.ATTACK, target)
        
        # HPが変化していないことを確認
        final_hp = target.current_hp if hasattr(target, 'current_hp') else target.derived_stats.current_hp
        assert final_hp == initial_hp
        assert result == CombatResult.CONTINUE
    
    def test_execute_defend(self):
        """防御実行テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # 防御実行
        result = self.combat_manager.execute_action(CombatAction.DEFEND)
        
        assert result == CombatResult.CONTINUE
        # 防御状態が付与されたかチェック（状態効果システムと連携）
    
    @patch('random.random')
    def test_execute_flee_success(self, mock_random):
        """逃走成功テスト"""
        # 必ず逃走成功するように設定
        mock_random.return_value = 0.1
        
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # キャラクターのターンまで進める
        while not self.combat_manager.is_player_turn():
            self.combat_manager._advance_turn()
        
        # 逃走実行
        result = self.combat_manager.execute_action(CombatAction.FLEE)
        
        assert result == CombatResult.FLED
        assert self.combat_manager.combat_state == CombatState.FLED
    
    @patch('random.random')
    def test_execute_flee_failure(self, mock_random):
        """逃走失敗テスト"""
        # 必ず逃走失敗するように設定
        mock_random.return_value = 0.99
        
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # キャラクターのターンまで進める
        while not self.combat_manager.is_player_turn():
            self.combat_manager._advance_turn()
        
        # 逃走実行
        result = self.combat_manager.execute_action(CombatAction.FLEE)
        
        assert result == CombatResult.CONTINUE
        assert self.combat_manager.combat_state == CombatState.IN_PROGRESS
    
    def test_combat_victory_condition(self):
        """戦闘勝利条件テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # モンスターを全て倒す
        for monster in self.monsters:
            monster.take_damage(1000)
        
        # 戦闘終了条件チェック
        result = self.combat_manager._check_combat_end()
        
        assert result == CombatResult.VICTORY
        assert self.combat_manager.combat_state == CombatState.VICTORY
    
    def test_combat_defeat_condition(self):
        """戦闘敗北条件テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # キャラクターを全て倒す
        self.character1.take_damage(1000)
        self.character2.take_damage(1000)
        
        # 戦闘終了条件チェック
        result = self.combat_manager._check_combat_end()
        
        assert result == CombatResult.DEFEAT
        assert self.combat_manager.combat_state == CombatState.DEFEAT
    
    def test_turn_advancement(self):
        """ターン進行テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        initial_actor = self.combat_manager.get_current_actor()
        initial_turn = self.combat_manager.turn_number
        
        # ターン進行
        self.combat_manager._advance_turn()
        
        new_actor = self.combat_manager.get_current_actor()
        
        # アクターが変わったことを確認
        assert new_actor != initial_actor or self.combat_manager.turn_number > initial_turn
    
    def test_get_valid_targets_character_attack(self):
        """キャラクター攻撃の有効対象取得テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        targets = self.combat_manager.get_valid_targets(self.character1, CombatAction.ATTACK)
        
        # モンスターのみが対象
        assert len(targets) == len([m for m in self.monsters if m.is_alive])
        assert all(isinstance(target, Monster) for target in targets)
    
    def test_get_valid_targets_monster_attack(self):
        """モンスター攻撃の有効対象取得テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        targets = self.combat_manager.get_valid_targets(self.monster, CombatAction.ATTACK)
        
        # キャラクターのみが対象
        living_chars = self.party.get_living_characters()
        assert len(targets) == len(living_chars)
        assert all(isinstance(target, Character) for target in targets)
    
    def test_get_valid_targets_item_use(self):
        """アイテム使用の有効対象取得テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        targets = self.combat_manager.get_valid_targets(self.character1, CombatAction.USE_ITEM)
        
        # 味方キャラクターのみが対象
        living_chars = self.party.get_living_characters()
        assert len(targets) == len(living_chars)
        assert all(isinstance(target, Character) for target in targets)
    
    def test_combat_status_tracking(self):
        """戦闘状況追跡テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        status = self.combat_manager.get_combat_status()
        
        assert status['state'] == CombatState.IN_PROGRESS.value
        assert status['turn_number'] == 1
        assert status['party_members'] == 2
        assert status['monsters_alive'] == 1
        assert isinstance(status['party_stats'], CombatStats)
    
    def test_damage_calculation(self):
        """ダメージ計算テスト"""
        damage = self.combat_manager._calculate_damage(self.character1, self.monster)
        
        # ダメージが正の値であることを確認
        assert damage > 0
        assert isinstance(damage, int)
    
    def test_hit_chance_calculation(self):
        """命中率計算テスト"""
        hit_chance = self.combat_manager._check_hit(self.character1, self.monster)
        
        # 命中率がブール値であることを確認
        assert isinstance(hit_chance, bool)
    
    def test_flee_chance_calculation(self):
        """逃走成功率計算テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        flee_chance = self.combat_manager._calculate_flee_chance()
        
        # 0-1の範囲内であることを確認
        assert 0.0 <= flee_chance <= 1.0
    
    def test_negotiate_chance_calculation(self):
        """交渉成功率計算テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        negotiate_chance = self.combat_manager._calculate_negotiate_chance()
        
        # 0-1の範囲内であることを確認
        assert 0.0 <= negotiate_chance <= 1.0
    
    def test_combat_reset(self):
        """戦闘リセットテスト"""
        # 戦闘開始
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # いくつかの行動を実行
        self.combat_manager.execute_action(CombatAction.ATTACK, self.monster)
        
        # リセット
        self.combat_manager.reset_combat()
        
        # 初期状態に戻っていることを確認
        assert self.combat_manager.combat_state == CombatState.PREPARATION
        assert self.combat_manager.party is None
        assert len(self.combat_manager.monsters) == 0
        assert len(self.combat_manager.turn_order) == 0
        assert self.combat_manager.turn_number == 1
        assert len(self.combat_manager.combat_log) == 0
    
    def test_combat_log_tracking(self):
        """戦闘ログ追跡テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        initial_log_size = len(self.combat_manager.combat_log)
        
        # 行動実行
        self.combat_manager.execute_action(CombatAction.ATTACK, self.monster)
        
        # ログが追加されたことを確認
        assert len(self.combat_manager.combat_log) == initial_log_size + 1
        
        # ログの内容確認
        last_turn = self.combat_manager.combat_log[-1]
        assert isinstance(last_turn, CombatTurn)
        assert last_turn.action == CombatAction.ATTACK
    
    def test_turn_effects_processing(self):
        """ターン効果処理テスト"""
        self.combat_manager.start_combat(self.party, self.monsters)
        
        # ターン効果処理を実行（エラーが発生しないことを確認）
        try:
            self.combat_manager._process_turn_effects()
        except Exception as e:
            pytest.fail(f"ターン効果処理でエラーが発生: {e}")
    
    def test_actor_name_retrieval(self):
        """アクター名取得テスト"""
        char_name = self.combat_manager._get_actor_name(self.character1)
        monster_name = self.combat_manager._get_actor_name(self.monster)
        
        assert char_name == self.character1.name
        assert monster_name == self.monster.name


class TestCombatStats:
    """戦闘統計のテスト"""
    
    def test_combat_stats_initialization(self):
        """戦闘統計初期化テスト"""
        stats = CombatStats()
        
        assert stats.total_damage_dealt == 0
        assert stats.total_damage_taken == 0
        assert stats.spells_cast == 0
        assert stats.items_used == 0
        assert stats.turns_taken == 0
        assert stats.critical_hits == 0


class TestCombatTurn:
    """戦闘ターンのテスト"""
    
    def test_combat_turn_creation(self):
        """戦闘ターン作成テスト"""
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("TestChar", "human", "fighter", stats)
        
        turn = CombatTurn(
            turn_number=1,
            actor=character,
            action=CombatAction.ATTACK,
            result="攻撃成功",
            damage_dealt=10
        )
        
        assert turn.turn_number == 1
        assert turn.actor == character
        assert turn.action == CombatAction.ATTACK
        assert turn.result == "攻撃成功"
        assert turn.damage_dealt == 10


class TestGlobalCombatManager:
    """グローバル戦闘マネージャーテスト"""
    
    def test_global_combat_manager_exists(self):
        """グローバル戦闘マネージャー存在テスト"""
        assert combat_manager is not None
        assert isinstance(combat_manager, CombatManager)
    
    def test_global_combat_manager_initialization(self):
        """グローバル戦闘マネージャー初期化テスト"""
        assert combat_manager.combat_state == CombatState.PREPARATION
        assert combat_manager.party is None
        assert len(combat_manager.monsters) == 0