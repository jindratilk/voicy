"""Exact-arithmetic inference work reuse for the pinned AuK MLX model.

No weights, timesteps, precision or attention operations are changed. The
upstream MIT-licensed forward path is retained, with identical input embeddings
computed once and reference embeddings reused only within one sampling call.
"""


def install_embedding_reuse():
    import mlx.core as mx
    from auk_mlx import infer
    from auk_mlx.dit import Flux2Edit

    class ReuseFlux2Edit(Flux2Edit):
        def clear_cache(self):
            super().clear_cache()
            self._reference_source = None
            self._reference_pair = None

        def __call__(self, x, text, t, ref=None, cfg_infer=False, cache=True):
            temb = self.time_embed(t)
            has_ref = ref is not None and ref.shape[1] > 0
            # Both CFG branches receive precisely the same noisy target.
            x_emb = self.audio_embed(x)
            prompt_len = 0
            if has_ref:
                if (cache and getattr(self, '_reference_source', None) is ref
                        and (not cfg_infer or self._reference_pair[1] is not None)):
                    ref_cond, ref_uncond = self._reference_pair
                else:
                    ref_cond = self.audio_embed(ref)
                    ref_uncond = self.audio_embed(mx.zeros_like(ref)) if cfg_infer else None
                    if cache:
                        self._reference_source = ref
                        self._reference_pair = (ref_cond, ref_uncond)
                prompt_len = ref_cond.shape[1]
                x_cond = mx.concatenate([ref_cond, x_emb], axis=1)
                x_uncond = mx.concatenate([ref_uncond, x_emb], axis=1) if cfg_infer else None
            else:
                x_cond = x_uncond = x_emb
            if cfg_infer:
                if cache and self._text_cond is not None:
                    c_cond, c_uncond = self._text_cond, self._text_uncond
                else:
                    c_cond = self.project_text(text, drop_text=False)
                    c_uncond = self.project_text(text, drop_text=True)
                    if cache:
                        self._text_cond, self._text_uncond = c_cond, c_uncond
                h = mx.concatenate([x_cond, x_uncond], axis=0)
                c = mx.concatenate([c_cond, c_uncond], axis=0)
                temb = mx.concatenate([temb, temb], axis=0)
            else:
                c = self.project_text(text, drop_text=False)
                h = x_cond
            for block in self.transformer_blocks:
                c, h = block(h, c, temb, self.rope)
            text_len = c.shape[1]
            h = mx.concatenate([c, h], axis=1)
            for block in self.single_transformer_blocks:
                h = block(h, temb, self.rope)
            h = h[:, text_len + prompt_len:]
            return self.proj_out(self.norm_out(h, temb))

    infer.Flux2Edit = ReuseFlux2Edit
