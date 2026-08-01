#!/usr/bin/env python3
"""CLI Q&A Tool — answer questions about pasted text using OpenRouter LLM.

Input: multi-paragraph text (terminated by 'END' on its own line), then a question.
Output: an answer with paragraph-level citations in [Paragraph X] format.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/free"

SYSTEM_PROMPT = """You are a precise research assistant.

Rules:
1. Answer ONLY using information from the provided text.
2. After EVERY claim, add a citation in the format [Paragraph X].
3. If a sentence uses information from multiple paragraphs, cite all of them.
4. If the text does not contain the answer, reply:
   "The text does not provide this information."
5. Do NOT add any information beyond what is in the text.

Example:
If the text says:
[Paragraph 1] The sky is blue.
[Paragraph 2] Grass is green.

And the question is: 'What color is the sky?'
Your answer should be: 'The sky is blue [Paragraph 1].'
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_api_key() -> str:
    """Load OPENROUTER_API_KEY from .env file (same directory as this script)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")

    if not os.path.isfile(env_path):
        print("Error: .env file not found. Create one with OPENROUTER_API_KEY=your-key",
              file=sys.stderr)
        sys.exit(1)

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("OPENROUTER_API_KEY="):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value

    print("Error: OPENROUTER_API_KEY not found in .env file.", file=sys.stderr)
    sys.exit(1)


def collect_text() -> str:
    """Read multi-line text from stdin until a line containing only 'END'."""
    print("Paste your text below. Type END on a new line when finished:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs on blank-line boundaries.

    Strips leading/trailing whitespace from each paragraph and filters
    out empty paragraphs so users don't get spurious paragraph numbers.
    """
    raw = text.split("\n\n")
    result = []
    for p in raw:
        stripped = p.strip()
        if stripped:
            result.append(stripped)
    return result


def build_user_message(paragraphs: list[str], question: str) -> str:
    """Build the user prompt with numbered paragraphs and the question."""
    parts = ["Here is the text:\n"]
    for i, p in enumerate(paragraphs, start=1):
        parts.append(f"[Paragraph {i}]\n{p}\n")
    parts.append(f"Question: {question}")
    return "\n".join(parts)


def call_openrouter(api_key: str, user_message: str) -> str:
    """Send the prompt to OpenRouter and return the assistant's reply."""
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(OPENROUTER_URL, data=body)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"Error: OpenRouter API returned HTTP {e.code}.", file=sys.stderr)
        print(body_text, file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Could not reach OpenRouter API — {e.reason}", file=sys.stderr)
        sys.exit(1)

    # Extract the assistant's message content.
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        print("Error: Unexpected response format from OpenRouter API.", file=sys.stderr)
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. Parse command-line arguments
    parser = argparse.ArgumentParser(description="CLI Q&A Tool")
    parser.add_argument(
        "--file",
        help="Path to a text file to use as input (instead of pasting)",
    )
    args = parser.parse_args()

    # 2. Load API key (never printed)
    api_key = load_api_key()

    # 3. Collect text (from file or interactive input)
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            raw_text = f.read()
        print(f"Read text from {args.file}.")
    else:
        raw_text = collect_text()

    # 4. Validate: empty text → friendly error, no API call
    paragraphs = split_paragraphs(raw_text)
    if not paragraphs:
        print("Error: No text provided. Please paste at least one paragraph "
              "before asking a question.")
        sys.exit(1)

    # 5. Report paragraph count
    print(f"\nFind {len(paragraphs)} paragraph(s).")
    print("Ask questions below. Type 'quit' or press Enter on an empty "
          "line to exit.\n")

    # 6. Multi-turn Q&A loop
    while True:
        try:
            question = input("Enter your question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            print("Goodbye!")
            break
        if question.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        # Build prompt & call LLM
        user_message = build_user_message(paragraphs, question)
        answer = call_openrouter(api_key, user_message)

        # Print result
        print(f"\n{answer}\n")


if __name__ == "__main__":
    main()
