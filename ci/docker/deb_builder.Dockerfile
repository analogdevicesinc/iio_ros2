# https://docs.ros.org/en/humble/How-To-Guides/Building-a-Custom-Deb-Package.html#id1
# WIP: come back later
FROM ros:humble

ENV WORKSPACE=/ros2_ws/src
ENV DEB_OUTPUT_DIR=/output

ARG PACKAGE_NAME=iio_ros2

WORKDIR ${WORKSPACE}

# Install prerequisites
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    python3-bloom \
    python3-rosdep \
    fakeroot \
    debhelper \
    dh-python \
    && rm -rf /var/lib/apt/lists/*

# Initialize rosdep
RUN apt-get update \
    && rosdep update --rosdistro ${ROS_DISTRO}

# Output directory for .deb files
RUN mkdir -p ${DEB_OUTPUT_DIR}

COPY ci/docker/deb_build.sh /usr/local/bin/deb_build.sh
RUN chmod +x /usr/local/bin/deb_build.sh

COPY . /ros2_ws/src/${PACKAGE_NAME}

ENTRYPOINT [ "/usr/local/bin/deb_build.sh" ]