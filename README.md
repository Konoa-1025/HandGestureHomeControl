
# HandGestureHomeControl

ハンドジェスチャーを用いて、照明やエアコンなどの家電を直感的に操作するシステムです。

## 概要
カメラで手の動きを認識し、ECHONET Liteを通じて家電を操作します。

## 使用技術
- Python
- OpenCV
- MediaPipe / PipeTRT
- ECHONET Lite

## 開発
川崎総合科学高等学校 情報工学科の課題研究として開発しています。

## 実行環境

Mac / Python 3.11は`requirements-mac.txt`、Jetson / Python 3.8は
`requirements-jetson.txt`を使用します。Jetson用にはPipeTRTとCUDA Pythonも含みます。
GPU関連の前提条件や導入手順は[依存関係の説明](docs/dependencies.md)を参照してください。
