#include <gtest/gtest.h>

#include <cmath>
#include <vector>

#include "tutorial_fbcsp/FbcspBank.h"

using tutorial::Band;
using tutorial::FbcspBank;
using tutorial::IirSection;

namespace {
const IirSection kIdentity{{1.0}, {1.0}};

Band band(std::vector<IirSection> sections, std::vector<double> w) { return Band{std::move(sections), std::move(w)}; }

constexpr double kPi = 3.14159265358979323846;
}  // namespace

TEST(FbcspBank, IdentityGivesLogOfMeanSquare) {
    FbcspBank bank({band({kIdentity}, {1.0})}, 1, 1, 4);
    const std::vector<double> x{1.0, 2.0, 3.0, 4.0};
    bank.push(x.data(), x.size());
    ASSERT_TRUE(bank.ready());
    EXPECT_NEAR(bank.features()[0], std::log((1.0 + 4.0 + 9.0 + 16.0) / 4.0), 1e-6);
}

TEST(FbcspBank, NotReadyBeforeAFullWindow) {
    FbcspBank bank({band({kIdentity}, {1.0})}, 1, 1, 8);
    const std::vector<double> x(7, 1.0);
    bank.push(x.data(), x.size());
    EXPECT_FALSE(bank.ready());
    bank.push(x.data(), 1);
    EXPECT_TRUE(bank.ready());
}

TEST(FbcspBank, IirSectionIsTheDifferenceEquation) {
    // y[n] = x[n] - x[n-1] + 0.5 y[n-1]: b = {1, -1}, a = {1, -0.5}, as MATLAB's filter(b, a, x)
    const IirSection section{{1.0, -1.0}, {1.0, -0.5}};
    const std::vector<double> x{1.0, 0.0, 2.0, -1.0, 0.5, 3.0};
    std::vector<double> y(x.size());
    double xp = 0.0, yp = 0.0;
    for (std::size_t n = 0; n < x.size(); ++n) { y[n] = x[n] - xp + 0.5 * yp; xp = x[n]; yp = y[n]; }
    double mean = 0.0;
    for (const double v : y) mean += v * v / static_cast<double>(y.size());

    FbcspBank bank({band({section}, {1.0})}, 1, 1, x.size());
    bank.push(x.data(), x.size());
    EXPECT_NEAR(bank.features()[0], std::log(mean), 1e-6);
}

TEST(FbcspBank, SpatialFilterMixesChannels) {
    // two channels, one component = ch0 + ch1: a constant (1, 1) becomes 2, mean square 4
    FbcspBank bank({band({kIdentity}, {1.0, 1.0})}, 2, 1, 4);
    const std::vector<double> x{1, 1, 1, 1, 1, 1, 1, 1};
    bank.push(x.data(), 4);
    EXPECT_NEAR(bank.features()[0], std::log(4.0), 1e-6);
}

TEST(FbcspBank, SineHasVarianceHalfTheSquaredAmplitude) {
    const std::size_t window = 512;
    FbcspBank bank({band({kIdentity}, {1.0})}, 1, 1, window);
    std::vector<double> x(window);
    for (std::size_t n = 0; n < window; ++n) x[n] = 3.0 * std::sin(2.0 * kPi * 8.0 * static_cast<double>(n) / 512.0);   // 8 full periods
    bank.push(x.data(), x.size());
    EXPECT_NEAR(bank.features()[0], std::log(4.5), 1e-6);
}

TEST(FbcspBank, FeaturesAreComponentMajor) {
    // two bands, two components, one channel: component k of band b is scaled by (b + 1) * (k + 1)
    Band b1 = band({kIdentity}, {1.0, 2.0});
    Band b2 = band({kIdentity}, {3.0, 4.0});
    FbcspBank bank({b1, b2}, 1, 2, 1);
    const std::vector<double> x{1.0};
    bank.push(x.data(), 1);
    const auto f = bank.features();                     // [component, band]: index = component * bands + band
    ASSERT_EQ(f.size(), 4U);
    EXPECT_NEAR(f[0], std::log(1.0), 1e-6);             // component 0, band 0
    EXPECT_NEAR(f[1], std::log(9.0), 1e-6);             // component 0, band 1
    EXPECT_NEAR(f[2], std::log(4.0), 1e-6);             // component 1, band 0
    EXPECT_NEAR(f[3], std::log(16.0), 1e-6);            // component 1, band 1
}

TEST(FbcspBank, TheSizeOfTheFramesDoesNotMatter) {
    const IirSection lp{{0.2, 0.2}, {1.0, -0.6}};
    std::vector<double> x(1000);
    for (std::size_t n = 0; n < x.size(); ++n) x[n] = std::sin(0.05 * static_cast<double>(n)) + 0.3 * std::cos(0.9 * static_cast<double>(n));
    FbcspBank a({band({lp}, {1.0})}, 1, 1, 128), b({band({lp}, {1.0})}, 1, 1, 128);
    a.push(x.data(), x.size());
    for (std::size_t n = 0; n < x.size(); n += 32) b.push(x.data() + n, std::min<std::size_t>(32, x.size() - n));
    EXPECT_NEAR(a.features()[0], b.features()[0], 1e-9);
}

TEST(FbcspBank, RunningSumDoesNotDrift) {
    // after many windows the value is still the mean square of the last window
    const std::size_t window = 64;
    std::vector<double> x(window * 200);
    for (std::size_t n = 0; n < x.size(); ++n) x[n] = 1000.0 * std::sin(0.31 * static_cast<double>(n)) + 1e-3 * static_cast<double>(n % 7);
    FbcspBank bank({band({kIdentity}, {1.0})}, 1, 1, window);
    bank.push(x.data(), x.size());
    double mean = 0.0;
    for (std::size_t n = x.size() - window; n < x.size(); ++n) mean += x[n] * x[n] / static_cast<double>(window);
    // the feature is a float: at 13 one ULP is 1e-6, so 2e-6 is two ULP. A drift of the running sum would show as much more.
    EXPECT_NEAR(bank.features()[0], std::log(mean), 2e-6);
}

TEST(FbcspBank, ABadSpatialFilterIsRefused) {
    EXPECT_THROW(FbcspBank({band({kIdentity}, {1.0, 1.0, 1.0})}, 2, 1, 4), std::invalid_argument);
    EXPECT_THROW(FbcspBank({band({IirSection{{1.0}, {2.0}}}, {1.0})}, 1, 1, 4), std::invalid_argument);
}
