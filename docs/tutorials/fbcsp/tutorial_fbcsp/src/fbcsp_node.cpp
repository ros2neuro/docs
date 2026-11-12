#include <algorithm>
#include <cstddef>
#include <memory>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "ros2neuro_msgs/msg/neuro_feature.hpp"
#include "ros2neuro_msgs/msg/neuro_frame.hpp"

#include "tutorial_fbcsp/FbcspBank.h"

namespace tutorial {

class FbcspNode : public rclcpp::Node {
  public:
    FbcspNode(void) : rclcpp::Node("fbcsp") {
        // --- parameters: the file written by train_fbcsp.m ---------------------------------------
        const auto input_topic = this->declare_parameter<std::string>("input_topic", "/neurodata");
        const auto output_topic = this->declare_parameter<std::string>("output_topic", "/features");
        this->sensor_ = this->declare_parameter<std::string>("sensor", "");
        this->feature_name_ = this->declare_parameter<std::string>("feature_name", "fbcsp");
        this->unit_ = this->declare_parameter<std::string>("unit", "ln(uV2)");
        this->labels_ = this->declare_parameter<std::vector<std::string>>("channels", std::vector<std::string>{});
        const auto window = static_cast<std::size_t>(this->declare_parameter<int>("window", 512));
        const auto components = static_cast<std::size_t>(this->declare_parameter<int>("components", 2));
        const auto n_bands = static_cast<std::size_t>(this->declare_parameter<int>("n_bands", 0));
        if (this->labels_.empty() || n_bands == 0U) {
            throw std::runtime_error("'channels' and 'n_bands' are required: load the parameter file written by train_fbcsp.m");
        }

        std::vector<Band> bands;
        for (std::size_t b = 1; b <= n_bands; ++b) {
            const std::string p = "band_" + std::to_string(b) + ".";
            Band band;
            for (const char* kind : {"hp", "lp"}) {
                IirSection section;
                section.b = this->numbers(p + kind + "_b");
                section.a = this->numbers(p + kind + "_a");
                band.sections.push_back(section);
            }
            band.w = this->numbers(p + "w");
            bands.push_back(band);
            this->centres_.push_back(static_cast<float>(this->declare_parameter<double>(p + "centre", 0.0)));
        }
        this->bank_ = std::make_unique<FbcspBank>(bands, this->labels_.size(), components, window);
        for (std::size_t k = 1; k <= components; ++k) {
            this->components_.push_back("csp" + std::to_string(k));
        }

        this->publisher_ = this->create_publisher<ros2neuro_msgs::msg::NeuroFeature>(output_topic, 10);
        this->subscription_ = this->create_subscription<ros2neuro_msgs::msg::NeuroFrame>(
            input_topic, 10, [this](const ros2neuro_msgs::msg::NeuroFrame::SharedPtr frame) { this->on_frame(*frame); });

        RCLCPP_INFO(this->get_logger(), "FBCSP: %zu bands x %zu components on %zu channels, window %zu samples, '%s' -> '%s'",
                    n_bands, components, this->labels_.size(), window, input_topic.c_str(), output_topic.c_str());
    }

  private:
    // a list of numbers that may be written as integers or as decimals in the yaml
    std::vector<double> numbers(const std::string& name) {
        rcl_interfaces::msg::ParameterDescriptor descriptor;
        descriptor.dynamic_typing = true;
        const auto value = this->declare_parameter(name, rclcpp::ParameterValue(std::vector<double>{}), descriptor);
        if (value.get_type() == rclcpp::PARAMETER_INTEGER_ARRAY) {
            const auto ints = value.get<std::vector<int64_t>>();
            return std::vector<double>(ints.begin(), ints.end());
        }
        return value.get<std::vector<double>>();
    }

    void on_frame(const ros2neuro_msgs::msg::NeuroFrame& frame) {
        const ros2neuro_msgs::msg::NeuroSensor* sensor = nullptr;
        for (const auto& s : frame.sensors) {
            if (this->sensor_.empty() || s.name == this->sensor_) { sensor = &s; break; }
        }
        if (sensor == nullptr || frame.samples == 0U) return;

        if (this->indices_.empty()) {                       // the channels of the training, found by label at the first frame
            for (const auto& wanted : this->labels_) {
                const auto it = std::find(sensor->labels.begin(), sensor->labels.end(), wanted);
                if (it == sensor->labels.end()) {
                    RCLCPP_ERROR_THROTTLE(this->get_logger(), *this->get_clock(), 5000,
                                          "Channel '%s' of the training is not in sensor '%s'", wanted.c_str(), sensor->name.c_str());
                    this->indices_.clear();
                    return;
                }
                this->indices_.push_back(static_cast<std::size_t>(std::distance(sensor->labels.begin(), it)));
            }
        }

        // sample-major: data[sample * channels + channel]; keep the channels of the training, in the order of the training
        std::vector<double> x(static_cast<std::size_t>(frame.samples) * this->indices_.size());
        for (std::size_t s = 0; s < frame.samples; ++s) {
            for (std::size_t c = 0; c < this->indices_.size(); ++c) {
                x[s * this->indices_.size() + c] = sensor->data[s * sensor->channels + this->indices_[c]];
            }
        }
        this->bank_->push(x.data(), frame.samples);
        if (!this->bank_->ready()) return;

        // the feature has the shape of a spectrum, [channels, frequency]: here the "channels" are the CSP components and the
        // "frequency" axis holds the centre of every band, so that the decoders that read a spectrum can read it as it is.
        ros2neuro_msgs::msg::NeuroFeature feature;
        feature.header = frame.header;
        feature.name = this->feature_name_;
        feature.type = ros2neuro_msgs::msg::NeuroFeature::TYPE_SPECTRUM;
        feature.unit = this->unit_;
        feature.window_length = static_cast<float>(this->window_samples() / frame.samplerate);
        feature.description = "ln of the variance of the CSP components of every band, shape [component, band]";
        feature.shape = {static_cast<uint32_t>(this->bank_->components()), static_cast<uint32_t>(this->bank_->bands())};
        feature.data = this->bank_->features();
        ros2neuro_msgs::msg::NeuroAxis components, bands;
        components.name = "channels";
        components.labels = this->components_;
        bands.name = "frequency";
        bands.unit = "Hz";
        bands.values = this->centres_;
        feature.axes = {components, bands};
        this->publisher_->publish(feature);
    }

    double window_samples() const { return static_cast<double>(this->get_parameter("window").as_int()); }

    std::string sensor_, feature_name_, unit_;
    std::vector<std::string> labels_, components_;
    std::vector<float> centres_;
    std::vector<std::size_t> indices_;
    std::unique_ptr<FbcspBank> bank_;
    rclcpp::Publisher<ros2neuro_msgs::msg::NeuroFeature>::SharedPtr publisher_;
    rclcpp::Subscription<ros2neuro_msgs::msg::NeuroFrame>::SharedPtr subscription_;
};

}  // namespace tutorial

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    try {
        rclcpp::spin(std::make_shared<tutorial::FbcspNode>());
    } catch (const std::exception& e) {
        RCLCPP_FATAL(rclcpp::get_logger("fbcsp"), "%s", e.what());
        rclcpp::shutdown();
        return 1;
    }
    rclcpp::shutdown();
    return 0;
}
