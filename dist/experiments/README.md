# Jetson＋Webカメラ実験

OpenCVのBGR画像をPipeTRTへそのまま渡す。HGHCのcascade、config.json、家電通信は使わない。
判定には既存の`Recognizers/gestureRecognizer.py`と`gestureStabilizer.py`を使用する。
システム全体ではなく、認識・判定部分の評価である。

## 配置・起動

ZIP内のexperimentsフォルダを、Jetsonの`~/HandGestureHomeControl/`直下に置く。
RecognizersフォルダとUtilsフォルダがある既存プロジェクト内で使用する。
Jetson本体のデスクトップでターミナルを開き、実行する。

```bash
cd ~/HandGestureHomeControl
source .venv-jetson/bin/activate
python experiments/01_accuracy.py --trials 1
```

`.venv-jetson`は先ほどPipeTRTの単体テストが動いた環境を使う。
NumPy、OpenCV、psutil、TensorRT、PipeTRTが必要。新しいパッケージの追加は不要。
TensorRT 8.5とNumPy 1.24の`np.bool`互換処理は内蔵している。
カメラを使う他のアプリは終了する。違うカメラなら`--camera 1`等を指定する。
普通のSSH接続では、Macにプレビュー画面は転送されない。

## 4本のプログラム

### 1. 認識精度

```bash
python experiments/01_accuracy.py --trials 20
```

4種類×各20回、合計80試行。順序はseedを固定してシャッフルする。
まず`--trials 1`で4試行の操作確認をするとよい。

1. targetに出た形を確認し、スペースを押す。
2. 2秒の準備時間で形を作る。
3. MEASURE中の3秒間、その形を保持する。
4. 次のtargetが出たら手を戻し、準備できたらスペースを押す。

OPEN_HAND＝パー、FIST＝グー、PEACE＝チョキ、POINT＝指差し。
Q／Esc／Ctrl+Cで途中終了。準備中・待機中のフレームは採点しない。

「試行正解」は、測定中のフレーム判定の最多ラベルがtargetと一致した場合。
同数首位はAMBIGUOUSで不正解。未検出・未確定はUNKNOWNとして分母に含める。
全フレームがUNKNOWNの場合も不正解。フレーム単位の正解率も別途記録する。
未完了試行は`completed=0`とし、試行正解率の集計から除外する。

### 2. 距離・角度条件

```bash
python experiments/02_conditions.py --distance-cm 50 --angle-deg 0 --angle-axis yaw --trials 5
python experiments/02_conditions.py --distance-cm 100 --angle-deg 0 --angle-axis yaw --trials 5
python experiments/02_conditions.py --distance-cm 50 --angle-deg 30 --angle-axis yaw --trials 5
```

1回の起動で1条件、4種類を各指定回数試す。距離・角度は人が実測・設定する値で、
プログラムによる自動測定ではない。距離はカメラから手まで。
角度0度は手のひらの面をカメラに正対させた状態。
yaw＝左右向き、pitch＝上下向き、roll＝画像面内の回転。
回転方向や左右どちらの手か等は`--note`に記録する。
比較時は変更したい要因以外（照明・背景・解像度等）をそろえる。

### 3. 安定化あり／なし

```bash
python experiments/03_stability.py --trials 5
```

操作は認識精度実験と同じ。同じフレームから得たrawラベルを安定化処理にも渡す。
推論を二重に実行しない。測定開始時に安定化状態をリセットし、各試行を独立した
保持課題として扱う。形の切替動作や家電コンボの評価ではない。

| 列 | 意味 |
| --- | --- |
| raw/stable_frame_accuracy | UNKNOWNを含む全測定フレームに対する正解割合 |
| raw/stable_state_changes | 隣接ラベルが変わった回数。UNKNOWNへの出入りも含む |
| raw/stable_wrong_entries | target以外の既知ラベルへ入った回数。同じ誤ラベルの継続は1回 |
| raw/stable_unknown_frames | 未検出・未確定などUNKNOWNのフレーム数 |
| raw/stable_cue_to_first_correct_s | 測定開始から初めて正解が出たフレームまでの秒数 |

