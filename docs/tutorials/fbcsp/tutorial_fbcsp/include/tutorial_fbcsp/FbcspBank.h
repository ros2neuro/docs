#ifndef TUTORIAL_FBCSP_FBCSPBANK_H
#define TUTORIAL_FBCSP_FBCSPBANK_H

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <utility>
#include <vector>

namespace tutorial {

// One IIR section, as MATLAB's filter(b, a, x) gives it: a[0] == 1, y = b0 x + z0, z[i] = b[i+1] x + z[i+1] - a[i+1] y.
// Direct form II transposed, in double, one state per channel: what `filter` does, so the numbers can be compared.
struct IirSection {
    std::vector<double> b;
    std::vector<double> a;
};

// What the training (train_fbcsp.m) leaves for one frequency band.
struct Band {
    std::vector<IirSection> sections;   // applied in order: the band-pass is a high-pass followed by a low-pass
    std::vector<double> w;              // spatial filters, [channels x components], row-major: w[channel * components + component]
};

// Filter bank + CSP + log-variance, with no ROS in it.
//
//   for every band:  x (channels) -> band-pass of every channel -> c = W' x (components) -> ln(mean(c^2)) over the last `window` samples
//
// The features come out as [components, bands], channel-major: index = component * bands + band.
class FbcspBank {
  public:
    FbcspBank(std::vector<Band> bands, std::size_t channels, std::size_t components, std::size_t window)
        : bands_(std::move(bands)), channels_(channels), components_(components), window_(window) {
        if (bands_.empty() || channels_ == 0 || components_ == 0 || window_ == 0) {
            throw std::invalid_argument("bands, channels, components and window must be positive");
        }
        for (const auto& band : bands_) {
            if (band.w.size() != channels_ * components_) {
                throw std::invalid_argument("W of a band must be channels x components");
            }
            for (const auto& s : band.sections) {
                if (s.b.empty() || s.b.size() != s.a.size() || s.a[0] != 1.0) {
                    throw std::invalid_argument("a filter section needs b and a of the same length, with a[0] = 1");
                }
            }
        }
        this->reset();
    }

    void reset() {
        this->state_.assign(this->bands_.size(), {});
        this->squares_.assign(this->bands_.size() * this->components_, std::vector<double>(this->window_, 0.0));
        this->sums_.assign(this->bands_.size() * this->components_, 0.0);
        for (std::size_t b = 0; b < this->bands_.size(); ++b) {
            for (const auto& s : this->bands_[b].sections) {
                this->state_[b].push_back(std::vector<double>(this->channels_ * (s.b.size() - 1), 0.0));
            }
        }
        this->seen_ = 0;
    }

    // `x` holds `samples` samples of `channels` values, sample-major: x[sample * channels + channel].
    void push(const double* x, std::size_t samples) {
        std::vector<double> v(this->channels_), c(this->components_);
        for (std::size_t s = 0; s < samples; ++s) {
            const std::size_t slot = this->seen_ % this->window_;
            for (std::size_t b = 0; b < this->bands_.size(); ++b) {
                for (std::size_t ch = 0; ch < this->channels_; ++ch) {
                    double value = x[s * this->channels_ + ch];
                    for (std::size_t k = 0; k < this->bands_[b].sections.size(); ++k) {
                        value = step(this->bands_[b].sections[k], this->state_[b][k], ch, value);
                    }
                    v[ch] = value;
                }
                for (std::size_t k = 0; k < this->components_; ++k) {
                    double sum = 0.0;
                    for (std::size_t ch = 0; ch < this->channels_; ++ch) {
                        sum += this->bands_[b].w[ch * this->components_ + k] * v[ch];
                    }
                    const std::size_t i = b * this->components_ + k;
                    this->sums_[i] += sum * sum - this->squares_[i][slot];      // running sum over the window
                    this->squares_[i][slot] = sum * sum;
                }
            }
            ++this->seen_;
            if (this->seen_ % this->window_ == 0) {                             // the running sum drifts a little: renew it
                for (std::size_t i = 0; i < this->sums_.size(); ++i) {
                    double sum = 0.0;
                    for (const double q : this->squares_[i]) sum += q;
                    this->sums_[i] = sum;
                }
            }
        }
    }

    bool ready() const { return this->seen_ >= this->window_; }

    // ln of the mean of the squares of every component, [components, bands] channel-major.
    std::vector<float> features() const {
        std::vector<float> out(this->components_ * this->bands_.size());
        for (std::size_t b = 0; b < this->bands_.size(); ++b) {
            for (std::size_t k = 0; k < this->components_; ++k) {
                const double mean = this->sums_[b * this->components_ + k] / static_cast<double>(this->window_);
                out[k * this->bands_.size() + b] = static_cast<float>(std::log(std::max(mean, 1e-12)));
            }
        }
        return out;
    }

    std::size_t bands() const { return this->bands_.size(); }
    std::size_t components() const { return this->components_; }

  private:
    // one sample through one section, for channel `ch` (its state is state[ch * order .. ch * order + order - 1])
    static double step(const IirSection& s, std::vector<double>& state, std::size_t ch, double x) {
        const std::size_t order = s.b.size() - 1;
        double* z = state.data() + ch * order;
        const double y = s.b[0] * x + (order > 0 ? z[0] : 0.0);
        for (std::size_t i = 0; i < order; ++i) {
            z[i] = s.b[i + 1] * x + (i + 1 < order ? z[i + 1] : 0.0) - s.a[i + 1] * y;
        }
        return y;
    }

    std::vector<Band> bands_;
    std::size_t channels_, components_, window_;
    std::vector<std::vector<std::vector<double>>> state_;   // [band][section][channel * order]
    std::vector<std::vector<double>> squares_;              // [band * components + component][window]
    std::vector<double> sums_;
    std::size_t seen_ = 0;
};

}  // namespace tutorial

#endif  // TUTORIAL_FBCSP_FBCSPBANK_H
