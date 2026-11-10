#include "tutorial_robot_control/robot_control.hpp"

#include <pluginlib/class_list_macros.hpp>

#include "tutorial_robot_control/robot_commands.hpp"

namespace tutorial {
namespace control {

bool RobotControl::configure(const rclcpp::Node::SharedPtr& node, ros2neuro::control::ControlContext&) {
    // The parameters are read from the node the plugin is given: this is the only thing it needs.
    node->declare_parameter<std::string>("output_topic", "/control_robot/command");
    node->declare_parameter<double>("threshold", 0.7);
    // The command of each class, in the order of the values of the prediction.
    node->declare_parameter<std::vector<int64_t>>("commands", {kForward, kTurnLeft});

    const std::string output_topic = node->get_parameter("output_topic").as_string();
    this->threshold_ = node->get_parameter("threshold").as_double();
    // (a copy of the parameter first: as_integer_array() returns a reference into it)
    const rclcpp::Parameter commands = node->get_parameter("commands");
    for (int64_t command : commands.as_integer_array())
        this->commands_.push_back(static_cast<int>(command));

    if (this->threshold_ <= 0.0 || this->threshold_ > 1.0) {
        RCLCPP_ERROR(node->get_logger(), "RobotControl: 'threshold' must be in (0, 1], got %.2f", this->threshold_);
        return false;
    }

    // The plugin creates its own publisher on the node.
    this->publisher_ = node->create_publisher<ros2neuro_msgs::msg::NeuroControl>(output_topic, 10);
    RCLCPP_INFO(node->get_logger(), "RobotControl: commands on '%s', threshold %.2f", output_topic.c_str(), this->threshold_);
    return true;
}

void RobotControl::on_prediction(const Input& prediction) {
    const int command = command_for(prediction.values, this->commands_, this->threshold_);

    ros2neuro_msgs::msg::NeuroControl message;
    message.header = prediction.header;          // the SAME header as the prediction: the key to synchronize
    message.source = "control_robot";
    message.fields = prediction.fields;
    message.values = prediction.values;
    message.actions = {"robot_command"};
    message.commands = {command};
    this->publisher_->publish(message);
}

}  // namespace control
}  // namespace tutorial

PLUGINLIB_EXPORT_CLASS(tutorial::control::RobotControl, ros2neuro::control::Control)
