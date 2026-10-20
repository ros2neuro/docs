#include "tutorial_integrator_plugin/MovingAverage.h"

#include <algorithm>
#include <stdexcept>

#include "pluginlib/class_list_macros.hpp"

namespace tutorial {
namespace integrator {

using ros2neuro::integrator::IntegrationResult;

bool MovingAverage::configure(void) {
    int window = static_cast<int>(this->window_);
    this->getParam("window", window);        // keeps the default when missing

    if (window < 1) {
        RCLCPP_ERROR(this->logger(), "[%s] 'window' must be >= 1 (got %d)", this->name().c_str(), window);
        return false;
    }

    this->window_ = static_cast<std::size_t>(window);
    return true;
}

IntegrationResult MovingAverage::apply(const ros2neuro_msgs::msg::NeuroPrediction& prediction) {
    if (prediction.values.empty()) {
        throw std::runtime_error("Prediction values are empty");
    }
    if (!this->history_.empty() && this->history_.front().size() != prediction.values.size()) {
        throw std::runtime_error("Prediction size changed after integrator initialization");
    }

    this->history_.push_back(prediction.values);
    this->trim();
    return this->current_result();
}

IntegrationResult MovingAverage::reset(const std::size_t class_count) {
    this->history_.clear();
    if (class_count > 0U) {
        // a single neutral sample: every class at 1/K
        this->history_.push_back(std::vector<float>(class_count, 1.0F / static_cast<float>(class_count)));
    }
    return this->current_result();
}

rcl_interfaces::msg::SetParametersResult MovingAverage::set_runtime_parameter(
    const rclcpp::Parameter& parameter) {
    rcl_interfaces::msg::SetParametersResult result;
    result.successful = false;

    if (parameter.get_name() != "window") {
        result.reason = "Unsupported runtime parameter '" + parameter.get_name() + "'";
        return result;
    }
    if (parameter.get_type() != rclcpp::ParameterType::PARAMETER_INTEGER || parameter.as_int() < 1) {
        result.reason = "Parameter 'window' must be an integer >= 1";
        return result;
    }

    this->window_ = static_cast<std::size_t>(parameter.as_int());
    this->trim();
    result.successful = true;
    return result;
}

IntegrationResult MovingAverage::current_result(void) const {
    IntegrationResult result;
    result.decision = -1;
    if (this->history_.empty()) {
        return result;
    }

    result.integrated.assign(this->history_.front().size(), 0.0F);
    for (const auto& sample : this->history_) {
        for (std::size_t k = 0; k < sample.size(); ++k) {
            result.integrated[k] += sample[k];
        }
    }
    for (auto& value : result.integrated) {
        value /= static_cast<float>(this->history_.size());
    }

    const auto best = std::max_element(result.integrated.begin(), result.integrated.end());
    result.decision = static_cast<int32_t>(std::distance(result.integrated.begin(), best));
    return result;
}

void MovingAverage::trim(void) {
    while (this->history_.size() > this->window_) {
        this->history_.pop_front();
    }
}

}  // namespace integrator
}  // namespace tutorial

PLUGINLIB_EXPORT_CLASS(tutorial::integrator::MovingAverage, ros2neuro::integrator::Integrator)
