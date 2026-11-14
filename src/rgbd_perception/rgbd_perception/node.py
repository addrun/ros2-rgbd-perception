# SPDX-License-Identifier: AGPL-3.0-only
"""Synchronized colour/depth observations published in the colour optical frame."""
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from message_filters import Subscriber, ApproximateTimeSynchronizer
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
from rgbd_interfaces.msg import Target, TargetArray
from .geometry import Intrinsics, depth_in_metres, estimate_target
from .detectors import FixtureDetector, UltralyticsDetector, YoloV5Detector


class TargetDetector(Node):
    def __init__(self):
        super().__init__("rgbd_detector")
        defaults = {"backend": "ultralytics", "model_path": "", "yolov5_repo": "",
                    "rgb_topic": "/camera/color/image_rect", "depth_topic": "/camera/aligned_depth/image_raw",
                    "camera_info_topic": "/camera/color/camera_info", "confidence": .25,
                    "sync_slop": .03, "min_depth_m": .1, "max_depth_m": 10.}
        for key, value in defaults.items():
            self.declare_parameter(key, value)
        self.param = lambda name: self.get_parameter(name).value
        confidence = self.param("confidence")
        if not (0 < confidence <= 1) or self.param("sync_slop") <= 0:
            raise ValueError("confidence and sync_slop must be positive")
        if not 0 < self.param("min_depth_m") < self.param("max_depth_m"):
            raise ValueError("invalid min_depth_m/max_depth_m")
        backend = self.param("backend")
        if backend == "fixture":
            self.detector = FixtureDetector()
            self.get_logger().warn("SYNTHETIC FIXTURE backend: no object detector is running")
        elif backend == "ultralytics":
            self.detector = UltralyticsDetector(self.param("model_path"), confidence)
        elif backend == "yolov5":
            self.detector = YoloV5Detector(self.param("yolov5_repo"), self.param("model_path"), confidence)
        else:
            raise ValueError("backend must be fixture, ultralytics or yolov5")
        self.camera_info = None
        self.last_error = None
        self.bridge = CvBridge()
        self.pub = self.create_publisher(TargetArray, "targets", 10)
        self.info_sub = self.create_subscription(CameraInfo, self.param("camera_info_topic"),
                                                 self.on_info, qos_profile_sensor_data)
        self.rgb_sub = Subscriber(self, Image, self.param("rgb_topic"), qos_profile=qos_profile_sensor_data)
        self.depth_sub = Subscriber(self, Image, self.param("depth_topic"), qos_profile=qos_profile_sensor_data)
        self.sync = ApproximateTimeSynchronizer([self.rgb_sub, self.depth_sub], 5, self.param("sync_slop"))
        self.sync.registerCallback(self.on_images)

    def on_info(self, info):
        self.camera_info = info

    def on_images(self, rgb_msg, depth_msg):
        try:
            info = self.camera_info
            if info is None:
                raise ValueError("waiting for colour CameraInfo")
            frame = rgb_msg.header.frame_id
            if not frame or frame != depth_msg.header.frame_id or frame != info.header.frame_id:
                raise ValueError("RGB, registered depth and CameraInfo must use the same optical frame")
            if not np.allclose(info.d, 0):
                raise ValueError("inputs must be undistorted; nonzero distortion is not supported")
            if not np.allclose(info.r, np.eye(3).ravel()) or not np.allclose(np.array(info.p).reshape(3, 4)[:, 3], 0):
                raise ValueError("only a monocular colour optical frame with identity rectification is supported")
            rgb = self.bridge.imgmsg_to_cv2(rgb_msg, desired_encoding="bgr8")
            raw_depth = self.bridge.imgmsg_to_cv2(depth_msg, desired_encoding="passthrough")
            if rgb.shape[:2] != raw_depth.shape or rgb.shape[:2] != (info.height, info.width):
                raise ValueError("registered depth, RGB and CameraInfo dimensions must match")
            camera = Intrinsics(info.k[0], info.k[4], info.k[2], info.k[5])
            depth = depth_in_metres(raw_depth, depth_msg.encoding)
            output = TargetArray(); output.header = rgb_msg.header
            for box in self.detector.predict(rgb):
                estimate = estimate_target(depth, box.xyxy, camera, self.param("min_depth_m"), self.param("max_depth_m"))
                if estimate is None:
                    continue
                position, axis, valid = estimate
                target = Target(label=box.label, confidence=float(box.score), bbox_xyxy=[float(v) for v in box.xyxy])
                target.position.x, target.position.y, target.position.z = [float(v) for v in position]
                target.principal_axis.x, target.principal_axis.y, target.principal_axis.z = [float(v) for v in axis]
                target.axis_valid = valid
                output.targets.append(target)
            self.pub.publish(output)
            self.last_error = None
        except Exception as error:
            # A bad frame must not crash the ROS executor; report changes without flooding logs.
            message = str(error)
            if message != self.last_error:
                self.get_logger().error(f"Frame rejected: {type(error).__name__}: {message}")
                self.last_error = message


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = TargetDetector()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
