# Overview

We have dockerfile recepies to build an image which acts as a builder tool to generate a .deb package for this project
It is base on this tutorial: https://docs.ros.org/en/humble/How-To-Guides/Building-a-Custom-Deb-Package.html#


Steps:
1. Build an Image using this dockerfile: suggestive name such as ros2_deb_builder
   TODO: define clear steps and the command for docker build
TODO: the image shouuld add a script which handles the process of building a .deb package. The user should mount at a predefined location this repository and the script should execute some steps from the tutorial on building .deb packages. The output should go to another mount location to persist the generated .deb

2. Once we obtaian the  .deb:
   - Run within a clean ros:humble container where we install the .deb
   - Mount this repository and try to colcon build -> colcon test -> needs a Pluto with USB connection to run.
   NOTE: commands are executed from the container and the user can see failing tests (also mention how to edit cmakelists to leave only the python tests if we want to avoid lint checks)


Steps:
- Build the Image:

   docker build \
      -f ./ci/docker/deb_builder.Dockerfile \
      --build-arg PACKAGE_NAME=$(basename -s .git `git rev-parse --show-toplevel`) \
      -t ros-deb-builder:humble \
      .

- Run the image: will execute the script and place in our host system the .deb
docker run -it --rm -v ~/output:/output ros-deb-builder:humble bash


- Run tests:
  - Should run the base image
  - Mount the output .deb in there
  - Install the .deb
   - Clone the repo -> build -> run tests: do it manually