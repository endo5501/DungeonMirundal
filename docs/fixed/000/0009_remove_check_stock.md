# TODO

[商店]の[在庫確認]メニューは削除すべき

## 実装結果

✅ **完了しました**

### 変更内容

1. **在庫確認メニューの削除**
   - `src/overworld/facilities/shop.py:56-71` からメニュー項目を削除
   - 商店メニューは「商品を購入する」「商品を売却する」「店主と話す」の3つに

2. **関連機能の削除**
   - `_show_inventory`メソッド（在庫確認ダイアログ表示）を削除
   - 不要になった在庫表示機能を完全に除去

3. **テストの更新**
   - `test_text_display_fixes.py` から在庫確認関連のテストを削除
   - `test_shop_menu_items.py` を新規作成して、メニュー構成を検証

### 削除理由

- 在庫確認機能は購入メニューで商品一覧が確認できるため冗長
- ユーザーインターフェースをシンプルに保つため
- 実際の商店では在庫を個別に確認するよりも、購入時に利用可能な商品を見る方が自然
