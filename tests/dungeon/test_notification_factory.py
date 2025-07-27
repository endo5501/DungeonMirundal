"""通知ファクトリーシステムのテスト"""

import pytest
from unittest.mock import Mock, patch
import time

from src.dungeon.base.notification_factory import NotificationFactory, NotificationType, Notification


class TestNotification:
    """Notificationクラスのテスト"""
    
    def test_notification_creation(self):
        """通知作成のテスト"""
        notification = Notification("テストメッセージ", NotificationType.INFO)
        
        assert notification.message == "テストメッセージ"
        assert notification.notification_type == NotificationType.INFO
        assert notification.duration == 3.0
        assert notification.timestamp > 0
    
    def test_notification_custom_duration(self):
        """カスタム持続時間のテスト"""
        notification = Notification("テスト", NotificationType.WARNING, 5.0)
        
        assert notification.duration == 5.0
    
    def test_timestamp_auto_set(self):
        """タイムスタンプ自動設定のテスト"""
        with patch('time.time', return_value=1234567890):
            notification = Notification("テスト", NotificationType.INFO)
            assert notification.timestamp == 1234567890


class TestNotificationFactory:
    """NotificationFactoryクラスのテスト"""
    
    def test_factory_initialization(self):
        """ファクトリー初期化のテスト"""
        factory = NotificationFactory()
        
        assert NotificationType.INFO in factory.default_durations
        assert NotificationType.WARNING in factory.notification_icons
    
    def test_create_basic_notification(self):
        """基本通知作成のテスト"""
        factory = NotificationFactory()
        
        notification = factory.create_notification("テスト", NotificationType.INFO)
        
        assert notification.message == "ℹ️ テスト"
        assert notification.notification_type == NotificationType.INFO
        assert notification.duration == 3.0
    
    def test_create_notification_without_icon(self):
        """アイコンなし通知作成のテスト"""
        factory = NotificationFactory()
        
        notification = factory.create_notification("テスト", NotificationType.INFO, add_icon=False)
        
        assert notification.message == "テスト"
        assert notification.notification_type == NotificationType.INFO
    
    def test_create_notification_custom_duration(self):
        """カスタム持続時間通知のテスト"""
        factory = NotificationFactory()
        
        notification = factory.create_notification("テスト", NotificationType.WARNING, 10.0)
        
        assert notification.duration == 10.0
    
    def test_create_trap_notification_detected(self):
        """トラップ探知通知のテスト"""
        factory = NotificationFactory()
        
        notification = factory.create_trap_notification("毒針の罠", detected=True)
        
        assert "毒針の罠を発見しました！" in notification.message
        assert notification.notification_type == NotificationType.WARNING
        assert notification.duration == 5.0
    
    def test_create_trap_notification_triggered(self):
        """トラップ発動通知のテスト"""
        factory = NotificationFactory()
        
        notification = factory.create_trap_notification("毒針の罠", detected=False)
        
        assert "毒針の罠が発動しました！" in notification.message
        assert notification.notification_type == NotificationType.DANGER
        assert notification.duration == 4.0
    
    def test_create_treasure_notification_empty(self):
        """空の宝箱通知のテスト"""
        factory = NotificationFactory()
        
        notification = factory.create_treasure_notification("木製の宝箱", [])
        
        assert "木製の宝箱は空でした..." in notification.message
        assert notification.notification_type == NotificationType.INFO
    
    def test_create_treasure_notification_with_items(self):
        """アイテム入り宝箱通知のテスト"""
        factory = NotificationFactory()
        
        items = ["金貨", "回復ポーション", "鉄の剣"]
        notification = factory.create_treasure_notification("金属の宝箱", items)
        
        assert "金属の宝箱から" in notification.message
        assert "金貨, 回復ポーション, 鉄の剣" in notification.message
        assert notification.notification_type == NotificationType.LOOT
        assert notification.duration == 6.0
    
    def test_create_treasure_notification_many_items(self):
        """多数アイテム宝箱通知のテスト"""
        factory = NotificationFactory()
        
        items = ["アイテム1", "アイテム2", "アイテム3", "アイテム4", "アイテム5"]
        notification = factory.create_treasure_notification("魔法の宝箱", items)
        
        assert "など5個のアイテム" in notification.message
    
    def test_create_combat_notification_encounter_start(self):
        """戦闘開始通知のテスト"""
        factory = NotificationFactory()
        
        details = {"monster_name": "オーク"}
        notification = factory.create_combat_notification("encounter_start", details)
        
        assert "オークとの戦闘開始！" in notification.message
        assert notification.notification_type == NotificationType.COMBAT
    
    def test_create_combat_notification_victory(self):
        """戦闘勝利通知のテスト"""
        factory = NotificationFactory()
        
        details = {"experience": 100, "gold": 50}
        notification = factory.create_combat_notification("combat_victory", details)
        
        assert "勝利！ 経験値+100, 金貨+50" in notification.message
        assert notification.notification_type == NotificationType.SUCCESS
        assert notification.duration == 5.0
    
    def test_create_combat_notification_level_up(self):
        """レベルアップ通知のテスト"""
        factory = NotificationFactory()
        
        details = {"character_name": "アリス", "new_level": 5}
        notification = factory.create_combat_notification("level_up", details)
        
        assert "アリスがレベル5に上がりました！" in notification.message
        assert notification.notification_type == NotificationType.SUCCESS
        assert notification.duration == 4.0
    
    def test_create_party_status_notification_low_health(self):
        """低HP通知のテスト"""
        factory = NotificationFactory()
        
        details = {"current_hp": 25, "max_hp": 100}
        notification = factory.create_party_status_notification("low_health", "ボブ", details)
        
        assert "ボブのHPが低下（25%）" in notification.message
        assert notification.notification_type == NotificationType.WARNING
        assert notification.duration == 4.0
    
    def test_create_party_status_notification_death(self):
        """キャラクター死亡通知のテスト"""
        factory = NotificationFactory()
        
        notification = factory.create_party_status_notification("character_death", "チャーリー")
        
        assert "チャーリーが倒れました！" in notification.message
        assert notification.notification_type == NotificationType.DANGER
        assert notification.duration == 6.0
    
    def test_create_exploration_notification_secret_passage(self):
        """隠し通路発見通知のテスト"""
        factory = NotificationFactory()
        
        notification = factory.create_exploration_notification("secret_passage", {})
        
        assert "隠し通路を発見しました！" in notification.message
        assert notification.notification_type == NotificationType.SUCCESS
        assert notification.duration == 5.0
    
    def test_create_exploration_notification_floor_change(self):
        """階層移動通知のテスト"""
        factory = NotificationFactory()
        
        details = {"floor": 3, "direction": "下"}
        notification = factory.create_exploration_notification("floor_change", details)
        
        assert "下の階（3階）へ移動しました" in notification.message
        assert notification.notification_type == NotificationType.INFO


class TestIntegration:
    """統合テスト"""
    
    def test_global_factory_instance(self):
        """グローバルファクトリーインスタンスのテスト"""
        from src.dungeon.base.notification_factory import notification_factory
        
        notification = notification_factory.create_notification("テスト", NotificationType.SUCCESS)
        
        assert notification.message == "✅ テスト"
        assert notification.notification_type == NotificationType.SUCCESS
    
    def test_notification_types_coverage(self):
        """全通知タイプのカバレッジテスト"""
        factory = NotificationFactory()
        
        for notification_type in NotificationType:
            # 各タイプで通知作成が可能であることを確認
            notification = factory.create_notification("テスト", notification_type)
            assert notification.notification_type == notification_type
            assert notification.duration > 0