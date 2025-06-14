"""アイテム使用システムのテスト"""

import pytest
from src.items.item_usage import ItemUsageManager, UsageResult, item_usage_manager
from src.items.item import ItemInstance, item_manager
from src.character.character import Character, CharacterStatus
from src.character.stats import BaseStats
from src.character.party import Party


class TestItemUsage:
    """アイテム使用システムのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.usage_manager = ItemUsageManager()
        
        # テスト用キャラクター作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        self.character = Character.create_character("TestHero", "human", "fighter", stats)
        
        # テスト用パーティ作成
        self.party = Party(party_id="test_party")
        self.party.add_character(self.character)
    
    def test_hp_healing_item_usage(self):
        """HP回復アイテム使用テスト"""
        # 回復ポーションのアイテムインスタンス作成
        potion_instance = ItemInstance(item_id="healing_potion", quantity=1, identified=True)
        
        # キャラクターのHPを減らす
        self.character.take_damage(20)
        old_hp = self.character.derived_stats.current_hp
        
        # アイテム使用
        result, message, results = self.usage_manager.use_item(
            potion_instance, self.character, self.character, self.party
        )
        
        # 結果確認
        assert result == UsageResult.SUCCESS
        assert "HP" in message and "回復" in message
        assert self.character.derived_stats.current_hp > old_hp
        assert potion_instance.quantity == 0  # アイテムが消費されている
        assert 'healed_amount' in results
        assert results['target'] == self.character.name
    
    def test_mp_healing_item_usage(self):
        """MP回復アイテム使用テスト"""
        # マナポーションのアイテムインスタンス作成
        mana_potion_instance = ItemInstance(item_id="mana_potion", quantity=1, identified=True)
        
        # キャラクターのMPを減らす
        self.character.derived_stats.current_mp = self.character.derived_stats.max_mp // 2
        old_mp = self.character.derived_stats.current_mp
        
        # アイテム使用
        result, message, results = self.usage_manager.use_item(
            mana_potion_instance, self.character, self.character, self.party
        )
        
        # 結果確認
        assert result == UsageResult.SUCCESS
        assert "MP" in message and "回復" in message
        assert self.character.derived_stats.current_mp > old_mp
        assert mana_potion_instance.quantity == 0  # アイテムが消費されている
        assert 'restored_amount' in results
    
    def test_unidentified_item_usage(self):
        """未鑑定アイテム使用テスト"""
        # 未鑑定のアイテムインスタンス作成
        unidentified_item = ItemInstance(item_id="healing_potion", quantity=1, identified=False)
        
        # アイテム使用（失敗するはず）
        result, message, results = self.usage_manager.use_item(
            unidentified_item, self.character, self.character, self.party
        )
        
        # 結果確認
        assert result == UsageResult.CANNOT_USE
        assert "未鑑定" in message
        assert unidentified_item.quantity == 1  # アイテムは消費されていない
    
    def test_insufficient_quantity_usage(self):
        """数量不足アイテム使用テスト"""
        # 数量0のアイテムインスタンス作成
        empty_item = ItemInstance(item_id="healing_potion", quantity=0, identified=True)
        
        # アイテム使用（失敗するはず）
        result, message, results = self.usage_manager.use_item(
            empty_item, self.character, self.character, self.party
        )
        
        # 結果確認
        assert result == UsageResult.INSUFFICIENT_QUANTITY
        assert "アイテムがありません" in message
    
    def test_invalid_target_usage(self):
        """無効な対象でのアイテム使用テスト"""
        # 回復ポーション（対象が必要）
        potion_instance = ItemInstance(item_id="healing_potion", quantity=1, identified=True)
        
        # 対象なしでアイテム使用（失敗するはず）
        result, message, results = self.usage_manager.use_item(
            potion_instance, self.character, None, self.party
        )
        
        # 結果確認
        assert result == UsageResult.CANNOT_USE
        assert "対象を指定" in message
        assert potion_instance.quantity == 1  # アイテムは消費されていない
    
    def test_revive_item_usage(self):
        """蘇生アイテム使用テスト"""
        # 蘇生の粉のアイテムインスタンス作成
        revive_item = ItemInstance(item_id="resurrection_powder", quantity=1, identified=True)
        
        # 対象キャラクターを作成し、死亡状態にする
        stats2 = BaseStats(strength=12, agility=10, intelligence=16, faith=14, luck=8)
        dead_character = Character.create_character("DeadHero", "elf", "priest", stats2)
        dead_character.status = CharacterStatus.DEAD
        dead_character.derived_stats.current_hp = 0
        
        # パーティに追加
        self.party.add_character(dead_character)
        
        # アイテム使用
        result, message, results = self.usage_manager.use_item(
            revive_item, self.character, dead_character, self.party
        )
        
        # 結果確認
        assert result == UsageResult.SUCCESS
        assert "蘇生" in message
        assert dead_character.status == CharacterStatus.GOOD
        assert dead_character.derived_stats.current_hp > 0
        assert revive_item.quantity == 0  # アイテムが消費されている
        assert results['revived'] == True
    
    def test_revive_item_on_living_character(self):
        """生存キャラクターへの蘇生アイテム使用テスト"""
        # 蘇生の粉のアイテムインスタンス作成
        revive_item = ItemInstance(item_id="resurrection_powder", quantity=1, identified=True)
        
        # 生存しているキャラクターに使用（失敗するはず）
        result, message, results = self.usage_manager.use_item(
            revive_item, self.character, self.character, self.party
        )
        
        # 結果確認
        assert result == UsageResult.CANNOT_USE
        assert "死亡していません" in message
        assert revive_item.quantity == 1  # アイテムは消費されていない
    
    def test_multiple_item_usage(self):
        """複数個アイテムの連続使用テスト"""
        # 複数個の回復ポーション
        potion_instance = ItemInstance(item_id="healing_potion", quantity=3, identified=True)
        
        # キャラクターのHPを少し減らす（3回回復で満タンにならないように）
        max_hp = self.character.derived_stats.max_hp
        self.character.take_damage(max_hp - 5)  # HPを5にする
        initial_quantity = potion_instance.quantity
        
        # 3回使用
        for i in range(3):
            old_hp = self.character.derived_stats.current_hp
            
            result, message, results = self.usage_manager.use_item(
                potion_instance, self.character, self.character, self.party
            )
            
            assert result == UsageResult.SUCCESS
            # HPが満タンでない場合のみ回復量をチェック
            if old_hp < self.character.derived_stats.max_hp:
                assert self.character.derived_stats.current_hp >= old_hp
            assert potion_instance.quantity == initial_quantity - (i + 1)
        
        # 4回目の使用（失敗するはず）
        result, message, results = self.usage_manager.use_item(
            potion_instance, self.character, self.character, self.party
        )
        
        assert result == UsageResult.INSUFFICIENT_QUANTITY
    
    def test_can_use_item_check(self):
        """アイテム使用可能性チェックテスト"""
        # 回復ポーション
        healing_potion = item_manager.get_item("healing_potion")
        assert healing_potion is not None
        
        # 生存キャラクターに対して使用可能
        can_use, reason = self.usage_manager.can_use_item(healing_potion, self.character, self.character)
        assert can_use == True
        assert reason == ""
        
        # 対象なしで使用不可
        can_use, reason = self.usage_manager.can_use_item(healing_potion, self.character, None)
        assert can_use == False
        assert "対象を指定" in reason
    
    def test_item_usage_info(self):
        """アイテム使用情報取得テスト"""
        # 回復ポーション
        healing_potion = item_manager.get_item("healing_potion")
        assert healing_potion is not None
        
        info = self.usage_manager.get_item_usage_info(healing_potion)
        
        assert info['usable'] == True
        assert info['effect_type'] == healing_potion.get_effect_type()
        assert info['effect_value'] == healing_potion.get_effect_value()
        assert info['target_required'] == True  # HP回復は対象が必要
        assert 'description' in info
        assert "HP" in info['description']
        
        # 武器（使用不可アイテム）
        dagger = item_manager.get_item("dagger")
        assert dagger is not None
        
        weapon_info = self.usage_manager.get_item_usage_info(dagger)
        assert weapon_info['usable'] == False
        assert "消耗品ではありません" in weapon_info['reason']
    
    def test_get_usable_items_for_character(self):
        """キャラクター使用可能アイテム一覧取得テスト"""
        # テスト用アイテムリスト作成
        inventory_items = [
            (None, ItemInstance(item_id="healing_potion", quantity=1, identified=True)),
            (None, ItemInstance(item_id="mana_potion", quantity=2, identified=True)),
            (None, ItemInstance(item_id="dagger", quantity=1, identified=True)),  # 武器（使用不可）
            (None, ItemInstance(item_id="antidote", quantity=1, identified=False)),  # 未鑑定（使用不可）
            (None, ItemInstance(item_id="torch", quantity=1, identified=True))
        ]
        
        # 使用可能アイテムを取得
        usable_items = self.usage_manager.get_usable_items_for_character(self.character, inventory_items)
        
        # 結果確認
        usable_item_ids = [item.item_id for _, _, item in usable_items]
        
        # 回復ポーション、マナポーションは使用可能
        assert "healing_potion" in usable_item_ids
        assert "mana_potion" in usable_item_ids
        # 松明はtoolタイプのため使用可能アイテムには含まれない
        
        # ダガー（武器）と未鑑定解毒剤は使用不可
        assert "dagger" not in usable_item_ids
        assert "antidote" not in usable_item_ids
    
    def test_effect_descriptions(self):
        """効果説明文生成テスト"""
        descriptions = [
            ('heal_hp', 30, 'HPを30回復します'),
            ('heal_mp', 20, 'MPを20回復します'),
            ('cure_poison', 0, '毒状態を治療します'),
            ('revive', 50, '死亡したキャラクターを最大HPの50%で蘇生します'),
            ('light', 5, '5ターンの間、光で照らします'),
            ('unknown_effect', 10, '不明な効果')
        ]
        
        for effect_type, effect_value, expected in descriptions:
            description = self.usage_manager._get_effect_description(effect_type, effect_value)
            assert description == expected
    
    def test_status_cure_items(self):
        """状態異常治療アイテムテスト"""
        # 解毒剤
        antidote_instance = ItemInstance(item_id="antidote", quantity=1, identified=True)
        
        # アイテム使用（状態異常システム未実装のため、基本的な動作確認のみ）
        result, message, results = self.usage_manager.use_item(
            antidote_instance, self.character, self.character, self.party
        )
        
        # 結果確認
        assert result == UsageResult.SUCCESS
        assert "毒" in message and "治療" in message
        assert antidote_instance.quantity == 0  # アイテムが消費されている
        assert 'cured' in results
        assert results['cured'] == 'poison'