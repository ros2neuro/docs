// The talker: publishes a text message on the topic "chatter", 10 times per second.
#include <chrono>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

// --8<-- [start:class]
class Talker : public rclcpp::Node {
public:
  Talker() : Node("talker") {
    // --8<-- [start:publisher]
    // a publisher of String messages on the topic "chatter"; 10 = how many messages can wait in the queue
    publisher_ = create_publisher<std_msgs::msg::String>("chatter", 10);
    // --8<-- [end:publisher]

    // --8<-- [start:timer]
    // every 100 ms (10 Hz) call publish()
    timer_ = create_wall_timer(100ms, [this]() { publish(); });
    // --8<-- [end:timer]
  }

private:
  // --8<-- [start:publish]
  void publish() {
    std_msgs::msg::String msg;
    msg.data = "hello world " + std::to_string(count_++);
    publisher_->publish(msg);
    RCLCPP_INFO(get_logger(), "published: '%s'", msg.data.c_str());
  }
  // --8<-- [end:publish]

  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  int count_ = 0;
};
// --8<-- [end:class]

// --8<-- [start:main]
int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Talker>());   // spin: keep the node alive, run its timer
  rclcpp::shutdown();
  return 0;
}
// --8<-- [end:main]
