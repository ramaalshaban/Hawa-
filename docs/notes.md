# Day 0 notes

## Model license table

Licenses read from each model's Hub metadata on 2026-11-04 (not copied from the build guide).

| Task | Model | License | Commercial use? |
| --- | --- | --- | --- |
| Text generation | Hosted Claude (`claude-haiku-5-5`, Anthropic API) | Anthropic API terms | Yes, under API terms |
| TTS | `facebook/mms-tts-ara` | CC-BY-NC 4.0 | **No** |
| ASR | `Systran/faster-whisper-small` | MIT | Yes |
| VAD | `silero-vad` (PyPI, not on the Hub) | MIT | Yes |
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Apache 2.0 | Yes |
| Zero-shot | `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` | MIT | Yes |
| Translation | `Helsinki-NLP/opus-mt-en-ar`, `opus-mt-ar-en` | Apache 2.0 | Yes |
| Summarization | `csebuetnlp/mT5_multilingual_XLSum` | Not declared on the Hub; trained on XL-Sum (CC BY-NC-SA 4.0), treat as non-commercial | **Assume no** |
| Music | `facebook/musicgen-small` | CC-BY-NC 4.0 | **No** |
| Audio classification | `MIT/ast-finetuned-audioset-10-10-0.4593` | BSD-3-Clause | Yes |

Differences from the build guide: mDeBERTa is MIT (guide: "check"), and the opus-mt models are Apache 2.0
(guide: CC-BY 4.0).

**Consequence:** the TTS voice, MusicGen jingles and the summarizer are non-commercial. Hawa is a portfolio
demo, not a product. Synthetic voices only, never clones of real people.

## Data source terms

| Source | Key? | Terms to respect |
| --- | --- | --- |
| Open-Meteo (weather) | No | Attribution required |
| Aladhan (prayer times) | No | Free, be polite with request rate |
| OpenSky (flights) | No | Non-commercial use, anonymous access is rate-limited |
| football-data.org | Free token | Free tier is rate-limited |
| CoinGecko (crypto, market fallback) | No | Free tier is rate-limited |
| Twelve Data / Alpha Vantage (markets) | Free key | Rate-limited; test a Saudi symbol first, Tadawul coverage is uncertain |
| TomTom traffic (optional) | Key | If skipped, skip traffic segments. Never invent traffic numbers |
| RSS feeds | No | Read headlines and link back; do not republish article text |

## Smoke test results (2026-11-04, CPU, Apple laptop)

All 10 steps pass (`python scripts/smoke_test.py`). Observations:

- **TTS** wrote ~7 s of audio in ~7 s (after warm-up).
- **Whisper small** transcribes the synthetic sentence approximately ("هوائي الجول يومي" for "هواء، الجو اليوم").
  Fine for call-in demos, not exact.
- **mT5-XLSum hallucinated**: asked to summarize a text about 42°C heat, it produced a sentence about British
  cities and a temperature drop. Never trust a summary without the numeric validator (Day 3).
- **transformers v5** removed the `translation` and `summarization` pipelines; the code calls
  `AutoModelForSeq2SeqLM` directly. `sentencepiece` is required by the Marian and mT5 tokenizers.
- `snapshot_download` pulls every weight format by default (ONNX, OpenVINO, `.bin` duplicates). The download
  script filters them out; the disk filled up before that fix.

## LLM bake-off

Hosted Hugging Face Inference Providers returned `402 Payment Required` (no credits), so the script-writing LLM
is Claude via the Anthropic API instead. Hidden "thinking" ate the whole token cap and returned no text, so it is
disabled. Tested `claude-haiku-5-5` (66 in / 228 out tokens, a fraction of a cent). The Levantine output was judged
good enough by a native Levantine speaker, so **`LLM_MODEL=claude-haiku-5-5`**. `claude-sonnet-5-5` is the upgrade
path if quality needs it.

## Understanding checkpoint (in my own words)

1. **Why does the microphone force HTTPS?** Browsers expose `getUserMedia` only in secure contexts. That means
   HTTPS or localhost, so a public call-in page needs a real certificate.
2. **Why check licenses first?** The license decides what I may publish or sell. MMS-TTS, MusicGen and the XLSum
   summarizer are non-commercial, so Hawa can only be a demo.
3. **What does `HF_HOME` control, and why inside `data/`?** It is the model cache location. Inside `data/` it is
   gitignored, easy to size, and can be reused as a Docker volume.
4. **Why hosted LLM but local TTS/ASR?** A large LLM is too slow on a CPU VPS. The small TTS and ASR models run
   fast enough locally and avoid per-call cost and latency. The LLM is the only piece that is billed per use.
