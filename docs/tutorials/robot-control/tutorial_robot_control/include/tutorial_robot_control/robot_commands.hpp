#ifndef TUTORIAL_ROBOT_CONTROL_ROBOT_COMMANDS_HPP_
#define TUTORIAL_ROBOT_CONTROL_ROBOT_COMMANDS_HPP_

#include <vector>

namespace tutorial {
namespace control {

// The commands of THIS robot. They are yours: ros2neuro knows nothing about them. A command travels as an integer in the
// `commands` of a NeuroControl, named by the action "robot_command".
enum RobotCommand : int {
    kStop = 0,
    kForward = 1,
    kTurnLeft = 2,
    kTurnRight = 3,
};

const char* command_name(int command);

// The command for one prediction: the class with the highest value, if that value reaches `threshold`, gives its own command
// (`commands[i]` for the i-th value); otherwise the robot stops. A prediction that is not the one this control was configured for
// (a different number of values) also stops it.
int command_for(const std::vector<float>& values, const std::vector<int>& commands, double threshold);

}  // namespace control
}  // namespace tutorial

#endif
