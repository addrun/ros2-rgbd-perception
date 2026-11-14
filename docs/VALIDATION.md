# 验证记录

日期：2026-11-14。此记录区分本次运行与早期项目产物。

## 本次完成

| 检查 | 结果与范围 |
| --- | --- |
| ROS 2 Jazzy `colcon build --symlink-install` | `rgbd_interfaces`、`rgbd_perception` 两包构建成功 |
| 几何 pytest | 5 项通过：深度单位、原图中心投影、无效输入、PCA 主轴边界 |
| `colcon test` / `colcon test-result --verbose` | 5 项测试，0 errors / failures / skipped |
| 16UC1 ROS 检查 | 实际启动两个节点并订阅 TargetArray；位置 `[0, 0, 1.5000001192]` 米 |
| 32FC1 ROS 检查 | 同一场景输出 `[0, 0, 1.5]` 米；Header 和 PCA 有效性检查通过 |
| Ultralytics 适配器 | 本地 YOLO11n + 上游 bus 示例图片，CPU 推理得到 5 个框，类别含 bus/person |
| YOLOv5 适配器 | 本地 YOLOv5 checkout + yolov5s.pt，同一示例得到 5 个框；已修正 inference_mode 外原地缩放的问题 |
| 文档图 | SVG 已渲染检查，无外部图片或绝对本机资源依赖 |

几何与 ROS 演示使用系统 Python 3.12.3、NumPy 1.26.4、OpenCV 4.6.0 和已安装的 ROS 2 Jazzy。
可选真实模型检查使用已有环境：PyTorch 2.5.0、Ultralytics 8.3.141、OpenCV 4.10.0、NumPy 1.26.4。
该已有环境报告 torchvision 0.21 与 torch 2.5 的版本配套警告，尽管两次 CPU 推理都完成；
这不作为全新环境依赖兼容性或所有历史权重兼容性的证明。未修改原有全局环境来压掉警告。

## 尚未完成的验收

- 未重新连接 RGB-D 相机进行驱动、配准、标定和同步效果验证。
- 未测真实距离/方向误差、吞吐率、长时稳定性；没有为这些指标填写推测数字。
- 合成 ROS fixture 的检测框来自已知矩形，不是神经网络识别结果。
- 模型适配器检查没有与真实 RGB-D 相机联跑，也不是自训练模型评估。
- 没有把原工作区中的高 mAP、视频文件或旧构建日志当作本发布版实测。

GitHub Actions 的结果以仓库实际运行状态为准；本记录中的数字是本机运行结果。
