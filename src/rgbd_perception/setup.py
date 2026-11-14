# SPDX-License-Identifier: AGPL-3.0-only
from glob import glob
from setuptools import find_packages, setup

setup(name="rgbd_perception", version="0.1.0", packages=find_packages(exclude=["test"]),
      data_files=[("share/ament_index/resource_index/packages", ["resource/rgbd_perception"]),
                  ("share/rgbd_perception", ["package.xml"]),
                  ("share/rgbd_perception/launch", glob("launch/*.launch.py")),
                  ("share/rgbd_perception/config", glob("config/*.yaml"))],
      install_requires=["setuptools"], extras_require={"test": ["pytest"]}, zip_safe=True,
      maintainer="shhr", maintainer_email="141168900+addrun@users.noreply.github.com",
      description="RGB-D localisation and reproducible geometry demo", license="AGPL-3.0-only",
      entry_points={"console_scripts": ["detector = rgbd_perception.node:main",
                                        "demo_source = rgbd_perception.demo:main"]})
