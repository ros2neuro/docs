cmake_minimum_required(VERSION 3.8)
project(tutorial_band_power)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ros2neuro_msgs REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(band_power_node src/band_power_node.cpp)
target_compile_features(band_power_node PUBLIC cxx_std_17)
target_include_directories(band_power_node PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
ament_target_dependencies(band_power_node rclcpp ros2neuro_msgs std_msgs)

install(TARGETS band_power_node DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})

# the maths is header-only and does not need ROS: it is tested on its own
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_band_power test/test_band_power.cpp)
  target_compile_features(test_band_power PUBLIC cxx_std_17)
  target_include_directories(test_band_power PRIVATE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
endif()

ament_package()
