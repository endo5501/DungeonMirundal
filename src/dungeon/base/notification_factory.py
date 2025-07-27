"""ダンジョン通知ファクトリー"""

from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import time

from src.utils.logger import logger


class NotificationType(Enum):
    """通知タイプ"""
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"
    DANGER = "danger"
    LOOT = "loot"
    COMBAT = "combat"


@dataclass
class Notification:
    """通知データ"""
    message: str
    notification_type: NotificationType
    duration: float = 3.0
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class NotificationFactory:
    """通知作成ファクトリー"""
    
    def __init__(self):
        self.default_durations = {
            NotificationType.INFO: 3.0,
            NotificationType.WARNING: 4.0,
            NotificationType.SUCCESS: 4.0,
            NotificationType.DANGER: 6.0,
            NotificationType.LOOT: 5.0,
            NotificationType.COMBAT: 3.0
        }
        
        self.notification_icons = {
            NotificationType.INFO: "ℹ️",
            NotificationType.WARNING: "⚠️",
            NotificationType.SUCCESS: "✅",
            NotificationType.DANGER: "❌",
            NotificationType.LOOT: "💰",
            NotificationType.COMBAT: "⚔️"
        }
    
    def create_notification(self, message: str, notification_type: NotificationType, 
                          duration: Optional[float] = None, add_icon: bool = True) -> Notification:
        """基本通知作成"""
        if duration is None:
            duration = self.default_durations.get(notification_type, 3.0)
        
        if add_icon:
            icon = self.notification_icons.get(notification_type, "")
            if icon:
                message = f"{icon} {message}"
        
        return Notification(message, notification_type, duration)
    
    def create_trap_notification(self, trap_name: str, detected: bool = False) -> Notification:
        """トラップ通知作成"""
        if detected:
            message = f"{trap_name}を発見しました！"
            return self.create_notification(message, NotificationType.WARNING, 5.0)
        else:
            message = f"{trap_name}が発動しました！"
            return self.create_notification(message, NotificationType.DANGER, 4.0, add_icon=False)
    
    def create_treasure_notification(self, treasure_name: str, contents: List[str]) -> Notification:
        """宝箱開封通知作成"""
        if not contents:
            message = f"{treasure_name}は空でした..."
            return self.create_notification(message, NotificationType.INFO, add_icon=False)
        else:
            items_text = ", ".join(contents[:3])
            if len(contents) > 3:
                items_text += f" など{len(contents)}個のアイテム"
            
            message = f"{treasure_name}から {items_text} を獲得！"
            return self.create_notification(message, NotificationType.LOOT, 6.0, add_icon=False)
    
    def create_combat_notification(self, event_type: str, details: Dict[str, Any]) -> Notification:
        """戦闘通知作成"""
        if event_type == "encounter_start":
            monster_name = details.get("monster_name", "モンスター")
            message = f"{monster_name}との戦闘開始！"
            return self.create_notification(message, NotificationType.COMBAT, add_icon=False)
            
        elif event_type == "combat_victory":
            exp_gained = details.get("experience", 0)
            gold_gained = details.get("gold", 0)
            message = f"勝利！ 経験値+{exp_gained}, 金貨+{gold_gained}"
            return self.create_notification(message, NotificationType.SUCCESS, 5.0, add_icon=False)
            
        elif event_type == "combat_defeat":
            message = "敗北... パーティが全滅しました"
            return self.create_notification(message, NotificationType.DANGER, 6.0, add_icon=False)
            
        elif event_type == "level_up":
            character_name = details.get("character_name", "キャラクター")
            new_level = details.get("new_level", 1)
            message = f"{character_name}がレベル{new_level}に上がりました！"
            return self.create_notification(message, NotificationType.SUCCESS, 4.0, add_icon=False)
        
        # デフォルト
        message = "戦闘イベントが発生しました"
        return self.create_notification(message, NotificationType.INFO)
    
    def create_party_status_notification(self, alert_type: str, character_name: str, 
                                       details: Optional[Dict[str, Any]] = None) -> Notification:
        """パーティステータス通知作成"""
        details = details or {}
        
        if alert_type == "low_health":
            current_hp = details.get("current_hp", 0)
            max_hp = details.get("max_hp", 1)
            hp_percent = int((current_hp / max_hp) * 100)
            message = f"{character_name}のHPが低下（{hp_percent}%）"
            return self.create_notification(message, NotificationType.WARNING, 4.0, add_icon=False)
            
        elif alert_type == "status_effect":
            effect = details.get("effect", "状態異常")
            message = f"{character_name}が{effect}状態になりました"
            return self.create_notification(message, NotificationType.INFO, add_icon=False)
            
        elif alert_type == "character_death":
            message = f"{character_name}が倒れました！"
            return self.create_notification(message, NotificationType.DANGER, 6.0, add_icon=False)
            
        elif alert_type == "character_revived":
            message = f"{character_name}が蘇生されました"
            return self.create_notification(message, NotificationType.SUCCESS, 4.0, add_icon=False)
        
        # デフォルト
        message = f"{character_name}のステータスが変更されました"
        return self.create_notification(message, NotificationType.INFO)
    
    def create_exploration_notification(self, discovery_type: str, details: Dict[str, Any]) -> Notification:
        """探索通知作成"""
        if discovery_type == "secret_passage":
            message = "隠し通路を発見しました！"
            return self.create_notification(message, NotificationType.SUCCESS, 5.0, add_icon=False)
            
        elif discovery_type == "hidden_treasure":
            message = "隠された宝物を発見しました！"
            return self.create_notification(message, NotificationType.LOOT, 5.0, add_icon=False)
            
        elif discovery_type == "floor_change":
            new_floor = details.get("floor", 1)
            direction = details.get("direction", "下")
            message = f"{direction}の階（{new_floor}階）へ移動しました"
            return self.create_notification(message, NotificationType.INFO, add_icon=False)
            
        elif discovery_type == "boss_chamber":
            message = "ボス部屋を発見しました！"
            return self.create_notification(message, NotificationType.WARNING, 6.0, add_icon=False)
        
        # デフォルト
        message = "何かを発見しました"
        return self.create_notification(message, NotificationType.INFO)


# グローバルインスタンス
notification_factory = NotificationFactory()