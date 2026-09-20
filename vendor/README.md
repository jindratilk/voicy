# Resemble Enhance inference adaptation

Source: https://github.com/resemble-ai/resemble-enhance
Pinned upstream commit: `8e978149bfe8abab3eb77d965d579a111afdb0ff`.
License: MIT, preserved in RESEMBLE_LICENSE.

Changes for CPU/macOS inference:
- Import model and hyperparameter classes directly, instead of importing the DeepSpeed training entry points.
- Avoid eager training imports in utils; move distributed training imports into their training-only function.
- Skip training visualization when the enhancer is in evaluation mode.
- Pin the Hugging Face model revision and verify SHA-256 checksums. Download into partial files and replace atomically.
- Use weights_only=True when loading model checkpoints.

The neural network architecture and pretrained parameters are unchanged. Clearvoice's own engine handles bounded chunks, fixed-seed inference, cancellation, overlap-add, resampling and export outside this package. Included training source is upstream context, not a supported Clearvoice training environment; use the upstream repository and its dependencies for training.
