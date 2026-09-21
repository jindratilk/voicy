// A single byte range is enough for browser downloads and resumed transfers.
// Unsupported units and multipart requests are ignored, as HTTP allows.
export function parseRange(header, size) {
  if (!header || !/^bytes=/.test(header) || header.includes(",")) return null;
  const match = /^bytes=(\d*)-(\d*)$/.exec(header);
  if (!match || (!match[1] && !match[2])) return null;
  if (!size) return { invalid: true };
  if (!match[1]) {
    const suffix = Number(match[2]);
    if (!Number.isSafeInteger(suffix) || suffix <= 0) return { invalid: true };
    const length = Math.min(suffix, size);
    return { offset: size - length, length };
  }
  const start = Number(match[1]);
  const end = match[2] ? Number(match[2]) : size - 1;
  if (
    !Number.isSafeInteger(start) ||
    !Number.isSafeInteger(end) ||
    start >= size ||
    end < start
  )
    return { invalid: true };
  return { offset: start, length: Math.min(end, size - 1) - start + 1 };
}
