#!/usr/bin/env python3
"""Prepare/serve a private, label-concealed E03 worksheet; never runs inference.

Standard library only. Audio and the sealed assignment stay outside Git.
The server binds only to IPv4 loopback and has no response-submission API.
"""
import argparse
import hashlib
import hmac
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import random
import secrets
import shutil
from urllib.parse import urlsplit
import wave

VARIANTS = {"reference", "input", "enhanced"}
PROTOCOL = "E03-private-listening-v1"


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def verify_asset(path, expected, frames):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("Missing or unexpectedly large listening asset")
    if digest(path) != expected:
        raise ValueError("Listening asset hash mismatch")
    with wave.open(str(path), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(),
                audio.getnframes()) != (1, 3, 48000, frames):
            raise ValueError("Unexpected listening asset format")


def prepare_packet(results_path, listening_root, seed=None):
    results = json.loads(Path(results_path).read_text())
    root = Path(listening_root).resolve()
    records = json.loads((root / "MANIFEST.json").read_text())["records"]
    if results["runtime"]["version"] != "0.3.2":
        raise ValueError("This protocol is specifically for historical 0.3.2")
    if [case["case"] for case in results["cases"]] != [1, 2, 3, 4, 5]:
        raise ValueError("Preserve the complete five-case set")
    seed = secrets.token_bytes(32) if seed is None else seed
    generator = random.Random(int.from_bytes(seed, "big"))
    public = {"protocol": PROTOCOL, "version": "0.3.2", "cases": []}
    assets = {}
    for case in results["cases"]:
        versions = case["listening_versions"]
        if len(versions) != 3 or {item["variant"] for item in versions} != VARIANTS:
            raise ValueError("Each case needs all three fixed variants")
        order = list(versions)
        generator.shuffle(order)
        clips = []
        for label, item in zip("ABC", order):
            candidates = [r for r in records if r["variant"] == item["variant"]
                          and r["sha256"] == item["sha256"]]
            if len(candidates) != 1:
                raise ValueError("Missing or ambiguous listening-manifest binding")
            path = (root / candidates[0]["path"]).resolve()
            if not path.is_relative_to(root):
                raise ValueError("Asset escapes the listening directory")
            verify_asset(path, item["sha256"], item["frames"])
            clip_id = hmac.new(seed, f'{case["case"]}:{item["variant"]}'.encode(),
                               hashlib.sha256).hexdigest()[:24]
            clips.append({"label": label, "token": clip_id})
            assets[clip_id] = {"path": str(path), "sha256": item["sha256"],
                             "frames": item["frames"], "variant": item["variant"],
                             "case": case["case"]}
        public["cases"].append({"number": case["case"], "clips": clips,
                                "utterance_id": case["utterance_id"],
                                "transcript": case["expected_transcript"]})
    public["id"] = hashlib.sha256(json.dumps(public, sort_keys=True).encode()).hexdigest()[:16]
    return {"public": public, "assets": assets, "assignment_seed": seed.hex(),
            "source_report_sha256": digest(results_path)}


STYLE = """
body{margin:0;background:#101112;color:#ededeb;font:16px/1.55 system-ui,sans-serif}
main{max-width:1040px;margin:auto;padding:32px 20px 64px}h1{font-size:36px;line-height:1.15}
p{max-width:78ch;color:#bfc0bd}a{color:#c9dfd4}section{margin:28px 0;padding:20px;background:#191b1c;border-radius:16px}
.clips{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.clip{min-width:0}
audio,select,textarea{display:block;box-sizing:border-box;width:100%;margin:10px 0}audio{height:44px}
select,textarea{background:#252829;color:#eee;border:1px solid #606565;border-radius:8px;padding:10px;font:inherit}
textarea{min-height:100px}label{display:block}button{font:inherit;padding:12px 20px;border:0;border-radius:24px;cursor:pointer}
.badge{color:#d7c8a0}.preview{padding:12px;border:1px solid #d7c8a0}details{margin:16px 0}summary{cursor:pointer}
:focus-visible{outline:3px solid #94ceb5;outline-offset:3px}input[type=checkbox]{margin-right:8px}
@media(max-width:700px){.clips{grid-template-columns:1fr}main{padding:20px 16px}h1{font-size:30px}}
"""

