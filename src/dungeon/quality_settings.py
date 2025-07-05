"""ダンジョン品質設定管理"""

from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import json
from pathlib import Path

from src.utils.logger import logger


class DifficultyLevel(Enum):
    """難易度レベル"""
    BEGINNER = "beginner"      # 初心者向け
    NORMAL = "normal"          # 通常
    HARD = "hard"              # 困難
    EXPERT = "expert"          # 専門家
    NIGHTMARE = "nightmare"    # 悪夢


class QualityPreset(Enum):
    """品質プリセット"""
    PERFORMANCE = "performance"    # 性能重視
    BALANCED = "balanced"          # バランス
    QUALITY = "quality"            # 品質重視
    CUSTOM = "custom"              # カスタム


@dataclass
class DifficultySettings:
    """難易度設定"""
    name: str
    description: str
    
    # 敵の強さ調整
    enemy_health_multiplier: float = 1.0
    enemy_damage_multiplier: float = 1.0
    enemy_spawn_rate_multiplier: float = 1.0
    
    # トラップ設定
    trap_frequency_multiplier: float = 1.0
    trap_damage_multiplier: float = 1.0
    trap_detection_difficulty: float = 1.0
    
    # 宝箱設定
    treasure_spawn_rate: float = 1.0
    treasure_quality_multiplier: float = 1.0
    treasure_lock_difficulty: float = 1.0
    
    # 経験値・報酬調整
    experience_multiplier: float = 1.0
    gold_multiplier: float = 1.0
    item_drop_rate: float = 1.0
    
    # ヘルプ機能
    show_hints: bool = True
    auto_map_generation: bool = True
    retreat_penalty_reduction: float = 1.0


@dataclass 
class QualitySettings:
    """品質設定"""
    preset_name: str
    description: str
    
    # グラフィック設定
    texture_quality: str = "medium"  # low, medium, high
    shadow_quality: str = "medium"   # low, medium, high, ultra
    particle_effects: bool = True
    screen_effects: bool = True
    
    # パフォーマンス設定
    max_visible_objects: int = 100
    animation_quality: str = "medium"  # low, medium, high
    update_frequency: int = 60  # FPS
    
    # オーディオ設定
    audio_quality: str = "medium"  # low, medium, high
    max_audio_channels: int = 16
    spatial_audio: bool = True
    
    # UI設定
    ui_animation_speed: float = 1.0
    ui_response_delay: float = 0.0
    notification_duration: float = 3.0


