#include "gtest/gtest.h"
#include "rclcpp/rclcpp.hpp"

#include "tutorial_filter_plugin/Clip.h"

namespace {

ros2neuro::filters::ParameterMap limit_param(double value) {
  return {{"limit", rclcpp::Parameter("limit", value)}};
}

}  // namespace

TEST(ClipFilterTest, ClipsToTheConfiguredRange) {
  ros2neuro::filters::Clip<float> filter;
  auto& base = static_cast<ros2neuro::filters::Filter<float>&>(filter);
  ASSERT_TRUE(base.configure("clip", "tutorial_filter_plugin/ClipFloat", limit_param(50.0),
                             rclcpp::get_logger("test_clip")));

  ros2neuro::filters::DynamicMatrix<float> input(3, 2);
  input << 10.0F, -200.0F,
           60.0F,   30.0F,
          -55.0F,  500.0F;

  const auto output = filter.apply(input);

  EXPECT_FLOAT_EQ(output(0, 0), 10.0F);
  EXPECT_FLOAT_EQ(output(0, 1), -50.0F);
  EXPECT_FLOAT_EQ(output(1, 0), 50.0F);
  EXPECT_FLOAT_EQ(output(1, 1), 30.0F);
  EXPECT_FLOAT_EQ(output(2, 0), -50.0F);
  EXPECT_FLOAT_EQ(output(2, 1), 50.0F);
}

TEST(ClipFilterTest, RejectsANonPositiveLimit) {
  ros2neuro::filters::Clip<float> filter;
  auto& base = static_cast<ros2neuro::filters::Filter<float>&>(filter);
  EXPECT_FALSE(base.configure("clip", "tutorial_filter_plugin/ClipFloat", limit_param(0.0),
                              rclcpp::get_logger("test_clip")));
}

int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);
  rclcpp::init(argc, argv);
  const int result = RUN_ALL_TESTS();
  rclcpp::shutdown();
  return result;
}
