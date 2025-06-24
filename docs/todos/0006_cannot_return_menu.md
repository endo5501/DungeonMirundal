# 現象

サブメニューから戻れなくなっている

# 再現方法
 [魔術師ギルド]-[魔法分析]-[キャラクター個別分析]-[戻る]を押しても[魔法分析]に戻れない

# 調査結果と修正

## 問題1: 魔術師ギルドのキャラクター分析ダイアログ ✅ 修正済み

### 根本原因
`MagicGuild._analyze_character()`でキャラクター分析ダイアログの戻るボタンが`self._close_dialog`に設定されていた。
`_close_dialog()`は施設のメインメニューに戻るため、期待される「キャラクター個別分析」メニューではなく「魔術師ギルドメインメニュー」に戻ってしまう。

### 修正内容
- キャラクター分析ダイアログの戻るボタンを`self._close_dialog`から`self._show_character_analysis_menu`に変更
- これにより、ダイアログから戻る時に適切な親メニュー（キャラクター個別分析）に戻るようになった

### 修正対象ファイル
- `src/overworld/facilities/magic_guild.py`: LINE 690の戻るボタンコマンド修正

## 問題2: 他の施設でも同様の問題が存在 ✅ 修正完了

### 調査結果と修正内容

#### Temple（教会） ✅ 修正完了
- **問題箇所**: 祝福、神父会話、祈祷書購入ダイアログで`self._close_dialog`を直接使用
- **修正内容**: 
  - `_back_to_main_menu_from_blessing_dialog()`
  - `_back_to_main_menu_from_priest_dialog()`
  - `_back_to_main_menu_from_prayerbook_dialog()`を追加
- **修正ファイル**: `src/overworld/facilities/temple.py`

#### Shop（商店） ✅ 修正完了
- **問題箇所**: キャラクター売却確認、宿屋倉庫売却確認、旧システム売却確認ダイアログ
- **修正内容**:
  - `_back_to_character_sell_list_from_confirmation()`
  - `_back_to_storage_sell_list_from_confirmation()`
  - `_back_to_sell_menu_from_confirmation()`を追加
  - コンテキスト保存機能追加（`_current_character_for_sell`）
- **修正ファイル**: `src/overworld/facilities/shop.py`

#### Inn（宿屋） ✅ 修正完了
- **問題箇所**: 主人会話、旅の情報、酒場の噂話、倉庫状況、アイテム詳細ダイアログ
- **修正内容**:
  - `_back_to_main_menu_from_innkeeper_dialog()`
  - `_back_to_main_menu_from_travel_info_dialog()`
  - `_back_to_main_menu_from_tavern_rumors_dialog()`
  - `_back_to_item_organization_from_storage_dialog()`
  - `_back_to_storage_list_from_item_details()`を追加
- **修正ファイル**: `src/overworld/facilities/inn.py`

#### Guild（冒険者ギルド） ✅ 調査完了（修正不要）
- **調査結果**: 既に適切に実装されており修正不要
- **理由**: メインメニューから直接呼ばれるダイアログのため、`_close_dialog`の使用は適切
- **特記**: 他施設と比較して最も模範的な実装

 # TODO
1. ✅ 調査後、上記エラーを検知するテストを作成する
2. ✅ 修正する（全施設の修正完了）
3. ✅ テストが成功することを確認する
4. ⏳ commitする

## 修正内容まとめ
**魔術師ギルド**: 
1. ✅ キャラクター分析ダイアログの戻るボタンを適切なメニューに修正完了
2. ✅ キャラクター個別分析メニューの戻るボタンを専用メソッドで修正完了

**修正対象ファイル（追加）**:
- `src/overworld/facilities/magic_guild.py`: 
  - LINE 690: ダイアログ戻るボタンコマンド修正
  - LINE 613: キャラクター個別分析メニュー戻るボタンコマンド修正  
  - 新規メソッド追加: `_close_dialog_and_return_to_character_analysis()`, `_back_to_analysis_menu_from_character_analysis()`

**動作確認**:
- [魔術師ギルド] → [魔法分析] → [キャラクター個別分析] → [戻る] → [魔法分析] ✅
- [キャラクター個別分析] → [キャラクター選択] → [ダイアログ] → [戻る] → [キャラクター個別分析] ✅

**全施設**: ダイアログ戻るボタンの適切な親メニューへの復帰処理修正完了

### 修正済み施設一覧
1. **MagicGuild（魔術師ギルド）**: キャラクター分析ダイアログとメニュー階層の修正
2. **Temple（教会）**: 祝福、神父会話、祈祷書購入ダイアログの修正
3. **Shop（商店）**: 売却確認ダイアログの修正とコンテキスト保存
4. **Inn（宿屋）**: 各種情報ダイアログと倉庫関連ダイアログの修正
5. **Guild（冒険者ギルド）**: 調査の結果、既に適切に実装済み
