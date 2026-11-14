# SPDX-License-Identifier: AGPL-3.0-only
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_nodes(context):
    demo = LaunchConfiguration("demo").perform(context).lower() == "true"
    if demo:
        return [Node(package="rgbd_perception", executable="demo_source", output="screen",
                     parameters=[{"depth_encoding": LaunchConfiguration("depth_encoding")}]),
                Node(package="rgbd_perception", executable="detector", output="screen",
                     parameters=[{"backend": "fixture", "rgb_topic": "/demo/color", "depth_topic": "/demo/depth",
                                  "camera_info_topic": "/demo/camera_info"}])]
    overrides = {}
    for argument, parameter in (("model", "model_path"), ("backend", "backend"), ("yolov5_repo", "yolov5_repo")):
        value = LaunchConfiguration(argument).perform(context)
        if value:
            overrides[parameter] = value
    return [Node(package="rgbd_perception", executable="detector", output="screen",
                 parameters=[LaunchConfiguration("config"), overrides])]


def generate_launch_description():
    config = Path(get_package_share_directory("rgbd_perception")) / "config" / "detector.yaml"
    return LaunchDescription([
        DeclareLaunchArgument("demo", default_value="false", choices=["true", "false"]),
        DeclareLaunchArgument("depth_encoding", default_value="16UC1", choices=["16UC1", "32FC1"]),
        DeclareLaunchArgument("config", default_value=str(config)),
        DeclareLaunchArgument("model", default_value=""),
        DeclareLaunchArgument("backend", default_value="", choices=["", "ultralytics", "yolov5"]),
        DeclareLaunchArgument("yolov5_repo", default_value=""),
        OpaqueFunction(function=launch_nodes)])
