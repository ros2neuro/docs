#include <gtest/gtest.h>

#include "tutorial_robot_control/robot_commands.hpp"

using namespace tutorial::control;

TEST(RobotCommands, TheClassOverTheThresholdGivesItsCommand) {
    EXPECT_EQ(command_for({0.8f, 0.2f}, {kForward, kTurnLeft}, 0.7), kForward);
    EXPECT_EQ(command_for({0.1f, 0.9f}, {kForward, kTurnLeft}, 0.7), kTurnLeft);
}

TEST(RobotCommands, UnderTheThresholdTheRobotStops) {
    EXPECT_EQ(command_for({0.6f, 0.4f}, {kForward, kTurnLeft}, 0.7), kStop);
    EXPECT_EQ(command_for({0.5f, 0.5f}, {kForward, kTurnLeft}, 0.7), kStop);
}

TEST(RobotCommands, TheThresholdIsInclusive) {
    EXPECT_EQ(command_for({0.7f, 0.3f}, {kForward, kTurnLeft}, 0.7), kForward);
}

TEST(RobotCommands, ThreeClassesThreeCommands) {
    EXPECT_EQ(command_for({0.1f, 0.1f, 0.8f}, {kForward, kTurnLeft, kTurnRight}, 0.7), kTurnRight);
}

TEST(RobotCommands, AnUnexpectedPredictionStopsTheRobot) {
    EXPECT_EQ(command_for({}, {kForward}, 0.7), kStop);                         // nothing
    EXPECT_EQ(command_for({0.9f, 0.05f, 0.05f}, {kForward, kTurnLeft}, 0.7), kStop);   // other number of classes
}

TEST(RobotCommands, TheCommandsHaveANameForTheLog) {
    EXPECT_STREQ(command_name(kForward), "FORWARD");
    EXPECT_STREQ(command_name(kStop), "STOP");
    EXPECT_STREQ(command_name(42), "UNKNOWN");
}