class DungeonQualityManager:
    """ダンジョン品質管理"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "dungeon_quality_config.json"
        
        # デフォルト難易度設定
        self.difficulty_presets = self._initialize_difficulty_presets()
        
        # デフォルト品質設定
        self.quality_presets = self._initialize_quality_presets()
        
        # 現在の設定
        self.current_difficulty = DifficultyLevel.NORMAL
        self.current_quality = QualityPreset.BALANCED
        
        # カスタム設定
        self.custom_difficulty: Optional[DifficultySettings] = None
        self.custom_quality: Optional[QualitySettings] = None
        
        # 設定をロード
        self.load_settings()
        
        logger.info("DungeonQualityManager初期化完了")
    
    def _initialize_difficulty_presets(self) -> Dict[DifficultyLevel, DifficultySettings]:
        """難易度プリセット初期化"""
        return {
            DifficultyLevel.BEGINNER: DifficultySettings(
                name="初心者",
                description="ダンジョン探索に慣れていない方向け",
                enemy_health_multiplier=0.7,
                enemy_damage_multiplier=0.6,
                enemy_spawn_rate_multiplier=0.8,
                trap_frequency_multiplier=0.5,
                trap_damage_multiplier=0.5,
                trap_detection_difficulty=0.7,
                treasure_spawn_rate=1.3,
                treasure_quality_multiplier=1.1,
                experience_multiplier=1.2,
                gold_multiplier=1.1,
                show_hints=True,
                auto_map_generation=True,
                retreat_penalty_reduction=0.5
            ),
            
            DifficultyLevel.NORMAL: DifficultySettings(
                name="通常",
                description="バランスの取れた標準的な難易度",
                enemy_health_multiplier=1.0,
                enemy_damage_multiplier=1.0,
                enemy_spawn_rate_multiplier=1.0,
                trap_frequency_multiplier=1.0,
                trap_damage_multiplier=1.0,
                trap_detection_difficulty=1.0,
                treasure_spawn_rate=1.0,
                treasure_quality_multiplier=1.0,
                experience_multiplier=1.0,
                gold_multiplier=1.0,
                show_hints=True,
                auto_map_generation=True,
                retreat_penalty_reduction=1.0
            ),
            
            DifficultyLevel.HARD: DifficultySettings(
                name="困難",
                description="挑戦的で緊張感のある探索体験",
                enemy_health_multiplier=1.3,
                enemy_damage_multiplier=1.2,
                enemy_spawn_rate_multiplier=1.1,
                trap_frequency_multiplier=1.2,
                trap_damage_multiplier=1.3,
                trap_detection_difficulty=1.2,
                treasure_spawn_rate=0.9,
                treasure_quality_multiplier=1.2,
                experience_multiplier=1.1,
                gold_multiplier=0.9,
                show_hints=False,
                auto_map_generation=False,
                retreat_penalty_reduction=1.5
            ),
            
            DifficultyLevel.EXPERT: DifficultySettings(
                name="専門家",
                description="熟練者向けの高難易度設定",
                enemy_health_multiplier=1.6,
                enemy_damage_multiplier=1.5,
                enemy_spawn_rate_multiplier=1.3,
                trap_frequency_multiplier=1.5,
                trap_damage_multiplier=1.6,
                trap_detection_difficulty=1.5,
                treasure_spawn_rate=0.8,
                treasure_quality_multiplier=1.4,
                experience_multiplier=1.2,
                gold_multiplier=0.8,
                show_hints=False,
                auto_map_generation=False,
                retreat_penalty_reduction=2.0
            ),
            
            DifficultyLevel.NIGHTMARE: DifficultySettings(
                name="悪夢",
                description="極限の挑戦を求める勇者向け",
                enemy_health_multiplier=2.0,
                enemy_damage_multiplier=1.8,
                enemy_spawn_rate_multiplier=1.5,
                trap_frequency_multiplier=2.0,
                trap_damage_multiplier=2.0,
                trap_detection_difficulty=2.0,
                treasure_spawn_rate=0.7,
                treasure_quality_multiplier=1.8,
                experience_multiplier=1.5,
                gold_multiplier=0.7,
                show_hints=False,
                auto_map_generation=False,
                retreat_penalty_reduction=3.0
            )
        }
    
    def _initialize_quality_presets(self) -> Dict[QualityPreset, QualitySettings]:
        """品質プリセット初期化"""
        return {
            QualityPreset.PERFORMANCE: QualitySettings(
                preset_name="性能重視",
                description="フレームレート重視、低スペック端末向け",
                texture_quality="low",
                shadow_quality="low",
                particle_effects=False,
                screen_effects=False,
                max_visible_objects=50,
                animation_quality="low",
                update_frequency=30,
                audio_quality="low",
                max_audio_channels=8,
                spatial_audio=False,
                ui_animation_speed=2.0,
                ui_response_delay=0.0,
                notification_duration=2.0
            ),
            
            QualityPreset.BALANCED: QualitySettings(
                preset_name="バランス",
                description="品質と性能のバランス型",
                texture_quality="medium",
                shadow_quality="medium",
                particle_effects=True,
                screen_effects=True,
                max_visible_objects=100,
                animation_quality="medium",
                update_frequency=60,
                audio_quality="medium",
                max_audio_channels=16,
                spatial_audio=True,
                ui_animation_speed=1.0,
                ui_response_delay=0.0,
                notification_duration=3.0
            ),
            
            QualityPreset.QUALITY: QualitySettings(
                preset_name="品質重視",
                description="最高品質、高スペック端末向け",
                texture_quality="high",
                shadow_quality="ultra",
                particle_effects=True,
                screen_effects=True,
                max_visible_objects=200,
                animation_quality="high",
                update_frequency=120,
                audio_quality="high",
                max_audio_channels=32,
                spatial_audio=True,
                ui_animation_speed=0.8,
                ui_response_delay=0.1,
                notification_duration=4.0
            )
        }
    
    def get_current_difficulty_settings(self) -> DifficultySettings:
        """現在の難易度設定取得"""
        if self.current_difficulty == DifficultyLevel.EXPERT and self.custom_difficulty:
            return self.custom_difficulty
        return self.difficulty_presets[self.current_difficulty]
    
    def get_current_quality_settings(self) -> QualitySettings:
        """現在の品質設定取得"""
        if self.current_quality == QualityPreset.CUSTOM and self.custom_quality:
            return self.custom_quality
        return self.quality_presets[self.current_quality]
    
    def set_difficulty(self, difficulty: DifficultyLevel) -> bool:
        """難易度設定"""
        if difficulty in self.difficulty_presets:
            self.current_difficulty = difficulty
            logger.info(f"難易度を{difficulty.value}に設定しました")
            return True
        return False
    
    def set_quality(self, quality: QualityPreset) -> bool:
        """品質設定"""
        if quality in self.quality_presets:
            self.current_quality = quality
            logger.info(f"品質を{quality.value}に設定しました")
            return True
        return False
    
    def create_custom_difficulty(self, base_difficulty: DifficultyLevel, 
                               modifications: Dict[str, Any]) -> DifficultySettings:
        """カスタム難易度作成"""
        base_settings = self.difficulty_presets[base_difficulty]
        
        # 基本設定をコピー
        custom_settings = DifficultySettings(
            name="カスタム",
            description="カスタマイズされた難易度設定"
        )
        
        # 基本設定の値を適用（name以外）
        for field_name, field_value in base_settings.__dict__.items():
            if hasattr(custom_settings, field_name) and field_name not in ['name', 'description']:
                setattr(custom_settings, field_name, field_value)
        
        # カスタム修正を適用
        for key, value in modifications.items():
            if hasattr(custom_settings, key):
                setattr(custom_settings, key, value)
        
        self.custom_difficulty = custom_settings
        return custom_settings
    
    def create_custom_quality(self, base_quality: QualityPreset,
                            modifications: Dict[str, Any]) -> QualitySettings:
        """カスタム品質作成"""
        base_settings = self.quality_presets[base_quality]
        
        # 基本設定をコピー
        custom_settings = QualitySettings(
            preset_name="カスタム",
            description="カスタマイズされた品質設定"
        )
        
        # 基本設定の値を適用（preset_name以外）
        for field_name, field_value in base_settings.__dict__.items():
            if hasattr(custom_settings, field_name) and field_name not in ['preset_name', 'description']:
                setattr(custom_settings, field_name, field_value)
        
        # カスタム修正を適用
        for key, value in modifications.items():
            if hasattr(custom_settings, key):
                setattr(custom_settings, key, value)
        
        self.custom_quality = custom_settings
        return custom_settings
    
    def apply_difficulty_to_trap_system(self, trap_system) -> None:
        """難易度設定をトラップシステムに適用"""
        settings = self.get_current_difficulty_settings()
        
        # トラップの発動率や難易度を調整
        for trap_data in trap_system.trap_definitions.values():
            trap_data.success_rate *= settings.trap_frequency_multiplier
            # ダメージ範囲調整
            min_dmg, max_dmg = trap_data.damage_range
            trap_data.damage_range = (
                int(min_dmg * settings.trap_damage_multiplier),
                int(max_dmg * settings.trap_damage_multiplier)
            )
    
    def apply_difficulty_to_treasure_system(self, treasure_system) -> None:
        """難易度設定を宝箱システムに適用"""
        settings = self.get_current_difficulty_settings()
        
        # 宝箱の生成率や品質を調整
        for treasure_data in treasure_system.treasure_definitions.values():
            treasure_data.lock_difficulty *= settings.treasure_lock_difficulty
            # 金貨範囲調整
            min_gold, max_gold = treasure_data.gold_range
            treasure_data.gold_range = (
                int(min_gold * settings.gold_multiplier),
                int(max_gold * settings.gold_multiplier)
            )
    
    def apply_difficulty_to_boss_system(self, boss_system) -> None:
        """難易度設定をボスシステムに適用"""
        settings = self.get_current_difficulty_settings()
        
        # ボスの強さを調整
        for boss_data in boss_system.boss_definitions.values():
            boss_data.max_hp = int(boss_data.max_hp * settings.enemy_health_multiplier)
            
            # 報酬調整
            if "experience" in boss_data.victory_rewards:
                boss_data.victory_rewards["experience"] = int(
                    boss_data.victory_rewards["experience"] * settings.experience_multiplier
                )
            if "gold" in boss_data.victory_rewards:
                boss_data.victory_rewards["gold"] = int(
                    boss_data.victory_rewards["gold"] * settings.gold_multiplier
                )
    
    def get_recommended_settings(self, system_specs: Dict[str, Any]) -> Tuple[DifficultyLevel, QualityPreset]:
        """システムスペックに応じた推奨設定"""
        cpu_score = system_specs.get("cpu_score", 50)  # 0-100
        memory_gb = system_specs.get("memory_gb", 4)
        gpu_score = system_specs.get("gpu_score", 50)  # 0-100
        
        # 品質設定の推奨
        if gpu_score >= 80 and cpu_score >= 70 and memory_gb >= 8:
            quality = QualityPreset.QUALITY
        elif gpu_score >= 50 and cpu_score >= 50 and memory_gb >= 4:
            quality = QualityPreset.BALANCED
        else:
            quality = QualityPreset.PERFORMANCE
        
        # 難易度は常にユーザーの好みに依存
        difficulty = DifficultyLevel.NORMAL
        
        return difficulty, quality
    
    def save_settings(self) -> bool:
        """設定をファイルに保存"""
        try:
            config_data = {
                "current_difficulty": self.current_difficulty.value,
                "current_quality": self.current_quality.value,
                "custom_difficulty": self.custom_difficulty.__dict__ if self.custom_difficulty else None,
                "custom_quality": self.custom_quality.__dict__ if self.custom_quality else None
            }
            
            config_path = Path(self.config_file)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"設定を保存しました: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"設定保存エラー: {e}")
            return False
    
    def load_settings(self) -> bool:
        """設定をファイルから読み込み"""
        try:
            config_path = Path(self.config_file)
            if not config_path.exists():
                logger.info("設定ファイルが存在しないため、デフォルト設定を使用します")
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 現在の設定復元
            difficulty_str = config_data.get("current_difficulty", "normal")
            quality_str = config_data.get("current_quality", "balanced")
            
            try:
                self.current_difficulty = DifficultyLevel(difficulty_str)
                self.current_quality = QualityPreset(quality_str)
            except ValueError as e:
                logger.warning(f"設定値が無効です、デフォルトを使用: {e}")
            
            # カスタム設定復元
            if config_data.get("custom_difficulty"):
                custom_diff_data = config_data["custom_difficulty"]
                self.custom_difficulty = DifficultySettings(**custom_diff_data)
            
            if config_data.get("custom_quality"):
                custom_qual_data = config_data["custom_quality"]
                self.custom_quality = QualitySettings(**custom_qual_data)
            
            logger.info("設定を読み込みました")
            return True
            
        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")
            return False


# グローバルインスタンス
dungeon_quality_manager = DungeonQualityManager()