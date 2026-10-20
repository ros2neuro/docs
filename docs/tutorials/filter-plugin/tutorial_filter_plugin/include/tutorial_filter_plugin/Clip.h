#ifndef TUTORIAL_FILTER_PLUGIN_CLIP_H
#define TUTORIAL_FILTER_PLUGIN_CLIP_H

#include "ros2neuro_filters/Filter.h"

namespace ros2neuro {
namespace filters {

// Clips every sample to [-limit, +limit]. Useful to bound the effect of large artifacts
// before the filters that follow in the chain.
template<typename T>
class Clip : public Filter<T> {
  public:
    Clip(void) {
      this->name_ = "clip";
    }

    // Called once, after the parameters of this filter have been loaded.
    bool configure(void) override {
      double limit = 100.0;
      this->getParam("limit", limit);   // keeps the default when the parameter is missing

      if (limit <= 0.0) {
        RCLCPP_ERROR(this->logger_, "[%s] 'limit' must be positive (got %f)", this->name_.c_str(), limit);
        return false;
      }

      this->limit_ = static_cast<T>(limit);
      return true;
    }

    // Called on every frame. Input and output are [samples x channels].
    DynamicMatrix<T> apply(const DynamicMatrix<T>& input) override {
      return input.cwiseMax(-this->limit_).cwiseMin(this->limit_);
    }

  private:
    T limit_ = static_cast<T>(100.0);
};

}  // namespace filters
}  // namespace ros2neuro

#endif  // TUTORIAL_FILTER_PLUGIN_CLIP_H
