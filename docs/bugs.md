# Bugs

発生しているバグ(Known bugs)と修正済みのバグをまとめます。
修正後、必ずテストを実施し、修正済みバグ(Fixed bugs)へ移動してください

## Known bugs

### 優先度:高

- [ ] ダンジョンに入ると、以下のエラーが発生してクラッシュする
```
2025-06-16 22:15:22 - dungeon - ERROR - 生存しているパーティメンバーがいません
2025-06-16 22:15:22 - dungeon - ERROR - ダンジョン遷移に失敗しました: 生存しているパーティメンバーがいません
2025-06-16 22:15:22 - dungeon - WARNING - テキストファイルが見つかりません: config/text/ダンジョン入場エラー.yaml
2025-06-16 22:15:22 - dungeon - WARNING - テキストキーが見つかりません: dungeon.entrance_error_title
2025-06-16 22:15:22 - dungeon - WARNING - テキストファイルが見つかりません: config/text/ダンジョンに入場できませんでした:.yaml
2025-06-16 22:15:22 - dungeon - WARNING - テキストキーが見つかりません: dungeon.entrance_error_prefix
Traceback (most recent call last):
  File "/home/satorue/Dungeon/src/overworld/overworld_manager.py", line 592, in _on_dungeon_selected
    self.on_enter_dungeon(dungeon_id)
  File "/home/satorue/Dungeon/src/core/game_manager.py", line 341, in transition_to_dungeon
    raise Exception("生存しているパーティメンバーがいません")
Exception: 生存しているパーティメンバーがいません

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/showbase/EventManager.py", line 49, in eventLoopTask
    self.doEvents()
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/showbase/EventManager.py", line 43, in doEvents
    processFunc(dequeueFunc())
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/showbase/EventManager.py", line 99, in processEvent
    messenger.send(eventName, paramList)
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/showbase/Messenger.py", line 337, in send
    self.__dispatch(acceptorDict, event, sentArgs, foundWatch)
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/showbase/Messenger.py", line 422, in __dispatch
    result = method (*(extraArgs + sentArgs))
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/gui/DirectButton.py", line 107, in commandFunc
    self['command'](*self['extraArgs'])
  File "/home/satorue/Dungeon/src/ui/base_ui.py", line 163, in _on_click
    self.command(*self.extraArgs)
  File "/home/satorue/Dungeon/src/ui/dungeon_selection_ui.py", line 148, in <lambda>
    {"text": "はい", "command": lambda: self._confirm_dungeon_selection(dungeon_id)},
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/satorue/Dungeon/src/ui/dungeon_selection_ui.py", line 167, in _confirm_dungeon_selection
    self.on_dungeon_selected(dungeon_id)
  File "/home/satorue/Dungeon/src/overworld/overworld_manager.py", line 598, in _on_dungeon_selected
    self._show_dungeon_entrance_error(str(e))
  File "/home/satorue/Dungeon/src/overworld/overworld_manager.py", line 732, in _show_dungeon_entrance_error
    ui_manager.show_dialog(
    ^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'UIManager' object has no attribute 'show_dialog'
:task(error): Exception occurred in PythonTask eventManager
2025-06-16 22:15:23 - dungeon - ERROR - ゲーム実行中にエラーが発生しました: 'UIManager' object has no attribute 'show_dialog'
2025-06-16 22:15:23 - dungeon - INFO - === Dungeon RPG 終了 ===
Traceback (most recent call last):
  File "/home/satorue/Dungeon/src/overworld/overworld_manager.py", line 592, in _on_dungeon_selected
    self.on_enter_dungeon(dungeon_id)
  File "/home/satorue/Dungeon/src/core/game_manager.py", line 341, in transition_to_dungeon
    raise Exception("生存しているパーティメンバーがいません")
Exception: 生存しているパーティメンバーがいません

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/satorue/Dungeon/main.py", line 33, in <module>
    main()
  File "/home/satorue/Dungeon/main.py", line 21, in main
    game.run_game()
  File "/home/satorue/Dungeon/src/core/game_manager.py", line 553, in run_game
    self.run()
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/showbase/ShowBase.py", line 3331, in run
    self.taskMgr.run()
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/task/Task.py", line 553, in run
    self.step()
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/task/Task.py", line 504, in step
    self.mgr.poll()
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/showbase/EventManager.py", line 49, in eventLoopTask
    self.doEvents()
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/showbase/EventManager.py", line 43, in doEvents
    processFunc(dequeueFunc())
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/showbase/EventManager.py", line 99, in processEvent
    messenger.send(eventName, paramList)
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/showbase/Messenger.py", line 337, in send
    self.__dispatch(acceptorDict, event, sentArgs, foundWatch)
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/showbase/Messenger.py", line 422, in __dispatch
    result = method (*(extraArgs + sentArgs))
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/satorue/Dungeon/.venv/lib/python3.12/site-packages/direct/gui/DirectButton.py", line 107, in commandFunc
    self['command'](*self['extraArgs'])
  File "/home/satorue/Dungeon/src/ui/base_ui.py", line 163, in _on_click
    self.command(*self.extraArgs)
  File "/home/satorue/Dungeon/src/ui/dungeon_selection_ui.py", line 148, in <lambda>
    {"text": "はい", "command": lambda: self._confirm_dungeon_selection(dungeon_id)},
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/satorue/Dungeon/src/ui/dungeon_selection_ui.py", line 167, in _confirm_dungeon_selection
    self.on_dungeon_selected(dungeon_id)
  File "/home/satorue/Dungeon/src/overworld/overworld_manager.py", line 598, in _on_dungeon_selected
    self._show_dungeon_entrance_error(str(e))
  File "/home/satorue/Dungeon/src/overworld/overworld_manager.py", line 732, in _show_dungeon_entrance_error
    ui_manager.show_dialog(
    ^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'UIManager' object has no attribute 'show_dialog'
```

### 優先度:中


## Fixed bugs

### 優先度:高 (2025-06-16修正完了)

- [x] 全体的にボタンの高さを増加してほしい
    - `base_ui.py`でボタン高さを0.15→0.22に増加
- [x] 地上メニューのレイアウトが使いにくくなっている。地上メニューでは、縦にボタンを配置してほしい
    - `UIMenu._rebuild_menu()`を横配置から縦配置に変更
- [x] 各施設のボタンが重なり合っている。
    - ボタン間の幅を増加してほしい
    - 縦配置により重なり問題を解決
- [x] 設定画面も縦にボタンを配置してほしい
    - 設定画面は`UIMenu`を使用しているため自動的に縦配置に
- [x] 各施設に入った後の[OK]ボタンが、施設の紹介メッセージの上に表示されてしまっている。[OK]ボタンの位置を下げることはできないか
    - `UIDialog._create_buttons()`でボタン位置を-0.3→-0.45に調整

