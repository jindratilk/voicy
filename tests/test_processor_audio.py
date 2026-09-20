import numpy as np
import pytest
from server.processor_audio import process_mm_info


def test_audio_array_slice_and_no_vision():
    audio = np.arange(48000, dtype=np.float32)
    result, images, videos = process_mm_info([{'content': [
        {'type': 'text', 'text': 'restore'},
        {'type': 'audio', 'audio': audio, 'audio_start': .5, 'audio_end': 1.5},
    ]}])
    np.testing.assert_array_equal(result[0], audio[8000:24000])
    assert images is None and videos is None


def test_rejects_remote_and_video():
    for item in [{'type':'audio','audio':'https://example.com/a.wav'}, {'type':'video','video':'a.mp4'}]:
        with pytest.raises(ValueError):
            process_mm_info([{'content':[item]}])
