// The plugin loaded by the node of ros2neuro_control, like in a real launch.
#include <gtest/gtest.h>

#include <chrono>
#include <memory>
#include <optional>

#include "rclcpp/rclcpp.hpp"
#include "ros2neuro_control/control_node.hpp"
#include "ros2neuro_msgs/msg/neuro_control.hpp"
#include "ros2neuro_msgs/msg/neuro_prediction.hpp"

using ros2neuro_msgs::msg::NeuroControl;
using ros2neuro_msgs::msg::NeuroPrediction;

namespace {

class RobotControlTest : public ::testing::Test {
protected:
    static void SetUpTestSuite() { rclcpp::init(0, nullptr); }
    static void TearDownTestSuite() { rclcpp::shutdown(); }

    void SetUp() override {
        rclcpp::NodeOptions options;
        options.parameter_overrides({
            {"plugin", "tutorial::control::RobotControl"},
            {"input_topic", "/test_robot/prediction"},
            {"output_topic", "/test_robot/command"},
            {"threshold", 0.7},
            {"commands", std::vector<int64_t>{1, 2}},
        });
        node_ = std::make_shared<ros2neuro::control::ControlNode>(options);
        ASSERT_TRUE(node_->configure());

        helper_ = std::make_shared<rclcpp::Node>("robot_control_test_helper");
        pub_ = helper_->create_publisher<NeuroPrediction>("/test_robot/prediction", 10);
        sub_ = helper_->create_subscription<NeuroControl>(
            "/test_robot/command", 10, [this](const NeuroControl::SharedPtr msg) { command_ = *msg; });
        executor_.add_node(node_);
        executor_.add_node(helper_);
    }

    void TearDown() override {
        executor_.remove_node(helper_);
        executor_.remove_node(node_);
        node_->release_plugin();
    }

    // Publishes the prediction until the robot control answers THAT prediction (the answer has its stamp: the ones of the previous
    // predictions, still in flight, are not it).
    std::optional<NeuroControl> ask(const std::vector<float>& values, int32_t stamp_sec) {
        NeuroPrediction prediction;
        prediction.header.stamp.sec = stamp_sec;
        prediction.header.stamp.nanosec = 123;
        prediction.fields = {"773", "771"};
        prediction.values = values;
        command_.reset();
        const auto end = std::chrono::steady_clock::now() + std::chrono::seconds(3);
        while ((!command_ || command_->header.stamp.sec != stamp_sec) && std::chrono::steady_clock::now() < end) {
            pub_->publish(prediction);
            executor_.spin_some(std::chrono::milliseconds(20));
        }
        return command_;
    }

    std::shared_ptr<ros2neuro::control::ControlNode> node_;
    std::shared_ptr<rclcpp::Node> helper_;
    rclcpp::Publisher<NeuroPrediction>::SharedPtr pub_;
    rclcpp::Subscription<NeuroControl>::SharedPtr sub_;
    rclcpp::executors::SingleThreadedExecutor executor_;
    std::optional<NeuroControl> command_;
};

}  // namespace

TEST_F(RobotControlTest, the_command_of_the_prediction_is_published) {
    const auto forward = ask({0.9F, 0.1F}, 10);
    ASSERT_TRUE(forward.has_value());
    EXPECT_EQ(forward->source, "control_robot");
    EXPECT_EQ(forward->actions, (std::vector<std::string>{"robot_command"}));
    EXPECT_EQ(forward->commands, (std::vector<int32_t>{1}));   // FORWARD

    const auto left = ask({0.2F, 0.8F}, 11);
    ASSERT_TRUE(left.has_value());
    EXPECT_EQ(left->commands, (std::vector<int32_t>{2}));      // TURN_LEFT

    const auto stop = ask({0.55F, 0.45F}, 12);
    ASSERT_TRUE(stop.has_value());
    EXPECT_EQ(stop->commands, (std::vector<int32_t>{0}));      // STOP
}

TEST_F(RobotControlTest, the_command_has_the_header_of_the_prediction) {
    // this is what the synchronization needs: the same stamp as the flow made from the same prediction
    const auto command = ask({0.9F, 0.1F}, 77);
    ASSERT_TRUE(command.has_value());
    EXPECT_EQ(command->header.stamp.sec, 77);
    EXPECT_EQ(command->header.stamp.nanosec, 123U);
}
