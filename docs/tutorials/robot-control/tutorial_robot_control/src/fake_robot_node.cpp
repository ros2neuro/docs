// The "robot" of the tutorial: it only says what it would do. Replace it with the driver of your robot.
#include <rclcpp/rclcpp.hpp>
#include <ros2neuro_msgs/msg/neuro_control.hpp>

#include "tutorial_robot_control/robot_commands.hpp"

namespace {

class FakeRobot : public rclcpp::Node {
public:
    FakeRobot() : rclcpp::Node("robot") {
        const std::string topic = this->declare_parameter<std::string>("command_topic", "/sync/command");
        this->sub_ = this->create_subscription<ros2neuro_msgs::msg::NeuroControl>(
            topic, 10, [this](const ros2neuro_msgs::msg::NeuroControl::SharedPtr message) {
                for (std::size_t i = 0; i < message->actions.size() && i < message->commands.size(); ++i) {
                    if (message->actions[i] != "robot_command")
                        continue;
                    const int command = message->commands[i];
                    if (command != this->last_) {
                        RCLCPP_INFO(this->get_logger(), "robot: %s", tutorial::control::command_name(command));
                        this->last_ = command;
                    }
                }
            });
        RCLCPP_INFO(this->get_logger(), "robot: waiting for commands on '%s'", topic.c_str());
    }

private:
    rclcpp::Subscription<ros2neuro_msgs::msg::NeuroControl>::SharedPtr sub_;
    int last_ = -1;
};

}  // namespace

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<FakeRobot>());
    rclcpp::shutdown();
    return 0;
}
