# CRANE+ V2 に「手を振る」動作を模倣学習させる (ROS 2 + Gazebo + LeRobot ACT)

Physical AI 応用1 最終課題。講義第5回の「お辞儀 (pekori)」演習を、**自分で設計した別の動作 (手振り)** に置き換えたもの。

## 概要
1. `scripts/wave_demo.py` : 手振り軌道をROS2ノードで自動生成してCRANE+V2 (Gazebo) に送る。
   キーボードテレオペの代わりに、再現性のあるデモを大量に作る。
2. `scripts/record_episodes.sh` : 15エピソードをrosbag2で記録 (各エピソードは毎回ホーム姿勢から開始)。
3. 講義の `pai_training` で rosbag → LeRobotDataset 変換 → ACT 学習 → Gazebo 上で推論。
4. 設定は `configs/` (講義の設定からの差分: データセット名・タスク名・学習ステップ数)。

## 工夫点
- **往復ではなく閉ループの軌道**にした。方策の入力は関節角のみ (画像なし) なので、
  単純な往復運動だと「行き」と「帰り」が同じ姿勢になり、ACTが苦手とする多峰性 (どちらに動くか不定) が起きる。
  joint1 の左右スイープ + joint3 の持ち上げ + joint4 の手首の動きを組み合わせ、軌道上の各位相が別の姿勢になるようにした。
- エピソードごとに振幅 (±10%) と周期 (±5%) をランダム化。終点は必ずホーム姿勢に戻す。
- データ収集を完全にスクリプト化したので、誰でも同じデータを再生成できる。

## 結果
- 15 エピソード × 162フレーム (20 Hz)。ACTをCPUで2000ステップ学習 (`results/train_loss.txt`)。
  損失は 平均 8.63 (先頭100ステップ) → 0.65 (末尾100ステップ)。
- 推論ノードをホーム姿勢から起動すると、手振りを自律的に繰り返す。推論した指令値の範囲 (16,179 ステップ分):

| 関節 | 推論の範囲 [rad] | デモの設計値 [rad] |
|---|---|---|
| joint1 | -0.54 ~ 0.51 | ±0.5 (±10%) |
| joint4 (手首) | -0.34 ~ 0.30 | ±0.3 (±10%) |
| joint3 (肘) | -0.03 ~ 0.60 | 0 ~ 0.6 (±10%) |

## 再現手順
講義の ROS 2 コンテナ (`airobotbook/ros2-desktop-ai-robot-book-humble`) と `pai_training` が前提。

```bash
# 1. Gazebo + CRANE+ V2 を起動 (コンテナ内)
ros2 launch crane_plus_gazebo crane_plus_with_table.launch.py

# 2. デモ記録 (別ターミナル)
./scripts/record_episodes.sh 15 ~/dataset/rosbags/wave

# 3. 変換・学習 (configs/*.yaml, crane_features.py を ~/pai_training/configs に置く)
cd ~/pai_training
pixi run convert
WANDB_MODE=offline pixi run train

# 4. 推論 (テレオペや wave_demo は必ず止めておく)
pixi run infer --model-path ~/checkpoints/train/crane_plus_wave_act
```

## 表示用ビュー
`configs/wave_view.rviz` : ロボットだけを大きく映すRViz設定 (動画撮影用)。
