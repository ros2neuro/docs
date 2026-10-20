#ifndef TUTORIAL_INTEGRATOR_PLUGIN_MOVING_AVERAGE_H
#define TUTORIAL_INTEGRATOR_PLUGIN_MOVING_AVERAGE_H

#include <cstddef>
#include <deque>
#include <vector>

#include "ros2neuro_integrator/Integrator.h"

namespace tutorial {
namespace integrator {

// Integrates the predictions with the mean of the last `window` ones.
//
// Unlike the exponential integrator, which remembers everything with a decaying weight, a
// prediction here counts fully for `window` steps and then disappears.
class MovingAverage : public ros2neuro::integrator::Integrator {
  public:
    using ros2neuro::integrator::Integrator::configure;

    MovingAverage(void) = default;

    // Reads the parameter `window` (integrator.params.window in the YAML file).
    bool configure(void) override;

    // Called for every NeuroPrediction: push it and return the mean of the window.
    ros2neuro::integrator::IntegrationResult apply(
        const ros2neuro_msgs::msg::NeuroPrediction& prediction) override;

    // Forgets the history and goes back to the neutral vector 1/K.
    ros2neuro::integrator::IntegrationResult reset(std::size_t class_count) override;

    // Lets `ros2 param set /integrator integrator.params.window N` change the window while running.
    rcl_interfaces::msg::SetParametersResult set_runtime_parameter(
        const rclcpp::Parameter& parameter) override;

  private:
    ros2neuro::integrator::IntegrationResult current_result(void) const;
    void trim(void);

    std::size_t window_ = 16;
    std::deque<std::vector<float>> history_;
};

}  // namespace integrator
}  // namespace tutorial

#endif  // TUTORIAL_INTEGRATOR_PLUGIN_MOVING_AVERAGE_H
