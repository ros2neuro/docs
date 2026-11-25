#include <cmath>
#include <vector>

#include "gtest/gtest.h"

#include "tutorial_band_power/BandPower.h"

using tutorial::BandPower;

namespace {
constexpr double kPi = 3.14159265358979323846;
}

// a constant of amplitude 3 has a mean square of 9: the band power is ln(9)
TEST(BandPower, ConstantSignal) {
    BandPower bp(1, 8);
    const float x = 3.0F;
    for (int i = 0; i < 8; ++i) bp.push(&x);
    EXPECT_TRUE(bp.ready());
    EXPECT_NEAR(bp.value()[0], std::log(9.0), 1e-5);
}

// a sine of amplitude A has mean square A^2 / 2 over a whole number of periods
TEST(BandPower, SineOfAmplitudeA) {
    const std::size_t window = 512;           // one second at 512 Hz
    BandPower bp(1, window);
    for (std::size_t i = 0; i < window * 3; ++i) {
        const float x = static_cast<float>(10.0 * std::sin(2.0 * kPi * 8.0 * static_cast<double>(i) / 512.0));   // 8 Hz, A = 10
        bp.push(&x);
    }
    EXPECT_NEAR(bp.value()[0], std::log(50.0), 1e-3);   // 10^2 / 2
}

// the window forgets: after `window` quiet samples the loud ones no longer count
TEST(BandPower, WindowForgetsOldSamples) {
    BandPower bp(1, 4);
    const float loud = 100.0F;
    const float quiet = 1.0F;
    for (int i = 0; i < 4; ++i) bp.push(&loud);
    const float with_loud = bp.value()[0];
    for (int i = 0; i < 4; ++i) bp.push(&quiet);
    EXPECT_GT(with_loud, bp.value()[0]);
    EXPECT_NEAR(bp.value()[0], std::log(1.0), 1e-5);
}

// the channels are independent
TEST(BandPower, ChannelsAreIndependent) {
    BandPower bp(2, 4);
    const float x[2] = {2.0F, 5.0F};
    for (int i = 0; i < 4; ++i) bp.push(x);
    const auto v = bp.value();
    EXPECT_NEAR(v[0], std::log(4.0), 1e-5);
    EXPECT_NEAR(v[1], std::log(25.0), 1e-5);
}

// not ready until the window is full; silence gives a finite number, not -inf
TEST(BandPower, WarmUpAndSilence) {
    BandPower bp(1, 4);
    EXPECT_FALSE(bp.ready());
    EXPECT_TRUE(std::isfinite(bp.value()[0]));
    const float zero = 0.0F;
    for (int i = 0; i < 4; ++i) bp.push(&zero);
    EXPECT_TRUE(bp.ready());
    EXPECT_TRUE(std::isfinite(bp.value()[0]));
}

TEST(BandPower, RejectsEmptyShapes) {
    EXPECT_THROW(BandPower(0, 4), std::invalid_argument);
    EXPECT_THROW(BandPower(1, 0), std::invalid_argument);
}
