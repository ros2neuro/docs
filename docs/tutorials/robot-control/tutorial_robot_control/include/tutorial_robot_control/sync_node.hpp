#ifndef TUTORIAL_ROBOT_CONTROL_SYNC_NODE_HPP_
#define TUTORIAL_ROBOT_CONTROL_SYNC_NODE_HPP_

#include <memory>
#include <string>

#include <message_filters/subscriber.h>
#include <message_filters/sync_policies/exact_time.h>
#include <message_filters/synchronizer.h>
#include <rclcpp/rclcpp.hpp>
#include <ros2neuro_msgs/msg/neuro_control.hpp>

namespace tutorial {
namespace control {

// Keeps the robot in step with the feedback.
//
// ros2neuro_control_feedback publishes the flow that the feedback draws (`flow_topic`, a NeuroControl), and the robot control
// publishes the command (`command_topic`, a NeuroControl): both are made from the same NeuroPrediction of the integrator and carry
// ITS header. This node pairs them by `header.stamp` (exact time) and, for every pair, publishes the command on `output_topic`:
// the robot receives a command only when the feedback has the values of the same prediction, so what the robot does is what the
// subject is shown at that moment.
//
// A message with no partner is dropped: the events that the flow forwards from the event bus have their own stamp, and a
// calibration (the autopilot) does not show integrator values at all.
class SyncNode : public rclcpp::Node {
public:
    explicit SyncNode(const rclcpp::NodeOptions& options = rclcpp::NodeOptions());

    // How many pairs have been released so far.
    int released(void) const { return this->released_; }

private:
    using Message = ros2neuro_msgs::msg::NeuroControl;
    using Policy = message_filters::sync_policies::ExactTime<Message, Message>;

    void on_pair(const Message::ConstSharedPtr& flow, const Message::ConstSharedPtr& command);

    message_filters::Subscriber<Message> flow_sub_;
    message_filters::Subscriber<Message> command_sub_;
    std::shared_ptr<message_filters::Synchronizer<Policy>> synchronizer_;
    rclcpp::Publisher<Message>::SharedPtr publisher_;
    int released_ = 0;
};

}  // namespace control
}  // namespace tutorial

#endif
