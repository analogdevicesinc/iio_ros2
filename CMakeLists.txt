cmake_minimum_required(VERSION 3.8)
project(adi_iio)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(adi_iio_interfaces REQUIRED)
find_path(
	IIO_INCLUDE_DIRS
	NAMES iio.h
	HINTS ${CMAKE_INSTALL_PREFIX}/include
	      /include
	      /usr/include
	      /usr/local/include
	      /opt/local/include
	      REQUIRED
)

find_library(
	IIO_LIBRARIES
	NAMES iio libiio
	HINTS ${CMAKE_INSTALL_PREFIX}/lib
	      /usr/lib
	      /usr/lib64
	      /usr/local/lib
	      /usr/local/lib64
	      /opt/local/lib
	      /opt/local/lib64
	      REQUIRED
)

add_executable(${PROJECT_NAME} 
		src/iio_node.cpp 
		src/adi_iio.cpp 
		src/iio_attr_topic.cpp
		src/attr_publisher.cpp)

target_include_directories(${PROJECT_NAME} 
							PUBLIC ${IIO_INCLUDE_DIRS}
							$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
							$<INSTALL_INTERFACE:include>)
target_link_libraries(${PROJECT_NAME} ${IIO_LIBRARIES})
ament_target_dependencies(${PROJECT_NAME} rclcpp adi_iio_interfaces std_msgs)

install(TARGETS
	adi_iio
  DESTINATION lib/${PROJECT_NAME}
)


if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
