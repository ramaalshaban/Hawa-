"""Hawa inference service: POST /script (LLM) and POST /tts (Arabic speech).

Run from services/inference with the env loaded:
    set -a; source ../../.env; set +a
    .venv/bin/uvicorn app.main:app --port 8001
"""
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root
os.environ.setdefault("HF_HOME", str(ROOT / "data" / "cache" / "hf"))  # before importing transformers

import anthropic  # noqa: E402
import numpy as np  # noqa: E402
import scipy.io.wavfile as wavfile  # noqa: E402
import torch  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from transformers import AutoTokenizer, VitsModel  # noqa: E402

from .normalize import normalize_ar  # noqa: E402
from .schemas import ScriptRequest, ScriptResponse, TtsRequest, TtsResponse  # noqa: E402

log = logging.getLogger("hawa.inference")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

TTS_MODEL_ID = "facebook/mms-tts-ara"
SEGMENTS_DIR = ROOT / "data" / "segments"
LLM_MODEL = os.environ.get("LLM_MODEL") or "claude-haiku-5-5"  # "or": .env may define it but leave it empty
LLM_TIMEOUT_S = 15

HOST_STYLE = {
    "anchor": " مذيع أخبار رسمي وهادئ يتحدث بالعربية العامية المبسطة بدون تشكيل",
    "nightowl": "مذيع ليلي ساخر بجفاف، يتحدث بلهجة خليجية بسيطة",
}
SYSTEM_PROMPT = (
    "أنت {style} في إذاعة اسمها هواء. اكتب نصا قصيرا للقراءة على الهواء:  ثلاث جمل أو أربع "
    "وبحد أقصى خمسة وأربعين كلمة. "
    "علّق على الحقائق الموجودة في بيانات JSON فقط، ولا تضف أي رقم أو معلومة أو نصيحة غير موجودة فيها. "
    "اذكر كل مدينة في البيانات باسمها مع درجة حرارتها، ولا تترك أي مدينة. "
    "لا تذكر اسم المصدر ولا الوقت ولا المنطقة الزمنية، واذكر درجة الحرارة كرقم صحيح مقرب. "
    "اكتب بالعربية فقط، بدون أحرف لاتينية، بدون رموز تنسيق، وأخرج النص النهائي فقط."
)

state: dict = {}
tts_lock = threading.Lock()  # one TTS inference at a time on CPU


@asynccontextmanager
async def lifespan(app: FastAPI):
    t0 = time.time()
    state["tok"] = AutoTokenizer.from_pretrained(TTS_MODEL_ID)
    state["tts"] = VitsModel.from_pretrained(TTS_MODEL_ID).eval()
    log.info("loaded %s in %.1fs", TTS_MODEL_ID, time.time() - t0)
    # max_retries=0: fail fast so the fallback kicks in instead of stalling the pipeline
    state["llm"] = anthropic.Anthropic(timeout=LLM_TIMEOUT_S, max_retries=0) if os.environ.get("ANTHROPIC_API_KEY") else None
    if state["llm"] is None:
        log.warning("ANTHROPIC_API_KEY not set: /script will always use the template fallback")
    SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    state.clear()


app = FastAPI(title="Hawa inference", lifespan=lifespan)


def _fallback_text(req: ScriptRequest) -> str:
    """Hard-coded Arabic sentence so the pipeline still runs when the LLM is down."""
    for f in req.facts:
        parts = [
            f"{c['city']} {round(c['temperature_2m'])} درجة"
            for c in f.data.get("cities", [])
            if c.get("temperature_2m") is not None
        ]
        if parts:
            return "الطقس الآن في المملكة، درجة الحرارة . في مشكلة بسيطة حنحلها" + "، ".join(parts) + "."
    return "أهلا بكم في إذاعة هواء."


@app.get("/health")
def health():
    return {"ok": "tts" in state, "llm": state.get("llm") is not None}


@app.post("/script", response_model=ScriptResponse)
def script(req: ScriptRequest) -> ScriptResponse:
    llm = state.get("llm")
    if llm is not None:
        try:
            facts_json = req.model_dump_json(include={"kind", "facts"}, indent=2)
            r = llm.messages.create(
                model=LLM_MODEL,
                max_tokens=400,  # required by the API; Arabic costs many tokens per word
                system=SYSTEM_PROMPT.format(style=HOST_STYLE[req.host]),  # top-level, not a "system" message
                thinking={"type": "disabled"},
                messages=[{"role": "user", "content": f"الحقائق:\n{facts_json}"}],
            )
            text = "".join(b.text for b in r.content if b.type == "text").strip()
            if text:
                return ScriptResponse(text=text, source="llm")
            log.warning("LLM returned empty text, using fallback")
        except Exception as e:  # network, auth, rate limit, timeout: keep the show on the air
            log.warning("LLM call failed (%s: %s), using fallback", type(e).__name__, str(e)[:200])
    return ScriptResponse(text=_fallback_text(req), source="fallback")


@app.post("/tts", response_model=TtsResponse)
def tts(req: TtsRequest) -> TtsResponse:
    t0 = time.time()
    clean = normalize_ar(req.text)
    if not clean:
        raise ValueError("text is empty after normalization")
    model = state["tts"]
    with tts_lock, torch.no_grad():
        wave = model(**state["tok"](clean, return_tensors="pt")).waveform[0].numpy()
    pcm = (np.clip(wave, -1.0, 1.0) * 32767).astype(np.int16)  # 16-bit PCM wav
    sr = model.config.sampling_rate
    out = SEGMENTS_DIR / f"{req.id}.wav"
    wavfile.write(out, sr, pcm)
    duration = len(pcm) / sr
    log.info("tts id=%s voice=%s %.1fs audio in %.1fs | %s", req.id, req.voice, duration, time.time() - t0, clean)
    return TtsResponse(path=f"segments/{req.id}.wav", durationS=duration)
