必要
sudo powermetrics --samplers gpu_power -n 1 -i 100

# 完成したもの一覧

## Cascade
All OK

## Core
[application](Core/application.py) NO


[applicationState](Core/applicationState.py) NO


[commandProcessor](Core/commandProcessor.py) NO


[initializer](Core/initializer.py) OK


[shutdown](Core/shutdown.py) NO


## EchonetLite
All OK

## FeedBack

## Managers
[actionManager](Managers/actionManager.py) NO


[cameraManager](Managers/cameraManager.py) OK


[cascadeManager](Managers/cascadeManager.py) OK


[comboManager](Managers/comboManager.py) NO


[echonetManager](Managers/echonetManager.py) NO


[experimentManager](Managers/experimentManager.py) NO


[feedbackManager](Managers/feedbackManager.py) NO


[modelManager](Managers/modelManager.py) OK


[previewManager](Managers/previewManager.py) NO


[recognitionManager](Managers/recognitionManager.py) OK


[systemManager](Managers/systemManager.py) OK


[tcpManager](Managers/tcpManager.py) NO


## Models
CPU All OK

GPU NO

## Networks

## Utils
[logger](Utils/logger.py) OK
## 人物位置と録画動画

既存の `camera → cascade（縮小・左右反転・RGB化）→ recognition` を維持し、
Cascade後の同じ画像を `human_position.update(cased_frame)` に渡します。
返り値は `"T1"` などの畳ID、検出なし／重なりなしなら `None` です。
静止中・手が見えない間も人物位置を更新します。

`config.json` に以下を設定します（`ex_config.json` にも記載）。

```json
"position": {
    "enabled": true,
    "csv_path": "Data/position/floor.csv",
    "image_size": [3840, 2160],
    "bottom_ratio": 0.3,
    "debug": true
}
```

- `image_size` は **CSVを作成した画像の幅・高さ** です。現在は設定済み動画の実サイズ3840×2160を基準としています。同じ画像からCSVを作成していない場合は修正してください。CSVの頂点最大値から画像サイズは推定できません。
- CSVを初期化時に1回読み、座標を幅・高さで正規化します。high/low Cascadeの解像度変更には毎フレーム対応します。反転・クロップ・カメラ画角はCSV作成時と合わせてください。位置推定内では再反転しません。
- 既存モデルは手のみなので、既存MediaPipeの同梱Poseモデルから全身ランドマークの概算BBoxを作ります。足が検出できない場合は `None` になります。新規ライブラリ・モデルのダウンロードは不要です。
- BBox下30%と各畳の重なり面積を比較します。同面積ならCSVで先に記載された畳を返します。座位判定・位置の時系列補正・複数人追跡はありません。
- `debug: false` で位置表示だけを停止、`enabled: false` で人物位置推定を停止できます。設定省略時も無効です。初期化／推論失敗時は警告を出して位置推定を停止し、手認識を続けます。
- Previewは黄色の畳境界、緑の現在畳、青の人物BBox、紫のPosition Box、現在IDを表示します。描画は表示用画像だけに行います。Q/Escまたはウィンドウを閉じると終了します。
- 現在位置は `gesture_process(..., current_position)` から `get_direction(..., current_position)` まで渡します。このチェックアウトの方向判定は画像上の8方向のみで、Wall実装はありません。家電選択の規則は変更していません。

録画動画は `camera.sources` 内で、以下のように選択します。
`id: "front"` の入力は1件だけ `enabled: true` にしてください。

```json
{
    "id": "front",
    "display_name": "録画映像",
    "enabled": true,
    "type": "movie",
    "movie": true,
    "loop": true,
    "connection": {"path": "/absolute/path/to/video.mp4"}
}
```

`loop` の省略時はループ再生、`false` なら動画終端で終了します。
再生速度は認識処理速度に依存し、元動画のFPSに同期しません。
通常のカメラへ戻すときはmovieを無効化し、既存webcam/axis等を有効化します。
動画とCSVの相対パスはプロジェクト直下基準です。

```sh
.venv/bin/python main.py
.venv/bin/python -m unittest discover -s tests -v
```

`config.json` は従来どおりGit管理外です。ブランチを戻す場合、追加した
`position` 設定は旧コードでは無視されます。
