#include <algorithm>
#include <cstddef>
#include <memory>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "ros2neuro_msgs/msg/neuro_event.hpp"
#include "ros2neuro_msgs/msg/neuro_frame.hpp"

#include "tutorial_eog_check/BlinkDetector.h"

namespace tutorial {

// Event ids of the ros2neuro stack: Blink is 1024 and its end is 1024 + 32768 ("Off").
// The manager listens to both on /neuroevent.
constexpr int kBlinkEvent = 1024;
constexpr int kOffFlag = 32768;

class EogBlinkNode : public rclcpp::Node {
  public:
    EogBlinkNode(void) : rclcpp::Node("eog_blink") {
        // --- parameters ---------------------------------------------------------------------
        const auto input_topic = this->declare_parameter<std::string>("input_topic", "/neurodata");
        const auto output_topic = this->declare_parameter<std::string>("output_topic", "/neuroevent");
        this->sensor_ = this->declare_parameter<std::string>("sensor", "EEG");
        this->labels_ = this->declare_parameter<std::vector<std::string>>(
            "channels", std::vector<std::string>{"Fp1", "Fp2"});
        this->threshold_ = this->declare_parameter<double>("threshold", 80.0);
        this->hysteresis_ = this->declare_parameter<double>("hysteresis", 0.5);
        this->release_s_ = this->declare_parameter<double>("release_s", 0.15);
        this->baseline_tau_s_ = this->declare_parameter<double>("baseline_tau_s", 2.0);

        // --- topics -------------------------------------------------------------------------
        this->publisher_ = this->create_publisher<ros2neuro_msgs::msg::NeuroEvent>(output_topic, 10);
        this->subscription_ = this->create_subscription<ros2neuro_msgs::msg::NeuroFrame>(
            input_topic, 10,
            [this](const ros2neuro_msgs::msg::NeuroFrame::SharedPtr frame) { this->on_frame(*frame); });

        RCLCPP_INFO(this->get_logger(), "Looking for blinks on '%s', threshold %.1f", input_topic.c_str(),
                    this->threshold_);
    }

  private:
    void on_frame(const ros2neuro_msgs::msg::NeuroFrame& frame) {
        // 1. find the sensor block and the frontal channels (by label, once)
        const auto sensor = std::find_if(frame.sensors.begin(), frame.sensors.end(),
            [this](const ros2neuro_msgs::msg::NeuroSensor& s) { return s.name == this->sensor_; });
        if (sensor == frame.sensors.end() || frame.samples == 0U || frame.samplerate <= 0.0F) {
            return;
        }
        if (this->indices_.empty() && !this->resolve_channels(*sensor)) {
            return;
        }
        if (!this->detector_) {      // needs the sampling rate, known from the first frame
            this->detector_ = std::make_unique<BlinkDetector>(
                frame.samplerate, this->threshold_, this->hysteresis_, this->release_s_, this->baseline_tau_s_);
        }

        // 2. one value per sample: the mean of the frontal channels (sample-major layout)
        const rclcpp::Time frame_start(frame.header.stamp);
        for (std::size_t s = 0; s < frame.samples; ++s) {
            double sum = 0.0;
            for (const std::size_t channel : this->indices_) {
                sum += sensor->data[s * sensor->channels + channel];
            }
            const double value = sum / static_cast<double>(this->indices_.size());

            // 3. the detector decides on this sample
            const auto event = this->detector_->process(value);
            if (event == BlinkDetector::Event::None) {
                continue;
            }

            // 4. the event is stamped with the time of THIS sample, not with the time of the frame
            rclcpp::Time stamp = frame_start;
            stamp += rclcpp::Duration::from_seconds(static_cast<double>(s) / frame.samplerate);

            ros2neuro_msgs::msg::NeuroEvent message;
            message.header.stamp = stamp;
            message.event_id = event == BlinkDetector::Event::Start ? kBlinkEvent : kBlinkEvent + kOffFlag;
            message.description = "blink";
            this->publisher_->publish(message);

            if (event == BlinkDetector::Event::Start) {
                ++this->blinks_;
                RCLCPP_INFO(this->get_logger(), "blink %zu", this->blinks_);
            }
        }
    }

    bool resolve_channels(const ros2neuro_msgs::msg::NeuroSensor& sensor) {
        for (const auto& wanted : this->labels_) {
            const auto it = std::find(sensor.labels.begin(), sensor.labels.end(), wanted);
            if (it == sensor.labels.end()) {
                RCLCPP_ERROR(this->get_logger(), "Channel '%s' is not in sensor '%s'", wanted.c_str(),
                             sensor.name.c_str());
                this->indices_.clear();
                return false;
            }
            this->indices_.push_back(static_cast<std::size_t>(std::distance(sensor.labels.begin(), it)));
        }
        RCLCPP_INFO(this->get_logger(), "Using %zu frontal channel(s)", this->indices_.size());
        return !this->indices_.empty();
    }

    std::string sensor_;
    std::vector<std::string> labels_;
    double threshold_ = 80.0;
    double hysteresis_ = 0.5;
    double release_s_ = 0.15;
    double baseline_tau_s_ = 2.0;

    std::vector<std::size_t> indices_;
    std::unique_ptr<BlinkDetector> detector_;
    std::size_t blinks_ = 0;

    rclcpp::Publisher<ros2neuro_msgs::msg::NeuroEvent>::SharedPtr publisher_;
    rclcpp::Subscription<ros2neuro_msgs::msg::NeuroFrame>::SharedPtr subscription_;
};

}  // namespace tutorial

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<tutorial::EogBlinkNode>());
    rclcpp::shutdown();
    return 0;
}
