"""ゲームバランステスト"""

import unittest
from typing import Dict, List
import statistics

from src.dungeon.trap_system import TrapSystem, TrapType
from src.dungeon.treasure_system import TreasureSystem, TreasureType  
from src.dungeon.boss_system import BossSystem, BossType
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.character.stats import BaseStats, DerivedStats
from src.character.character import Experience


class TestGameBalance(unittest.TestCase):
    """ゲームバランステスト"""
    
    def setUp(self):
        self.trap_sys = TrapSystem()
        self.treasure_sys = TreasureSystem()
        self.boss_sys = BossSystem()
        self.party = self._create_balanced_party()
    
    def _create_balanced_party(self) -> Party:
        """バランス調整用パーティ作成"""
        party = Party("BalanceTestParty")
        
        # 戦士（レベル5）
        fighter = Character(
            name="BalanceFighter",
            race="human",
            character_class="fighter", 
            base_stats=BaseStats(strength=16, agility=12, intelligence=10, faith=8, luck=10),
            derived_stats=DerivedStats(max_hp=50, current_hp=50, max_mp=10, current_mp=10),
            experience=Experience(level=5)
        )
        
        # 盗賊（レベル5）
        thief = Character(
            name="BalanceThief",
            race="human",
            character_class="thief",
            base_stats=BaseStats(strength=12, agility=18, intelligence=14, faith=6, luck=12),
            derived_stats=DerivedStats(max_hp=35, current_hp=35, max_mp=15, current_mp=15),
            experience=Experience(level=5)
        )
        
        # 魔法使い（レベル5）
        mage = Character(
            name="BalanceMage",
            race="elf",
            character_class="mage",
            base_stats=BaseStats(strength=8, agility=12, intelligence=18, faith=14, luck=10),
            derived_stats=DerivedStats(max_hp=25, current_hp=25, max_mp=40, current_mp=40),
            experience=Experience(level=5)
        )
        
        party.add_character(fighter)
        party.add_character(thief)
        party.add_character(mage)
        party.gold = 1000
        
        return party
    
    def test_trap_damage_balance_by_level(self):
        """レベル別トラップダメージバランステスト"""
        damage_data = {}
        
        for level in [1, 5, 10, 15, 20]:
            damages = []
            for _ in range(100):
                result = self.trap_sys.activate_trap(TrapType.ARROW, self.party, level)
                if result["success"] and result["effects"]:
                    # ダメージ値を抽出
                    effect_text = result["effects"][0]
                    if "ダメージ" in effect_text:
                        import re
                        damage_match = re.search(r'(\d+)ダメージ', effect_text)
                        if damage_match:
                            damages.append(int(damage_match.group(1)))
            
            if damages:
                damage_data[level] = {
                    'min': min(damages),
                    'max': max(damages),
                    'avg': statistics.mean(damages),
                    'median': statistics.median(damages)
                }
        
        # レベルが上がるとダメージも増加するかチェック
        levels = sorted(damage_data.keys())
        for i in range(len(levels) - 1):
            current_level = levels[i]
            next_level = levels[i + 1]
            
            if current_level in damage_data and next_level in damage_data:
                current_avg = damage_data[current_level]['avg']
                next_avg = damage_data[next_level]['avg']
                
                # レベルが上がると平均ダメージも増加するはず
                self.assertGreater(next_avg, current_avg, 
                    f"レベル{next_level}の平均ダメージ({next_avg})がレベル{current_level}({current_avg})より低い")
    
    def test_treasure_value_progression(self):
        """宝箱価値の段階的進行テスト"""
        treasure_values = {}
        
        for level in [1, 5, 10, 15, 20]:
            values = []
            for treasure_type in [TreasureType.WOODEN, TreasureType.METAL, TreasureType.MAGICAL]:
                for _ in range(50):
                    # 開封状態をリセット
                    treasure_id = f"balance_test_{treasure_type.value}_{level}_{_}"
                    result = self.treasure_sys.open_treasure(
                        treasure_id, treasure_type, self.party, level
                    )
                    
                    if result["success"]:
                        total_value = result["gold"]
                        # アイテム価値も計算
                        for item in result.get("items", []):
                            if hasattr(item, 'base_price'):
                                total_value += item.base_price
                        values.append(total_value)
            
            if values:
                treasure_values[level] = {
                    'min': min(values),
                    'max': max(values), 
                    'avg': statistics.mean(values),
                    'count': len(values)
                }
        
        # レベルが上がると宝箱価値も増加するかチェック
        levels = sorted(treasure_values.keys())
        for i in range(len(levels) - 1):
            current_level = levels[i]
            next_level = levels[i + 1]
            
            if current_level in treasure_values and next_level in treasure_values:
                current_avg = treasure_values[current_level]['avg']
                next_avg = treasure_values[next_level]['avg']
                
                # レベルが上がると平均価値も増加するはず
                self.assertGreater(next_avg, current_avg,
                    f"レベル{next_level}の平均価値({next_avg})がレベル{current_level}({current_avg})より低い")
    
    def test_boss_difficulty_scaling(self):
        """ボスの難易度スケーリングテスト"""
        boss_stats = {}
        
        for level in [5, 10, 15, 20]:
            for boss_id in ["skeleton_king", "dragon_whelp", "ancient_golem"]:
                encounter = self.boss_sys.create_boss_encounter(boss_id, level, f"test_{boss_id}_{level}")
                if encounter:
                    boss_monster = encounter.initialize_boss_monster()
                    
                    boss_stats[f"{boss_id}_level_{level}"] = {
                        'hp': boss_monster.max_hp,
                        'attack': boss_monster.stats.attack_bonus,
                        'ac': boss_monster.stats.armor_class,
                        'level': boss_monster.stats.level
                    }
        
        # 同じボスでもレベルが上がると強くなるかチェック
        for boss_id in ["skeleton_king", "dragon_whelp", "ancient_golem"]:
            levels = [5, 10, 15, 20]
            for i in range(len(levels) - 1):
                current_key = f"{boss_id}_level_{levels[i]}"
                next_key = f"{boss_id}_level_{levels[i + 1]}"
                
                if current_key in boss_stats and next_key in boss_stats:
                    current_hp = boss_stats[current_key]['hp']
                    next_hp = boss_stats[next_key]['hp']
                    
                    # レベルが上がるとHPも増加するはず
                    self.assertGreater(next_hp, current_hp,
                        f"{boss_id}のレベル{levels[i + 1]}のHP({next_hp})がレベル{levels[i]}({current_hp})より低い")
    
    def test_survival_rate_balance(self):
        """生存率バランステスト"""
        survival_stats = {}
        
        for level in [1, 5, 10, 15]:
            surviving_parties = 0
            total_tests = 100
            
            for test_run in range(total_tests):
                # テスト用パーティ作成
                test_party = self._create_balanced_party()
                
                # 複数のトラップを連続で発動
                trap_count = level // 2 + 1  # レベルに応じてトラップ数調整
                for _ in range(trap_count):
                    trap_type = self.trap_sys.generate_random_trap(level)
                    result = self.trap_sys.activate_trap(trap_type, test_party, level)
                
                # 生存メンバーがいるかチェック
                living_count = len(test_party.get_living_characters())
                if living_count > 0:
                    surviving_parties += 1
            
            survival_rate = surviving_parties / total_tests
            survival_stats[level] = survival_rate
        
        # 生存率が適切な範囲にあるかチェック
        for level, rate in survival_stats.items():
            if level <= 5:
                # 低レベルでは80%以上の生存率
                self.assertGreater(rate, 0.8, f"レベル{level}の生存率{rate}が低すぎます")
            elif level <= 10:
                # 中レベルでは60%以上の生存率
                self.assertGreater(rate, 0.6, f"レベル{level}の生存率{rate}が低すぎます")
            else:
                # 高レベルでは40%以上の生存率
                self.assertGreater(rate, 0.4, f"レベル{level}の生存率{rate}が低すぎます")
    
    def test_reward_risk_balance(self):
        """報酬とリスクのバランステスト"""
        balance_data = {}
        
        for level in [1, 5, 10, 15, 20]:
            # 宝箱の期待値計算
            treasure_rewards = []
            treasure_risks = []
            
            for _ in range(100):
                treasure_type = self.treasure_sys.generate_treasure_type(level)
                treasure_id = f"risk_test_{level}_{_}"
                
                result = self.treasure_sys.open_treasure(
                    treasure_id, treasure_type, self.party, level
                )
                
                if result["success"]:
                    reward = result["gold"]
                    treasure_rewards.append(reward)
                
                # トラップリスク評価
                if result.get("trapped", False):
                    treasure_risks.append(1)
                else:
                    treasure_risks.append(0)
            
            if treasure_rewards:
                avg_reward = statistics.mean(treasure_rewards)
                risk_rate = statistics.mean(treasure_risks)
                
                balance_data[level] = {
                    'avg_reward': avg_reward,
                    'risk_rate': risk_rate,
                    'risk_reward_ratio': avg_reward / max(risk_rate, 0.01)
                }
        
        # レベルが上がると報酬も増加するがリスクも増加するかチェック
        levels = sorted(balance_data.keys())
        for i in range(len(levels) - 1):
            current = balance_data[levels[i]]
            next_level = balance_data[levels[i + 1]]
            
            # 報酬増加チェック
            self.assertGreater(next_level['avg_reward'], current['avg_reward'],
                f"レベル{levels[i + 1]}の報酬が前レベルより低い")
    
    def test_character_class_balance(self):
        """キャラクタークラスバランステスト"""
        class_performance = {}
        
        # 各クラスの特殊能力テスト
        classes = ["fighter", "thief", "mage", "priest"]
        
        for char_class in classes:
            # クラス特化能力テスト
            test_character = Character(
                name=f"Test{char_class}",
                race="human",
                character_class=char_class,
                base_stats=BaseStats(strength=15, agility=15, intelligence=15, faith=15, luck=10),
                derived_stats=DerivedStats(max_hp=40, current_hp=40, max_mp=30, current_mp=30),
                experience=Experience(level=5)
            )
            
            performance = {}
            
            # トラップ発見・解除能力（盗賊が有利なはず）
            detection_success = 0
            disarm_success = 0
            for _ in range(100):
                if self.trap_sys.can_detect_trap(test_character, TrapType.ARROW):
                    detection_success += 1
                if self.trap_sys.can_disarm_trap(test_character, TrapType.ARROW):
                    disarm_success += 1
            
            performance['trap_detection'] = detection_success / 100
            performance['trap_disarm'] = disarm_success / 100
            
            # 鍵開け能力（盗賊が有利なはず）
            lockpick_success = 0
            for _ in range(100):
                if self.treasure_sys._attempt_lock_picking(30, test_character):
                    lockpick_success += 1
            
            performance['lockpicking'] = lockpick_success / 100
            
            class_performance[char_class] = performance
        
        # 盗賊のトラップ・鍵開け能力が他より高いかチェック
        thief_performance = class_performance.get("thief", {})
        for other_class in ["fighter", "mage", "priest"]:
            if other_class in class_performance:
                other_performance = class_performance[other_class]
                
                self.assertGreater(thief_performance.get('trap_detection', 0),
                                 other_performance.get('trap_detection', 0),
                                 f"盗賊のトラップ発見能力が{other_class}より低い")
                
                self.assertGreater(thief_performance.get('lockpicking', 0),
                                 other_performance.get('lockpicking', 0),
                                 f"盗賊の鍵開け能力が{other_class}より低い")


if __name__ == '__main__':
    unittest.main()