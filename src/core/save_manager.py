"""セーブ・ロード管理システム"""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, field
import shutil

from src.character.party import Party
from src.character.character import Character
from src.utils.logger import logger
from src.utils.constants import SAVE_DIR


@dataclass
class SaveSlot:
    """セーブスロット情報"""
    slot_id: int
    name: str
    party_name: str
    total_playtime: float = 0.0
    last_saved: datetime = field(default_factory=datetime.now)
    party_level: int = 1
    location: str = "overworld"
    screenshot_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'slot_id': self.slot_id,
            'name': self.name,
            'party_name': self.party_name,
            'total_playtime': self.total_playtime,
            'last_saved': self.last_saved.isoformat(),
            'party_level': self.party_level,
            'location': self.location,
            'screenshot_path': self.screenshot_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SaveSlot':
        return cls(
            slot_id=data.get('slot_id', 0),
            name=data.get('name', ''),
            party_name=data.get('party_name', ''),
            total_playtime=data.get('total_playtime', 0.0),
            last_saved=datetime.fromisoformat(data.get('last_saved', datetime.now().isoformat())),
            party_level=data.get('party_level', 1),
            location=data.get('location', 'overworld'),
            screenshot_path=data.get('screenshot_path')
        )


@dataclass
class GameSave:
    """ゲームセーブデータ"""
    save_slot: SaveSlot
    party: Party
    game_state: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    flags: Dict[str, bool] = field(default_factory=dict)
    version: str = "0.1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'save_slot': self.save_slot.to_dict(),
            'party': self.party.to_dict(),
            'game_state': self.game_state,
            'settings': self.settings,
            'flags': self.flags,
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameSave':
        return cls(
            save_slot=SaveSlot.from_dict(data.get('save_slot', {})),
            party=Party.from_dict(data.get('party', {})),
            game_state=data.get('game_state', {}),
            settings=data.get('settings', {}),
            flags=data.get('flags', {}),
            version=data.get('version', '0.1.0')
        )


