#include "tutorial_robot_control/sync_node.hpp"

namespace tutorial {
namespace control {

SyncNode::SyncNode(const rclcpp::NodeOptions& options) : rclcpp::Node("sync", options) {
    const std::string flow_topic = this->declare_parameter<std::string>("flow_topic", "/control_feedback/probabilities");
    const std::string command_topic = this->declare_parameter<std::string>("command_topic", "/control_robot/command");
    const std::string output_topic = this->declare_parameter<std::string>("output_topic", "/sync/command");
    const int queue = static_cast<int>(this->declare_parameter<int64_t>("queue_size", 100));

    this->flow_sub_.subscribe(this, flow_topic);
    this->command_sub_.subscribe(this, command_topic);

    // Exact time: the two messages carry the header of the same prediction, so their stamps are equal.
    this->synchronizer_ = std::make_shared<message_filters::Synchronizer<Policy>>(Policy(queue), this->flow_sub_, this->command_sub_);
    this->synchronizer_->registerCallback(std::bind(&SyncNode::on_pair, this, std::placeholders::_1, std::placeholders::_2));

    this->publisher_ = this->create_publisher<Message>(output_topic, 10);
    RCLCPP_INFO(
        this->get_logger(), "Sync: '%s' + '%s' (same header stamp) -> '%s'", flow_topic.c_str(), command_topic.c_str(),
        output_topic.c_str());
}

void SyncNode::on_pair(const Message::ConstSharedPtr& flow, const Message::ConstSharedPtr& command) {
    (void)flow;   // it is there to say that the feedback has the same values; the robot only needs the command
    this->publisher_->publish(*command);
    ++this->released_;
}

}  // namespace control
}  // namespace tutorial
