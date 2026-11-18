# Python依存関係

## ファイルの使い分け

| ファイル | 対象 | 内容 |
| --- | --- | --- |
| requirements.txt | Python 3.11のデスクトップ | 共通ライブラリ、NumPy、OpenCV、MediaPipe |
| requirements-mac.txt | Mac / Python 3.11 | requirements.txtを参照 |
| requirements-common.txt | 全環境 | HGHCが直接使用するart、psutil、pygame |
| requirements-jetson.txt | Xavier NX / JetPack 5.1.2 / Python 3.8 | 共通ライブラリ、NumPy、PipeTRT、CUDA Python。単独でコピー可能 |
| old_requirements.txt | 過去の環境記録 | 現行環境のインストールには使用しない |

全依存を固定したロックファイルではない。間接依存はpipが解決する。
Jetsonでは2026-11-17にインストール成功の報告あり。HGHCの推論動作・全間接依存は未確認。

## Mac

既存の仮想環境は変更せず、別の環境にインストールする。

```bash
python3.11 -m venv .venv-desktop
source .venv-desktop/bin/activate
python -m pip install -r requirements-mac.txt
python -m pip check
python -c "import cv2, mediapipe, numpy, psutil, pygame, art; print(cv2.__version__, mediapipe.__version__, numpy.__version__)"
```

2026-11-17に確認した既存Mac環境にはNumPy 2.4.6が入っていたが、
インストール済みMediaPipe 0.10.21のメタデータは`numpy<2`を要求している。
そのため新しい定義ではNumPyを1.26.4に固定した。
`opencv-python`と`opencv-contrib-python`も両方入っていたため、
新しい定義ではMediaPipeが依存するcontrib版に統一した。
既存環境にこの定義を上書きするだけでは、重複したOpenCVは解消しない。

## Jetson

まず現在使っているPython環境で確認する。既存環境を削除したり、GPU関連を一括更新しない。

```bash
python3 --version
python3 -m pip show pipetrt numpy opencv-python opencv-contrib-python
python3 -c "import cv2; print(cv2.__version__, cv2.__file__)"
python3 -c "import tensorrt; print(tensorrt.__version__)"
python3 -c "import pipetrt; print(pipetrt.__file__)"
```

必要なら、JetPackが提供するPythonモジュールを参照できる環境を作成する。
既存の仮想環境内にだけインストールされたPipeTRTは新環境には引き継がれない。

```bash
python3 -m venv --system-site-packages .venv-jetson
source .venv-jetson/bin/activate
python -m pip install --upgrade "pip<25.1"
python -c "import tensorrt; assert tensorrt.__version__ == '8.5.2.2', tensorrt.__version__"
python -m pip install -r requirements-jetson.txt
```

Python 3.8向けにNumPyは1.24.4、PipeTRTは0.1.2、CUDA Pythonは11.8.2に固定した。
無指定時の依存解決ではCUDA Python 12.3.0が選ばれたため、実機のCUDA 11.4上で
確認する候補として11.8.2を指定し、その後ユーザーから成功の報告があった。
これはCUDA Toolkitの更新ではない。TensorRTは既存のJetPack提供版8.5.2.2を利用する。
TensorRT 8.5の`nptype`がNumPy 1.24で削除された`np.bool`を参照するため、
HGHCのPipeTRT初期化時に、TensorRT 8.5かつ別名が存在しない場合だけ
`np.bool = bool`を設定する。プロセス内の互換処理であり、パッケージ本体は変更しない。
インストール成功とHGHCの推論成功は区別し、録画入力で別途確認する。
TensorRTの事前確認が失敗した場合はインストールを進めず、JetPack側の環境を確認する。
OpenCV、ONNX、ModelOpt等の間接依存はpipが解決する。
dry-runで提示された版は実際のインストール済み版とは区別し、ここでは固定しない。

実機の全バージョンも、インストールが完了した仮想環境内で記録する。

```bash
python -m pip freeze > requirements-jetson-snapshot.txt
```

`--system-site-packages`環境のfreezeにはOS提供パッケージやユーザー用パッケージも
含まれる。snapshotは環境の記録として使い、新規環境への一括インストールには使わない。
CUDA ToolkitやJetPack等はfreezeでは再現できない。

config.jsonの`model.backend`は`pipetrt`に設定する。
モデルの`full` / `fp16`等は既存の`model.profiles.high`で指定する。
今回、MediaPipeバックエンドのimportを初期化時に遅延するよう変更したため、
PipeTRT使用時にMediaPipeをインストールする必要はない。

最後に以下で依存関係と起動を確認する。カメラ・録画・推論の実機確認は別途必要。

```bash
python -m pip check
python main.py --help
```

## 直接依存と間接依存

HGHCが直接importする外部パッケージは、art / psutil / pygame / NumPy /
OpenCV、および選択したMediaPipeまたはPipeTRT。
ECHONET Liteはリポジトリ内の実装を使用する。
JAX、Matplotlib、protobuf等はMediaPipe等の間接依存なので個別の直接依存から除いた。
Linuxでは同梱ECHONET Liteがipgetをimportするため、ipget 0.0.3も必要。
ECHONET Liteの3モジュールは型注釈を遅延評価し、Python 3.8でもimportできるようにする。

## 参照

- https://pypi.org/project/pipetrt/0.1.2/
- https://pypi.org/project/numpy/1.24.4/
- MediaPipe / OpenCVの依存条件はMacのインストール済みパッケージのメタデータを確認。
