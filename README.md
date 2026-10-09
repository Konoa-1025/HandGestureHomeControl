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

## ジェスチャーの確認

`main.py` がカメラ、認識、家電選択、コンボ、アクションの順に呼び出します。
家電中心との角度は `Recognizers/pointingEstimator.py`、指差し保持は
`Recognizers/gestureStabilizer.py`、表示は `Managers/previewManager.py` にあります。
既存のジェスチャー認識、家電・コンボCSV、アクション名はそのまま使います。

`config.json` に `"pointing": {"enabled": true}` を追加すると家電中心への指差しになります。
設定例は `ex_config.json` にあります。既存の `config.json` を使う場合は必要な項目だけ追加してください。
カメラは `camera.sources` の `id` が `front` のものを使用します。

- `Data/homeAppliances/pointCenters.csv`：反転後の映像上の家電中心。画面外も指定できます。
- `Data/homeAppliances/pointingTrial.json`：保持時間0.5秒、角度20度、最小の指の長さは画像幅の0.005倍、途切れ許容0.15秒。
- `LIGHT` を保持すると全灯OFF。他の家電は選択後に既存のコンボへ進みます。
- POINTのまま実行した後は、OPEN_HAND・FIST・PEACEのいずれかが確定するまで次の操作を待ちます。手が消えただけでは解除しません。
- 短い認識途切れは保持時間を残しますが、見えていない時間は加算しません。

録画の確認は次のように実行します。録画入力は標準で実機送信なしです。

```sh
python main.py --video path/to/movie.mp4
python main.py --video path/to/movie.mp4 --headless --frames 100 --snapshot preview.png
python main.py --video path/to/movie.mp4 --edit-centers
```

Spaceで一時停止、Nで1フレーム進め、QまたはEscで終了します。
中心編集中は `[`・`]` で家電を選び、クリックで中心を移動し、Sで保存、Xで削除します。
編集は常に実機送信なしです。保存先は中心CSVです。
`--start-frame` で開始位置、`--paused` で最初のフレームでの停止を指定できます。
録画は標準でループし、巻き戻ると選択・コンボ・保持時間をリセットします。
設定の録画ソースに `"loop": false` を指定すると末尾で終了します。

カメラ入力は標準で実機制御ありです。表示のみなら `--dry-run` を指定してください。
録画で実機制御も行う場合は `--live` を明示します。
プレビューの `SENT` は送信処理の成功で、家電の実動作の確認ではありません。

`pointing.enabled` がfalse、または項目がなければ従来の方向選択になります。
`home_appliances.files.positionmap` がある場合は畳別の方向表を使います。
この場合は `position` の設定と `Data/position/floor.csv` で人物の足元から畳を判定します。
位置不明や未登録方向では選択しません。固定の方向表だけを使う場合は `positionmap` を指定しないでください。

参考の `codex/gesture-preview` とは中心編集の起動方法とプレビューの配置が異なります。
中心編集は `pointing_preview.py` の代わりに `main.py --edit-centers` を使います。
待機中のコンボ音は既存の動作を残しています。

## テスト

```sh
python -B -m unittest discover -s tests -v
```

Python 3.11、MediaPipe 0.10.21、OpenCV 4.11、NumPy 1.26.4で確認しています。
通常の起動と同じくart、pygame、psutilも必要です。テストは家電へ送信しません。
短い動画を一時生成して、MediaPipeでの読み込み、ループ、画像保存、終了処理も確認します。
実際の手の認識精度、カメラの向き・家電中心の校正、実機制御、PipeTRTは別途実機での確認が必要です。
