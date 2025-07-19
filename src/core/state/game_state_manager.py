"""Game state management module."""

import logging
from typing import Any, Dict, Optional, List
from datetime import datetime

from src.core.interfaces import ManagedComponent
from src.utils.logger import logger
from src.utils.constants import GameLocation
from src.core.event_bus import publish_event, EventType


class GameStateManager(ManagedComponent):
    """ゲーム状態の統合管理
    
    GameManagerから抽出されたセーブ・ロード処理を統合管理し、
    ゲーム状態の永続化と復元を行う。
    """
    
    def __init__(self):
        super().__init__()
        
        # 外部依存コンポーネント
        self.save_manager = None
        self.current_party = None
        self.current_location = GameLocation.OVERWORLD
        
        # 管理対象コンポーネント
        self.dungeon_manager = None
        self.overworld_manager = None
        
        # 状態管理
        self._last_save_info = {}
        self._auto_save_enabled = True
        self._save_history = []
    
    def _do_initialize(self, context: Dict[str, Any]) -> bool:
        """GameStateManagerの初期化"""
        try:
            # 必要なコンポーネントを取得
            self.save_manager = context.get('save_manager')
            self.current_party = context.get('current_party')
            self.current_location = context.get('current_location', GameLocation.OVERWORLD)
            
            # 管理対象コンポーネントを取得
            self.dungeon_manager = context.get('dungeon_manager')
            self.overworld_manager = context.get('overworld_manager')
            
            # 自動セーブ設定
            self._auto_save_enabled = context.get('auto_save_enabled', True)
            
            if not self.save_manager:
                logger.error("GameStateManager: save_manager not provided")
                return False
            
            logger.info("GameStateManager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"GameStateManager initialization failed: {e}")
            return False
    
    def _do_cleanup(self) -> None:
        """GameStateManagerのクリーンアップ"""
        self._save_history.clear()
        logger.info("GameStateManager cleaned up")
    
    def handle_game_event(self, event: Any) -> bool:
        """ゲームイベントの処理（現在は使用しない）"""
        return False
    
    def save_current_game(self, slot_id: int, save_name: str = "") -> bool:
        """現在のゲーム状態を保存（GameManagerから抽出）"""
        try:
            if not self.current_party:
                logger.error("保存するパーティがありません")
                return False
            
            # ギルドキャラクターを取得
            guild_characters = self._get_guild_characters()
            
            # ダンジョン情報を取得
            dungeon_list = self._get_dungeon_list()
            
            # ゲーム状態を作成
            game_state = {
                'location': self.current_location.value if hasattr(self.current_location, 'value') else str(self.current_location),
                'timestamp': self._get_timestamp(),
                'version': '1.0'
            }
            
            # セーブ実行
            success = self.save_manager.save_game(
                party=self.current_party,
                slot_id=slot_id,
                save_name=save_name,
                game_state=game_state,
                guild_characters=guild_characters,
                dungeon_list=dungeon_list
            )
            
            if success:
                # セーブ履歴を更新
                save_info = {
                    'slot_id': slot_id,
                    'save_name': save_name,
                    'timestamp': self._get_timestamp(),
                    'party_name': self.current_party.name if self.current_party else 'Unknown',
                    'location': self.current_location.value if hasattr(self.current_location, 'value') else str(self.current_location),
                    'guild_character_count': len(guild_characters),
                    'dungeon_count': len(dungeon_list)
                }
                
                self._last_save_info = save_info
                self._add_save_history(save_info)
                
                logger.info(f"ゲームを保存しました: スロット{slot_id}, ギルドキャラクター{len(guild_characters)}人, ダンジョン{len(dungeon_list)}個")
                
                # セーブ完了イベントを発行
                publish_event(
                    EventType.GAME_SAVED,
                    "game_state_manager",
                    save_info
                )
            
            return success
            
        except Exception as e:
            logger.error(f"ゲーム保存エラー: {e}")
            return False
    
    def save_game_state(self, slot_id: str) -> bool:
        """ゲーム状態の保存（簡易版）"""
        try:
            # slot_idが文字列の場合は整数に変換
            if isinstance(slot_id, str):
                try:
                    slot_id_int = int(slot_id)
                except ValueError:
                    logger.error(f"Invalid slot_id format: {slot_id}")
                    return False
            else:
                slot_id_int = slot_id
            
            return self.save_current_game(slot_id_int, f"Auto Save {self._get_timestamp()}")
            
        except Exception as e:
            logger.error(f"ゲーム状態保存エラー: {e}")
            return False
    
    def load_game_state(self, slot_id: str) -> bool:
        """ゲーム状態の復元（GameManagerから抽出）"""
        try:
            # slot_idが文字列の場合は整数に変換
            if isinstance(slot_id, str):
                try:
                    slot_id_int = int(slot_id)
                except ValueError:
                    logger.error(f"Invalid slot_id format: {slot_id}")
                    return False
            else:
                slot_id_int = slot_id
            
            # セーブデータの読み込み
            save_data = self.save_manager.load_game(slot_id_int)
            if not save_data:
                logger.error(f"セーブデータの読み込みに失敗: スロット{slot_id_int}")
                return False
            
            # パーティの復元
            party = save_data.get('party')
            if not party:
                logger.error("パーティデータが見つかりません")
                return False
            
            # 現在のパーティを更新（呼び出し元が設定する必要がある）
            self.current_party = party
            
            # ゲーム状態の復元
            game_state = save_data.get('game_state', {})
            location_str = game_state.get('location', 'overworld')
            
            # ロケーションの復元
            try:
                if location_str == 'overworld':
                    self.current_location = GameLocation.OVERWORLD
                elif location_str == 'dungeon':
                    self.current_location = GameLocation.DUNGEON
                else:
                    self.current_location = GameLocation.OVERWORLD
                    logger.warning(f"不明なロケーション: {location_str}, overworldに設定")
            except Exception as e:
                logger.warning(f"ロケーション復元エラー: {e}")
                self.current_location = GameLocation.OVERWORLD
            
            # ギルドキャラクターの復元
            guild_characters = save_data.get('guild_characters', [])
            if guild_characters:
                self._restore_guild_characters(guild_characters)
            
            # ダンジョンリストの復元
            dungeon_list = save_data.get('dungeon_list', [])
            if dungeon_list:
                self._restore_dungeon_list(dungeon_list)
            
            logger.info(f"ゲームをロードしました: スロット {slot_id_int}, パーティ: {party.name if party else 'Unknown'}")
            
            # ロード完了イベントを発行
            publish_event(
                EventType.GAME_LOADED,
                "game_state_manager",
                {
                    'slot_id': slot_id_int,
                    'party_name': party.name if party else 'Unknown',
                    'location': self.current_location.value,
                    'timestamp': self._get_timestamp()
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"ゲーム状態復元エラー: {e}")
            return False
    
    def try_auto_load(self) -> bool:
        """自動ロードの試行（GameManagerから抽出）"""
        try:
            # 最新のセーブデータを検索
            save_slots = self.save_manager.get_save_slots()
            if not save_slots:
                logger.info("自動ロード対象のセーブデータが見つかりません")
                return False
            
            # 最新のセーブデータを取得（リストの最初の要素）
            latest_save = save_slots[0]
            slot_id = latest_save.slot_id
            save_name = latest_save.party_name or 'Unknown'
            
            logger.info(f"最新のセーブデータを自動ロードします: スロット{slot_id} ({save_name})")
            
            # ロード実行
            success = self.load_game_state(str(slot_id))
            
            if success:
                logger.info("自動ロードが成功しました")
            else:
                logger.warning("自動ロードに失敗しました")
            
            return success
            
        except Exception as e:
            logger.error(f"自動ロードエラー: {e}")
            return False
    
    def get_save_history(self) -> List[Dict[str, Any]]:
        """セーブ履歴の取得"""
        return self._save_history.copy()
    
    def get_last_save_info(self) -> Dict[str, Any]:
        """最新のセーブ情報取得"""
        return self._last_save_info.copy()
    
    def is_auto_save_enabled(self) -> bool:
        """自動セーブが有効かどうか"""
        return self._auto_save_enabled
    
    def set_auto_save_enabled(self, enabled: bool) -> None:
        """自動セーブの有効/無効設定"""
        self._auto_save_enabled = enabled
        logger.info(f"自動セーブ: {'有効' if enabled else '無効'}")
    
    def _get_guild_characters(self) -> List[Any]:
        """ギルドキャラクターの取得"""
        try:
            if self.overworld_manager and hasattr(self.overworld_manager, 'get_guild_characters'):
                return self.overworld_manager.get_guild_characters()
            else:
                logger.warning("OverworldManager not available for guild characters")
                return []
        except Exception as e:
            logger.error(f"ギルドキャラクター取得エラー: {e}")
            return []
    
    def _get_dungeon_list(self) -> List[Dict[str, Any]]:
        """ダンジョンリストの取得"""
        try:
            if self.dungeon_manager and hasattr(self.dungeon_manager, 'get_dungeon_list'):
                return self.dungeon_manager.get_dungeon_list()
            else:
                logger.warning("DungeonManager not available for dungeon list")
                return []
        except Exception as e:
            logger.error(f"ダンジョンリスト取得エラー: {e}")
            return []
    
    def _restore_guild_characters(self, guild_characters: List[Any]) -> None:
        """ギルドキャラクターの復元"""
        try:
            if self.overworld_manager and hasattr(self.overworld_manager, 'restore_guild_characters'):
                self.overworld_manager.restore_guild_characters(guild_characters)
                logger.info(f"ギルドキャラクターを復元しました: {len(guild_characters)}人")
            else:
                logger.warning("OverworldManager not available for restoring guild characters")
        except Exception as e:
            logger.error(f"ギルドキャラクター復元エラー: {e}")
    
    def _restore_dungeon_list(self, dungeon_list: List[Dict[str, Any]]) -> None:
        """ダンジョンリストの復元"""
        try:
            if self.dungeon_manager and hasattr(self.dungeon_manager, 'restore_dungeon_list'):
                self.dungeon_manager.restore_dungeon_list(dungeon_list)
                logger.info(f"ダンジョンリストを復元しました: {len(dungeon_list)}個")
            else:
                logger.warning("DungeonManager not available for restoring dungeon list")
        except Exception as e:
            logger.error(f"ダンジョンリスト復元エラー: {e}")
    
    def _add_save_history(self, save_info: Dict[str, Any]) -> None:
        """セーブ履歴の追加"""
        self._save_history.append(save_info)
        
        # 履歴は最大20件まで保持
        if len(self._save_history) > 20:
            self._save_history.pop(0)
    
    def _get_timestamp(self) -> str:
        """現在のタイムスタンプ取得"""
        return datetime.now().isoformat()