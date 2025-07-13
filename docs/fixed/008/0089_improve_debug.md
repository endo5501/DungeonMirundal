# デバッグ機能の改善

./docs/how_to_debug_game.md に記載のデバッグ機能を改善します

現在のデバッグ機能はスクリーンショット、キーコード入力、マウス入力、UI階層の取得が可能です。今回、これ以外の情報の取得を可能にします

## パーティ情報の読み取り

現在のパーティ情報を読み取るAPIを追加しましょう。
パーティ情報は以下の通り。

* パーティ内のキャラクター情報(名前、レベル、HP/MAX_HP)
* 所持金

まず、上記情報を返すREST APIを実装しましょう。
他の機能と同様に ./src/core/dbg_api.py に実装すべきです。
エンドポイント名は`/party/info`などが良いでしょう

その後、`src/debug/game_debug_client.py`に上記REST APIを実行してパーティ情報を取得できるようにしましょう
例:
`uv run python src/debug/game_debug_client.py party`

## パーティのキャラクター情報の読み取り

パーティ内のキャラクター情報を取得するAPIを追加しましょう。
キャラクター情報は以下の通り

* 名前
* 種族
* 職業
* HPなど各種ステータス
* 所持アイテム(装備中のものには*をつけましょう)

エンドポイントは`/party/character/0` のように`/party/character/`+(数字)でキャラクターを指定できるようにしましょう。
game_debug_client.pyも、`uv run python src/debug/game_debug_client.py party_character 0`でキャラクター情報を取得できるようにしましょう

## 冒険者ギルド情報の読み取り

冒険者ギルドに所属の(過去の操作で作成された)キャラクター情報(名前、レベル、HP/MAX_HP)の一覧を取得できるようにしましょう

エンドポイントは`/adventure/list` で取得できるようにしましょう。
game_debug_client.pyも、`uv run python src/debug/game_debug_client.py adventure_list`でキャラクター情報を取得できるようにしましょう
