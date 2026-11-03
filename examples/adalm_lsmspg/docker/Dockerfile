# syntax=docker/dockerfile:1

ARG ROS_DISTRO=lyrical

FROM adi_ros2:$ROS_DISTRO-base

# Copy files into container
RUN mkdir -p /ros2_ws/src
WORKDIR /ros2_ws
COPY . src/adalm_lsmspg

RUN rosdep install --from-paths src --ignore-src -r -y || true
RUN . /opt/ros/adi_ros2/setup.sh && colcon build

# Setup entrypoint to source our workspace
RUN sed -i 's|exec "\$@"|source /ros2_ws/install/setup.bash\nexec "\$@"|' /ros_entrypoint.sh

