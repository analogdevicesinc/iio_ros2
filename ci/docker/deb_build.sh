#!/usr/bin/env bash

set -e

ROS_DISTRO=${ROS_DISTRO:-humble}
WORKSPACE=${WORKSPACE:-/ros2_ws/src}
DEB_OUTPUT_DIR=${DEB_OUTPUT_DIR:-/output}

echo "Building Debian package for ROS 2 workspace ..."
echo "ROS_DISTRO: $ROS_DISTRO"
echo "WORKSPACE: $WORKSPACE"
echo "DEB_OUTPUT_DIR: $DEB_OUTPUT_DIR"

# Check if the source workspace is empty. The user must mount their source code.
if [ -z "$(ls -A ${WORKSPACE})" ]; then
    echo "Error: ${WORKSPACE} is empty. Please mount your ROS package source code."
    echo "Example: docker run -v /local/path/to/my_ros_package:/ros2_ws/src ..."
    exit 1
fi

echo "Sourcing the ROS 2 environment ..."
. "/opt/ros/${ROS_DISTRO}/setup.bash"

cd "${WORKSPACE}"/..
echo "Entering workspace directory: $(pwd)"

rosdep init || true
rosdep update || true
rosdep install --from-paths src --ignore-src -r -y

echo "Entering ${WORKSPACE} directory ..."
cd "${WORKSPACE}"

PACKAGE_DIRS=$(find . -maxdepth 2 -name "package.xml" -print0 | xargs -0 -n1 dirname)

if [ -z "${PACKAGE_DIRS}" ]; then
    echo "Error: No ROS package (package.xml) found in ${WORKSPACE} or its immediate subdirectories."
    echo "Please ensure your ROS package(s) are correctly mounted."
    exit 1
fi

for PKG_DIR in ${PACKAGE_DIRS}; do
    PKG_NAME=$(basename "${PKG_DIR}")
    echo "--- Processing ROS package: ${PKG_NAME} located at ${PKG_DIR} ---"

    if [ "${PKG_NAME}" != "iio_ros2" ]; then
        echo "Skipping package ${PKG_NAME} (not iio_ros2) ..."
        continue
    fi
    (
        cd "${PKG_DIR}" || exit 1

        echo "Generating Debian rules for ${PKG_NAME} using bloom..."
        bloom-generate rosdebian

        echo "Building .deb package for ${PKG_NAME} using fakeroot..."
        fakeroot debian/rules binary
    )
    # The .deb file is now in the ${WORKSPACE} directory (parent of PKG_DIR if PKG_DIR is a subdirectory).
done

echo "Moving generated .deb files to the final output directory: ${DEB_OUTPUT_DIR}..."

find "${WORKSPACE}" -maxdepth 1 -name "*.*deb" -exec mv {} "${DEB_OUTPUT_DIR}" \;