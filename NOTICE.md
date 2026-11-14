# 来源、改造与验证边界

## 原实验与开源基座

本项目整理自 shhr 的本地 `ros2_ws/src/ros2_yolov5` 视觉实验，并参考桌面同家族的历史工作区。
原实验基于 [TochusC/ros2-yolov8](https://github.com/TochusC/ros2-yolov8) 的 ROS 2 图像传输/检测示例扩展，
本地参考基座提交为 `a3c74e2a814f1006ec3fcd261ba4a4bb35ba6a58`。
该示例检测节点保留的声明包含 `Copyright 2016 Open Source Robotics Foundation, Inc.` 和 Apache-2.0；
完整 Apache-2.0 文本保留于 `LICENSES/Apache-2.0.txt`。

原实验增加了 YOLOv5 后端、RGB/深度/点云处理、XYZ/PCA 原型、TF 尝试和自定义消息。
这些属于开源库上的应用层集成，不是自研 YOLO、驱动或新定位算法。
相机驱动来自 Astra/Orbbec 生态，未把第三方 SDK 或驱动整包复制进来。

## 2026-11-14 发布整理

发布版重新组织节点和接口，不将新增的测试与修正追溯成早期实验已通过的成果：

- 用近似时间同步替代三路“最近一帧”缓存；CameraInfo 提供标定，输入要求明确。
- 区分毫米整数深度与米制浮点深度；避免检测框坐标重复还原。
- 从已配准深度 ROI 生成局部点云，限制 PCA 采样规模；删除未经标定的静态 TF 和强行的航向角输出。
- 将结果改成带 Header 的目标数组，标出 PCA 是否有效。
- 将配置、模型路径和后端选择参数化；添加清楚标为 fixture 的无硬件演示。
- 新增构建、几何测试与实际 ROS 消息检查。真实硬件测距精度没有在这次整理中完成验收。

## 依赖与许可

- [YOLOv5](https://github.com/ultralytics/yolov5) 和 [Ultralytics](https://github.com/ultralytics/ultralytics) 是可选检测后端；不随仓库附带源码和权重。本仓库 AGPL-3.0-only 与开源后端采用一致许可方向。
- ROS 2、message_filters、cv_bridge、NumPy、OpenCV 实现通信与基础计算。遵循各上游许可证。
- 合成矩形场景由本项目生成。fixtures 不执行目标检测，也不是实船、真实相机或导航闭环的证明。

本仓库完整许可见 LICENSE。
