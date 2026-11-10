// The synchronization: a command is released only when the flow of the feedback has a message with the same header stamp.
#include <gtest/gtest.h>

#include <chrono>
#include <memory>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "ros2neuro_msgs/msg/neuro_control.hpp"
#include "tutorial_robot_control/sync_node.hpp"

using ros2neuro_msgs::msg::NeuroControl;

namespace {

class SyncNodeTest : public ::testing::Test {
protected:
    static void SetUpTestSuite() { rclcpp::init(0, nullptr); }
    static void TearDownTestSuite() { rclcpp::shutdown(); }

    void SetUp() override {
        rclcpp::NodeOptions options;
        options.parameter_overrides({
            {"flow_topic", "/test_sync/flow"}, {"command_topic", "/test_sync/command"}, {"output_topic", "/test_sync/released"}});
        node_ = std::make_shared<tutorial::control::SyncNode>(options);
        helper_ = std::make_shared<rclcpp::Node>("sync_test_helper");
        flow_pub_ = helper_->create_publisher<NeuroControl>("/test_sync/flow", 10);
        command_pub_ = helper_->create_publisher<NeuroControl>("/test_sync/command", 10);
        sub_ = helper_->create_subscription<NeuroControl>(
            "/test_sync/released", 10, [this](const NeuroControl::SharedPtr msg) { released_.push_back(*msg); });
        executor_.add_node(node_);
        executor_.add_node(helper_);
        spin(std::chrono::milliseconds(400));   // discovery
    }

    void TearDown() override {
        executor_.remove_node(helper_);
        executor_.remove_node(node_);
    }

    void spin(std::chrono::milliseconds duration) {
        const auto end = std::chrono::steady_clock::now() + duration;
        while (std::chrono::steady_clock::now() < end)
            executor_.spin_some(std::chrono::milliseconds(5));
    }

    static NeuroControl message(int32_t sec, int32_t command) {
        NeuroControl msg;
        msg.header.stamp.sec = sec;
        msg.header.stamp.nanosec = 500;
        msg.actions = {"robot_command"};
        msg.commands = {command};
        return msg;
    }

    std::shared_ptr<tutorial::control::SyncNode> node_;
    std::shared_ptr<rclcpp::Node> helper_;
    rclcpp::Publisher<NeuroControl>::SharedPtr flow_pub_;
    rclcpp::Publisher<NeuroControl>::SharedPtr command_pub_;
    rclcpp::Subscription<NeuroControl>::SharedPtr sub_;
    rclcpp::executors::SingleThreadedExecutor executor_;
    std::vector<NeuroControl> released_;
};

}  // namespace

TEST_F(SyncNodeTest, a_command_is_released_when_the_flow_has_the_same_stamp) {
    flow_pub_->publish(message(5, 0));
    command_pub_->publish(message(5, 1));
    spin(std::chrono::milliseconds(500));

    ASSERT_EQ(released_.size(), 1U);
    EXPECT_EQ(released_[0].commands, (std::vector<int32_t>{1}));    // the command, not the flow
    EXPECT_EQ(released_[0].header.stamp.sec, 5);
    EXPECT_EQ(node_->released(), 1);
}

TEST_F(SyncNodeTest, the_order_of_arrival_does_not_matter) {
    command_pub_->publish(message(6, 2));
    spin(std::chrono::milliseconds(100));
    flow_pub_->publish(message(6, 0));
    spin(std::chrono::milliseconds(500));

    ASSERT_EQ(released_.size(), 1U);
    EXPECT_EQ(released_[0].commands, (std::vector<int32_t>{2}));
}

TEST_F(SyncNodeTest, nothing_is_released_when_the_stamps_differ) {
    flow_pub_->publish(message(7, 0));
    command_pub_->publish(message(8, 1));   // another prediction
    spin(std::chrono::milliseconds(500));

    EXPECT_TRUE(released_.empty());
}

TEST_F(SyncNodeTest, a_flow_without_a_command_releases_nothing) {
    // the events that the flow forwards from the event bus have a stamp of their own and no command with it
    flow_pub_->publish(message(9, 0));
    spin(std::chrono::milliseconds(500));
    EXPECT_TRUE(released_.empty());
}

TEST_F(SyncNodeTest, every_matching_pair_is_released_in_a_stream) {
    for (int32_t s = 20; s < 25; ++s) {
        flow_pub_->publish(message(s, 0));
        command_pub_->publish(message(s, s % 4));
    }
    flow_pub_->publish(message(99, 0));   // no partner
    spin(std::chrono::milliseconds(700));

    EXPECT_EQ(released_.size(), 5U);
}