class SaveManager:
    """セーブ・ロード管理クラス"""
    
    def __init__(self, save_directory: str = SAVE_DIR):
        self.save_dir = Path(save_directory)
        self.save_dir.mkdir(exist_ok=True)
        
        self.auto_save_enabled = True
        self.auto_save_interval = 300  # 5分
        self.last_auto_save = datetime.now()
        
        self.current_save: Optional[GameSave] = None
        self.max_save_slots = 10
        
        logger.info(f"SaveManagerを初期化しました: {self.save_dir}")
    
    def get_save_path(self, slot_id: int) -> Path:
        """セーブファイルのパスを取得"""
        return self.save_dir / f"save_{slot_id:02d}.json"
    
    def get_backup_path(self, slot_id: int) -> Path:
        """バックアップファイルのパスを取得"""
        return self.save_dir / f"save_{slot_id:02d}.bak"
    
    def get_metadata_path(self) -> Path:
        """メタデータファイルのパスを取得"""
        return self.save_dir / "saves_metadata.json"
    
    def save_game(
        self, 
        party: Party, 
        slot_id: int, 
        save_name: str = "",
        game_state: Optional[Dict[str, Any]] = None,
        create_backup: bool = True
    ) -> bool:
        """ゲームを保存"""
        try:
            save_path = self.get_save_path(slot_id)
            
            # バックアップ作成
            if create_backup and save_path.exists():
                backup_path = self.get_backup_path(slot_id)
                shutil.copy2(save_path, backup_path)
                logger.debug(f"バックアップを作成しました: {backup_path}")
            
            # セーブスロット情報の作成
            if not save_name:
                save_name = f"Save {slot_id:02d}"
            
            save_slot = SaveSlot(
                slot_id=slot_id,
                name=save_name,
                party_name=party.name,
                party_level=int(party.get_average_level()),
                location=game_state.get('location', 'overworld') if game_state else 'overworld'
            )
            
            # ゲームセーブデータの作成
            game_save = GameSave(
                save_slot=save_slot,
                party=party,
                game_state=game_state or {},
                settings={},
                flags={}
            )
            
            # JSONファイルに保存
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(game_save.to_dict(), f, ensure_ascii=False, indent=2)
            
            # メタデータ更新
            self._update_metadata(save_slot)
            
            # 現在のセーブとして設定
            self.current_save = game_save
            
            logger.info(f"ゲームを保存しました: スロット {slot_id}, パーティ: {party.name}")
            return True
            
        except Exception as e:
            logger.error(f"ゲーム保存に失敗しました: {e}")
            return False
    
    def load_game(self, slot_id: int) -> Optional[GameSave]:
        """ゲームをロード"""
        try:
            save_path = self.get_save_path(slot_id)
            
            if not save_path.exists():
                logger.warning(f"セーブファイルが見つかりません: スロット {slot_id}")
                return None
            
            with open(save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            game_save = GameSave.from_dict(data)
            self.current_save = game_save
            
            logger.info(f"ゲームをロードしました: スロット {slot_id}, パーティ: {game_save.party.name}")
            return game_save
            
        except Exception as e:
            logger.error(f"ゲームロードに失敗しました: {e}")
            return None
    
    def delete_save(self, slot_id: int) -> bool:
        """セーブデータを削除"""
        try:
            save_path = self.get_save_path(slot_id)
            backup_path = self.get_backup_path(slot_id)
            
            # ファイル削除
            if save_path.exists():
                save_path.unlink()
            if backup_path.exists():
                backup_path.unlink()
            
            # メタデータから削除
            self._remove_from_metadata(slot_id)
            
            logger.info(f"セーブデータを削除しました: スロット {slot_id}")
            return True
            
        except Exception as e:
            logger.error(f"セーブデータ削除に失敗しました: {e}")
            return False
    
    def get_save_slots(self) -> List[SaveSlot]:
        """利用可能なセーブスロット一覧を取得"""
        try:
            metadata_path = self.get_metadata_path()
            
            if not metadata_path.exists():
                return []
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            slots = []
            for slot_data in metadata.get('slots', []):
                slots.append(SaveSlot.from_dict(slot_data))
            
            # 最終保存日時でソート
            slots.sort(key=lambda x: x.last_saved, reverse=True)
            return slots
            
        except Exception as e:
            logger.error(f"セーブスロット一覧取得に失敗しました: {e}")
            return []
    
    def has_save(self, slot_id: int) -> bool:
        """指定スロットにセーブデータがあるかチェック"""
        save_path = self.get_save_path(slot_id)
        return save_path.exists()
    
    def auto_save(self, party: Party, game_state: Optional[Dict[str, Any]] = None) -> bool:
        """オートセーブ"""
        if not self.auto_save_enabled:
            return False
        
        now = datetime.now()
        if (now - self.last_auto_save).total_seconds() < self.auto_save_interval:
            return False
        
        # スロット0をオートセーブ用として使用
        auto_save_slot = 0
        success = self.save_game(
            party=party,
            slot_id=auto_save_slot,
            save_name="Auto Save",
            game_state=game_state,
            create_backup=False
        )
        
        if success:
            self.last_auto_save = now
            logger.debug("オートセーブが完了しました")
        
        return success
    
    def export_save(self, slot_id: int, export_path: str) -> bool:
        """セーブデータのエクスポート"""
        try:
            save_path = self.get_save_path(slot_id)
            if not save_path.exists():
                logger.warning(f"エクスポート対象のセーブファイルが見つかりません: スロット {slot_id}")
                return False
            
            shutil.copy2(save_path, export_path)
            logger.info(f"セーブデータをエクスポートしました: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"セーブデータエクスポートに失敗しました: {e}")
            return False
    
    def import_save(self, import_path: str, slot_id: int) -> bool:
        """セーブデータのインポート"""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                logger.warning(f"インポート対象のファイルが見つかりません: {import_path}")
                return False
            
            # 有効性チェック
            with open(import_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                GameSave.from_dict(data)  # バリデーション
            
            save_path = self.get_save_path(slot_id)
            shutil.copy2(import_file, save_path)
            
            logger.info(f"セーブデータをインポートしました: スロット {slot_id}")
            return True
            
        except Exception as e:
            logger.error(f"セーブデータインポートに失敗しました: {e}")
            return False
    
    def _update_metadata(self, save_slot: SaveSlot):
        """メタデータを更新"""
        try:
            metadata_path = self.get_metadata_path()
            metadata = {'slots': []}
            
            # 既存メタデータの読み込み
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            # スロット情報の更新
            slots = metadata.get('slots', [])
            updated = False
            
            for i, slot_data in enumerate(slots):
                if slot_data.get('slot_id') == save_slot.slot_id:
                    slots[i] = save_slot.to_dict()
                    updated = True
                    break
            
            if not updated:
                slots.append(save_slot.to_dict())
            
            metadata['slots'] = slots
            
            # メタデータ保存
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"メタデータ更新に失敗しました: {e}")
    
    def _remove_from_metadata(self, slot_id: int):
        """メタデータからスロット情報を削除"""
        try:
            metadata_path = self.get_metadata_path()
            
            if not metadata_path.exists():
                return
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            slots = metadata.get('slots', [])
            metadata['slots'] = [slot for slot in slots if slot.get('slot_id') != slot_id]
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"メタデータからの削除に失敗しました: {e}")
    
    def cleanup_old_saves(self, keep_count: int = 5):
        """古いセーブデータのクリーンアップ"""
        try:
            slots = self.get_save_slots()
            
            # オートセーブ以外をフィルタリング
            manual_saves = [slot for slot in slots if slot.slot_id != 0]
            
            if len(manual_saves) <= keep_count:
                return
            
            # 古いセーブを削除
            to_delete = manual_saves[keep_count:]
            for slot in to_delete:
                self.delete_save(slot.slot_id)
            
            logger.info(f"{len(to_delete)} 個の古いセーブデータを削除しました")
            
        except Exception as e:
            logger.error(f"セーブデータクリーンアップに失敗しました: {e}")
    
    def save_additional_data(self, slot_id: str, data_type: str, data: Any) -> bool:
        """追加データの保存（遷移システム用）"""
        try:
            additional_dir = self.save_dir / slot_id / "additional"
            additional_dir.mkdir(parents=True, exist_ok=True)
            
            data_path = additional_dir / f"{data_type}.json"
            
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"追加データを保存しました: {slot_id}/{data_type}")
            return True
            
        except Exception as e:
            logger.error(f"追加データ保存に失敗しました: {e}")
            return False
    
    def load_additional_data(self, slot_id: str, data_type: str) -> Optional[Any]:
        """追加データの読み込み（遷移システム用）"""
        try:
            data_path = self.save_dir / slot_id / "additional" / f"{data_type}.json"
            
            if not data_path.exists():
                logger.debug(f"追加データが見つかりません: {slot_id}/{data_type}")
                return None
            
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"追加データを読み込みました: {slot_id}/{data_type}")
            return data
            
        except Exception as e:
            logger.error(f"追加データ読み込みに失敗しました: {e}")
            return None


# グローバルインスタンス
save_manager = SaveManager()