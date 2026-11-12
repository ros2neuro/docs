cmake_minimum_required(VERSION 3.8)
project(tutorial_fbcsp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ros2neuro_msgs REQUIRED)
find_package(ros2neuro_decoder_lda REQUIRED)
find_package(yaml-cpp REQUIRED)

# the node: filter bank + CSP + log-variance
add_executable(fbcsp_node src/fbcsp_node.cpp)
target_compile_features(fbcsp_node PUBLIC cxx_std_17)
target_include_directories(fbcsp_node PRIVATE $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
ament_target_dependencies(fbcsp_node rclcpp ros2neuro_msgs)

# the tool that writes the LDA model for the decoder
add_executable(write_fbcsp_lda src/write_fbcsp_lda.cpp)
target_compile_features(write_fbcsp_lda PUBLIC cxx_std_17)
ament_target_dependencies(write_fbcsp_lda ros2neuro_msgs ros2neuro_decoder_lda)
target_link_libraries(write_fbcsp_lda yaml-cpp)

install(TARGETS fbcsp_node write_fbcsp_lda DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY config launch model DESTINATION share/${PROJECT_NAME})

# the bank is header-only and does not need ROS: it is tested on its own
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_fbcsp_bank test/test_fbcsp_bank.cpp)
  target_compile_features(test_fbcsp_bank PUBLIC cxx_std_17)
  target_include_directories(test_fbcsp_bank PRIVATE $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
endif()

ament_package()
