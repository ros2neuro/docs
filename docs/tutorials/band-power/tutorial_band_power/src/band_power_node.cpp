// The band power node: reads a band-passed NeuroFrame and publishes the band power of every channel, once per frame.
#include <algorithm>
#include <cmath>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "ros2neuro_msgs/msg/neuro_frame.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"

#include "tutorial_band_power/BandPower.h"

namespace tutorial {

class BandPowerNode : public rclcpp::Node {
  public:
    BandPowerNode() : rclcpp::Node("band_power") {
        // --8<-- [start:parameters]
        sensor_ = declare_parameter<std::string>("sensor", "EEG");    // which block of the frame to analyse
        window_s_ = declare_parameter<double>("window_s", 1.0);       // length of the moving average, in seconds
        // --8<-- [end:parameters]

        // --8<-- [start:topics]
        publisher_ = create_publisher<std_msgs::msg::Float32MultiArray>("bandpower", 10);
        subscription_ = create_subscription<ros2neuro_msgs::msg::NeuroFrame>(
            "/neurodata", 10,    // remap it to the topic of the band-pass chain
            [this](const ros2neuro_msgs::msg::NeuroFrame::SharedPtr frame) { on_frame(*frame); });
        // --8<-- [end:topics]
    }

  private:
    void on_frame(const ros2neuro_msgs::msg::NeuroFrame& frame) {
        // --8<-- [start:find]
        // 1. the block of the frame we want (by name)
        const auto sensor = std::find_if(frame.sensors.begin(), frame.sensors.end(),
            [this](const ros2neuro_msgs::msg::NeuroSensor& s) { return s.name == sensor_; });
        if (sensor == frame.sensors.end() || frame.samples == 0U || frame.samplerate <= 0.0F) {
            return;
        }
        // --8<-- [end:find]

        // --8<-- [start:create]
        // 2. the maths object, built at the first frame: only then we know the channels and the sampling rate
        const std::size_t channels = sensor->channels;
        if (!band_power_) {
            const auto window = static_cast<std::size_t>(std::max(1.0, std::round(window_s_ * frame.samplerate)));
            band_power_ = std::make_unique<BandPower>(channels, window);
            RCLCPP_INFO(get_logger(), "%zu channel(s) of '%s', window of %zu samples", channels, sensor_.c_str(), window);
        }
        // --8<-- [end:create]

        // --8<-- [start:loop]
        // 3. the data is sample-major: the samples of one instant are next to each other
        for (std::size_t s = 0; s < frame.samples; ++s) {
            band_power_->push(&sensor->data[s * channels]);
        }
        // --8<-- [end:loop]

        // --8<-- [start:publish]
        // 4. one value per channel, once per frame
        std_msgs::msg::Float32MultiArray out;
        out.data = band_power_->value();
        publisher_->publish(out);
        // --8<-- [end:publish]
    }

    std::string sensor_;
    double window_s_ = 1.0;
    std::unique_ptr<BandPower> band_power_;
    rclcpp::Publisher<std_msgs::msg::Float32MultiArray>::SharedPtr publisher_;
    rclcpp::Subscription<ros2neuro_msgs::msg::NeuroFrame>::SharedPtr subscription_;
};

}  // namespace tutorial

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<tutorial::BandPowerNode>());
    rclcpp::shutdown();
    return 0;
}