SCRIPT = """
const preview=new URLSearchParams(location.search).has('preview');
const key=`${packet.id}:${preview?'qa':'review'}`;
let saved={};
try{saved=JSON.parse(localStorage.getItem(key)||'{}')}catch{}
if(preview)document.querySelector('#preview').hidden=false;
const fields=[...document.querySelectorAll('[data-note]')];
for(const field of fields)if(saved[field.id]!==undefined)field.value=saved[field.id];
document.querySelector('#attest').checked=saved.attested===true;
const transcripts={...saved.transcripts};
function persist(){
  const state=Object.fromEntries(fields.map(f=>[f.id,f.value]));
  state.attested=document.querySelector('#attest').checked;state.transcripts=transcripts;
  try{localStorage.setItem(key,JSON.stringify(state))}catch{document.querySelector('#storage').hidden=false}
  const count=[...document.querySelectorAll('select')].filter(f=>f.value!=='not-reviewed').length;
  document.querySelector('#count').textContent=`Notes selected: ${count}/15`;
}
for(const field of fields)field.addEventListener('input',persist);
document.querySelector('#attest').addEventListener('change',persist);
for(const detail of document.querySelectorAll('details[data-case]'))detail.addEventListener('toggle',()=>{
  if(detail.open){transcripts[detail.dataset.case]=true;persist()}
});
for(const audio of document.querySelectorAll('audio'))audio.addEventListener('play',()=>{
  for(const other of document.querySelectorAll('audio'))if(other!==audio)other.pause();
});
document.querySelector('#export').addEventListener('click',()=>{
  const entries=packet.cases.flatMap(c=>c.clips.map(clip=>({case:c.number,clip:clip.token,label:clip.label,
    observation:document.querySelector(`#r-${clip.token}`).value,
    notes:document.querySelector(`#n-${clip.token}`).value,
    transcript_opened:transcripts[c.number]===true})));
  const attested=document.querySelector('#attest').checked;
  const status=preview?'qa_fixture':attested&&entries.every(e=>e.observation!=='not-reviewed')?'self_attested_review':'draft';
  const result={protocol:packet.protocol,packet_id:packet.id,sample_version:packet.version,
    created_utc:new Date().toISOString(),provenance:preview?'qa_fixture':'unverified_self_report',
    status,attested,entries};
  const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download=`${packet.id}-${preview?'qa':'review'}-notes.json`;
  link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
persist();
"""


