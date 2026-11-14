# SPDX-License-Identifier: AGPL-3.0-only
"""Publish an aligned synthetic scene. No camera, model or network is used."""
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image
from cv_bridge import CvBridge


class DemoSource(Node):
    def __init__(self):
        super().__init__("rgbd_demo_source")
        self.declare_parameter("depth_encoding", "16UC1")
        self.encoding = self.get_parameter("depth_encoding").value
        if self.encoding not in ("16UC1", "32FC1"):
            raise ValueError("depth_encoding must be 16UC1 or 32FC1")
        self.bridge = CvBridge()
        self.rgb = self.create_publisher(Image, "/demo/color", qos_profile_sensor_data)
        self.depth = self.create_publisher(Image, "/demo/depth", qos_profile_sensor_data)
        self.info = self.create_publisher(CameraInfo, "/demo/camera_info", qos_profile_sensor_data)
        self.timer = self.create_timer(.2, self.tick)

    def tick(self):
        image = np.full((480, 640, 3), 30, np.uint8)
        image[180:300, 180:460] = [40, 170, 230]
        depth = np.zeros((480, 640), np.uint16 if self.encoding == "16UC1" else np.float32)
        depth[180:300, 180:460] = 1500 if self.encoding == "16UC1" else 1.5
        rgb_msg = self.bridge.cv2_to_imgmsg(image, encoding="bgr8")
        depth_msg = self.bridge.cv2_to_imgmsg(depth, encoding=self.encoding)
        info = CameraInfo(height=480, width=640, distortion_model="plumb_bob")
        info.k = [600., 0., 320., 0., 600., 240., 0., 0., 1.]
        info.p = [600., 0., 320., 0., 0., 600., 240., 0., 0., 0., 1., 0.]
        info.r = [1., 0., 0., 0., 1., 0., 0., 0., 1.]
        info.d = [0.] * 5
        for msg in (info, rgb_msg, depth_msg):
            msg.header.stamp = self.get_clock().now().to_msg() if msg is info else info.header.stamp
            msg.header.frame_id = "demo_color_optical_frame"
        self.info.publish(info); self.rgb.publish(rgb_msg); self.depth.publish(depth_msg)


def main(args=None):
    rclpy.init(args=args)
    node = DemoSource()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
