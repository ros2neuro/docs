cmake_minimum_required(VERSION 3.8)
project(tutorial_robot_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(message_filters REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ros2neuro_control REQUIRED)
find_package(ros2neuro_msgs REQUIRED)

# 1. the control plugin is a shared library (a control plugin derives from ros2neuro::control::Control)
add_library(${PROJECT_NAME} SHARED src/robot_commands.cpp src/robot_control.cpp)
target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_17)
target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(${PROJECT_NAME} pluginlib rclcpp ros2neuro_control ros2neuro_msgs)

# 2. plugins.xml is registered with the package that loads the plugins: ros2neuro_control
pluginlib_export_plugin_description_file(ros2neuro_control plugins.xml)

# 3. the synchronization node (not a plugin: an ordinary node) and the robot
add_library(${PROJECT_NAME}_sync SHARED src/sync_node.cpp)
target_compile_features(${PROJECT_NAME}_sync PUBLIC cxx_std_17)
target_include_directories(${PROJECT_NAME}_sync PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(${PROJECT_NAME}_sync message_filters rclcpp ros2neuro_msgs)

add_executable(sync_node src/sync_node_main.cpp)
target_link_libraries(sync_node ${PROJECT_NAME}_sync)
ament_target_dependencies(sync_node rclcpp)

add_executable(fake_robot_node src/fake_robot_node.cpp)
target_link_libraries(fake_robot_node ${PROJECT_NAME})
ament_target_dependencies(fake_robot_node rclcpp ros2neuro_msgs)

install(TARGETS ${PROJECT_NAME} ${PROJECT_NAME}_sync
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib)
install(TARGETS sync_node fake_robot_node RUNTIME DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY include/ DESTINATION include)
install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})

# 4. tests: the command of a prediction, the plugin loaded by the control node, the synchronization
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_robot_commands test/test_robot_commands.cpp)
  target_link_libraries(test_robot_commands ${PROJECT_NAME})

  ament_add_gtest(test_robot_control test/test_robot_control.cpp)
  target_link_libraries(test_robot_control ${PROJECT_NAME})
  ament_target_dependencies(test_robot_control pluginlib rclcpp ros2neuro_control ros2neuro_msgs)

  ament_add_gtest(test_sync_node test/test_sync_node.cpp)
  target_link_libraries(test_sync_node ${PROJECT_NAME}_sync)
  ament_target_dependencies(test_sync_node message_filters rclcpp ros2neuro_msgs)
endif()

ament_export_include_directories(include)
ament_export_libraries(${PROJECT_NAME} ${PROJECT_NAME}_sync)
ament_export_dependencies(message_filters pluginlib rclcpp ros2neuro_control ros2neuro_msgs)
ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)

ament_package()