準備中に形を作るため、cue_to_first_correctは「人が動き始めてからの反応時間」や
「純粋な安定化遅延」ではない。rawとstableの初回正解時間を比較する際もこの制限に留意する。
安定化が古い誤ラベルを保持している場合も、そのまま採点する。
出力が減っただけなのかを区別するため、正解率・UNKNOWN数・誤ラベル進入回数を併せて見る。

設定を変える場合：

```bash
python experiments/03_stability.py --trials 5 --confirmation-seconds 0.3 --mismatch-seconds 0.1 --lost-seconds 0.5
```

### 4. 検出・追跡の処理時間

```bash
python experiments/04_timing.py --seconds 30
```

初めの30フレームはウォームアップとして集計から除外する。
測定中は手を出したり隠したりして、DETECTIONとTRACKINGを両方含める。
モデル初期化・エンジン生成は計測外。

SSHで画面表示なしで測る場合：

```bash
python experiments/04_timing.py --seconds 30 --headless
```

- detect_wall_ms：detect()呼出し全体の実経過時間。
- palm_trt_ms等：PipeTRTが返す内部計測。独自のCUDAイベント計測ではない。
- pipeline_ms：カメラ取得開始から推論・認識・安定化完了まで。CSV書込み・描画等は含めない。
- throughput_fps（session.json）：ウォームアップ後の処理枚数÷実測時間。
  描画・CSV書込み等の影響も含むため、1000÷detect_wall_msとは異なる。
- CPUはpsutilによるマシン全体の使用率。GPU使用率・電力は計測しない。

プレビューの有無、カメラ解像度、モデル、Jetsonの電力モード等をそろえて比較する。
表示ありの実験結果を、推論だけの最大性能とは解釈しない。

## 出力ファイル

起動ごとに`results/experiments/日時-実験名-固有ID/`を新規作成する。
既存結果は上書きしない。CSVはUTF-8 BOM付きでExcelでも開ける。
率は0〜1、時間は列名末尾にあるms／s。

| ファイル | 内容 |
| --- | --- |
| frames.csv | 測定フレームごとの判定、時刻、検出状態、処理時間、CPU・メモリ使用率 |
| trials.csv | 試行別正解率・最多ラベル・安定化比較・距離・角度・完了状態 |
| accuracy_summary.csv | 完了試行だけの、ジェスチャー別試行正解率 |
| confusion.csv | 完了試行の「正解ラベル→判定ラベル」の件数。raw／stableを別集計 |
| timing_summary.csv | ALL／DETECTION／TRACKING等ごとの平均・中央値・95パーセンタイル |
| session.json | 実行条件、バージョン、コードのハッシュ、実解像度、試行順序、完了状態 |

timing実験ではtrials.csvとconfusion.csvは見出しのみ、accuracy_summaryの試行数は0。
途中停止・カメラ切断でも取得済み結果を残す。毎フレームflushするが、停電時の保存を保証しない。
映像・顔画像は保存しない。結果の集計もJetson内で完結する。

記録例：

```bash
python experiments/01_accuracy.py --participant P01 --distance-cm 50 --angle-deg 0 --note "right hand; indoor lighting; Jetson 20W"
```

`--model lite`、`--precision fp32`で別条件も測定できる。
`--fresh-engines`は既存キャッシュを残し、新規の一時キャッシュでエンジンを生成する。
新キャッシュの場所はsession.jsonのengine_directoryに記録する。

## 検証範囲

CSV集計、同じBGRフレームの受け渡し、ウォームアップ除外、試行の完了、
カメラ切断時の部分保存は模擬テストで検証する。
Jetson実機のカメラ・GPU・プレビューは、実験前の`--trials 1`で確認する。
