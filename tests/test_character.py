"""キャラクタークラスのテスト"""

import pytest
from src.character.character import Character, CharacterStatus
from src.character.stats import BaseStats


@pytest.mark.unit
class TestCharacter:
    """Characterのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # テスト用の統計値
        self.test_stats = BaseStats(
            strength=15, agility=12, intelligence=14, faith=10, luck=13
        )
    
    def test_character_creation(self):
        """キャラクター作成のテスト"""
        character = Character.create_character(
            name="TestHero",
            race="human",
            character_class="fighter",
            base_stats=self.test_stats
        )
        
        assert character.name == "TestHero"
        assert character.race == "human"
        assert character.character_class == "fighter"
        assert character.status == CharacterStatus.GOOD
        assert character.experience.level == 1
    
    def test_take_damage(self):
        """ダメージ処理のテスト"""
        character = Character.create_character(
            name="TestHero", race="human", character_class="fighter", base_stats=self.test_stats
        )
        
        initial_hp = character.derived_stats.current_hp
        character.take_damage(5)
        
        assert character.derived_stats.current_hp == initial_hp - 5
        assert character.status == CharacterStatus.GOOD
    
    def test_heal(self):
        """回復処理のテスト"""
        character = Character.create_character(
            name="TestHero", race="human", character_class="fighter", base_stats=self.test_stats
        )
        
        # ダメージを与えてから回復
        character.take_damage(10)
        damaged_hp = character.derived_stats.current_hp
        character.heal(5)
        
        assert character.derived_stats.current_hp == damaged_hp + 5
    
    def test_serialization(self):
        """シリアライゼーションのテスト"""
        character = Character.create_character(
            name="TestHero", race="human", character_class="fighter", base_stats=self.test_stats
        )
        
        # 辞書化してから復元
        data = character.to_dict()
        restored = Character.from_dict(data)
        
        assert restored.name == character.name
        assert restored.race == character.race
        assert restored.character_class == character.character_class
        assert restored.base_stats.strength == character.base_stats.strength
    
    def test_character_status_effects(self):
        """キャラクターステータス効果のテスト"""
        character = Character.create_character(
            name="TestHero", race="human", character_class="fighter", base_stats=self.test_stats
        )
        
        # 初期状態は正常
        assert character.status == CharacterStatus.GOOD
        
        # HPが0になると状態が変化（死亡または気絶）
        initial_hp = character.derived_stats.current_hp
        character.take_damage(initial_hp)  # 全HPを失う
        
        # 状態が正常でなくなることを確認
        assert character.status != CharacterStatus.GOOD
    
    def test_character_level_progression(self):
        """キャラクターレベル進行のテスト"""
        character = Character.create_character(
            name="TestHero", race="human", character_class="fighter", base_stats=self.test_stats
        )
        
        initial_level = character.experience.level
        # 経験値テーブルは実装依存のため、基本的な動作のみテスト
        assert initial_level >= 1
        assert character.experience.current_xp >= 0


@pytest.mark.unit
class TestCharacterKnownSpells:
    """Character known_spells属性のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.test_stats = BaseStats(
            strength=15, agility=12, intelligence=14, faith=10, luck=13
        )
    
    def test_known_spells_initialization(self):
        """known_spells属性の初期化テスト"""
        # 初期魔法を持たない戦士でテスト
        character = Character.create_character(
            name="TestFighter", race="human", character_class="fighter", base_stats=self.test_stats
        )
        
        # known_spells属性が存在し、空のリストで初期化されることを確認
        assert hasattr(character, 'known_spells')
        assert isinstance(character.known_spells, list)
        assert len(character.known_spells) == 0
    
    def test_learn_spell(self):
        """魔法習得メソッドのテスト"""
        character = Character.create_character(
            name="TestMage", race="human", character_class="mage", base_stats=self.test_stats
        )
        
        # 初期魔法fireは既に習得済みなので、別の魔法で習得テスト
        initial_spell_count = len(character.known_spells)
        result = character.learn_spell("lightning")
        assert result is True
        assert "lightning" in character.known_spells
        assert len(character.known_spells) == initial_spell_count + 1
        
        # 既に習得している魔法は重複しない
        result = character.learn_spell("lightning")
        assert result is False
        assert len(character.known_spells) == initial_spell_count + 1
    
    def test_forget_spell(self):
        """魔法忘却メソッドのテスト"""
        character = Character.create_character(
            name="TestMage", race="human", character_class="mage", base_stats=self.test_stats
        )
        
        # まず魔法を習得
        character.learn_spell("fire")
        character.learn_spell("lightning")
        assert len(character.known_spells) == 2
        
        # 魔法を忘却
        result = character.forget_spell("fire")
        assert result is True
        assert "fire" not in character.known_spells
        assert "lightning" in character.known_spells
        assert len(character.known_spells) == 1
        
        # 存在しない魔法の忘却は失敗
        result = character.forget_spell("fire")
        assert result is False
        assert len(character.known_spells) == 1
    
    def test_has_spell(self):
        """魔法習得確認メソッドのテスト"""
        character = Character.create_character(
            name="TestMage", race="human", character_class="mage", base_stats=self.test_stats
        )
        
        # 初期魔法fireは既に習得済み
        assert character.has_spell("fire") is True
        
        # 未習得の魔法は確認できない
        assert character.has_spell("lightning") is False
        
        # 魔法習得後は確認できる
        character.learn_spell("lightning")
        assert character.has_spell("lightning") is True
    
    def test_known_spells_serialization(self):
        """known_spells属性のシリアライゼーションテスト"""
        character = Character.create_character(
            name="TestMage", race="human", character_class="mage", base_stats=self.test_stats
        )
        
        # 初期魔法の確認
        initial_spells = character.known_spells.copy()
        
        # 追加で魔法を習得
        character.learn_spell("lightning")
        
        # シリアライゼーション
        data = character.to_dict()
        assert "known_spells" in data
        assert isinstance(data["known_spells"], list)
        assert "fire" in data["known_spells"]  # 初期魔法
        assert "lightning" in data["known_spells"]  # 新規習得
        
        # デシリアライゼーション
        restored = Character.from_dict(data)
        assert hasattr(restored, 'known_spells')
        assert isinstance(restored.known_spells, list)
        assert len(restored.known_spells) == len(initial_spells) + 1
        assert "fire" in restored.known_spells
        assert "lightning" in restored.known_spells
    
    def test_class_spell_restrictions(self):
        """職業による魔法習得制限のテスト"""
        # 魔術師：魔術のみ習得可能
        mage = Character.create_character(
            name="TestMage", race="human", character_class="mage", base_stats=self.test_stats
        )
        
        # 魔術師は初期魔法fire習得済み、他の魔術は習得可能
        assert mage.learn_spell("lightning") is True  # 魔術
        assert "lightning" in mage.known_spells
        
        # 魔術師は祈祷を習得不可
        assert mage.learn_spell("heal") is False  # 祈祷
        assert "heal" not in mage.known_spells
        
        # 僧侶：祈祷のみ習得可能
        priest = Character.create_character(
            name="TestPriest", race="human", character_class="priest", 
            base_stats=BaseStats(strength=10, agility=10, intelligence=10, faith=15, luck=10)
        )
        
        # 僧侶は初期魔法heal習得済み、他の祈祷は習得可能
        assert "heal" in priest.known_spells  # 初期習得確認
        assert priest.learn_spell("cure") is True  # 祈祷
        assert "cure" in priest.known_spells
        
        # 僧侶は魔術を習得不可
        assert priest.learn_spell("fire") is False  # 魔術
        assert "fire" not in priest.known_spells
    
    def test_spellbook_integration(self):
        """SpellBookとの統合テスト"""
        character = Character.create_character(
            name="TestMage", race="human", character_class="mage", base_stats=self.test_stats
        )
        
        # キャラクターで魔法を習得
        character.learn_spell("fire")
        character.learn_spell("lightning")
        
        # SpellBookを取得（初回は同期される）
        spellbook = character.get_spellbook()
        
        # SpellBookの習得魔法リストが同期されていることを確認
        assert "fire" in spellbook.learned_spells
        assert "lightning" in spellbook.learned_spells
        assert len(spellbook.learned_spells) == 2
        
        # キャラクターが魔法を忘却すると同期は手動で行う必要がある
        # （この統合では基本的な同期動作のみテスト）
        assert character.has_spell("fire") is True
        assert character.has_spell("lightning") is True
    
    def test_initial_spell_learning(self):
        """初期魔法習得のテスト"""
        # 魔術師は初期魔法としてfireを習得
        mage = Character.create_character(
            name="TestMage", race="human", character_class="mage", base_stats=self.test_stats
        )
        assert len(mage.known_spells) == 1
        assert "fire" in mage.known_spells
        
        # 僧侶は初期魔法としてhealを習得
        priest = Character.create_character(
            name="TestPriest", race="human", character_class="priest", 
            base_stats=BaseStats(strength=10, agility=10, intelligence=10, faith=15, luck=10)
        )
        assert len(priest.known_spells) == 1
        assert "heal" in priest.known_spells
        
        # 戦士は初期魔法なし
        fighter = Character.create_character(
            name="TestFighter", race="human", character_class="fighter", base_stats=self.test_stats
        )
        assert len(fighter.known_spells) == 0