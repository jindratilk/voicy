#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/ffmpeg-source
if [ ! -f build/ffmpeg-source/ffmpeg-7.1.tar.xz ]; then
  curl --fail --location --retry 3 https://ffmpeg.org/releases/ffmpeg-7.1.tar.xz -o build/ffmpeg-source/ffmpeg-7.1.tar.xz
fi
printf '%s  %s\n' '40973d44970dbc83ef302b0609f2e74982be2d85916dd2ee7472d30678a7abe6' 'build/ffmpeg-source/ffmpeg-7.1.tar.xz' | shasum -a 256 -c -
if [ ! -d build/ffmpeg-source/ffmpeg-7.1 ]; then
  tar -xf build/ffmpeg-source/ffmpeg-7.1.tar.xz -C build/ffmpeg-source
fi
cd build/ffmpeg-source/ffmpeg-7.1
./configure --cc=clang --extra-cflags='-mmacosx-version-min=14.0' --extra-ldflags='-mmacosx-version-min=14.0' --disable-autodetect --disable-network --disable-doc --disable-debug --disable-ffplay --disable-ffprobe --disable-avdevice --disable-postproc --disable-everything --enable-ffmpeg --enable-avcodec --enable-avformat --enable-avfilter --enable-swresample --enable-protocol='file,pipe' --enable-demuxer='wav,mp3,mov,flac,ogg,matroska,aiff,aac' --enable-decoder='pcm_s16le,pcm_s24le,pcm_s32le,pcm_f32le,pcm_s16be,pcm_s24be,pcm_s32be,pcm_f32be,pcm_f64le,pcm_u8,mp3,mp3float,aac,aac_fixed,flac,vorbis,opus,alac' --enable-encoder='pcm_s24le,pcm_f32le,pcm_s16le,aac' --enable-muxer='wav,null,ipod' --enable-filter='aresample,aformat,anull,loudnorm,abuffer,abuffersink' --enable-parser='aac,mpegaudio,opus,flac,vorbis' --disable-shared --enable-static --enable-small
make -j6
