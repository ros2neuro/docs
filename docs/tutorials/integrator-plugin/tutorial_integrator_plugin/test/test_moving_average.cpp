#include "gtest/gtest.h"
#include "rclcpp/rclcpp.hpp"

#include "tutorial_integrator_plugin/MovingAverage.h"

namespace {

ros2neuro_msgs::msg::NeuroPrediction make_prediction(float a, float b) {
  ros2neuro_msgs::msg::NeuroPrediction prediction;
  prediction.fields = {"773", "771"};
  prediction.values = {a, b};
  prediction.type = ros2neuro_msgs::msg::NeuroPrediction::TYPE_PROBABILITIES;
  return prediction;
}

void configure(tutorial::integrator::MovingAverage& integrator, int window) {
  ros2neuro::integrator::ParameterMap params = {{"window", rclcpp::Parameter("window", window)}};
  ASSERT_TRUE(integrator.configure("avg", "tutorial::integrator::MovingAverage", params,
                                   rclcpp::get_logger("test_moving_average")));
}

}  // namespace

TEST(MovingAverageTest, AveragesTheLastWindowPredictions) {
  tutorial::integrator::MovingAverage integrator;
  configure(integrator, 2);

  integrator.reset(2);
  integrator.apply(make_prediction(1.0F, 0.0F));
  const auto result = integrator.apply(make_prediction(0.0F, 1.0F));   // the neutral sample is gone

  ASSERT_EQ(result.integrated.size(), 2U);
  EXPECT_FLOAT_EQ(result.integrated[0], 0.5F);
  EXPECT_FLOAT_EQ(result.integrated[1], 0.5F);
}

TEST(MovingAverageTest, OldPredictionsLeaveTheWindow) {
  tutorial::integrator::MovingAverage integrator;
  configure(integrator, 2);

  integrator.apply(make_prediction(1.0F, 0.0F));
  integrator.apply(make_prediction(0.0F, 1.0F));
  const auto result = integrator.apply(make_prediction(0.0F, 1.0F));   // the first one is gone

  EXPECT_FLOAT_EQ(result.integrated[0], 0.0F);
  EXPECT_FLOAT_EQ(result.integrated[1], 1.0F);
  EXPECT_EQ(result.decision, 1);
}

TEST(MovingAverageTest, ResetGivesTheNeutralVector) {
  tutorial::integrator::MovingAverage integrator;
  configure(integrator, 4);

  integrator.apply(make_prediction(1.0F, 0.0F));
  const auto result = integrator.reset(2);

  EXPECT_FLOAT_EQ(result.integrated[0], 0.5F);
  EXPECT_FLOAT_EQ(result.integrated[1], 0.5F);
}

TEST(MovingAverageTest, RejectsAnInvalidWindow) {
  tutorial::integrator::MovingAverage integrator;
  ros2neuro::integrator::ParameterMap params = {{"window", rclcpp::Parameter("window", 0)}};
  EXPECT_FALSE(integrator.configure("avg", "tutorial::integrator::MovingAverage", params,
                                    rclcpp::get_logger("test_moving_average")));
}

int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);
  rclcpp::init(argc, argv);
  const int result = RUN_ALL_TESTS();
  rclcpp::shutdown();
  return result;
}
