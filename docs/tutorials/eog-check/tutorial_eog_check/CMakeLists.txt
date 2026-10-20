cmake_minimum_required(VERSION 3.8)
project(tutorial_eog_check)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ros2neuro_msgs REQUIRED)

# the detector node and the simulator used by the demo
foreach(node eog_blink_node fake_eog_node)
  add_executable(${node} src/${node}.cpp)
  target_compile_features(${node} PUBLIC cxx_std_17)
  target_include_directories(${node} PRIVATE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
  ament_target_dependencies(${node} rclcpp ros2neuro_msgs)
  install(TARGETS ${node} DESTINATION lib/${PROJECT_NAME})
endforeach()

install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})

# the detector is header-only and does not need ROS: it is tested on its own
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_blink_detector test/test_blink_detector.cpp)
  target_compile_features(test_blink_detector PUBLIC cxx_std_17)
  target_include_directories(test_blink_detector PRIVATE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
endif()

ament_package()
