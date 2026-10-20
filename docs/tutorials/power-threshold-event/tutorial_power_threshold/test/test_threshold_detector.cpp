#include <cmath>
#include <vector>

#include "gtest/gtest.h"

#include "tutorial_power_threshold/ThresholdDetector.h"

using tutorial::ThresholdDetector;

TEST(ChannelPowerTest, ReadsTheRightChannelOfASampleMajorBlock) {
    // 2 channels, 4 samples, sample-major: channel 0 is constant, channel 1 alternates +-1
    const std::vector<float> data = {5.0F, 1.0F,
                                     5.0F, -1.0F,
                                     5.0F, 1.0F,
                                     5.0F, -1.0F};

    EXPECT_NEAR(tutorial::channel_power(data, 4, 2, 0), 0.0F, 1e-6F);   // the offset is not power
    EXPECT_NEAR(tutorial::channel_power(data, 4, 2, 1), 1.0F, 1e-6F);
}

TEST(ChannelPowerTest, IsTheVarianceOfASine) {
    const std::size_t samples = 512;
    std::vector<float> data(samples);
    for (std::size_t s = 0; s < samples; ++s) {
        data[s] = 10.0F * std::sin(2.0F * 3.14159265F * 8.0F * static_cast<float>(s) / 512.0F);
    }
    // power of a sine of amplitude A is A^2 / 2
    EXPECT_NEAR(tutorial::channel_power(data, samples, 1, 0), 50.0F, 0.1F);
}

TEST(ChannelPowerTest, InvalidInputGivesZero) {
    EXPECT_FLOAT_EQ(tutorial::channel_power({}, 0, 1, 0), 0.0F);
    EXPECT_FLOAT_EQ(tutorial::channel_power({1.0F, 2.0F}, 2, 1, 3), 0.0F);
}

TEST(ThresholdDetectorTest, RisesOnceAndFallsOnceWithHysteresis) {
    ThresholdDetector detector(100.0, 0.8);

    EXPECT_EQ(detector.update({10.0F}).type, ThresholdDetector::Type::None);
    EXPECT_EQ(detector.update({120.0F}).type, ThresholdDetector::Type::Rising);
    EXPECT_TRUE(detector.above());

    // still above, and dipping below the threshold but not below threshold * hysteresis (80)
    EXPECT_EQ(detector.update({150.0F}).type, ThresholdDetector::Type::None);
    EXPECT_EQ(detector.update({90.0F}).type, ThresholdDetector::Type::None);

    EXPECT_EQ(detector.update({70.0F}).type, ThresholdDetector::Type::Falling);
    EXPECT_FALSE(detector.above());
}

TEST(ThresholdDetectorTest, AnyChannelRaisesAndAllMustFallBack) {
    ThresholdDetector detector(100.0, 0.5);

    const auto rise = detector.update({10.0F, 200.0F, 30.0F});
    EXPECT_EQ(rise.type, ThresholdDetector::Type::Rising);
    EXPECT_EQ(rise.channel, 1U);                    // the strongest one is reported
    EXPECT_FLOAT_EQ(rise.power, 200.0F);

    // channel 1 went quiet but channel 2 is still above the falling level (50)
    EXPECT_EQ(detector.update({10.0F, 10.0F, 60.0F}).type, ThresholdDetector::Type::None);
    EXPECT_EQ(detector.update({10.0F, 10.0F, 20.0F}).type, ThresholdDetector::Type::Falling);
}

TEST(ThresholdDetectorTest, TheThresholdCanChangeAtRuntime) {
    ThresholdDetector detector(100.0, 0.8);
    EXPECT_EQ(detector.update({50.0F}).type, ThresholdDetector::Type::None);

    detector.set_threshold(40.0);
    EXPECT_EQ(detector.update({50.0F}).type, ThresholdDetector::Type::Rising);
}
