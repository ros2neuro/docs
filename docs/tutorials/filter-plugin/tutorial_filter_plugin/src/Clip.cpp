#include "pluginlib/class_list_macros.hpp"

#include "tutorial_filter_plugin/Clip.h"

namespace ros2neuro {
namespace filters {

// The name used in plugins.xml and in the YAML configuration refers to this concrete type.
using ClipFloat = Clip<float>;

}  // namespace filters
}  // namespace ros2neuro

PLUGINLIB_EXPORT_CLASS(ros2neuro::filters::ClipFloat, ros2neuro::filters::Filter<float>)
