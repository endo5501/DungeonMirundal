"""魔法管理UI システム"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum

from src.ui.base_ui import UIElement, UIButton, UIText, UIMenu, UIDialog, UIState, ui_manager
from src.magic.spells import SpellBook, SpellSlot, Spell, SpellManager, spell_manager, SpellSchool, SpellType
from src.character.party import Party
from src.character.character import Character
from src.core.config_manager import config_manager
from src.utils.logger import logger


class MagicUIMode(Enum):
    """魔法UI表示モード"""
    OVERVIEW = "overview"               # 魔法概要
    SPELLBOOK = "spellbook"            # 魔法書管理
    SLOT_MANAGEMENT = "slot_management" # スロット管理
    SPELL_LEARNING = "spell_learning"   # 魔法習得
    SPELL_CASTING = "spell_casting"     # 魔法詠唱


class MagicUI:
    """魔法UI管理クラス"""
    
    def __init__(self):
        self.current_party: Optional[Party] = None
        self.current_character: Optional[Character] = None
        self.current_spellbook: Optional[SpellBook] = None
        self.current_mode = MagicUIMode.OVERVIEW
        self.selected_level: Optional[int] = None
        self.selected_slot_index: Optional[int] = None
        
        # UI状態
        self.is_open = False
        self.callback_on_close: Optional[Callable] = None
        
        # 魔法マネージャー
        self.spell_manager = spell_manager
        
        logger.info("MagicUIを初期化しました")
    
    def set_party(self, party: Party):
        """パーティを設定"""
        self.current_party = party
        logger.debug(f"パーティを設定: {party.name}")
    
    def show_party_magic_menu(self, party: Party):
        """パーティ魔法メニューを表示"""
        self.set_party(party)
        self.current_mode = MagicUIMode.OVERVIEW
        
        main_menu = UIMenu("party_magic_main", "パーティ魔法管理")
        
        # 各キャラクターの魔法
        for character in party.get_all_characters():
            spellbook = character.get_spellbook()
            summary = spellbook.get_spell_summary()
            learned_count = summary['learned_count']
            equipped_slots = summary['equipped_slots']
            
            char_info = f"{character.name} (習得:{learned_count} 装備:{equipped_slots})"
            main_menu.add_menu_item(
                char_info,
                self._show_character_magic,
                [character]
            )
        
        # パーティ魔法統計
        main_menu.add_menu_item(
            "パーティ魔法統計",
            self._show_party_magic_stats
        )
        
        # 魔法習得（地上部でのみ）
        main_menu.add_menu_item(
            "魔法習得（宿屋・ギルド）",
            self._show_spell_learning_info
        )
        
        main_menu.add_menu_item(
            config_manager.get_text("menu.close"),
            self._close_magic_ui
        )
        
        ui_manager.register_element(main_menu)
        ui_manager.show_element(main_menu.element_id, modal=True)
        self.is_open = True
        
        logger.info("パーティ魔法メニューを表示")
    
    def _show_character_magic(self, character: Character):
        """キャラクター魔法画面を表示"""
        self.current_character = character
        self.current_spellbook = character.get_spellbook()
        
        magic_menu = UIMenu("character_magic", f"{character.name}の魔法")
        
        # 魔法書管理
        magic_menu.add_menu_item(
            "魔法スロット管理",
            self._show_spell_slots
        )
        
        # 習得済み魔法一覧
        magic_menu.add_menu_item(
            "習得済み魔法一覧",
            self._show_learned_spells
        )
        
        # 魔法使用（戦闘外使用可能なもの）
        magic_menu.add_menu_item(
            "魔法使用",
            self._show_spell_usage
        )
        
        # 魔法統計
        magic_menu.add_menu_item(
            "魔法統計・詳細",
            self._show_character_magic_stats
        )
        
        magic_menu.add_menu_item(
            "戻る",
            self._back_to_main_menu
        )
        
        ui_manager.register_element(magic_menu)
        ui_manager.show_element(magic_menu.element_id, modal=True)
    
    def _show_spell_slots(self):
        """魔法スロット管理画面を表示"""
        if not self.current_spellbook:
            return
        
        slots_menu = UIMenu("spell_slots", "魔法スロット管理")
        
        summary = self.current_spellbook.get_spell_summary()
        
        # レベル別スロット表示
        for level in sorted(summary['slots_by_level'].keys()):
            level_info = summary['slots_by_level'][level]
            
            level_text = f"レベル{level} スロット ({level_info['equipped']}/{level_info['total']})"
            slots_menu.add_menu_item(
                level_text,
                self._show_level_slots,
                [level]
            )
        
        # 全スロット回復
        slots_menu.add_menu_item(
            "全スロット使用回数回復",
            self._restore_all_spell_uses
        )
        
        slots_menu.add_menu_item(
            "戻る",
            self._back_to_character_magic
        )
        
        ui_manager.register_element(slots_menu)
        ui_manager.show_element(slots_menu.element_id, modal=True)
    
    def _show_level_slots(self, level: int):
        """レベル別スロット表示"""
        self.selected_level = level
        
        if not self.current_spellbook or level not in self.current_spellbook.spell_slots:
            return
        
        level_slots = self.current_spellbook.spell_slots[level]
        
        level_menu = UIMenu("level_slots", f"レベル{level} 魔法スロット")
        
        for i, slot in enumerate(level_slots):
            if slot.is_empty():
                slot_text = f"[{i+1}] (空) - 使用可能回数: {slot.max_uses}"
            else:
                spell = self.spell_manager.get_spell(slot.spell_id)
                spell_name = spell.get_name() if spell else "不明な魔法"
                slot_text = f"[{i+1}] {spell_name} ({slot.current_uses}/{slot.max_uses})"
            
            level_menu.add_menu_item(
                slot_text,
                self._show_slot_options,
                [level, i]
            )
        
        level_menu.add_menu_item(
            "戻る",
            self._back_to_spell_slots
        )
        
        ui_manager.register_element(level_menu)
        ui_manager.show_element(level_menu.element_id, modal=True)
    
    def _show_slot_options(self, level: int, slot_index: int):
        """スロットオプションメニューを表示"""
        self.selected_level = level
        self.selected_slot_index = slot_index
        
        if not self.current_spellbook:
            return
        
        slot = self.current_spellbook.spell_slots[level][slot_index]
        
        options_menu = UIMenu("slot_options", f"レベル{level} スロット{slot_index+1}の操作")
        
        if not slot.is_empty():
            # 装備中の場合
            spell = self.spell_manager.get_spell(slot.spell_id)
            if spell:
                options_menu.add_menu_item(
                    "魔法詳細",
                    self._show_spell_details,
                    [spell]
                )
            
            options_menu.add_menu_item(
                "魔法の装備解除",
                self._unequip_spell,
                [level, slot_index]
            )
        
        # 魔法装備
        options_menu.add_menu_item(
            "魔法を装備する",
            self._show_spell_selection,
            [level, slot_index]
        )
        
        # スロット使用回数回復
        if slot.current_uses < slot.max_uses:
            options_menu.add_menu_item(
                "使用回数回復",
                self._restore_slot_uses,
                [level, slot_index]
            )
        
        options_menu.add_menu_item(
            "戻る",
            self._back_to_level_slots
        )
        
        ui_manager.register_element(options_menu)
        ui_manager.show_element(options_menu.element_id, modal=True)
    
    def _show_spell_selection(self, level: int, slot_index: int):
        """魔法選択メニューを表示"""
        if not self.current_spellbook:
            return
        
        selection_menu = UIMenu("spell_selection", f"レベル{level}スロットに装備する魔法")
        
        # 習得済み魔法から装備可能なものを取得
        learned_spells = self.current_spellbook.learned_spells
        suitable_spells = []
        
        for spell_id in learned_spells:
            spell = self.spell_manager.get_spell(spell_id)
            if spell and spell.level <= level:
                suitable_spells.append(spell)
        
        if not suitable_spells:
            selection_menu.add_menu_item(
                "装備可能な魔法がありません",
                lambda: None
            )
        else:
            # 学派別にソート
            suitable_spells.sort(key=lambda s: (s.school.value, s.level, s.get_name()))
            
            for spell in suitable_spells:
                spell_info = f"{spell.get_name()} (Lv.{spell.level} {self._get_school_name(spell.school)})"
                
                # MP消費量を表示
                spell_info += f" MP:{spell.mp_cost}"
                
                selection_menu.add_menu_item(
                    spell_info,
                    self._equip_spell_to_slot,
                    [spell.spell_id, level, slot_index]
                )
        
        selection_menu.add_menu_item(
            "キャンセル",
            self._back_to_slot_options
        )
        
        ui_manager.register_element(selection_menu)
        ui_manager.show_element(selection_menu.element_id, modal=True)
    
    def _equip_spell_to_slot(self, spell_id: str, level: int, slot_index: int):
        """スロットに魔法を装備"""
        if not self.current_spellbook:
            return
        
        success = self.current_spellbook.equip_spell_to_slot(spell_id, level, slot_index)
        
        if success:
            spell = self.spell_manager.get_spell(spell_id)
            spell_name = spell.get_name() if spell else spell_id
            self._show_message(f"{spell_name}をレベル{level}スロット{slot_index+1}に装備しました")
            
            # 画面を更新
            self._back_to_level_slots()
        else:
            self._show_message("魔法の装備に失敗しました")
    
    def _unequip_spell(self, level: int, slot_index: int):
        """魔法の装備を解除"""
        if not self.current_spellbook:
            return
        
        spell_id = self.current_spellbook.unequip_spell_from_slot(level, slot_index)
        
        if spell_id:
            spell = self.spell_manager.get_spell(spell_id)
            spell_name = spell.get_name() if spell else spell_id
            self._show_message(f"{spell_name}の装備を解除しました")
            
            # 画面を更新
            self._back_to_level_slots()
    
    def _show_learned_spells(self):
        """習得済み魔法一覧を表示"""
        if not self.current_spellbook:
            return
        
        learned_menu = UIMenu("learned_spells", "習得済み魔法一覧")
        
        learned_spells = self.current_spellbook.learned_spells
        
        if not learned_spells:
            learned_menu.add_menu_item(
                "習得済みの魔法がありません",
                lambda: None
            )
        else:
            # 魔法を取得してソート
            spell_objects = []
            for spell_id in learned_spells:
                spell = self.spell_manager.get_spell(spell_id)
                if spell:
                    spell_objects.append(spell)
            
            # 学派・レベル別にソート
            spell_objects.sort(key=lambda s: (s.school.value, s.level, s.get_name()))
            
            for spell in spell_objects:
                spell_info = f"{spell.get_name()} (Lv.{spell.level} {self._get_school_name(spell.school)})"
                
                learned_menu.add_menu_item(
                    spell_info,
                    self._show_spell_details,
                    [spell]
                )
        
        learned_menu.add_menu_item(
            "戻る",
            self._back_to_character_magic
        )
        
        ui_manager.register_element(learned_menu)
        ui_manager.show_element(learned_menu.element_id, modal=True)
    
    def _show_spell_usage(self):
        """魔法使用メニューを表示"""
        if not self.current_spellbook:
            return
        
        usage_menu = UIMenu("spell_usage", "魔法使用")
        
        # 使用可能な魔法を収集
        usable_spells = []
        
        for level, slots in self.current_spellbook.spell_slots.items():
            for i, slot in enumerate(slots):
                if slot.can_use():
                    spell = self.spell_manager.get_spell(slot.spell_id)
                    if spell and self._can_use_outside_combat(spell):
                        usable_spells.append((spell, level, i, slot))
        
        if not usable_spells:
            usage_menu.add_menu_item(
                "使用可能な魔法がありません",
                lambda: None
            )
        else:
            for spell, level, slot_index, slot in usable_spells:
                spell_info = f"{spell.get_name()} (Lv.{level} 残り:{slot.current_uses})"
                
                usage_menu.add_menu_item(
                    spell_info,
                    self._use_spell,
                    [spell, level, slot_index]
                )
        
        usage_menu.add_menu_item(
            "戻る",
            self._back_to_character_magic
        )
        
        ui_manager.register_element(usage_menu)
        ui_manager.show_element(usage_menu.element_id, modal=True)
    
    def _use_spell(self, spell: Spell, level: int, slot_index: int):
        """魔法を使用"""
        if not self.current_spellbook or not self.current_character:
            return
        
        # 対象選択が必要か確認
        if self._requires_target_selection(spell):
            self._show_target_selection(spell, level, slot_index)
        else:
            self._execute_spell_usage(spell, level, slot_index, None)
    
    def _show_target_selection(self, spell: Spell, level: int, slot_index: int):
        """魔法対象選択を表示"""
        if not self.current_party:
            return
        
        target_menu = UIMenu("spell_target", f"{spell.get_name()}の対象選択")
        
        # パーティメンバーを対象として追加
        for character in self.current_party.get_all_characters():
            if character.is_alive():
                status = "生存"
            else:
                status = "死亡"
            
            target_text = f"{character.name} ({status})"
            target_menu.add_menu_item(
                target_text,
                self._execute_spell_usage,
                [spell, level, slot_index, character]
            )
        
        target_menu.add_menu_item(
            "キャンセル",
            self._back_to_spell_usage
        )
        
        ui_manager.register_element(target_menu)
        ui_manager.show_element(target_menu.element_id, modal=True)
    
    def _execute_spell_usage(self, spell: Spell, level: int, slot_index: int, target: Optional[Character]):
        """魔法使用を実行"""
        if not self.current_spellbook or not self.current_character:
            return
        
        # MP消費チェック
        current_mp = self.current_character.derived_stats.current_mp
        if current_mp < spell.mp_cost:
            self._show_message(f"MPが不足しています (必要:{spell.mp_cost} 現在:{current_mp})")
            return
        
        # スロット使用
        success = self.current_spellbook.use_spell(level, slot_index)
        if not success:
            self._show_message("魔法の使用に失敗しました")
            return
        
        # MP消費
        self.current_character.derived_stats.current_mp -= spell.mp_cost
        
        # 魔法効果を実行
        result = self._apply_spell_effect(spell, self.current_character, target)
        
        self._show_message(f"{spell.get_name()}を使用しました\\n{result}")
        
        # 画面を更新
        self._back_to_spell_usage()
    
    def _apply_spell_effect(self, spell: Spell, caster: Character, target: Optional[Character]) -> str:
        """魔法効果を適用"""
        if spell.spell_type == SpellType.HEALING and target:
            # 回復魔法
            heal_amount = spell.calculate_effect_value({
                'faith': caster.derived_stats.faith,
                'intelligence': caster.derived_stats.intelligence
            })
            
            old_hp = target.derived_stats.current_hp
            target.derived_stats.current_hp = min(
                target.derived_stats.max_hp,
                target.derived_stats.current_hp + heal_amount
            )
            actual_heal = target.derived_stats.current_hp - old_hp
            
            return f"{target.name}のHPが{actual_heal}回復しました"
            
        elif spell.spell_type == SpellType.BUFF and target:
            # 強化魔法
            return f"{target.name}に{spell.get_name()}の効果をかけました"
            
        elif spell.spell_type == SpellType.UTILITY:
            # 汎用魔法
            return f"{spell.get_name()}の効果を発動しました"
            
        else:
            return "魔法効果を実行しました"
    
    def _show_spell_details(self, spell: Spell):
        """魔法詳細を表示"""
        details = f"【{spell.get_name()}】\\n\\n"
        details += f"説明: {spell.get_description()}\\n"
        details += f"レベル: {spell.level}\\n"
        details += f"学派: {self._get_school_name(spell.school)}\\n"
        details += f"種別: {self._get_type_name(spell.spell_type)}\\n"
        details += f"対象: {self._get_target_name(spell.target)}\\n"
        details += f"MP消費: {spell.mp_cost}\\n"
        
        if spell.effect.base_value > 0:
            details += f"基本効果値: {spell.effect.base_value}\\n"
        
        if spell.effect.scaling_stat:
            details += f"能力値依存: {spell.effect.scaling_stat}\\n"
        
        if spell.effect.element:
            details += f"属性: {spell.effect.element}\\n"
        
        if spell.effect.duration > 0:
            details += f"持続時間: {spell.effect.duration}ターン\\n"
        
        dialog = UIDialog(
            "spell_detail_dialog",
            "魔法詳細",
            details,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _show_character_magic_stats(self):
        """キャラクター魔法統計を表示"""
        if not self.current_spellbook:
            return
        
        summary = self.current_spellbook.get_spell_summary()
        
        stats_text = "【魔法統計】\\n\\n"
        stats_text += f"習得済み魔法: {summary['learned_count']}個\\n"
        stats_text += f"装備済みスロット: {summary['equipped_slots']}/{summary['total_slots']}\\n"
        stats_text += f"使用可能魔法: {summary['available_uses']}個\\n\\n"
        
        stats_text += "【レベル別スロット】\\n"
        for level in sorted(summary['slots_by_level'].keys()):
            level_info = summary['slots_by_level'][level]
            stats_text += f"レベル{level}: {level_info['equipped']}/{level_info['total']} "
            stats_text += f"(使用可能:{level_info['available']})\\n"
        
        dialog = UIDialog(
            "character_magic_stats",
            "魔法統計",
            stats_text,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _show_party_magic_stats(self):
        """パーティ魔法統計を表示"""
        if not self.current_party:
            return
        
        stats_text = "【パーティ魔法統計】\\n\\n"
        
        total_learned = 0
        total_equipped = 0
        total_available = 0
        
        for character in self.current_party.get_all_characters():
            spellbook = character.get_spellbook()
            summary = spellbook.get_spell_summary()
            
            total_learned += summary['learned_count']
            total_equipped += summary['equipped_slots']
            total_available += summary['available_uses']
        
        stats_text += f"総習得魔法数: {total_learned}\\n"
        stats_text += f"総装備スロット: {total_equipped}\\n"
        stats_text += f"総使用可能魔法: {total_available}\\n\\n"
        
        stats_text += "【キャラクター別】\\n"
        for character in self.current_party.get_all_characters():
            spellbook = character.get_spellbook()
            summary = spellbook.get_spell_summary()
            
            stats_text += f"{character.name}: "
            stats_text += f"習得{summary['learned_count']} "
            stats_text += f"装備{summary['equipped_slots']} "
            stats_text += f"使用可能{summary['available_uses']}\\n"
        
        dialog = UIDialog(
            "party_magic_stats",
            "パーティ魔法統計",
            stats_text,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _show_spell_learning_info(self):
        """魔法習得情報を表示"""
        info_text = "【魔法習得について】\\n\\n"
        info_text += "魔法は地上部の以下の施設で習得できます:\\n\\n"
        info_text += "• 魔術師ギルド: 攻撃魔法・汎用魔法\\n"
        info_text += "• 神殿: 神聖魔法・回復魔法\\n"
        info_text += "• 宿屋: 基本的な魔法の復習\\n\\n"
        info_text += "魔法習得には金貨と該当するレベルが必要です。\\n"
        info_text += "習得した魔法は魔法書のスロットに装備して使用します。"
        
        dialog = UIDialog(
            "spell_learning_info",
            "魔法習得情報",
            info_text,
            buttons=[
                {"text": "閉じる", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _restore_all_spell_uses(self):
        """全魔法スロット使用回数回復"""
        if not self.current_spellbook:
            return
        
        self.current_spellbook.restore_all_uses()
        self._show_message("全ての魔法スロットの使用回数を回復しました")
    
    def _restore_slot_uses(self, level: int, slot_index: int):
        """指定スロットの使用回数回復"""
        if not self.current_spellbook:
            return
        
        slot = self.current_spellbook.spell_slots[level][slot_index]
        slot.restore_uses()
        
        self._show_message(f"レベル{level}スロット{slot_index+1}の使用回数を回復しました")
        self._back_to_slot_options()
    
    def _can_use_outside_combat(self, spell: Spell) -> bool:
        """戦闘外で使用可能かチェック"""
        # 回復魔法、強化魔法、汎用魔法は戦闘外で使用可能
        return spell.spell_type in [SpellType.HEALING, SpellType.BUFF, SpellType.UTILITY, SpellType.REVIVAL]
    
    def _requires_target_selection(self, spell: Spell) -> bool:
        """対象選択が必要かチェック"""
        from src.magic.spells import SpellTarget
        return spell.target in [
            SpellTarget.SINGLE_ALLY, SpellTarget.SINGLE_TARGET
        ]
    
    def _get_school_name(self, school: SpellSchool) -> str:
        """学派名を取得"""
        school_names = {
            SpellSchool.MAGE: "魔術",
            SpellSchool.PRIEST: "神聖",
            SpellSchool.BOTH: "汎用"
        }
        return school_names.get(school, school.value)
    
    def _get_type_name(self, spell_type: SpellType) -> str:
        """魔法種別名を取得"""
        type_names = {
            SpellType.OFFENSIVE: "攻撃",
            SpellType.HEALING: "回復",
            SpellType.BUFF: "強化",
            SpellType.DEBUFF: "弱体化",
            SpellType.UTILITY: "汎用",
            SpellType.REVIVAL: "蘇生",
            SpellType.ULTIMATE: "究極"
        }
        return type_names.get(spell_type, spell_type.value)
    
    def _get_target_name(self, target) -> str:
        """対象名を取得"""
        from src.magic.spells import SpellTarget
        target_names = {
            SpellTarget.SELF: "自分",
            SpellTarget.SINGLE_ALLY: "味方1体",
            SpellTarget.SINGLE_ENEMY: "敵1体",
            SpellTarget.GROUP_ALLY: "味方グループ",
            SpellTarget.GROUP_ENEMY: "敵グループ",
            SpellTarget.ALL_ALLIES: "全味方",
            SpellTarget.ALL_ENEMIES: "全敵",
            SpellTarget.SINGLE_TARGET: "任意1体",
            SpellTarget.PARTY: "パーティ",
            SpellTarget.AREA: "エリア",
            SpellTarget.BATTLEFIELD: "戦場全体"
        }
        return target_names.get(target, str(target))
    
    def show(self):
        """魔法UIを表示"""
        if self.current_party:
            self.show_party_magic_menu(self.current_party)
        else:
            logger.warning("パーティが設定されていません")
    
    def hide(self):
        """魔法UIを非表示"""
        try:
            ui_manager.hide_element("party_magic_main")
        except:
            pass
        self.is_open = False
        logger.debug("魔法UIを非表示にしました")
    
    def destroy(self):
        """魔法UIを破棄"""
        self.hide()
        self.current_party = None
        self.current_character = None
        self.current_spellbook = None
        self.selected_level = None
        self.selected_slot_index = None
        logger.debug("MagicUIを破棄しました")
    
    def set_close_callback(self, callback: Callable):
        """閉じるコールバックを設定"""
        self.callback_on_close = callback
    
    def _back_to_main_menu(self):
        """メインメニューに戻る"""
        if self.current_party:
            self.show_party_magic_menu(self.current_party)
    
    def _back_to_character_magic(self):
        """キャラクター魔法画面に戻る"""
        if self.current_character:
            self._show_character_magic(self.current_character)
    
    def _back_to_spell_slots(self):
        """魔法スロット画面に戻る"""
        self._show_spell_slots()
    
    def _back_to_level_slots(self):
        """レベル別スロット画面に戻る"""
        if self.selected_level is not None:
            self._show_level_slots(self.selected_level)
    
    def _back_to_slot_options(self):
        """スロットオプション画面に戻る"""
        if self.selected_level is not None and self.selected_slot_index is not None:
            self._show_slot_options(self.selected_level, self.selected_slot_index)
    
    def _back_to_spell_usage(self):
        """魔法使用画面に戻る"""
        self._show_spell_usage()
    
    def _close_magic_ui(self):
        """魔法UIを閉じる"""
        self.hide()
        if self.callback_on_close:
            self.callback_on_close()
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        ui_manager.hide_all_elements()
    
    def _show_message(self, message: str):
        """メッセージを表示"""
        dialog = UIDialog(
            "magic_message",
            "魔法",
            message,
            buttons=[
                {"text": "OK", "command": self._close_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)


# グローバルインスタンス
magic_ui = MagicUI()