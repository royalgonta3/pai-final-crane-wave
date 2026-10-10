#!/usr/bin/env python3
"""Scripted "wave" demonstration for CRANE+ V2 (replaces keyboard teleop).

Publishes the same command topics as physicalai_teleop (20 Hz), so rosbag
recordings can be converted by the course's rosbag2lerobot.py as-is.

The wave is a closed loop in joint space (joint1 sweep + wrist/elbow lift),
so every phase of the motion has a distinct state. A state-only policy such
as ACT cannot tell "going left" from "going right" in a plain back-and-forth
motion; a loop avoids that ambiguity.

Usage:
    python3 wave_demo.py --seed 0            # one episode
    python3 wave_demo.py --home-only         # just move to the home pose
"""
import argparse
import math
import random

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

ARM_JOINT_NAMES = ['crane_plus_joint1', 'crane_plus_joint2', 'crane_plus_joint4', 'crane_plus_joint3']
GRIPPER_JOINT_NAME = 'crane_plus_joint_hand'
GRIPPER_OPEN = -0.5236
HZ = 20.0


def wave_pose(phase, amp1, amp3, amp4):
    """Joint targets [j1, j2, j4, j3] for phase in [0, 2*pi]; 0 and 2*pi = home."""
    j1 = amp1 * math.sin(phase)                  # sweep left-right
    lift = 0.5 * (1.0 - math.cos(phase))         # 0 -> 1 -> 0 over one loop
    j3 = amp3 * lift                             # raise the forearm
    j4 = amp4 * math.sin(2.0 * phase)            # wrist flick (figure-eight)
    return [j1, 0.0, j4, j3]


class WaveNode(Node):
    def __init__(self, args):
        super().__init__('crane_plus_wave_demo')
        self.arm_pub = self.create_publisher(JointTrajectory, '/crane_plus_arm_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(JointTrajectory, '/crane_plus_gripper_controller/joint_trajectory', 10)
        rng = random.Random(args.seed)
        # Small per-episode variation so the dataset is not 20 identical copies
        self.amp1 = args.amp1 * rng.uniform(0.9, 1.1)
        self.amp3 = args.amp3 * rng.uniform(0.9, 1.1)
        self.amp4 = args.amp4 * rng.uniform(0.9, 1.1)
        # Vary the speed, not the end point: always finish at the home pose
        self.period = args.period * rng.uniform(0.95, 1.05)
        self.duration = self.period * args.loops
        self.home_only = args.home_only
        self.t = 0.0
        self.done = False
        self.timer = self.create_timer(1.0 / HZ, self.tick)

    def publish(self, arm):
        jt = JointTrajectory()
        jt.joint_names = ARM_JOINT_NAMES
        pt = JointTrajectoryPoint()
        pt.positions = [float(x) for x in arm]
        pt.time_from_start.nanosec = int(0.1 * 1e9)
        jt.points.append(pt)
        self.arm_pub.publish(jt)
        jg = JointTrajectory()
        jg.joint_names = [GRIPPER_JOINT_NAME]
        pg = JointTrajectoryPoint()
        pg.positions = [GRIPPER_OPEN]
        pg.time_from_start.nanosec = int(0.1 * 1e9)
        jg.points.append(pg)
        self.gripper_pub.publish(jg)

    def tick(self):
        if self.home_only:
            self.publish([0.0, 0.0, 0.0, 0.0])
            self.t += 1.0 / HZ
            if self.t > 3.0:
                self.done = True
            return
        phase = 2.0 * math.pi * (self.t / self.period)
        self.publish(wave_pose(phase, self.amp1, self.amp3, self.amp4))
        self.t += 1.0 / HZ
        if self.t >= self.duration:
            self.publish([0.0, 0.0, 0.0, 0.0])
            self.done = True


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--period', type=float, default=4.0, help='seconds per wave loop')
    p.add_argument('--loops', type=int, default=2)
    p.add_argument('--amp1', type=float, default=0.5, help='joint1 sweep [rad]')
    p.add_argument('--amp3', type=float, default=0.6, help='joint3 lift [rad]')
    p.add_argument('--amp4', type=float, default=0.3, help='joint4 wrist [rad]')
    p.add_argument('--home-only', action='store_true')
    args = p.parse_args()
    rclpy.init()
    node = WaveNode(args)
    while rclpy.ok() and not node.done:
        rclpy.spin_once(node, timeout_sec=0.05)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
