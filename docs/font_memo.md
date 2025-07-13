# `test_font_from_chatgpt.py` で **日本語フォント** を確実に表示させるポイント  

*(Claude Code 向け共有メモ／関西弁 ver.)*

## 1. 候補フォントの優先順位とリスト構造

| 優先度 | パス例 | 理由 |
| :-: | :- | :- |
| ① | `/System/Library/Fonts/Supplemental/ヒラギノ角ゴシック W3.ttc` | **macOS 純正ヒラギノ**。`.ttc` コレクションやけど信頼性◎ |
| ② | `assets/fonts/NotoSansCJKJP-Regular.otf` | Google Noto。OS 非依存で **Windows／Linux／mac** 共通可 |
| ③ | `assets/fonts/ipag.ttf` | IPA ゴシック。入手しやすいが壊れたファイル混入率がちょい高め |

> **コツ**  
>
> * 候補は *タプル*（`(Path, face_index)`）で持たせておくと `.ttc` の **face index** を渡せる。  
> * 「壊れてるフォントで break しちゃって後続を試さない」ミスを避けるために、**`continue` で次へ回す**ロジックを推奨。

---

## 2. `pygame.freetype` を使う理由

* **`.ttc` や `.otf`** の取り扱いが旧 `pygame.font` より安定。  
* アンチエイリアスや縦書き・行間調整など **拡張 API** も豊富。  
* 初期化は `ft.init()`、ロードは `ft.Font(path, size, index=0)` が基本形。

---

## 3. サンプル実装での落とし穴と対策

| 落とし穴 | 現状コード | 改善案 |
| --- | --- | --- |
| **壊れたフォントで即 `break`** | `break` でループ終了 | `continue` で次候補を試行 |
| **face index 未指定** | `.ttc` ファイルでも `index` 省略 | `ft.Font(path, 36, index=0)` と明示 |
| **フォールバックが欧文だけ** | `ft.SysFont("sans-serif", 36)` | `ft.SysFont("Hiragino Sans", 36)` など CJK 対応フォント名を渡すか、別の日本語フォントを最後に追加 |
| **ログが少ない** | 成否のみ表示 | `print("Trying:", p)` を最初に入れてトレースしやすく |

修正版ループ例:

```python
for p, idx in candidates:          # ← (Path, face_index) でもたせる
    if not p.exists():
        continue
    print("Trying:", p)
    try:
        font = ft.Font(str(p), 36, index=idx)
        print("Loaded:", p)
        break                      # ← 成功時だけ break
    except Exception as e:
        print("Failed:", p, e)
        continue                   # ← 失敗なら次の候補へ
```

## 4. 典型的エラーとデバッグフロー

1. unknown file format
    * file ipag.ttf でフォーマット確認。0 byte や gzip 圧縮残骸なら差し替え。
2. UserWarning: The system font 'sans-serif' couldn't be found
    * mac では sans-serif エイリアスが通らん場合あり。実体名 (Helvetica, Hiragino Sans, など) を指定。
3. 描画は出来るが豆腐
    * metrics = font.get_metrics("あ") が None → その face に日本語グリフ無し。face index or フォント自体を見直す。

## 5. まとめ（TL;DR）

* 候補フォントを複数持っておき、continue で粘り強く試す
* .ttc は face index、壊れてたら即スキップ
* pygame.freetype でクロスプラットフォーム互換性アップ
* デフォルト欧文フォントに落ちんよう、最終候補まで日本語フォントを並べる

これを押さえときゃ、Linux でも macOS でも 「□ □ □」が「こんにちは」に化けるはずやで。ほな、Claude Code での実装時にも気ぃつけてな〜。
