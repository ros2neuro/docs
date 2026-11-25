cmake_minimum_required(VERSION 3.8)
project(tutorial_signal_chain)

find_package(ament_cmake REQUIRED)

# No code here: only parameters and launch files, installed where `ros2 launch` looks for them.
install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})

ament_package()
