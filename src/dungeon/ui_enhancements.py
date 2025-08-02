"""ダンジョンUI/UX拡張機能"""

from typing import Dict, List, Tuple, Optional, Any
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
class UINotification:
    """UI通知データ"""
    message: str
    notification_type: NotificationType
    duration: float = 3.0
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class DungeonUIEnhancer:
    """ダンジョンUI/UX拡張機能管理"""
    
    def __init__(self):
        self.notifications: List[UINotification] = []
        self.auto_mapping_enabled = True
        self.show_trap_hints = True
        self.combat_animations_enabled = True
        self.quick_loot_enabled = True
        self.party_status_alerts = True
        
        # UI設定
        self.ui_settings = {
            "show_minimap": True,
            "show_compass": True,
            "show_party_health_bars": True,
            "show_experience_notifications": True,
            "auto_pause_on_low_health": True,
            "highlight_interactables": True,
            "show_damage_numbers": True,
            "play_sound_effects": True,
            "ui_animation_speed": 1.0,
            "ui_response_delay": 0.0,
            "notification_duration": 3.0,
            "show_hints": True
        }
        
        logger.info("DungeonUIEnhancer初期化完了")
    
    def add_notification(self, message: str, notification_type: NotificationType, 
                        duration: float = 3.0) -> None:
        """通知を追加"""
        notification = UINotification(message, notification_type, duration)
        self.notifications.append(notification)
        
        # 古い通知を削除（最大10件）
        if len(self.notifications) > 10:
            self.notifications = self.notifications[-10:]
        
        logger.debug(f"UI通知追加: {message} ({notification_type.value})")
    
    def get_active_notifications(self) -> List[UINotification]:
        """アクティブな通知を取得"""
        current_time = time.time()
        active = []
        
        for notification in self.notifications:
            if current_time - notification.timestamp < notification.duration:
                active.append(notification)
        
        return active
    
    def clear_expired_notifications(self) -> None:
        """期限切れ通知をクリア"""
        current_time = time.time()
        self.notifications = [
            n for n in self.notifications 
            if current_time - n.timestamp < n.duration
        ]
    
    def create_trap_warning(self, trap_type: str, detected: bool = False) -> str:
        """トラップ警告メッセージ作成"""
        if detected:
            message = f"⚠️ {trap_type}を発見しました！"
            self.add_notification(message, NotificationType.WARNING, 5.0)
        else:
            message = f"💥 {trap_type}が発動しました！"
            self.add_notification(message, NotificationType.DANGER, 4.0)
        
        return message
    
    def create_treasure_notification(self, treasure_name: str, contents: List[str]) -> str:
        """宝箱開封通知作成"""
        if not contents:
            message = f"📦 {treasure_name}は空でした..."
            self.add_notification(message, NotificationType.INFO)
        else:
            items_text = ", ".join(contents[:3])  # 最初の3個だけ表示
            if len(contents) > 3:
                items_text += f" など{len(contents)}個のアイテム"
            
            message = f"💰 {treasure_name}から {items_text} を獲得！"
            self.add_notification(message, NotificationType.LOOT, 6.0)
        
        return message
    
    def create_combat_notification(self, event_type: str, details: Dict[str, Any]) -> str:
        """戦闘通知作成"""
        message = ""
        
        if event_type == "encounter_start":
            monster_name = details.get("monster_name", "モンスター")
            message = f"⚔️ {monster_name}との戦闘開始！"
            self.add_notification(message, NotificationType.COMBAT, 3.0)
            
        elif event_type == "combat_victory":
            exp_gained = details.get("experience", 0)
            gold_gained = details.get("gold", 0)
            message = f"🎉 勝利！ 経験値+{exp_gained}, 金貨+{gold_gained}"
            self.add_notification(message, NotificationType.SUCCESS, 5.0)
            
        elif event_type == "combat_defeat":
            message = "💀 敗北... パーティが全滅しました"
            self.add_notification(message, NotificationType.DANGER, 6.0)
            
        elif event_type == "level_up":
            character_name = details.get("character_name", "キャラクター")
            new_level = details.get("new_level", 1)
            message = f"✨ {character_name}がレベル{new_level}に上がりました！"
            self.add_notification(message, NotificationType.SUCCESS, 4.0)
        
        return message
    
    def create_party_status_alert(self, alert_type: str, character_name: str, 
                                 details: Optional[Dict[str, Any]] = None) -> str:
        """パーティステータス警告作成"""
        details = details or {}
        message = ""
        
        if alert_type == "low_health":
            current_hp = details.get("current_hp", 0)
            max_hp = details.get("max_hp", 1)
            hp_percent = int((current_hp / max_hp) * 100)
            message = f"❤️ {character_name}のHPが低下（{hp_percent}%）"
            self.add_notification(message, NotificationType.WARNING, 4.0)
            
        elif alert_type == "status_effect":
            effect = details.get("effect", "状態異常")
            message = f"🔮 {character_name}が{effect}状態になりました"
            self.add_notification(message, NotificationType.INFO, 3.0)
            
        elif alert_type == "character_death":
            message = f"💀 {character_name}が倒れました！"
            self.add_notification(message, NotificationType.DANGER, 6.0)
            
        elif alert_type == "character_revived":
            message = f"✨ {character_name}が蘇生されました"
            self.add_notification(message, NotificationType.SUCCESS, 4.0)
        
        return message
    
    def create_exploration_notification(self, discovery_type: str, details: Dict[str, Any]) -> str:
        """探索通知作成"""
        message = ""
        
        if discovery_type == "secret_passage":
            message = "🔍 隠し通路を発見しました！"
            self.add_notification(message, NotificationType.SUCCESS, 5.0)
            
        elif discovery_type == "hidden_treasure":
            message = "💎 隠された宝物を発見しました！"
            self.add_notification(message, NotificationType.LOOT, 5.0)
            
        elif discovery_type == "floor_change":
            new_floor = details.get("floor", 1)
            direction = details.get("direction", "下")
            message = f"🏰 {direction}の階（{new_floor}階）へ移動しました"
            self.add_notification(message, NotificationType.INFO, 3.0)
            
        elif discovery_type == "boss_chamber":
            message = "👑 ボス部屋を発見しました！"
            self.add_notification(message, NotificationType.WARNING, 6.0)
        
        return message
    
    def get_ui_hint_for_situation(self, situation: str, context: Optional[Dict[str, Any]] = None) -> str:
        """状況に応じたUIヒント取得"""
        context = context or {}
        
        hints = {
            "first_trap": "💡 ヒント: 盗賊がいると罠を発見・解除しやすくなります",
            "first_treasure": "💡 ヒント: 宝箱によっては鍵開けが必要です",
            "first_combat": "💡 ヒント: 戦闘中は装備や魔法の効果が重要です",
            "low_health_party": "💡 ヒント: 宿屋で休息するか回復アイテムを使用しましょう",
            "full_inventory": "💡 ヒント: 不要なアイテムは売却して持ち物を整理しましょう",
            "boss_approach": "💡 ヒント: ボス戦前に準備を整えることをお勧めします",
            "character_death": "💡 ヒント: 教会で蘇生サービスを受けられます",
            "exploration_tips": "💡 ヒント: 壁を調べることで隠し通路を見つけられることがあります"
        }
        
        hint = hints.get(situation, "")
        if hint and self.ui_settings.get("show_hints", True):
            self.add_notification(hint, NotificationType.INFO, 8.0)
        
        return hint
    
    def format_damage_display(self, damage: int, damage_type: str = "physical") -> str:
        """ダメージ表示フォーマット"""
        if not self.ui_settings.get("show_damage_numbers", True):
            return ""
        
        damage_icons = {
            "physical": "⚔️",
            "magical": "🔮",
            "fire": "🔥",
            "ice": "❄️",
            "poison": "☠️",
            "holy": "✨"
        }
        
        icon = damage_icons.get(damage_type, "💥")
        return f"{icon} {damage}"
    
    def create_minimap_data(self, dungeon_data: Dict[str, Any]) -> Dict[str, Any]:
        """ミニマップデータ作成"""
        if not self.ui_settings.get("show_minimap", True):
            return {}
        
        return {
            "current_position": dungeon_data.get("player_position", (0, 0)),
            "visited_cells": dungeon_data.get("visited_cells", []),
            "known_walls": dungeon_data.get("known_walls", []),
            "known_doors": dungeon_data.get("known_doors", []),
            "special_locations": dungeon_data.get("special_locations", {}),
            "floor_size": dungeon_data.get("floor_size", (10, 10))
        }
    
    def update_ui_settings(self, settings: Dict[str, Any]) -> None:
        """UI設定更新"""
        for key, value in settings.items():
            if key in self.ui_settings:
                self.ui_settings[key] = value
                logger.debug(f"UI設定更新: {key} = {value}")
    
    def get_accessibility_options(self) -> Dict[str, Any]:
        """アクセシビリティオプション取得"""
        return {
            "high_contrast_mode": self.ui_settings.get("high_contrast", False),
            "large_text_mode": self.ui_settings.get("large_text", False),
            "screen_reader_mode": self.ui_settings.get("screen_reader", False),
            "colorblind_assistance": self.ui_settings.get("colorblind_assist", False),
            "reduced_animations": self.ui_settings.get("reduced_animations", False),
            "audio_cues_enabled": self.ui_settings.get("audio_cues", True)
        }
    
    def create_progress_summary(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """セッション進行状況サマリー作成"""
        return {
            "floors_explored": session_data.get("floors_visited", 0),
            "monsters_defeated": session_data.get("monsters_killed", 0),
            "treasures_found": session_data.get("treasures_opened", 0),
            "traps_encountered": session_data.get("traps_triggered", 0),
            "secrets_discovered": session_data.get("secrets_found", 0),
            "experience_gained": session_data.get("total_exp_gained", 0),
            "gold_earned": session_data.get("total_gold_gained", 0),
            "time_played": session_data.get("session_duration", 0.0)
        }


# グローバルインスタンス
dungeon_ui_enhancer = DungeonUIEnhancer()