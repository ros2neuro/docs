#include <rclcpp/rclcpp.hpp>

#include "tutorial_robot_control/sync_node.hpp"

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<tutorial::control::SyncNode>());
    rclcpp::shutdown();
    return 0;
}
