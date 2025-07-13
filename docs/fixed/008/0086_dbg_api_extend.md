# デバッグ用APIの改良

## UI階層情報

@docs/how_to_debug_game.md

現在、UI階層APIを使用すると、以下のようにUI Elements以下に表示されている要素が全て1階層で表示される。
原因は、この階層データを作成している src/core/dbg_api.py の`def get_ui_hierarchy()`で`UI Elements`に全て詰め込んでいるため、このような現象が発生している。

def get_ui_hierarchy()の処理を見直し、階層化されたUI Elementsの情報を取得するようにしてください

```md
UI Hierarchy Tree:
├── Window Stack:
│   ├── OverworldMainWindow(overworld_main, main, stack_depth=0)
│   └── Window(facility_inn_window, shown, modal=False)
└── UI Elements:
    ├── UIContainer (#root_container) [visible]
    ├── UILabel (None) [hidden] (text='地上')
    ├── UIButton (None) [hidden] (text='冒険者ギルド', key=1, label='冒険者ギルド', id=guild)
    ├── UIButton (None) [hidden] (text='宿屋', key=2, label='宿屋', id=inn)
    ├── UIButton (None) [hidden] (text='商店', key=3, label='商店', id=shop)
    ├── UIButton (None) [hidden] (text='教会', key=4, label='教会', id=temple)
    ├── UIButton (None) [hidden] (text='魔術師ギルド', key=5, label='魔術師ギルド', id=magic_guild)
    ├── UIButton (None) [hidden] (text='ダンジョン入口', key=6, label='ダンジョン入口', id=dungeon_entrance)
    ├── UIContainer (None) [hidden]
    ├── UIPanel (None) [hidden]
    ├── UILabel (None) [hidden] (text='ゴールド: 200G')
    ├── UIContainer (None) [visible]
    ├── UIPanel (None) [visible]
    ├── UILabel (None) [hidden] (text='パーティ: New Party')
    ├── UILabel (None) [hidden] (text='TestHero Lv.3 HP:40/40 [good]')
    ├── UILabel (None) [visible] (text='宿屋')
    ├── UIContainer (None) [visible]
    ├── UIPanel (None) [visible]
    ├── UIContainer (None) [visible]
    ├── UIPanel (None) [visible]
    ├── UIButton (None) [visible] (text='休憩する')
    ├── UIButton (None) [visible] (text='冒険準備')
    ├── UIButton (None) [visible] (text='アイテム保管')
    ├── UIButton (None) [visible] (text='パーティ名変更')
    ├── UIButton (None) [visible] (text='宿屋を出る')
    ├── UILabel (None) [visible] (text='休憩する')
    ├── UILabel (None) [visible] (text='パーティを休ませてHPとMPを回復します')
    └── UILabel (None) [visible] (text='このサービスは現在実装中です。')
```
