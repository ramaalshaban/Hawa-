#!/usr/bin/env python3
"""Run one CPU inference per model. Prints model ID + elapsed seconds per step.

Expected: data/smoke.wav is audible Arabic and Whisper returns roughly the same sentence.

Usage: python scripts/smoke_test.py [--skip-optional]
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("HF_HOME", str(ROOT / "data" / "cache" / "hf"))

SENTENCE = "مرحبا بكم في إذاعة هواء، الجو اليوم حار جدا"
WAV = ROOT / "data" / "smoke.wav"

results = []


def step(model_id, fn):
    t0 = time.time()
    try:
        out = fn()
        dt = time.time() - t0
        print(f"OK   {model_id}  {dt:.1f}s  {out}")
        results.append((model_id, True))
    except Exception as e:
        print(f"FAIL {model_id}  {time.time() - t0:.1f}s  {type(e).__name__}: {e}")
        results.append((model_id, False))


def tts(mid):
    import scipy.io.wavfile as wavfile
    import torch
    from transformers import AutoTokenizer, VitsModel

    tok = AutoTokenizer.from_pretrained(mid)
    model = VitsModel.from_pretrained(mid)
    with torch.no_grad():
        wav = model(**tok(SENTENCE, return_tensors="pt")).waveform[0].numpy()
    WAV.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(WAV, model.config.sampling_rate, wav)
    return f"wrote {WAV} ({len(wav) / model.config.sampling_rate:.1f}s audio)"


def asr(mid):
    from faster_whisper import WhisperModel

    model = WhisperModel(mid, device="cpu", compute_type="int8")
    segs, _ = model.transcribe(str(WAV), language="ar")
    return "heard: " + " ".join(s.text.strip() for s in segs)


def vad():
    import soundfile as sf
    import torch
    from silero_vad import get_speech_timestamps, load_silero_vad

    # Read with soundfile (silero's read_audio needs torchaudio). Silero wants 16 kHz mono.
    audio, sr = sf.read(str(WAV), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        from scipy.signal import resample_poly
        from math import gcd

        g = gcd(sr, 16000)
        audio = resample_poly(audio, 16000 // g, sr // g).astype("float32")
    ts = get_speech_timestamps(torch.from_numpy(audio), load_silero_vad(), sampling_rate=16000)
    return f"{len(ts)} speech span(s)"


def embedding(mid):
    from sentence_transformers import SentenceTransformer, util

    m = SentenceTransformer(mid)
    a, b = m.encode(["الجو حار اليوم", "الطقس ساخن جدا"])
    return f"cosine similarity {float(util.cos_sim(a, b)):.2f}"


def zeroshot(mid):
    from transformers import pipeline

    p = pipeline("zero-shot-classification", model=mid)
    r = p("فاز الفريق بالمباراة بثلاثة أهداف", candidate_labels=["رياضة", "طقس", "اقتصاد"])
    return f"{r['labels'][0]} ({r['scores'][0]:.2f})"


def seq2seq(mid, text, **gen):
    # transformers v5 removed the translation/summarization pipelines; call the model directly.
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(mid)
    model = AutoModelForSeq2SeqLM.from_pretrained(mid)
    out = model.generate(**tok(text, return_tensors="pt", truncation=True), **gen)
    return tok.decode(out[0], skip_special_tokens=True)


def translate(mid, text):
    return seq2seq(mid, text, max_new_tokens=60)


def summarize(mid):
    text = ("أعلنت الأرصاد الجوية أن درجات الحرارة ستصل إلى اثنين وأربعين درجة مئوية في عدة مدن خلال الأيام "
            "القادمة، وحذرت من التعرض المباشر للشمس في ساعات الظهيرة، ودعت السكان إلى شرب كميات كافية من الماء.")
    return seq2seq(mid, text, max_new_tokens=40, num_beams=2)


def music(mid):
    from transformers import AutoProcessor, MusicgenForConditionalGeneration

    proc = AutoProcessor.from_pretrained(mid)
    model = MusicgenForConditionalGeneration.from_pretrained(mid)
    inputs = proc(text=["calm lo-fi radio jingle"], padding=True, return_tensors="pt")
    audio = model.generate(**inputs, max_new_tokens=64)  # ~50 tokens per second of audio
    return f"generated {audio.shape[-1] / model.config.audio_encoder.sampling_rate:.1f}s"


def ast(mid):
    from transformers import pipeline

    r = pipeline("audio-classification", model=mid)(str(WAV))[0]
    return f"{r['label']} ({r['score']:.2f})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-optional", action="store_true")
    args = ap.parse_args()

    ids = {m["key"]: m["id"] for m in json.loads((Path(__file__).parent / "models.json").read_text())["models"]}
    print(f"HF_HOME = {os.environ['HF_HOME']}")

    step(ids["tts"], lambda: tts(ids["tts"]))
    if not WAV.exists():
        print("TTS did not produce data/smoke.wav; cannot continue with ASR/VAD.")
        return 1
    step(ids["asr"], lambda: asr(ids["asr"]))
    step("silero-vad (pip)", vad)
    step(ids["embedding"], lambda: embedding(ids["embedding"]))
    step(ids["zeroshot"], lambda: zeroshot(ids["zeroshot"]))

    if not args.skip_optional:
        step(ids["en_ar"], lambda: translate(ids["en_ar"], "It is very hot today."))
        step(ids["ar_en"], lambda: translate(ids["ar_en"], SENTENCE))
        step(ids["summarize"], lambda: summarize(ids["summarize"]))
        step(ids["music"], lambda: music(ids["music"]))
        step(ids["ast"], lambda: ast(ids["ast"]))

    bad = [m for m, ok in results if not ok]
    print(f"\n{len(results) - len(bad)}/{len(results)} passed" + (f"; failed: {', '.join(bad)}" if bad else ""))
    print(f"Now listen to {WAV} and compare Whisper's transcript to: {SENTENCE}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
