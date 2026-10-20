#ifndef TUTORIAL_POWER_THRESHOLD_THRESHOLD_DETECTOR_H
#define TUTORIAL_POWER_THRESHOLD_THRESHOLD_DETECTOR_H

#include <cstddef>
#include <vector>

namespace tutorial {

// Power of one channel of a sample-major block: the variance of its samples, in unit^2.
//
// A NeuroSensor stores its data sample by sample: index = sample * channels + channel.
// The mean is removed so that a constant offset does not count as power.
inline float channel_power(const std::vector<float>& data, std::size_t samples, std::size_t channels,
                           std::size_t channel) {
    if (samples == 0U || channels == 0U || channel >= channels || data.size() < samples * channels) {
        return 0.0F;
    }

    double sum = 0.0;
    for (std::size_t s = 0; s < samples; ++s) {
        sum += data[s * channels + channel];
    }
    const double mean = sum / static_cast<double>(samples);

    double squares = 0.0;
    for (std::size_t s = 0; s < samples; ++s) {
        const double d = data[s * channels + channel] - mean;
        squares += d * d;
    }
    return static_cast<float>(squares / static_cast<double>(samples));
}

// Detects when the power of a set of channels crosses a threshold.
//
// The detector has two states, below and above. It goes above when ANY channel reaches the
// threshold, and goes back below only when ALL the channels are under threshold * hysteresis.
// The gap between the two levels stops a power that hovers around the threshold from producing
// a burst of events.
class ThresholdDetector {
  public:
    enum class Type { None, Rising, Falling };

    struct Crossing {
        Type type = Type::None;
        std::size_t channel = 0;   // index (in the list passed to update) of the strongest channel
        float power = 0.0F;        // its power
    };

    ThresholdDetector(double threshold, double hysteresis)
        : threshold_(threshold), hysteresis_(hysteresis) {}

    void set_threshold(double threshold) { this->threshold_ = threshold; }
    void set_hysteresis(double hysteresis) { this->hysteresis_ = hysteresis; }
    bool above(void) const { return this->above_; }

    // One power per selected channel. Returns the crossing produced by this update, if any.
    Crossing update(const std::vector<float>& powers) {
        Crossing result;
        if (powers.empty()) {
            return result;
        }

        std::size_t strongest = 0;
        for (std::size_t k = 1; k < powers.size(); ++k) {
            if (powers[k] > powers[strongest]) {
                strongest = k;
            }
        }
        result.channel = strongest;
        result.power = powers[strongest];

        if (!this->above_ && result.power >= this->threshold_) {
            this->above_ = true;
            result.type = Type::Rising;
        } else if (this->above_ && result.power < this->threshold_ * this->hysteresis_) {
            this->above_ = false;
            result.type = Type::Falling;
        }
        return result;
    }

  private:
    double threshold_;
    double hysteresis_;
    bool above_ = false;
};

}  // namespace tutorial

#endif  // TUTORIAL_POWER_THRESHOLD_THRESHOLD_DETECTOR_H
