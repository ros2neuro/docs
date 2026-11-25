cmake_minimum_required(VERSION 3.8)
project(tutorial_feedback_gui)

find_package(ament_cmake REQUIRED)

# a Python script is not compiled: it is installed as an executable where `ros2 run` looks for it
install(PROGRAMS scripts/bar_gui.py DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})

ament_package()
