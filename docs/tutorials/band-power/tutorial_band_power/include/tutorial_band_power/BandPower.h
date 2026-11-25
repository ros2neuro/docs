// The power of a band: square, average over a window, logarithm. No ROS in this file.
#pragma once

#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <vector>

namespace tutorial {

// The input is a signal that is ALREADY band-passed (by the filter chain): this class only measures how much of it there is.
// It keeps one moving average per channel, over the last `window` samples.
class BandPower {
  public:
    // --8<-- [start:constructor]
    BandPower(std::size_t channels, std::size_t window)
        : channels_(channels), window_(window), squares_(channels * window, 0.0), sum_(channels, 0.0) {
        if (channels == 0U || window == 0U) {
            throw std::invalid_argument("BandPower: channels and window must be positive");
        }
    }
    // --8<-- [end:constructor]

    // --8<-- [start:push]
    // One sample of every channel (x has `channels` values). The oldest square leaves the window, the new one enters.
    void push(const float* x) {
        for (std::size_t c = 0; c < channels_; ++c) {
            const double square = static_cast<double>(x[c]) * static_cast<double>(x[c]);   // 1. square
            double& slot = squares_[position_ * channels_ + c];
            sum_[c] += square - slot;                                                       // 2. moving sum: add the new, drop the oldest
            slot = square;
        }
        position_ = (position_ + 1U) % window_;                                             // the ring buffer moves on
        if (filled_ < window_) {
            ++filled_;
        }
    }
    // --8<-- [end:push]

    // --8<-- [start:value]
    // The band power of every channel: the logarithm of the mean square of the window.
    std::vector<float> value() const {
        std::vector<float> out(channels_);
        for (std::size_t c = 0; c < channels_; ++c) {
            const double mean = filled_ == 0U ? 0.0 : sum_[c] / static_cast<double>(filled_);   // 3. average
            out[c] = static_cast<float>(std::log(mean + kFloor));                                // 4. logarithm
        }
        return out;
    }
    // --8<-- [end:value]

    // true when the window is full: before that the average is made of fewer samples
    bool ready() const { return filled_ == window_; }

  private:
    static constexpr double kFloor = 1e-12;   // the logarithm of 0 is minus infinity: never take it

    std::size_t channels_;
    std::size_t window_;
    std::vector<double> squares_;   // ring buffer, sample-major like the frame: [position * channels + channel]
    std::vector<double> sum_;       // the sum of the squares in the window, per channel
    std::size_t position_ = 0;
    std::size_t filled_ = 0;
};

}  // namespace tutorial
