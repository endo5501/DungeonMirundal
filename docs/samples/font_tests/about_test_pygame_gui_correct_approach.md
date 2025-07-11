おおきに、コードざっと読ましてもろたで！
結論から言うと 「テーマの階層（cascade）で defaults より上位にある button／label のフォント設定が残ったままやから、せっかく登録した jp_font が呼ばれてへん」 んや。それでボタンやラベルだけ豆腐（□）が出とるわけやな。

⸻

pygame_gui のフォント決定手順をざっくりおさらい
	1.	UI 要素（たとえば UIButton）は、まず 自分専用のテーマブロック（"button": {...}）を探す。
	2.	無ければ object_id / class_id を探す。
	3.	さらに無ければ defaults を見る。
	4.	そこで指定された font_name を FontDictionary から探す。
なければ pygame.font.match_font() → 英字フォントだけヒット → 日本語は豆腐。

つまり今回のスクリプトみたいに

theme_data = {
    "defaults": {  # ← いちばん下位
        "font": {"name": "jp_font", ...}
    }
}

だけ書くと、
button や label は 既定テーマの "button" "label" ブロックにある "font": {"name": "default"}
を優先してしまうんよ。せやから jp_font まで降りて来ぇへん。

⸻

サクッと直す 3 つの方法

方法	やること	メリット	注意点
A. “button / label ブロック” も上書き	python<br>"button": {"font": {"name": "jp_font", "size": "24"}},<br>"label":  {"font": {"name": "jp_font", "size": "24"}} を theme_data に追加	手っ取り早い	要素が増えるたびに列挙が面倒やけど小規模ならOK
B. “default” エイリアスを潰す	先に manager.add_font_paths("default", jp_font_path) で 既定フォントを乗っ取る	既存テーマ全部に効く	将来別フォント使いたい時に分けにくい
C. 独自テーマ JSON をファイルで用意	既定テーマをコピーして "font_name": "default" を 一括置換 → “jp_font”	大規模でも管理しやすい	ちょい手間やけど本番運用ならオススメ


⸻

例：方法 A をコードに組み込む場合

theme_data = {
    "defaults": {
        "font": {"name": "jp_font", "size": "24", "style": "regular"},
        "colours": { ... }
    },
    "button": {  # ← ここ追加
        "font": {"name": "jp_font", "size": "24", "style": "regular"}
    },
    "label": {   # ← ここも追加
        "font": {"name": "jp_font", "size": "24", "style": "regular"}
    }
}
manager.get_theme().load_theme_from_dict(theme_data)  # ← dict 用 API

ポイント
load_theme() はファイルパス向けメソッドやから、辞書なら
load_theme_from_dict() を呼ぶ方が公式。実はここも落とし穴やで！

⸻

ついでチェックしとくと吉なところ
	1.	add_font_paths → 1 個目だけで OK？
いま bold_path=None など渡してへんけど、英語だけ太字にしたいとか無ければ問題なし。
	2.	プリロードサイズ
point_size も 24 に合わせてあるから、同じサイズを UI で指定するのが無難やで。
	3.	テーマ再読込
もしテーマを動的に書き換える時は manager.refresh_theme() を忘れずに。

⸻

まとめ
	•	文字化けの根っこは テーマ階層。
defaults だけやと button / label ブロックが勝ってまう。
	•	jp_font を確実に使わせるには
A) ボタン＆ラベル用ブロックで上書き
B) “default” エイリアスを乗っ取る
C) 独自テーマファイル化 のどれかを選んだらええで。
	•	その際、辞書を渡すなら load_theme_from_dict() を使うと安心や。

ほな、これで豆腐ともおさらばや！ 試してみて、また疑問あったらツッコミ入れてな〜。