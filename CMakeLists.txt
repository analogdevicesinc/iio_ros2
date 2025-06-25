cmake_minimum_required(VERSION 3.8)
project(adi_iio)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

find_path(
  IIO_INCLUDE_DIRS
  NAMES iio.h
  REQUIRED
)

find_library(
  IIO_LIBRARIES
  NAMES iio libiio
  REQUIRED
)

find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/AttrEnableTopic.srv"
  "srv/AttrDisableTopic.srv"
  "srv/AttrReadString.srv"
  "srv/AttrWriteString.srv"
  "srv/BufferRead.srv"
  "srv/BufferWrite.srv"
  "srv/BufferRefill.srv"
  "srv/BufferCreate.srv"
  "srv/BufferDestroy.srv"
  "srv/BufferEnableTopic.srv"
  "srv/BufferDisableTopic.srv"
  "srv/ListDevices.srv"
  "srv/ListChannels.srv"
  "srv/ListAttributes.srv"
  "srv/ScanContext.srv"

  DEPENDENCIES std_msgs
)
set(NODE_NAME ${PROJECT_NAME}_node)
rosidl_get_typesupport_target(adi_iio_srvs_typesupport_target ${PROJECT_NAME} "rosidl_typesupport_cpp")

add_executable(${NODE_NAME}
    src/iio_node.cpp
    src/iio_path.cpp
    src/adi_iio.cpp
    src/iio_buffer.cpp
    src/iio_attr_topic.cpp
    src/attr_publisher.cpp)

target_include_directories(${NODE_NAME}
              PUBLIC ${IIO_INCLUDE_DIRS}
              $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
              $<INSTALL_INTERFACE:include>)

target_link_libraries(${NODE_NAME} ${IIO_LIBRARIES} "${adi_iio_srvs_typesupport_target}")
ament_target_dependencies(${NODE_NAME} rclcpp std_msgs)
ament_export_dependencies(rosidl_default_runtime)

install(TARGETS
  ${NODE_NAME}
  DESTINATION lib/${PROJECT_NAME}
)

# Install files
install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}/
)


if(BUILD_TESTING)
  # ============================================================================
  # Linters tests
  # ============================================================================
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
  # ============================================================================
  # Integration tests
  # ============================================================================
  find_package(ament_cmake_ros REQUIRED)
  find_package(launch_testing_ament_cmake)

  function(add_ros_isolated_launch_test path)
    set(RUNNER "${ament_cmake_ros_DIR}/run_test_isolated.py")
    add_launch_test("${path}" RUNNER "${RUNNER}" ${ARGN})
  endfunction()

endif()

ament_package()
