cmake_minimum_required(VERSION 3.8)
project(tutorial_power_threshold)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ros2neuro_msgs REQUIRED)

# the node
add_executable(power_threshold_node src/power_threshold_node.cpp)
target_compile_features(power_threshold_node PUBLIC cxx_std_17)
target_include_directories(power_threshold_node PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
ament_target_dependencies(power_threshold_node rclcpp ros2neuro_msgs)

# executables go to lib/<package> so that `ros2 run` finds them
install(TARGETS power_threshold_node DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY config DESTINATION share/${PROJECT_NAME})

# the detector is header-only and does not need ROS: it is tested on its own
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_threshold_detector test/test_threshold_detector.cpp)
  target_compile_features(test_threshold_detector PUBLIC cxx_std_17)
  target_include_directories(test_threshold_detector PRIVATE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
endif()

ament_package()
