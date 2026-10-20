#include <cmath>
#include <vector>

#include "gtest/gtest.h"

#include "tutorial_eog_check/BlinkDetector.h"

using tutorial::BlinkDetector;

namespace {

constexpr double kRate = 512.0;

// A Gaussian blink of the given amplitude centred at `center_s`, sampled for `duration_s`.
std::vector<double> signal_with_blink(double amplitude, double center_s, double duration_s, double offset = 0.0) {
    std::vector<double> x;
    for (std::size_t n = 0; n < static_cast<std::size_t>(duration_s * kRate); ++n) {
        const double t = static_cast<double>(n) / kRate;
        x.push_back(offset + amplitude * std::exp(-0.5 * std::pow((t - center_s) / 0.07, 2.0)));
    }
    return x;
}

struct Counts {
    int starts = 0;
    int ends = 0;
};

Counts run(BlinkDetector& detector, const std::vector<double>& signal) {
    Counts counts;
    for (const double value : signal) {
        const auto event = detector.process(value);
        counts.starts += event == BlinkDetector::Event::Start;
        counts.ends += event == BlinkDetector::Event::End;
    }
    return counts;
}

}  // namespace

TEST(BlinkDetectorTest, OneBlinkGivesOneStartAndOneEnd) {
    BlinkDetector detector(kRate, 80.0, 0.5, 0.15, 2.0);
    const auto counts = run(detector, signal_with_blink(150.0, 1.0, 2.0));

    EXPECT_EQ(counts.starts, 1);
    EXPECT_EQ(counts.ends, 1);
    EXPECT_FALSE(detector.active());
}

TEST(BlinkDetectorTest, ASmallDeflectionIsNotABlink) {
    BlinkDetector detector(kRate, 80.0, 0.5, 0.15, 2.0);
    const auto counts = run(detector, signal_with_blink(40.0, 1.0, 2.0));

    EXPECT_EQ(counts.starts, 0);
    EXPECT_EQ(counts.ends, 0);
}

TEST(BlinkDetectorTest, ANegativeBlinkIsDetectedToo) {
    BlinkDetector detector(kRate, 80.0, 0.5, 0.15, 2.0);
    const auto counts = run(detector, signal_with_blink(-150.0, 1.0, 2.0));

    EXPECT_EQ(counts.starts, 1);
    EXPECT_EQ(counts.ends, 1);
}

TEST(BlinkDetectorTest, AConstantOffsetIsIgnored) {
    BlinkDetector detector(kRate, 80.0, 0.5, 0.15, 2.0);
    // the signal starts at 5000 uV: the baseline must start there, without a false blink
    const auto counts = run(detector, signal_with_blink(150.0, 1.0, 2.0, 5000.0));

    EXPECT_EQ(counts.starts, 1);
    EXPECT_EQ(counts.ends, 1);
}

TEST(BlinkDetectorTest, TwoBlinksGiveTwoEvents) {
    BlinkDetector detector(kRate, 80.0, 0.5, 0.15, 2.0);
    auto first = signal_with_blink(150.0, 1.0, 2.0);
    const auto second = signal_with_blink(150.0, 1.0, 2.0);
    first.insert(first.end(), second.begin(), second.end());

    const auto counts = run(detector, first);
    EXPECT_EQ(counts.starts, 2);
    EXPECT_EQ(counts.ends, 2);
}
