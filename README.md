# Hawa

An AI-generated Arabic radio station: live data (weather, scores, markets, news) becomes scripted
segments, spoken with local TTS, mixed and streamed over HLS, with listener call-ins.

> Status: Day 0 (setup). See [docs/build-guide.md](docs/build-guide.md).

## Layout

| Path | What |
| --- | --- |
| `services/api` | NestJS: collectors, planner, workers, playout, gateway, SSE |
| `services/inference` | FastAPI (Python 3.11): TTS, ASR, VAD, embeddings, zero-shot, mixer |
| `apps/web` | Next.js frontend |
| `scripts` | `download_models.py`, `smoke_test.py`, `models.json` |
| `data` | gitignored: segments, HLS, fillers, beds, model cache |
| `docs` | build guide, notes, architecture |

## Setup

```bash
cp .env.example .env                      # fill in HF_TOKEN, ANTHROPIC_API_KEY etc.
python3.11 -m venv services/inference/.venv
source services/inference/.venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r services/inference/requirements.txt
set -a; source .env; set +a               # exports HF_TOKEN, HF_HOME
python scripts/download_models.py         # ~6-10 GB into HF_HOME
python scripts/smoke_test.py              # one inference per model; writes data/smoke.wav
```

Use `--skip-optional` on either script to leave out the large optional models.

TTS, ASR, VAD, embeddings, translation and the other models run locally on CPU. Only the
script-writing LLM is hosted (Claude via the Anthropic API). Compare candidates with
`python scripts/llm_bakeoff.py` and set `LLM_MODEL` in `.env`.

## Model licenses

Several weights are **non-commercial** (MMS-TTS, MusicGen, mT5-XLSum). This is a portfolio demo and is
not for commercial use. Synthetic voices only, never clones of real people. Full license table and data
terms: [docs/notes.md](docs/notes.md).
