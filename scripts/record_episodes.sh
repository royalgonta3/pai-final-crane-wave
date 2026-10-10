#!/bin/bash
# Record N scripted wave episodes as rosbags (run inside the ROS 2 container,
# with Gazebo + CRANE+ V2 already running).
#   ./record_episodes.sh [N] [OUT_DIR]
set -e
N=${1:-15}
OUT=${2:-$HOME/dataset/rosbags/wave}
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
for i in $(seq 0 $((N-1))); do
  echo "=== episode $i / $N ==="
  python3 "$HERE/wave_demo.py" --home-only          # always start from the same pose
  ros2 bag record -o "$OUT/ep$i" \
    /joint_states \
    /crane_plus_arm_controller/joint_trajectory \
    /crane_plus_gripper_controller/joint_trajectory > /dev/null 2>&1 &
  REC=$!
  sleep 2                                           # let the recorder subscribe
  python3 "$HERE/wave_demo.py" --seed "$i"
  sleep 0.5
  kill -INT $REC; wait $REC 2>/dev/null || true
done
echo "done: $OUT"
