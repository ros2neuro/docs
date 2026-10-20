cmake_minimum_required(VERSION 3.8)
project(tutorial_integrator_plugin)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ros2neuro_integrator REQUIRED)
find_package(ros2neuro_msgs REQUIRED)

# 1. the plugin is a shared library
add_library(${PROJECT_NAME} SHARED src/MovingAverage.cpp)
target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_17)
target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(${PROJECT_NAME} pluginlib rclcpp ros2neuro_integrator ros2neuro_msgs)

# 2. plugins.xml is registered with the package that loads the plugins
pluginlib_export_plugin_description_file(ros2neuro_integrator plugins.xml)

install(TARGETS ${PROJECT_NAME}
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib)
install(DIRECTORY include/ DESTINATION include)
install(DIRECTORY config DESTINATION share/${PROJECT_NAME})

# 3. unit test
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_moving_average test/test_moving_average.cpp)
  target_link_libraries(test_moving_average ${PROJECT_NAME})
  ament_target_dependencies(test_moving_average pluginlib rclcpp ros2neuro_integrator ros2neuro_msgs)
endif()

ament_export_include_directories(include)
ament_export_libraries(${PROJECT_NAME})
ament_export_dependencies(pluginlib rclcpp ros2neuro_integrator ros2neuro_msgs)
ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)

ament_package()
