#ifndef TUTORIAL_ROBOT_CONTROL_ROBOT_CONTROL_HPP_
#define TUTORIAL_ROBOT_CONTROL_ROBOT_CONTROL_HPP_

#include <vector>

#include <ros2neuro_control/control.hpp>
#include <ros2neuro_msgs/msg/neuro_control.hpp>

namespace tutorial {
namespace control {

// A control plugin for a robot. It takes the NeuroPrediction of the integrator (the input of every control) and does what it wants
// with it: here, it turns it into one of the commands of the robot and publishes it.
//
// The header of the message it publishes is the header of the prediction it is made from. That is what lets another node
// pair this command with the flow that ros2neuro_control_feedback builds from the SAME prediction (see SyncNode).
class RobotControl : public ros2neuro::control::Control {
public:
    bool configure(const rclcpp::Node::SharedPtr& node, ros2neuro::control::ControlContext& context) override;
    void on_prediction(const Input& prediction) override;

private:
    rclcpp::Publisher<ros2neuro_msgs::msg::NeuroControl>::SharedPtr publisher_;
    std::vector<int> commands_;
    double threshold_ = 0.7;
};

}  // namespace control
}  // namespace tutorial

#endif
