cmake_minimum_required(VERSION 3.8)
project(adi_iio)

# Default to C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ==============================================================================
# Find dependencies
# ==============================================================================
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

find_path(IIO_INCLUDE_DIRS
  NAMES iio.h
  REQUIRED
)

find_library(IIO_LIBRARIES
  NAMES iio libiio
  REQUIRED
)

# ==============================================================================
# Generate interfaces
# ==============================================================================
set(srv_files
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
)

rosidl_generate_interfaces(${PROJECT_NAME}
  ${srv_files}
  DEPENDENCIES std_msgs
)

rosidl_get_typesupport_target(adi_iio_srvs_typesupport_target ${PROJECT_NAME} "rosidl_typesupport_cpp")

# ==============================================================================
# Create executable
# ==============================================================================
set(NODE_NAME ${PROJECT_NAME}_node)

add_executable(${NODE_NAME}
    src/adi_iio.cpp
    src/attr_publisher.cpp
    src/iio_attr_topic.cpp
    src/iio_buffer.cpp
    src/iio_node.cpp
    src/iio_path.cpp
)

target_include_directories(${NODE_NAME}
              PUBLIC ${IIO_INCLUDE_DIRS}
              $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
              $<INSTALL_INTERFACE:include>)

target_link_libraries(${NODE_NAME}
  ${IIO_LIBRARIES}
  "${adi_iio_srvs_typesupport_target}"
  ${std_msgs_TARGETS}
  rclcpp::rclcpp)
ament_target_dependencies(${NODE_NAME} rclcpp std_msgs)
ament_export_dependencies(rosidl_default_runtime)

# ==============================================================================
# Install targets
# ==============================================================================

# Install executable
install(TARGETS ${NODE_NAME}
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

# Install configuration files
install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

# ==============================================================================
# Testing
# ==============================================================================
if(BUILD_TESTING)
  # Linters tests
  find_package(ament_lint_auto REQUIRED)
  list(APPEND AMENT_LINT_AUTO_EXCLUDE
    ament_cmake_flake8
  )
  ament_lint_auto_find_test_dependencies()

  # Check for environment variable
  if(DEFINED ENV{IIO_ROS2_ENABLE_HW_TESTS})
    set(BUILD_INTEGRATION_TESTS ON)
  else()
    set(BUILD_INTEGRATION_TESTS OFF)
  endif()

  if(BUILD_INTEGRATION_TESTS)
    find_package(ament_cmake_ros REQUIRED)
    find_package(launch_testing_ament_cmake)

    function(add_ros_isolated_launch_test path)
      set(RUNNER "${ament_cmake_ros_DIR}/run_test_isolated.py")
      add_launch_test("${path}" RUNNER "${RUNNER}" ${ARGN})
    endfunction()

    # Test configuration
    set(TEST_TIMEOUT $ENV{TEST_TIMEOUT})
    if(NOT TEST_TIMEOUT)
      set(TEST_TIMEOUT 30)
    endif()

    set(TEST_NODE_NAME $ENV{TEST_NODE_NAME})
    if(NOT TEST_NODE_NAME)
      set(TEST_NODE_NAME "adi_iio_node")
    endif()

    set(TEST_URI $ENV{TEST_URI})
    if(NOT TEST_URI)
      set(TEST_URI "ip:192.168.2.1")
    endif()

    set(DEFAULT_TEST_ARGS "node_name:=${TEST_NODE_NAME}" "uri:=${TEST_URI}" "timeout:=${TEST_TIMEOUT}")

    message(STATUS "Building integration tests:")
    message(STATUS "  - Node name: ${TEST_NODE_NAME}")
    message(STATUS "  - Test URI: ${TEST_URI}")
    message(STATUS "  - Timeout: ${TEST_TIMEOUT}s")

    add_ros_isolated_launch_test(
      test/smoke_test.test.py
        ARGS ${DEFAULT_TEST_ARGS}
    )
    add_ros_isolated_launch_test(
      test/iio_path_utils.test.py
        ARGS ${DEFAULT_TEST_ARGS}
    )
    add_ros_isolated_launch_test(
      test/buffer_srv.test.py
        ARGS ${DEFAULT_TEST_ARGS}
    )
    add_ros_isolated_launch_test(
      test/attr_topic.test.py
        ARGS ${DEFAULT_TEST_ARGS}
    )
    add_ros_isolated_launch_test(
      test/attr_srv.test.py
        ARGS ${DEFAULT_TEST_ARGS}
    )
  else()
    message(STATUS "Integration tests disabled. Set IIO_ROS2_ENABLE_HW_TESTS=1 environment variable to enable.")
  endif()
endif()

# ==============================================================================
# Export information
# ==============================================================================

ament_package()
