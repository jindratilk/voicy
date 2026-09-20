# Third-party notices

Voicy's application code is MIT licensed. This does not replace the licenses of dependencies, model parameters or bundled executables.

| Component | License / source |
| --- | --- |
| Tauri | MIT / Apache-2.0, https://github.com/tauri-apps/tauri |
| React | MIT, https://github.com/facebook/react |
| shadcn/ui and Radix UI | MIT, https://github.com/shadcn-ui/ui and https://github.com/radix-ui/primitives |
| Geist | SIL Open Font License 1.1, https://github.com/vercel/geist-font |
| AuK source and weights | Tencent MIT license, https://github.com/Tencent-Hunyuan/AuK and https://huggingface.co/tencent/AuK |
| Qwen2.5-Omni-3B | Apache-2.0, https://huggingface.co/Qwen/Qwen2.5-Omni-3B |
| MLX | MIT, https://github.com/ml-explore/mlx |
| CPython | Python Software Foundation license, https://www.python.org/psf/license/ |
| FFmpeg 7.1 audio CLI | LGPL 2.1 or later; built without GPL or nonfree modules. https://ffmpeg.org |

The app bundle retains AuK and Qwen license files beside their weights. Python packages retain their distribution metadata and supplied license files. The audio CLI is invoked as a separate process. Its **unmodified corresponding source archive and exact build script** are included in `Contents/Resources/runtime/licenses/ffmpeg/`, with the LGPL text. Source releases also include the build script.

The development tree contains optional older enhancement engines with their upstream notices under `vendor/`. They are not selected by the Voicy interface and are not included in the standalone AuK runtime.

No Adobe code, artwork, model weights or branding is included. The Voicy wave icon is an original SVG drawing.