def render_page(public):
    sections = []
    for case in public["cases"]:
        clips = []
        for clip in case["clips"]:
            token, label = clip["token"], clip["label"]
            clips.append(f'''<div class="clip"><h3>Clip {label}</h3>
<audio controls preload="none" aria-label="Case {case['number']} clip {label}" src="/clips/{token}.wav"></audio>
<label for="r-{token}">Case {case['number']} clip {label}: words and artifacts</label>
<select id="r-{token}" data-note><option value="not-reviewed">Not reviewed</option>
<option value="no-issue-heard">No issue heard</option><option value="possible-issue">Possible issue</option>
<option value="cannot-judge">Cannot judge</option></select>
<label for="n-{token}">Case {case['number']} clip {label}: observations</label>
<textarea id="n-{token}" data-note maxlength="4000"></textarea></div>''')
        sections.append(f'''<section><h2>Case {case['number']}</h2><div class="clips">{''.join(clips)}</div>
<details data-case="{case['number']}"><summary>Reveal source transcript for case {case['number']}</summary>
<p>{html.escape(case['transcript'])}</p><p>Source utterance: {html.escape(case['utterance_id'])}</p></details></section>''')
    data = json.dumps(public).replace("<", "\\u003c")
    script = "const packet=" + data + ";\n" + SCRIPT
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Voicy · Private listening review</title><style>{STYLE}</style><main>
<p class="badge">Private worksheet · historical Voicy 0.3.2 · {public['id']}</p><h1>Check the words. Note the artifacts.</h1>
<p id="preview" class="preview" hidden>QA PREVIEW — test notes, not a human assessment.</p>
<p>Use headphones at a comfortable, fixed volume. Listen to every clip. Note missing or changed words, unnatural texture and other artifacts.
Listen once before revealing the source transcript. Clip labels conceal the three variants; their sound may still reveal them.</p>
<p>These five short English audiobook cases were processed on 15 October 2026. Listening judgments remain unverified.
This worksheet does not calculate a quality score or an Adobe comparison. Audio stays on this Mac; notes stay in this browser until you export them.</p>
<p id="storage" hidden>Browser storage is unavailable. Export notes before closing this page.</p>
{''.join(sections)}<label><input id="attest" type="checkbox">These are my own listening notes after reviewing every clip.</label>
<p id="count" role="status"></p><button id="export">Export notes as JSON</button>
<p>Exported notes are self-reported. Playback and form completion do not establish a human panel, independent review or general audio quality.</p>
<p>LibriSpeech © 2014 Vassil Panayotov · <a href="https://www.openslr.org/12">OpenSLR SLR12</a> ·
<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Full utterances were resampled and normalized,
controlled degradations added to four, then enhanced and separately mastered. No reader endorsement is implied.</p>
</main><script>{script}</script></html>'''
    return page.encode(), script


def make_server(packet, port=54835):
    public, assets = packet["public"], packet["assets"]
    if len(assets) != 15:
        raise ValueError("Expected exactly fifteen listening files")
    for item in assets.values():
        verify_asset(item["path"], item["sha256"], item["frames"])
    body, script = render_page(public)
    import base64
    encoded = lambda value: base64.b64encode(hashlib.sha256(value.encode()).digest()).decode()
    policy = ("default-src 'none'; media-src 'self'; connect-src 'none'; base-uri 'none'; "
              "form-action 'none'; frame-ancestors 'none'; "
              f"style-src 'sha256-{encoded(STYLE)}'; script-src 'sha256-{encoded(script)}'")

    class Handler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.respond(head=True)

        def do_GET(self):
            self.respond()

        def respond(self, head=False):
            actual_port = self.server.server_address[1]
            if self.headers.get("Host") not in {f"127.0.0.1:{actual_port}", f"localhost:{actual_port}"}:
                self.send_error(400)
                return
            path = urlsplit(self.path).path
            item = next((v for k, v in assets.items() if path == f"/clips/{k}.wav"), None)
            if path != "/" and item is None:
                self.send_error(404)
                return
            if item:
                try:
                    verify_asset(item["path"], item["sha256"], item["frames"])
                except (OSError, ValueError, wave.Error):
                    self.send_error(409, "Listening asset changed; restart after verification")
                    return
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav" if item else "text/html; charset=utf-8")
            self.send_header("Content-Length", str(Path(item["path"]).stat().st_size if item else len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", policy)
            self.end_headers()
            if not head:
                try:
                    if item:
                        with Path(item["path"]).open("rb") as source:
                            shutil.copyfileobj(source, self.wfile)
                    else:
                        self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--results", type=Path, required=True)
    prepare.add_argument("--listening-root", type=Path, required=True)
    prepare.add_argument("--packet", type=Path, required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--packet", type=Path, required=True)
    serve.add_argument("--port", type=int, default=54835)
    args = parser.parse_args()
    if args.command == "prepare":
        destination = args.packet.resolve()
        if any((parent / ".git").exists() for parent in destination.parents):
            parser.error("Keep the private assignment packet outside every Git checkout")
        packet = prepare_packet(args.results, args.listening_root)
        with os.fdopen(os.open(args.packet, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as target:
            json.dump(packet, target, indent=2)
            target.write("\n")
        print("Prepared private packet", packet["public"]["id"])
    else:
        if not 0 < args.port < 65536:
            parser.error("Choose a port between 1 and 65535")
        packet = json.loads(args.packet.read_text())
        with make_server(packet, args.port) as server:
            print(f"Private listening review: http://127.0.0.1:{args.port}/", flush=True)
            server.serve_forever()


if __name__ == "__main__":
    main()
