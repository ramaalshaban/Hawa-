#!/usr/bin/env python3
"""Send one prompt to Claude models and print the replies, so you can pick LLM_MODEL.

Cheap by design: Haiku first, a hard cap of 300 output tokens per call, one call per model.
Add --models claude-sonnet-5-5 to also try the pricier, better model.
Needs ANTHROPIC_API_KEY.

Usage: python scripts/llm_bakeoff.py [--models claude-haiku-5-5 claude-sonnet-5-5]
"""
import argparse
import os
import sys
import time

import anthropic

PROMPT = (
    "Write two dry, deadpan lines in Gulf Arabic about 42°C weather, "
    "then two openly sarcastic lines in Levantine Arabic. Output only the four lines."
)
DEFAULT_MODELS = ["claude-haiku-5-5"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    ap.add_argument("--max-tokens", type=int, default=300)
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set. Run: set -a; source .env; set +a")
        return 1

    client = anthropic.Anthropic()
    print(f"PROMPT: {PROMPT}\n")
    for mid in args.models:
        t0 = time.time()
        print("=" * 70)
        print(mid)
        try:
            r = client.messages.create(
                model=mid,
                max_tokens=args.max_tokens,
                thinking={"type": "disabled"},  # otherwise hidden reasoning eats the token cap and costs more
                messages=[{"role": "user", "content": PROMPT}],
            )
            text = "".join(b.text for b in r.content if b.type == "text")
            print(f"({time.time() - t0:.1f}s, {r.usage.input_tokens} in / {r.usage.output_tokens} out tokens)\n")
            print(text)
        except Exception as e:
            print(f"FAILED: {type(e).__name__}: {str(e)[:300]}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
