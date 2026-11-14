"""Launch the installed demo and verify real DDS target messages, for either depth encoding."""
import argparse
import json
import os
import signal
import subprocess
import tempfile
import time
import rclpy
from rgbd_interfaces.msg import TargetArray


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--encoding", choices=["16UC1", "32FC1"], default="16UC1")
    args = parser.parse_args()
    with tempfile.TemporaryFile(mode="w+") as log:
        process = subprocess.Popen(["ros2", "launch", "rgbd_perception", "perception.launch.py",
                                    "demo:=true", f"depth_encoding:={args.encoding}"],
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        rclpy.init()
        node = rclpy.create_node("rgbd_smoke_observer")
        seen = []
        node.create_subscription(TargetArray, "/targets", seen.append, 10)
        try:
            deadline = time.monotonic() + 20
            while not seen and time.monotonic() < deadline and process.poll() is None:
                rclpy.spin_once(node, timeout_sec=.2)
            if not seen:
                log.seek(0)
                raise RuntimeError("No target messages: " + log.read()[-4000:])
            observation = seen[-1]
            assert observation.header.frame_id == "demo_color_optical_frame"
            assert len(observation.targets) == 1
            target = observation.targets[0]
            assert target.label == "synthetic_target"
            assert abs(target.position.x) < .001 and abs(target.position.y) < .001
            assert abs(target.position.z - 1.5) < .001
            assert target.axis_valid and abs(target.principal_axis.x) > .99
            print(json.dumps({"encoding": args.encoding, "source": "synthetic fixture",
                              "frame_id": observation.header.frame_id,
                              "position_m": [target.position.x, target.position.y, target.position.z],
                              "pca_axis_valid": target.axis_valid}))
        finally:
            node.destroy_node(); rclpy.shutdown()
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGINT)
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=3)


if __name__ == "__main__":
    main()
