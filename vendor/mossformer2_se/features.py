# Extracted from ClearVoice 0.1.2 utils/misc.py, Apache-2.0.
import torch
import torchaudio

def stft(x, args, center=False, periodic=False, onesided=None):
    """Computes the Short-Time Fourier Transform (STFT) of an audio signal.

    Args:
        x (torch.Tensor): Input audio signal.
        args (Namespace): Configuration arguments containing window type and lengths.
        center (bool): Whether to center the window.

    Returns:
        torch.Tensor: The computed STFT of the input signal.
    """
    win_type = args.win_type
    win_len = args.win_len
    win_inc = args.win_inc
    fft_len = args.fft_len

    # Select window type and create window tensor
    if win_type == 'hamming':
        window = torch.hamming_window(win_len, periodic=periodic).to(x.device)
    elif win_type == 'hanning':
        window = torch.hann_window(win_len, periodic=periodic).to(x.device)
    else:
        print(f"In STFT, {win_type} is not supported!")
        return

    # Compute and return the STFT
    return torch.stft(x, fft_len, win_inc, win_len, center=center, window=window, onesided=onesided, return_complex=False)

def istft(x, args, slen=None, center=False, normalized=False, periodic=False, onesided=None, return_complex=False):
    """Computes the inverse Short-Time Fourier Transform (ISTFT) of a complex spectrogram.

    Args:
        x (torch.Tensor): Input complex spectrogram.
        args (Namespace): Configuration arguments containing window type and lengths.
        slen (int, optional): Length of the output signal.
        center (bool): Whether to center the window.
        normalized (bool): Whether to normalize the output.
        onesided (bool, optional): If True, computes only the one-sided transform.
        return_complex (bool): If True, returns complex output.

    Returns:
        torch.Tensor: The reconstructed audio signal from the spectrogram.
    """
    win_type = args.win_type
    win_len = args.win_len
    win_inc = args.win_inc
    fft_len = args.fft_len

    # Select window type and create window tensor
    if win_type == 'hamming':
        window = torch.hamming_window(win_len, periodic=periodic).to(x.device)
    elif win_type == 'hanning':
        window = torch.hann_window(win_len, periodic=periodic).to(x.device)
    else:
        print(f"In ISTFT, {win_type} is not supported!")
        return

    try:
        # Attempt to compute ISTFT
        output = torch.istft(x, n_fft=fft_len, hop_length=win_inc, win_length=win_len,
                              window=window, center=center, normalized=normalized,
                              onesided=onesided, length=slen, return_complex=False)
    except:
        # Handle potential errors by converting x to a complex tensor
        x_complex = torch.view_as_complex(x)
        output = torch.istft(x_complex, n_fft=fft_len, hop_length=win_inc, win_length=win_len,
                              window=window, center=center, normalized=normalized,
                              onesided=onesided, length=slen, return_complex=False)
    return output

def compute_fbank(audio_in, args):
    """Computes the filter bank features from an audio signal.

    Args:
        audio_in (torch.Tensor): Input audio signal.
        args (Namespace): Configuration arguments containing window length, shift, and sampling rate.

    Returns:
        torch.Tensor: Computed filter bank features.
    """
    frame_length = args.win_len / args.sampling_rate * 1000  # Frame length in milliseconds
    frame_shift = args.win_inc / args.sampling_rate * 1000  # Frame shift in milliseconds

    # Compute and return filter bank features using Kaldi's implementation
    return torchaudio.compliance.kaldi.fbank(audio_in, dither=1.0, frame_length=frame_length,
                                             frame_shift=frame_shift, num_mel_bins=args.num_mels,
                                             sample_frequency=args.sampling_rate, window_type=args.win_type)