#ifndef TUTORIAL_EOG_CHECK_BLINK_DETECTOR_H
#define TUTORIAL_EOG_CHECK_BLINK_DETECTOR_H

#include <cmath>
#include <cstddef>

namespace tutorial {

// Detects eye blinks in a single signal, sample by sample.
//
// A blink is a large, slow deflection that is strongest on the frontal channels (Fp1, Fp2) and has
// the same polarity on both. The detector works on one signal, normally the mean of Fp1 and Fp2.
//
//   1. a slow baseline follows the signal (a one-pole low-pass), and the detector looks at the
//      difference between the signal and that baseline, so drifts and offsets do not matter;
//   2. a blink STARTS when the difference reaches `threshold` (in absolute value: depending on the
//      reference the deflection can be positive or negative);
//   3. the blink ENDS when the difference stays under `threshold * hysteresis` for `release_s`.
//      The release time avoids ending the blink at the first zero-crossing of the waveform.
//
// While a blink is open the baseline is frozen, otherwise it would follow the blink and hide it.
class BlinkDetector {
  public:
    enum class Event { None, Start, End };

    BlinkDetector(double samplerate, double threshold, double hysteresis, double release_s,
                  double baseline_tau_s)
        : threshold_(threshold),
          hysteresis_(hysteresis),
          release_samples_(static_cast<std::size_t>(std::ceil(release_s * samplerate))),
          alpha_(1.0 / (baseline_tau_s * samplerate)) {}

    void set_threshold(double threshold) { this->threshold_ = threshold; }
    bool active(void) const { return this->active_; }

    // Feeds one sample, returns the event it produced, if any.
    Event process(double value) {
        if (!this->initialized_) {          // start from the first value: no initial transient
            this->baseline_ = value;
            this->initialized_ = true;
        }

        const double deviation = std::fabs(value - this->baseline_);

        if (!this->active_) {
            this->baseline_ += this->alpha_ * (value - this->baseline_);
            if (deviation >= this->threshold_) {
                this->active_ = true;
                this->quiet_ = 0;
                return Event::Start;
            }
            return Event::None;
        }

        // blink open: the baseline is frozen
        if (deviation < this->threshold_ * this->hysteresis_) {
            if (++this->quiet_ >= this->release_samples_) {
                this->active_ = false;
                return Event::End;
            }
        } else {
            this->quiet_ = 0;
        }
        return Event::None;
    }

  private:
    double threshold_;
    double hysteresis_;
    std::size_t release_samples_;
    double alpha_;

    double baseline_ = 0.0;
    bool initialized_ = false;
    bool active_ = false;
    std::size_t quiet_ = 0;
};

}  // namespace tutorial

#endif  // TUTORIAL_EOG_CHECK_BLINK_DETECTOR_H
