# MossFormer2 SE 48K

Source: ClearVoice 0.1.2 package, from https://github.com/modelscope/ClearerVoice-Studio. Apache-2.0; see MOSSFORMER_LICENSE.

Only the speech-enhancement architecture is included. Removed unused torchinfo import. Extracted the three STFT/filterbank helpers verbatim from utils/misc.py. Application inference, checkpoint verification and chunk handling are in server/mossformer.py.

Weights: https://huggingface.co/alibabasglab/MossFormer2_SE_48K at eff8c97925c8bec812af707814b3e5d777fd4503; SHA-256 03692b9f773bbd6bb43b9c5a41f96b1e28affd66e13796b7bec66ad3d8b227c6.
