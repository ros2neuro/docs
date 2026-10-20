// A tiny simulator, so that the tutorial runs without hardware and without frontal electrodes.
//
// It publishes NeuroFrame messages with five EEG channels (Fp1, Fp2, C3, Cz, C4): background
// activity (a 10 Hz rhythm plus noise) and, every `period_s` seconds, an eye blink. A blink is a
// Gaussian pulse that is large and has the same polarity on Fp1 and Fp2, and is ten times smaller
// on the central channels, as in real recordings.
#include <chrono>
#include <cmath>
#include <cstddef>
#include <memory>
#include <random>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "ros2neuro_msgs/msg/neuro_frame.hpp"

class FakeEogNode : public rclcpp::Node {
  public:
    FakeEogNode(void) : rclcpp::Node("fake_eog"), noise_(0.0, 5.0), generator_(1234) {
        this->samplerate_ = this->declare_parameter<double>("samplerate", 512.0);
        this->framerate_ = this->declare_parameter<double>("framerate", 16.0);
        this->period_s_ = this->declare_parameter<double>("period_s", 4.0);
        this->amplitude_ = this->declare_parameter<double>("amplitude_uv", 150.0);
        const auto topic = this->declare_parameter<std::string>("output_topic", "/neurodata");

        this->samples_per_frame_ = static_cast<std::size_t>(std::round(this->samplerate_ / this->framerate_));
        this->start_ = this->now();

        this->publisher_ = this->create_publisher<ros2neuro_msgs::msg::NeuroFrame>(topic, 10);
        this->timer_ = this->create_wall_timer(
            std::chrono::duration<double>(1.0 / this->framerate_), [this]() { this->publish_frame(); });

        RCLCPP_INFO(this->get_logger(), "Publishing on '%s': a blink of %.0f uV every %.1f s", topic.c_str(),
                    this->amplitude_, this->period_s_);
    }

  private:
    void publish_frame(void) {
        const std::size_t channels = 5;                  // Fp1, Fp2, C3, Cz, C4
        const double gain[channels] = {1.0, 1.0, 0.1, 0.1, 0.1};

        ros2neuro_msgs::msg::NeuroFrame frame;
        frame.header.stamp = this->start_ + rclcpp::Duration::from_seconds(
            static_cast<double>(this->sample_) / this->samplerate_);
        frame.device_id = "fake_eog";
        frame.samples = static_cast<std::uint32_t>(this->samples_per_frame_);
        frame.samplerate = static_cast<float>(this->samplerate_);

        ros2neuro_msgs::msg::NeuroSensor eeg;
        eeg.name = "EEG";
        eeg.channels = channels;
        eeg.labels = {"Fp1", "Fp2", "C3", "Cz", "C4"};
        eeg.data.resize(this->samples_per_frame_ * channels);

        for (std::size_t s = 0; s < this->samples_per_frame_; ++s) {
            const double t = static_cast<double>(this->sample_ + s) / this->samplerate_;
            const double phase = std::fmod(t, this->period_s_);
            const double blink = this->amplitude_ *
                                 std::exp(-0.5 * std::pow((phase - this->period_s_ / 2.0) / 0.07, 2.0));
            const double rhythm = 15.0 * std::sin(2.0 * M_PI * 10.0 * t);

            for (std::size_t c = 0; c < channels; ++c) {
                // sample-major: index = sample * channels + channel
                eeg.data[s * channels + c] =
                    static_cast<float>(rhythm + this->noise_(this->generator_) + gain[c] * blink);
            }
        }
        this->sample_ += this->samples_per_frame_;

        frame.sensors.push_back(eeg);
        this->publisher_->publish(frame);
    }

    double samplerate_ = 512.0;
    double framerate_ = 16.0;
    double period_s_ = 4.0;
    double amplitude_ = 150.0;
    std::size_t samples_per_frame_ = 32;
    std::size_t sample_ = 0;
    rclcpp::Time start_{0, 0, RCL_ROS_TIME};

    std::normal_distribution<double> noise_;
    std::mt19937 generator_;
    rclcpp::Publisher<ros2neuro_msgs::msg::NeuroFrame>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<FakeEogNode>());
    rclcpp::shutdown();
    return 0;
}
