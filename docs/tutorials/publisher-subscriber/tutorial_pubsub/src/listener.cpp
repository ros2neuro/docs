// The listener: prints every message that arrives on the topic "chatter".
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

// --8<-- [start:class]
class Listener : public rclcpp::Node {
public:
  Listener() : Node("listener") {
    // --8<-- [start:subscription]
    // the callback is called once for every message received on "chatter"
    subscription_ = create_subscription<std_msgs::msg::String>(
        "chatter", 10, [this](const std_msgs::msg::String& msg) { on_message(msg); });
    // --8<-- [end:subscription]
  }

private:
  // --8<-- [start:callback]
  void on_message(const std_msgs::msg::String& msg) {
    RCLCPP_INFO(get_logger(), "heard: '%s'", msg.data.c_str());
  }
  // --8<-- [end:callback]

  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};
// --8<-- [end:class]

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Listener>());
  rclcpp::shutdown();
  return 0;
}
