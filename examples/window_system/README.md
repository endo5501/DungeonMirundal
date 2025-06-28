# Window System Examples

このディレクトリには、Window Systemの動作確認用サンプルコードが含まれています。

## ファイル説明

### test_window_system.py
Window Systemの基本動作を確認するためのテストプログラムです。
シンプルなウィンドウの作成、モーダルダイアログ、子ウィンドウの作成などの機能を確認できます。

### simple_test_window.py
テスト用の簡単なウィンドウクラスです。
基本的なUI要素（ラベル、ボタン）とイベント処理を実装しています。

## 実行方法

```bash
# プロジェクトルートから実行
uv run python examples/window_system/test_window_system.py
```

## 操作方法

- **ESC**: ウィンドウを閉じる / 戻る
- **1**: モーダルダイアログを作成
- **2**: 子ウィンドウを作成
- **Q**: プログラムを終了

## 注意事項

これらのファイルはWindow Systemの動作確認用であり、本番環境では使用しません。
実際のアプリケーションでは、各画面に対応した専用のWindowクラスを使用してください。