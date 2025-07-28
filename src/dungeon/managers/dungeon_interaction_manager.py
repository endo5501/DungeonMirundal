"""ダンジョンインタラクション管理"""

from typing import Dict, List, Tuple, Optional, Any
import random

from ..dungeon_generator import DungeonCell, CellType
from ..trap_system import trap_system, TrapType
from ..treasure_system import treasure_system, TreasureType
from ..boss_system import boss_system, BossEncounter
from src.character.party import Party
from src.character.character import Character
from src.utils.logger import logger


class DungeonInteractionManager:
    """ダンジョンインタラクション管理"""
    
    def __init__(self, state_manager, navigation_manager):
        self.state_manager = state_manager
        self.navigation_manager = navigation_manager
        
        # 強制撤退コールバック
        self.force_retreat_callback = None
        
        logger.debug("DungeonInteractionManager初期化完了")
    
    def set_force_retreat_callback(self, callback):
        """強制撤退コールバックを設定"""
        self.force_retreat_callback = callback
    
    def interact_with_current_cell(self, party: Party, character = None) -> Dict[str, Any]:
        """現在位置のセルとのインタラクション"""
        current_cell = self.navigation_manager.get_current_cell()
        if not current_cell:
            return {"success": False, "message": "現在位置が無効です"}
        
        result = {"success": True, "message": "", "interactions": []}
        
        # トラップチェック
        if current_cell.has_trap and current_cell.trap_type:
            trap_result = self._handle_trap_interaction(current_cell, party)
            result["interactions"].append(trap_result)
        
        # 宝箱チェック
        if current_cell.has_treasure and current_cell.treasure_id:
            treasure_result = self._handle_treasure_interaction(current_cell, party, character)
            result["interactions"].append(treasure_result)
        
        # ボス戦チェック
        if current_cell.cell_type == CellType.BOSS:
            boss_result = self._handle_boss_interaction(current_cell, party)
            result["interactions"].append(boss_result)
        
        if not result["interactions"]:
            result["message"] = "特に何もない"
        else:
            result["message"] = f"{len(result['interactions'])}個のインタラクションが発生"
        
        return result
    
    def _handle_trap_interaction(self, cell: DungeonCell, party: Party) -> Dict[str, Any]:
        """トラップとのインタラクション"""
        try:
            trap_type = TrapType(cell.trap_type)
        except ValueError:
            logger.warning(f"無効なトラップタイプ: {cell.trap_type}")
            return {"type": "trap", "success": False, "message": "無効なトラップです"}
        
        # トラップ発見判定
        living_members = party.get_living_characters()
        detected = False
        detector = None
        
        for member in living_members:
            if trap_system.can_detect_trap(member, trap_type):
                detected = True
                detector = member
                break
        
        if detected and detector:
            # 解除試行
            if trap_system.can_disarm_trap(detector, trap_type):
                detector_name = detector.name
                logger.info(f"{detector_name}がトラップを解除しました")
                cell.has_trap = False
                cell.trap_type = None
                return {
                    "type": "trap", 
                    "success": True, 
                    "message": f"{detector_name}がトラップを発見・解除した！",
                    "disarmed": True
                }
            else:
                detector_name = detector.name
                logger.info(f"{detector_name}がトラップを発見しましたが解除に失敗")
                # 発見したが解除失敗 - 発動
                current_dungeon = self.state_manager.get_current_dungeon()
                trap_result = trap_system.activate_trap(trap_type, party, current_dungeon.player_position.level)
                trap_result["type"] = "trap"
                trap_result["detected"] = True
                trap_result["disarm_failed"] = True
                return trap_result
        else:
            # 発見失敗 - 発動
            current_dungeon = self.state_manager.get_current_dungeon()
            trap_result = trap_system.activate_trap(trap_type, party, current_dungeon.player_position.level)
            trap_result["type"] = "trap"
            trap_result["detected"] = False
            return trap_result
    
    def _handle_treasure_interaction(self, cell: DungeonCell, party: Party, opener_character = None) -> Dict[str, Any]:
        """宝箱とのインタラクション"""
        treasure_id = cell.treasure_id
        if not treasure_id:
            return {"type": "treasure", "success": False, "message": "宝箱IDが無効です"}
        
        # 宝箱タイプを決定（既存の場合は保持、新規の場合は生成）
        treasure_type = getattr(cell, 'treasure_type', None)
        current_dungeon = self.state_manager.get_current_dungeon()
        
        if not treasure_type:
            treasure_type = treasure_system.generate_treasure_type(current_dungeon.player_position.level)
            # DungeonCellに動的属性を設定（pyright対応）
            setattr(cell, 'treasure_type', treasure_type)
        else:
            try:
                treasure_type = TreasureType(treasure_type)
            except ValueError:
                treasure_type = treasure_system.generate_treasure_type(current_dungeon.player_position.level)
        
        # 宝箱開封
        treasure_result = treasure_system.open_treasure(
            treasure_id, 
            treasure_type, 
            party, 
            current_dungeon.player_position.level,
            opener_character
        )
        treasure_result["type"] = "treasure"
        
        # ミミックの場合は戦闘発生
        if treasure_result.get("mimic"):
            treasure_result["start_combat"] = True
            treasure_result["mimic_monster"] = self._generate_mimic_monster()
        
        # 開封成功時はセルから宝箱を除去
        if treasure_result.get("success") and not treasure_result.get("mimic"):
            cell.has_treasure = False
            cell.treasure_id = None
            if hasattr(cell, 'treasure_type'):
                delattr(cell, 'treasure_type')
        
        return treasure_result
    
    def _handle_boss_interaction(self, cell: DungeonCell, party: Party) -> Dict[str, Any]:
        """ボス戦とのインタラクション"""
        current_dungeon = self.state_manager.get_current_dungeon()
        dungeon_level = current_dungeon.player_position.level
        
        # ボス生成
        boss_id = boss_system.generate_boss_for_level(dungeon_level)
        if not boss_id:
            logger.warning(f"レベル {dungeon_level} に適したボスが見つかりません")
            return {"type": "boss", "success": False, "message": "ボスが見つかりません"}
        
        # ボス戦エンカウンター作成
        encounter_id = f"boss_{current_dungeon.dungeon_id}_{dungeon_level}_{cell.x}_{cell.y}"
        encounter = boss_system.create_boss_encounter(boss_id, dungeon_level, encounter_id)
        
        if not encounter:
            return {"type": "boss", "success": False, "message": "ボス戦の準備に失敗しました"}
        
        # ボスモンスター初期化
        boss_monster = encounter.initialize_boss_monster()
        
        return {
            "type": "boss",
            "success": True,
            "message": f"強大な敵「{encounter.boss_data.name}」が現れた！",
            "start_combat": True,
            "boss_encounter": encounter,
            "boss_monster": boss_monster,
            "encounter_id": encounter_id
        }
    
    def _generate_mimic_monster(self):
        """ミミックモンスターを生成"""
        from src.monsters.monster import Monster, MonsterStats, MonsterType, MonsterSize
        
        current_dungeon = self.state_manager.get_current_dungeon()
        level = current_dungeon.player_position.level
        
        stats = MonsterStats(
            level=level + 2,
            hit_points=40 + level * 8,
            armor_class=12 + level,
            attack_bonus=2 + level,
            damage_dice="1d8",
            strength=12 + level * 2,
            agility=10 + level,
            intelligence=5,
            faith=3,
            luck=8
        )
        
        mimic = Monster(
            monster_id=f"mimic_{level}",
            name="ミミック",
            description="宝箱に擬態した奸計深いモンスター",
            monster_type=MonsterType.ABERRATION,
            size=MonsterSize.MEDIUM,
            stats=stats,
            experience_value=30 + level * 5
        )
        
        return mimic
    
    def check_for_secret_interactions(self, party: Party) -> Dict[str, Any]:
        """隠された要素との相互作用をチェック"""
        current_cell = self.navigation_manager.get_current_cell()
        if not current_cell:
            return {"success": False, "message": "現在位置が無効です"}
        
        interactions = []
        
        # 隠し通路チェック
        if self._check_secret_passage():
            interactions.append({
                "type": "secret_passage",
                "message": "隠し通路を発見した！",
                "action_available": True
            })
        
        # 隠し宝箱チェック
        if self._check_secret_treasure(party):
            interactions.append({
                "type": "secret_treasure", 
                "message": "隠された宝箱を発見した！",
                "action_available": True
            })
        
        return {
            "success": True,
            "interactions": interactions,
            "count": len(interactions)
        }
    
    def _check_secret_passage(self) -> bool:
        """隠し通路の発見判定"""
        # 簡易実装: 各セルで5%の確率で隠し通路
        return random.random() < 0.05
    
    def _check_secret_treasure(self, party: Party) -> bool:
        """隠し宝箱の発見判定"""
        # パーティメンバーの知力・レベルに応じて発見率が変動
        living_members = party.get_living_characters()
        if not living_members:
            return False
        
        best_intelligence = max(member.base_stats.intelligence for member in living_members)
        best_level = max(member.experience.level for member in living_members)
        
        discovery_rate = 0.02 + (best_intelligence - 10) * 0.005 + best_level * 0.001
        
        return random.random() < discovery_rate
    
    def complete_boss_encounter(self, encounter_id: str, victory: bool, party: Party) -> Dict[str, Any]:
        """ボス戦完了処理"""
        result = boss_system.complete_boss_encounter(encounter_id, victory)
        
        if victory and "rewards" in result:
            rewards = result["rewards"]
            
            # 経験値付与
            if "experience" in rewards:
                for character in party.get_living_characters():
                    character.add_experience(rewards["experience"])
            
            # 金貨付与
            if "gold" in rewards:
                party.gold += rewards["gold"]
            
            # アイテム付与
            if "items" in rewards:
                for item_name in rewards["items"]:
                    # 実際のアイテム生成は省略
                    logger.info(f"特別アイテム「{item_name}」を獲得しました")
        
        return result
    
    # === パーティ状態管理機能 ===
    
    def check_party_status(self, party) -> Dict[str, Any]:
        """パーティ状態をチェック"""
        if not party:
            logger.warning("check_party_status: パーティが設定されていません")
            return {"can_continue": False, "reason": "パーティが設定されていません"}
        
        living_members = party.get_living_characters()
        total_members = len(party.members)
        
        status = {
            "can_continue": len(living_members) > 0,
            "living_count": len(living_members),
            "total_count": total_members,
            "all_dead": len(living_members) == 0,
            "needs_healing": False,
            "critically_injured": [],
            "dead_members": []
        }
        
        # 詳細な状態分析
        for member in party.members:
            if not member.is_alive():
                status["dead_members"].append(member.name)
            elif member.derived_stats.current_hp <= member.derived_stats.max_hp * 0.2:
                # HP20%以下は重傷
                status["critically_injured"].append(member.name)
                status["needs_healing"] = True
        
        return status
    
    def should_force_retreat(self, party) -> Tuple[bool, str]:
        """強制的な撤退が必要かチェック"""
        status = self.check_party_status(party)
        
        if status["all_dead"]:
            return True, "パーティ全滅"
        
        if status["living_count"] == 1 and status["critically_injured"]:
            return True, "残り1名が重傷"
        
        return False, ""
    
    def handle_member_death(self, party, dead_character_name: str):
        """メンバー死亡時の処理"""
        logger.warning(f"ダンジョン内でメンバー死亡: {dead_character_name}")
        
        # パーティ状態をチェック
        should_retreat, reason = self.should_force_retreat(party)
        
        if should_retreat:
            logger.critical(f"強制撤退条件: {reason}")
            # GameManagerに強制撤退を通知（コールバック経由）
            if self.force_retreat_callback:
                self.force_retreat_callback(reason)