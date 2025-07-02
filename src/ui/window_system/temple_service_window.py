"""神殿サービス専用ウィンドウ"""

from typing import Dict, Any, List, Optional
import pygame
import pygame_gui
from src.ui.window_system.facility_sub_window import FacilitySubWindow
from src.core.config_manager import config_manager
from src.utils.logger import logger


class TempleServiceWindow(FacilitySubWindow):
    """神殿サービス専用ウィンドウ
    
    蘇生サービス、状態異常治療サービスを統合したWindow実装。
    レガシーメニューの3箇所（resurrection_menu, status_cure_menu, char_status_cure）を代替。
    """
    
    def __init__(self, window_id: str, facility_config: Dict[str, Any], parent: 'Window' = None):
        """初期化
        
        Args:
            window_id: ウィンドウID（例: 'temple_service'）
            facility_config: 神殿設定データ
                - parent_facility: 親神殿インスタンス
                - current_party: 現在のパーティ
                - service_types: ['resurrection', 'status_cure']
                - title: ウィンドウタイトル（オプション）
            parent: 親ウィンドウ（オプション）
        """
        super().__init__(window_id, facility_config, parent)
        
        # 神殿固有の設定
        self.title = facility_config.get('title', '神殿サービス')
        self.available_services = self._validate_services(self.service_types)
        
        # UI要素
        self.service_buttons = {}
        self.character_list = None
        self.service_info_panel = None
        self.cost_display = None
        self.confirm_button = None
        self.back_button = None
        
        # 選択状態
        self.selected_service = None
        self.selected_character = None
        
    def _validate_services(self, services: List[str]) -> List[str]:
        """サービスタイプを検証
        
        Args:
            services: サービスタイプリスト
            
        Returns:
            有効なサービスタイプのリスト
        """
        valid_services = ['resurrection', 'status_cure', 'blessing']
        return [s for s in services if s in valid_services]
    
    def get_resurrection_candidates(self) -> List:
        """蘇生対象キャラクターを取得
        
        Returns:
            蘇生可能なキャラクターのリスト（死亡状態のキャラクター）
        """
        if not self.has_party():
            return []
        
        candidates = []
        for character in self.get_party_members():
            # Mock対応：derived_stats.current_hpまたはcurrent_hpをチェック
            if hasattr(character, 'derived_stats') and hasattr(character.derived_stats, 'current_hp'):
                hp = character.derived_stats.current_hp
            else:
                hp = getattr(character, 'current_hp', 1)  # デフォルトは生存
            
            # 死亡状態判定
            if hp == 0:
                candidates.append(character)
            # または status が死亡を示している場合
            elif hasattr(character, 'status'):
                status_value = getattr(character.status, 'value', None) if hasattr(character.status, 'value') else str(character.status)
                if status_value in ['dead', 'ashes']:
                    candidates.append(character)
        
        return candidates
    
    def get_status_cure_candidates(self) -> List:
        """状態異常治療対象キャラクターを取得
        
        Returns:
            治療可能なキャラクターのリスト（状態異常のあるキャラクター）
        """
        if not self.has_party():
            return []
        
        candidates = []
        for character in self.get_party_members():
            # Mock対応：status_effectsまたはhas_status_effectをチェック
            if hasattr(character, 'status_effects') and character.status_effects:
                candidates.append(character)
            elif hasattr(character, 'has_status_effect') and callable(character.has_status_effect):
                # 一般的な状態異常をチェック
                common_effects = ['poison', 'paralysis', 'sleep', 'charm', 'curse']
                for effect in common_effects:
                    if character.has_status_effect(effect):
                        candidates.append(character)
                        break
        
        return candidates
    
    def calculate_resurrection_cost(self, character) -> int:
        """蘇生コストを計算
        
        Args:
            character: 対象キャラクター
            
        Returns:
            蘇生コスト（ゴールド）
        """
        if not character:
            return 0
        
        # キャラクターレベルベースのコスト計算
        level = 1
        if hasattr(character, 'experience') and hasattr(character.experience, 'level'):
            level = character.experience.level
        elif hasattr(character, 'level'):
            level = character.level
        
        # 基本コスト + レベル依存コスト
        base_cost = 500
        level_multiplier = 100
        return base_cost + (level * level_multiplier)
    
    def calculate_cure_cost(self, character, effect_type: str) -> int:
        """状態異常治療コストを計算
        
        Args:
            character: 対象キャラクター
            effect_type: 状態異常タイプ
            
        Returns:
            治療コスト（ゴールド）
        """
        if not character or not effect_type:
            return 0
        
        # 状態異常タイプ別のコスト
        effect_costs = {
            'poison': 50,
            'paralysis': 100,
            'sleep': 25,
            'charm': 150,
            'curse': 300
        }
        
        return effect_costs.get(effect_type, 100)  # デフォルト100ゴールド
    
    def handle_service_request(self, service_type: str, **kwargs) -> bool:
        """サービスリクエストの処理
        
        Args:
            service_type: サービスタイプ（'resurrection' または 'status_cure'）
            **kwargs: サービス固有のパラメータ
                - character: 対象キャラクター
                - effect_type: 状態異常タイプ（status_cure時）
                
        Returns:
            サービス処理が成功したらTrue
        """
        if not self.can_provide_service(service_type):
            logger.warning(f"提供できないサービスです: {service_type}")
            return False
        
        character = kwargs.get('character')
        if not character:
            logger.warning("対象キャラクターが指定されていません")
            return False
        
        if service_type == 'resurrection':
            return self._perform_resurrection(character)
        elif service_type == 'status_cure':
            effect_type = kwargs.get('effect_type')
            return self._perform_status_cure(character, effect_type)
        elif service_type == 'blessing':
            return self._perform_blessing()
        
        return False
    
    def _perform_resurrection(self, character) -> bool:
        """蘇生処理を実行
        
        Args:
            character: 対象キャラクター
            
        Returns:
            蘇生が成功したらTrue
        """
        # コスト計算と支払い確認は省略（実装時に追加）
        cost = self.calculate_resurrection_cost(character)
        
        # 蘇生処理（Mock対応）
        if hasattr(character, 'revive') and callable(character.revive):
            character.revive()
        else:
            # Mock用の簡易蘇生
            if hasattr(character, 'derived_stats') and hasattr(character.derived_stats, 'current_hp'):
                character.derived_stats.current_hp = 1
            elif hasattr(character, 'current_hp'):
                character.current_hp = 1
        
        logger.info(f"{character.name}を蘇生しました（コスト: {cost}G）")
        return True
    
    def _perform_status_cure(self, character, effect_type: str = None) -> bool:
        """状態異常治療を実行
        
        Args:
            character: 対象キャラクター
            effect_type: 状態異常タイプ（指定なしの場合は全治療）
            
        Returns:
            治療が成功したらTrue
        """
        if not effect_type:
            # 全状態異常の治療
            if hasattr(character, 'status_effects'):
                character.status_effects.clear()
            logger.info(f"{character.name}の全状態異常を治療しました")
        else:
            # 特定状態異常の治療
            if hasattr(character, 'status_effects') and effect_type in character.status_effects:
                character.status_effects.remove(effect_type)
            logger.info(f"{character.name}の{effect_type}を治療しました")
        
        return True
    
    def _perform_blessing(self) -> bool:
        """祝福処理を実行
        
        Returns:
            祝福が成功したらTrue
        """
        if not self.has_party():
            logger.warning("パーティが設定されていません")
            return False
        
        # 祝福コスト（固定）
        blessing_cost = 100
        
        # TODO: パーティのゴールドチェック（実装時に追加）
        # TODO: パーティへの祝福効果付与（実装時に追加）
        
        logger.info(f"パーティに祝福を付与しました（コスト: {blessing_cost}G）")
        return True
    
    def create_service_ui(self):
        """サービス用UIの作成
        
        神殿サービス選択、キャラクター選択、確認ボタンなどのUI要素を作成。
        """
        # 実装はPhase 2の具体的なUI実装時に追加
        # 現在はテスト用のプレースホルダー
        pass
    
    def handle_message(self, message_type: str, message_data: Dict[str, Any]) -> bool:
        """Windowメッセージの処理
        
        Args:
            message_type: メッセージタイプ
            message_data: メッセージデータ
            
        Returns:
            メッセージ処理が成功したらTrue
        """
        if message_type == 'service_selected':
            service_type = message_data.get('service')
            target_character = message_data.get('target_character')
            
            if service_type and target_character:
                return self.handle_service_request(service_type, character=target_character)
        
        # 親クラスのメッセージ処理にフォールバック
        return super().handle_message(message_type, message_data) if hasattr(super(), 'handle_message') else False
    
    def create(self) -> None:
        """ウィンドウの作成
        
        Windowクラスの抽象メソッド実装。
        実際のUI要素の作成はcreate_service_ui()で行う。
        """
        self.create_service_ui()
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理
        
        Args:
            event: pygameイベント
            
        Returns:
            イベントを処理したらTrue
        """
        # 神殿サービス固有のイベント処理
        # 現在はプレースホルダー実装
        return False