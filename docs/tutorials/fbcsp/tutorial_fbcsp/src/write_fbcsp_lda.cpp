// Turns the LDA that train_fbcsp.m trained (a yaml of numbers) into what the decoder node loads: a .r2nd model and its manifest.yaml.
//
//   ros2 run tutorial_fbcsp write_fbcsp_lda fbcsp_lda.yaml model_folder
#include <cstdint>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include <yaml-cpp/yaml.h>

#include "ros2neuro_decoder_lda/LDAModel.h"
#include "ros2neuro_msgs/msg/neuro_feature.hpp"
#include "ros2neuro_msgs/msg/neuro_prediction.hpp"

namespace {
std::string list(const std::vector<std::string>& v, bool quote) {
    std::string out = "[";
    for (std::size_t i = 0; i < v.size(); ++i) out += (i ? ", " : "") + (quote ? "\"" + v[i] + "\"" : v[i]);
    return out + "]";
}
}  // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: write_fbcsp_lda <fbcsp_lda.yaml> <model_folder>\n";
        return 1;
    }
    try {
        const YAML::Node in = YAML::LoadFile(argv[1]);
        const auto labels = in["component_labels"].as<std::vector<std::string>>();
        const auto centres = in["band_centres"].as<std::vector<float>>();
        const auto classes = in["classes"].as<std::vector<std::string>>();
        const std::string name = in["name"].as<std::string>("fbcsp_lda");
        const std::string unit = in["unit"].as<std::string>("ln(uV2)");

        ros2neuro::decoder::LDAModel model;
        model.decoder_name = name;
        model.decoder_subject = in["subject"].as<std::string>("tutorial");
        model.decoder_type = "ros2neuro::decoder::LDA";
        model.parameterization = "linear_discriminants";
        model.training.priors.assign(classes.size(), 1.0F / static_cast<float>(classes.size()));
        model.training.regularization = {"shrinkage", true, in["shrinkage"].as<float>(0.1F)};
        model.training.solver = "matlab_train_fbcsp";
        model.training.source = in["source"].as<std::string>("train_fbcsp.m");
        model.feature_name = in["feature_name"].as<std::string>("fbcsp");
        model.feature_unit = unit;
        model.feature_type = ros2neuro_msgs::msg::NeuroFeature::TYPE_SPECTRUM;
        model.output_type = ros2neuro_msgs::msg::NeuroPrediction::TYPE_PROBABILITIES;
        model.channel_labels = labels;
        model.frequency_values = centres;
        model.classes = classes;
        // every cell [component, band] is a feature, in the order component-major (the order of the data of the NeuroFeature)
        std::vector<std::string> sel_channels, sel_freqs;
        for (std::uint32_t k = 0; k < labels.size(); ++k) {
            for (std::uint32_t b = 0; b < centres.size(); ++b) {
                model.selection.push_back({k, b});
                sel_channels.push_back(labels[k]);
                sel_freqs.push_back(YAML::Dump(YAML::Node(centres[b])));
            }
        }
        for (const auto& row : in["weights"]) for (const auto& w : row) model.weights.push_back(w.as<float>());
        model.bias = in["bias"].as<std::vector<float>>();
        if (model.weights.size() != classes.size() * model.selection.size() || model.bias.size() != classes.size()) {
            throw std::runtime_error("weights must be classes x (components * bands) and bias one per class");
        }

        const std::filesystem::path folder = argv[2];
        std::filesystem::create_directories(folder);
        ros2neuro::decoder::write_r2nd_lda(folder / (name + ".r2nd"), model);

        std::ofstream m(folder / "manifest.yaml");
        std::vector<std::string> freq_text, class_text = classes;
        for (const float f : centres) freq_text.push_back(YAML::Dump(YAML::Node(f)));
        m << "decoder:\n    name: " << name << "\n    subject: " << model.decoder_subject
          << "\n    type: ros2neuro::decoder::LDA\n    path: " << name << ".r2nd\n\n"
          << "input:\n    name: " << model.feature_name << "\n    type: NeuroFeature::TYPE_SPECTRUM\n    unit: " << unit
          << "\n    order: row_major\n    axes:\n        - name: channels\n          labels: " << list(labels, true)
          << "\n        - name: frequency\n          unit: Hz\n          values: " << list(freq_text, false) << "\n\n"
          << "features:\n    mode: selection\n    selection:\n        channels: " << list(sel_channels, true)
          << "\n        frequencies: " << list(sel_freqs, false) << "\n\n"
          << "output:\n    fields: " << list(class_text, false) << "\n    type: NeuroPrediction::TYPE_PROBABILITIES\n";
        std::cout << "wrote " << (folder / (name + ".r2nd")).string() << " and " << (folder / "manifest.yaml").string() << "\n";
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
    return 0;
}
