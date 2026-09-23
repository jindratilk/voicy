// Pinned C ABI for the same pinned ATen log-mel operations.
// Arithmetic follows HF WhisperFeatureExtractor.
#include <ATen/ATen.h>
#include <c10/core/InferenceMode.h>
#include <cstring>
#include <cstdio>

extern "C" int voicy_logmel(const float* samples, const float* filters,
                            float* output, char* error, int error_capacity) {
  try {
    c10::InferenceMode guard(true);
    auto options = at::TensorOptions().dtype(at::kFloat).device(at::kCPU);
    auto waveform = at::zeros({1, 4800000}, options);
    std::memcpy(waveform.data_ptr<float>(), samples, 192000 * sizeof(float));
    auto window = at::hann_window(400, options);
    auto transform = at::stft(waveform, 400, 160, 400, window,
                              true, "reflect", false, true, true);
    auto power = transform.slice(-1, 0, transform.size(-1) - 1).abs().pow(2);
    auto filter = at::from_blob(const_cast<float*>(filters), {201, 128}, options);
    auto mel = at::matmul(filter.transpose(0, 1), power);
    auto logarithm = mel.clamp_min(1e-10).log10();
    auto maximum = std::get<0>(std::get<0>(logarithm.max(2, true)).max(1, true));
    auto result = ((at::maximum(logarithm, maximum - 8.) + 4.) / 4.).contiguous();
    std::memcpy(output, result.data_ptr<float>(), 128 * 30000 * sizeof(float));
    return 0;
  } catch (const std::exception& failure) {
    if (error_capacity > 0) std::snprintf(error, error_capacity, "%s", failure.what());
    return 1;
  }
}
