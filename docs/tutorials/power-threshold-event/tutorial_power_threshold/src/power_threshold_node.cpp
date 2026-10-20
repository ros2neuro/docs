#include <algorithm>
#include <chrono>
#include <cstddef>
#include <memory>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "ros2neuro_msgs/msg/neuro_event.hpp"
#include "ros2neuro_msgs/msg/neuro_frame.hpp"

#include "tutorial_power_threshold/ThresholdDetector.h"

namespace tutorial {

// Event ids of the ros2neuro stack: the end of an event is its id plus 32768 ("Off").
constexpr int kOffFlag = 32768;

class PowerThresholdNode : public rclcpp::Node {
  public:
    PowerThresholdNode(void)
        : rclcpp::Node("power_threshold"),
          detector_(0.0, 0.8) {
        // --- parameters ---------------------------------------------------------------------
        const auto input_topic = this->declare_parameter<std::string>("input_topic", "/neurodata");
        const auto output_topic = this->declare_parameter<std::string>("output_topic", "/neuroevent");
        this->sensor_ = this->declare_parameter<std::string>("sensor", "");
        this->labels_ = this->declare_parameter<std::vector<std::string>>("channels", std::vector<std::string>{});
        this->event_id_ = static_cast<int>(this->declare_parameter<int>("event_id", 2001));
        this->emit_off_ = this->declare_parameter<bool>("emit_off", true);
        this->log_period_s_ = this->declare_parameter<double>("log_period_s", 2.0);
        this->detector_.set_threshold(this->declare_parameter<double>("threshold", 100.0));
        this->detector_.set_hysteresis(this->declare_parameter<double>("hysteresis", 0.8));

        // threshold and hysteresis can be changed while the node runs
        this->callback_handle_ = this->add_on_set_parameters_callback(
            [this](const std::vector<rclcpp::Parameter>& parameters) {
                rcl_interfaces::msg::SetParametersResult result;
                result.successful = true;
                for (const auto& parameter : parameters) {
                    if (parameter.get_name() == "threshold") {
                        if (parameter.as_double() <= 0.0) {
                            result.successful = false;
                            result.reason = "threshold must be positive";
                        } else {
                            this->detector_.set_threshold(parameter.as_double());
                        }
                    } else if (parameter.get_name() == "hysteresis") {
                        if (parameter.as_double() <= 0.0 || parameter.as_double() > 1.0) {
                            result.successful = false;
                            result.reason = "hysteresis must be in (0, 1]";
                        } else {
                            this->detector_.set_hysteresis(parameter.as_double());
                        }
                    }
                }
                return result;
            });

        // --- topics -------------------------------------------------------------------------
        this->publisher_ = this->create_publisher<ros2neuro_msgs::msg::NeuroEvent>(output_topic, 10);
        this->subscription_ = this->create_subscription<ros2neuro_msgs::msg::NeuroFrame>(
            input_topic, 10,
            [this](const ros2neuro_msgs::msg::NeuroFrame::SharedPtr frame) { this->on_frame(*frame); });

        RCLCPP_INFO(this->get_logger(), "Listening on '%s', publishing events %d on '%s'",
                    input_topic.c_str(), this->event_id_, output_topic.c_str());
    }

