#include "tutorial_robot_control/robot_commands.hpp"

#include <algorithm>

namespace tutorial {
namespace control {

const char* command_name(int command) {
    switch (command) {
        case kStop:      return "STOP";
        case kForward:   return "FORWARD";
        case kTurnLeft:  return "TURN_LEFT";
        case kTurnRight: return "TURN_RIGHT";
        default:         return "UNKNOWN";
    }
}

int command_for(const std::vector<float>& values, const std::vector<int>& commands, double threshold) {
    if (values.empty() || values.size() != commands.size())
        return kStop;
    const auto best = std::max_element(values.begin(), values.end());
    if (*best < static_cast<float>(threshold))
        return kStop;
    return commands[static_cast<std::size_t>(best - values.begin())];
}

}  // namespace control
}  // namespace tutorial
