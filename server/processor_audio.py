"""Audio-only adapter for AuK's Qwen processor.

Matches qwen-omni-utils' local audio path (librosa, 16 kHz, identical slice
and resampling defaults), without importing video codecs into an audio app.
"""
from pathlib import Path
import numpy as np


def process_mm_info(conversations, use_audio_in_video=False):
    import librosa

    if isinstance(conversations[0], dict):
        conversations = [conversations]
    audios = []
    for conversation in conversations:
        for message in conversation:
            content = message.get('content', [])
            if not isinstance(content, list):
                continue
            for item in content:
                kind = item.get('type')
                if kind in ('image', 'video'):
                    raise ValueError('Voicy accepts audio only.')
                if kind != 'audio':
                    continue
                source = item.get('audio', item.get('audio_url'))
                start, end = item.get('audio_start', 0.0), item.get('audio_end')
                if isinstance(source, np.ndarray):
                    if source.ndim != 1:
                        raise ValueError('Expected mono audio.')
                    audios.append(source[int(16000 * start):None if end is None else int(16000 * end)])
                else:
                    source = str(source)
                    if source.startswith('file://'):
                        source = source[7:]
                    if '://' in source or not Path(source).is_file():
                        raise ValueError('Expected a local audio file.')
                    audios.append(librosa.load(source, sr=16000, offset=start,
                        duration=None if end is None else end - start)[0])
    return audios or None, None, None
