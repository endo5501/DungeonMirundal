"""ステータス効果表示UI"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from src.ui.base_ui import UIElement, UIButton, UIText, UIMenu, UIDialog, UIState, ui_manager
from src.effects.status_effects import StatusEffectType, status_effect_manager
from src.character.party import Party
from src.character.character import Character
from src.core.config_manager import config_manager
from src.utils.logger import logger


class StatusEffectsUI:
    """ステータス効果表示UI管理クラス"""
    
    def __init__(self):
        self.current_party: Optional[Party] = None
        self.current_character: Optional[Character] = None
        
        # UI状態
        self.is_open = False
        self.callback_on_close: Optional[Callable] = None
        
        logger.info("StatusEffectsUIを初期化しました")
    
    def set_party(self, party: Party):
        """パーティを設定"""
        self.current_party = party
        logger.debug(f"パーティを設定: {party.name}")
    
    def show_party_status_effects(self, party: Party):
        """パーティステータス効果を表示"""
        self.set_party(party)
        
        main_menu = UIMenu("party_status_effects", "パーティステータス効果")
        
        # 各キャラクターのステータス効果
        for character in party.get_all_characters():
            effects = character.get_status_effects()
            active_effects = effects.get_active_effects()
            effect_count = len(active_effects)
            
            char_info = f"{character.name} ({effect_count}個の効果)"
            main_menu.add_menu_item(
                char_info,
                self._show_character_status_effects,
                [character]
            )
        
        # パーティ効果統計
        main_menu.add_menu_item(
            "パーティ効果統計",
            self._show_party_effects_stats
        )
        
        main_menu.add_menu_item(
            config_manager.get_text("menu.close"),
            self._close_status_effects_ui
        )
        
        ui_manager.register_element(main_menu)
        ui_manager.show_element(main_menu.element_id, modal=True)
        self.is_open = True
        
        logger.info("パーティステータス効果メニューを表示")
    
    def _show_character_status_effects(self, character: Character):
        """キャラクターステータス効果を表示"""
        self.current_character = character
        
        effects_menu = UIMenu("character_status_effects", f"{character.name}のステータス効果")
        
        effects = character.get_status_effects()
        active_effects = effects.get_active_effects()
        
        if not active_effects:
            effects_menu.add_menu_item(
                "現在有効な効果はありません",
                lambda: None
            )
        else:
            # アクティブな効果を表示
            for effect in active_effects:
                effect_name = self._get_effect_name(effect.effect_type)
                duration_text = f"残り{effect.duration}ターン"
                
                effect_text = f"{effect_name} ({duration_text})"
                effects_menu.add_menu_item(
                    effect_text,
                    self._show_effect_details,
                    [effect]
                )
        
        # 効果の手動解除（回復アイテム等）
        effects_menu.add_menu_item(
            "効果の解除",
            self._show_effect_removal_options
        )
        
        effects_menu.add_menu_item(
            "戻る",
            self._back_to_main_menu
        )
        
        ui_manager.register_element(effects_menu)
        ui_manager.show_element(effects_menu.element_id, modal=True)
    
    def _show_effect_details(self, effect):
        """効果詳細を表示"""
        effect_name = self._get_effect_name(effect.effect_type)
        
        details = f"【{effect_name}】\\n\\n"
        details += f"効果: {self._get_effect_description(effect.effect_type)}\\n"
        details += f"強度: {effect.strength}\\n"
        details += f"残り時間: {effect.duration}ターン\\n"
        details += f"発生源: {effect.source}\\n\\n"
        
        # 効果の具体的な影響
        if effect.effect_type in [StatusEffectType.POISON]:
            details += f"毎ターン {effect.strength} のダメージを受けます。"
        elif effect.effect_type in [StatusEffectType.REGEN]:
            details += f"毎ターン {effect.strength} のHPを回復します。"
        elif effect.effect_type in [StatusEffectType.STRENGTH_UP]:
            details += f"筋力が {effect.strength} 上昇しています。"
        elif effect.effect_type in [StatusEffectType.DEFENSE_UP]:
            details += f"防御力が {effect.strength} 上昇しています。"
        elif effect.effect_type in [StatusEffectType.HASTE]:
            details += "行動速度が上昇しています。"
        elif effect.effect_type in [StatusEffectType.SLOW]:
            details += "行動速度が低下しています。"
        elif effect.effect_type in [StatusEffectType.PARALYSIS]:
            details += "麻痺により行動できない可能性があります。"
        elif effect.effect_type in [StatusEffectType.SILENCE]:
            details += "魔法を使用することができません。"
        
        dialog = UIDialog(
            "effect_detail_dialog",
            "ステータス効果詳細",
            details,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _show_effect_removal_options(self):
        """効果解除オプションを表示"""
        if not self.current_character:
            return
        
        removal_menu = UIMenu("effect_removal", "効果の解除")
        
        effects = self.current_character.get_status_effects()
        removable_effects = []
        
        # 除去可能な効果をフィルタ
        for effect in effects.get_active_effects():
            if self._can_remove_effect(effect.effect_type):
                removable_effects.append(effect)
        
        if not removable_effects:
            removal_menu.add_menu_item(
                "除去可能な効果はありません",
                lambda: None
            )
        else:
            for effect in removable_effects:
                effect_name = self._get_effect_name(effect.effect_type)
                removal_menu.add_menu_item(
                    f"{effect_name}を解除",
                    self._remove_effect,
                    [effect]
                )
        
        removal_menu.add_menu_item(
            "戻る",
            self._back_to_character_effects
        )
        
        ui_manager.register_element(removal_menu)
        ui_manager.show_element(removal_menu.element_id, modal=True)
    
    def _remove_effect(self, effect):
        """効果を除去"""
        if not self.current_character:
            return
        
        effects = self.current_character.get_status_effects()
        
        try:
            effects.remove_effect(effect.effect_type)
            effect_name = self._get_effect_name(effect.effect_type)
            self._show_message(f"{effect_name}を解除しました")
            
            # 画面を更新
            self._back_to_character_effects()
        except Exception as e:
            self._show_message(f"効果の解除に失敗しました: {str(e)}")
    
    def _show_party_effects_stats(self):
        """パーティ効果統計を表示"""
        if not self.current_party:
            return
        
        stats_text = "【パーティステータス効果統計】\\n\\n"
        
        total_effects = 0
        effect_types = {}
        
        for character in self.current_party.get_all_characters():
            effects = character.get_status_effects()
            active_effects = effects.get_active_effects()
            
            total_effects += len(active_effects)
            
            for effect in active_effects:
                effect_name = self._get_effect_name(effect.effect_type)
                if effect_name not in effect_types:
                    effect_types[effect_name] = 0
                effect_types[effect_name] += 1
        
        stats_text += f"総効果数: {total_effects}\\n\\n"
        
        if effect_types:
            stats_text += "【効果種別】\\n"
            for effect_name, count in sorted(effect_types.items()):
                stats_text += f"{effect_name}: {count}個\\n"
        else:
            stats_text += "現在有効な効果はありません。"
        
        stats_text += "\\n【キャラクター別】\\n"
        for character in self.current_party.get_all_characters():
            effects = character.get_status_effects()
            active_count = len(effects.get_active_effects())
            stats_text += f"{character.name}: {active_count}個\\n"
        
        dialog = UIDialog(
            "party_effects_stats",
            "パーティ効果統計",
            stats_text,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _can_remove_effect(self, effect_type: StatusEffectType) -> bool:
        """効果が除去可能かチェック"""
        # 除去可能な効果（デバフ系）
        removable_effects = [
            StatusEffectType.POISON,
            StatusEffectType.PARALYSIS,
            StatusEffectType.SLEEP,
            StatusEffectType.CONFUSION,
            StatusEffectType.FEAR,
            StatusEffectType.BLIND,
            StatusEffectType.SILENCE,
            StatusEffectType.SLOW
        ]
        return effect_type in removable_effects
    
    def _get_effect_name(self, effect_type: StatusEffectType) -> str:
        """効果名を取得"""
        effect_names = {
            StatusEffectType.POISON: "毒",
            StatusEffectType.PARALYSIS: "麻痺",
            StatusEffectType.SLEEP: "睡眠",
            StatusEffectType.CONFUSION: "混乱",
            StatusEffectType.CHARM: "魅力",
            StatusEffectType.FEAR: "恐怖",
            StatusEffectType.BLIND: "盲目",
            StatusEffectType.SILENCE: "沈黙",
            StatusEffectType.STONE: "石化",
            StatusEffectType.REGEN: "再生",
            StatusEffectType.HASTE: "加速",
            StatusEffectType.SLOW: "減速",
            StatusEffectType.STRENGTH_UP: "筋力強化",
            StatusEffectType.DEFENSE_UP: "防御強化",
            StatusEffectType.MAGIC_UP: "魔力強化",
            StatusEffectType.RESIST_UP: "耐性強化"
        }
        return effect_names.get(effect_type, effect_type.value)
    
    def _get_effect_description(self, effect_type: StatusEffectType) -> str:
        """効果説明を取得"""
        descriptions = {
            StatusEffectType.POISON: "毎ターンダメージを受ける",
            StatusEffectType.PARALYSIS: "行動できない可能性がある",
            StatusEffectType.SLEEP: "行動できない（攻撃で解除）",
            StatusEffectType.CONFUSION: "ランダムな行動を取る",
            StatusEffectType.CHARM: "敵として行動する",
            StatusEffectType.FEAR: "逃走する可能性が高い",
            StatusEffectType.BLIND: "命中率が低下する",
            StatusEffectType.SILENCE: "魔法が使用できない",
            StatusEffectType.STONE: "完全に行動不能",
            StatusEffectType.REGEN: "毎ターンHPが回復する",
            StatusEffectType.HASTE: "行動速度が上昇する",
            StatusEffectType.SLOW: "行動速度が低下する",
            StatusEffectType.STRENGTH_UP: "筋力が上昇する",
            StatusEffectType.DEFENSE_UP: "防御力が上昇する",
            StatusEffectType.MAGIC_UP: "魔力が上昇する",
            StatusEffectType.RESIST_UP: "魔法耐性が上昇する"
        }
        return descriptions.get(effect_type, "効果の詳細不明")
    
    def show(self):
        """ステータス効果UIを表示"""
        if self.current_party:
            self.show_party_status_effects(self.current_party)
        else:
            logger.warning("パーティが設定されていません")
    
    def hide(self):
        """ステータス効果UIを非表示"""
        try:
            ui_manager.hide_element("party_status_effects")
        except:
            pass
        self.is_open = False
        logger.debug("ステータス効果UIを非表示にしました")
    
    def destroy(self):
        """ステータス効果UIを破棄"""
        self.hide()
        self.current_party = None
        self.current_character = None
        logger.debug("StatusEffectsUIを破棄しました")
    
    def set_close_callback(self, callback: Callable):
        """閉じるコールバックを設定"""
        self.callback_on_close = callback
    
    def _back_to_main_menu(self):
        """メインメニューに戻る"""
        if self.current_party:
            self.show_party_status_effects(self.current_party)
    
    def _back_to_character_effects(self):
        """キャラクター効果画面に戻る"""
        if self.current_character:
            self._show_character_status_effects(self.current_character)
    
    def _close_status_effects_ui(self):
        """ステータス効果UIを閉じる"""
        self.hide()
        if self.callback_on_close:
            self.callback_on_close()
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        ui_manager.hide_all_elements()
    
    def _show_message(self, message: str):
        """メッセージを表示"""
        dialog = UIDialog(
            "status_effects_message",
            "ステータス効果",
            message,
            buttons=[
                {"text": "OK", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)


# グローバルインスタンス
status_effects_ui = StatusEffectsUI()