  private:
    void on_frame(const ros2neuro_msgs::msg::NeuroFrame& frame) {
        const ros2neuro_msgs::msg::NeuroSensor* sensor = this->find_sensor(frame);
        if (sensor == nullptr || frame.samples == 0U || sensor->channels == 0U) {
            return;
        }

        // 1. which channels? (resolved from the labels at the first frame)
        if (!this->resolved_) {
            this->resolve_channels(*sensor);
        }
        if (this->indices_.empty()) {
            return;
        }

        // 2. the power of every selected channel in this frame
        std::vector<float> powers;
        powers.reserve(this->indices_.size());
        for (const std::size_t channel : this->indices_) {
            powers.push_back(channel_power(sensor->data, frame.samples, sensor->channels, channel));
        }

        // 3. did the strongest channel cross the threshold?
        const auto crossing = this->detector_.update(powers);
        this->log_power(frame, crossing.power);

        if (crossing.type == ThresholdDetector::Type::None) {
            return;
        }
        if (crossing.type == ThresholdDetector::Type::Falling && !this->emit_off_) {
            return;
        }

        // 4. publish the event, stamped with the time at the END of the frame: the decision uses
        //    all of its samples, so this is the earliest instant it could have been taken.
        rclcpp::Time stamp(frame.header.stamp);
        stamp += rclcpp::Duration::from_seconds(static_cast<double>(frame.samples) / frame.samplerate);

        const std::string& label = this->selected_labels_[crossing.channel];
        ros2neuro_msgs::msg::NeuroEvent event;
        event.header.stamp = stamp;
        event.event_id = crossing.type == ThresholdDetector::Type::Rising ? this->event_id_
                                                                          : this->event_id_ + kOffFlag;
        event.description = "power " + label;
        this->publisher_->publish(event);

        RCLCPP_INFO(this->get_logger(), "%s: channel %s power %.1f (threshold %.1f)",
                    crossing.type == ThresholdDetector::Type::Rising ? "ABOVE" : "below",
                    label.c_str(), crossing.power, this->get_parameter("threshold").as_double());
    }

    const ros2neuro_msgs::msg::NeuroSensor* find_sensor(const ros2neuro_msgs::msg::NeuroFrame& frame) const {
        for (const auto& sensor : frame.sensors) {
            if (this->sensor_.empty() || sensor.name == this->sensor_) {
                return &sensor;
            }
        }
        return nullptr;
    }

    void resolve_channels(const ros2neuro_msgs::msg::NeuroSensor& sensor) {
        this->indices_.clear();
        this->selected_labels_.clear();

        if (this->labels_.empty()) {                       // no list: use every channel
            for (std::size_t c = 0; c < sensor.channels; ++c) {
                this->indices_.push_back(c);
                this->selected_labels_.push_back(c < sensor.labels.size() ? sensor.labels[c]
                                                                          : std::to_string(c));
            }
        } else {
            for (const auto& wanted : this->labels_) {
                const auto it = std::find(sensor.labels.begin(), sensor.labels.end(), wanted);
                if (it == sensor.labels.end()) {
                    RCLCPP_ERROR(this->get_logger(), "Channel '%s' is not in sensor '%s'",
                                 wanted.c_str(), sensor.name.c_str());
                    continue;
                }
                this->indices_.push_back(static_cast<std::size_t>(std::distance(sensor.labels.begin(), it)));
                this->selected_labels_.push_back(wanted);
            }
        }
        this->resolved_ = true;
        RCLCPP_INFO(this->get_logger(), "Monitoring %zu channel(s) of sensor '%s'",
                    this->indices_.size(), sensor.name.c_str());
    }

    // Prints the strongest power now and then, to help choosing the threshold.
    void log_power(const ros2neuro_msgs::msg::NeuroFrame& frame, float power) {
        if (this->log_period_s_ <= 0.0) {
            return;
        }
        const rclcpp::Time now(frame.header.stamp);
        if ((now - this->last_log_).seconds() >= this->log_period_s_) {
            RCLCPP_INFO(this->get_logger(), "strongest channel power: %.1f", power);
            this->last_log_ = now;
        }
    }

    // parameters
    std::string sensor_;
    std::vector<std::string> labels_;
    int event_id_ = 2001;
    bool emit_off_ = true;
    double log_period_s_ = 2.0;

    // state
    ThresholdDetector detector_;
    bool resolved_ = false;
    std::vector<std::size_t> indices_;
    std::vector<std::string> selected_labels_;
    rclcpp::Time last_log_{0, 0, RCL_ROS_TIME};

    rclcpp::Publisher<ros2neuro_msgs::msg::NeuroEvent>::SharedPtr publisher_;
    rclcpp::Subscription<ros2neuro_msgs::msg::NeuroFrame>::SharedPtr subscription_;
    rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr callback_handle_;
};

}  // namespace tutorial

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<tutorial::PowerThresholdNode>());
    rclcpp::shutdown();
    return 0;
}
