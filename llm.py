import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

BACKEND = os.getenv("BACKEND", "ollama")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1/chat/completions")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
SF_HOST = os.getenv("SF_HOST", "")
SF_PAT = os.getenv("SF_PAT", "")
SF_MODEL = os.getenv("SF_MODEL", "claude-sonnet-4-5")  # use a model your account lists


def _chat_ollama(messages, temperature):
    r = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "messages": messages,
              "temperature": temperature, "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _chat_snowflake(messages, temperature):
    if not SF_HOST or not SF_PAT:
        raise RuntimeError("SF_HOST and SF_PAT must be set in .env")
    url = f"https://{SF_HOST}/api/v2/cortex/inference:complete"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {SF_PAT}",
    }
    body = {"model": SF_MODEL, "messages": messages, "temperature": temperature}
    out = []
    with requests.post(url, headers=headers, json=body, stream=True, timeout=120) as r:
        r.raise_for_status()
        if "text/event-stream" not in r.headers.get("Content-Type", ""):
            choice = r.json()["choices"][0]
            return choice.get("message", {}).get("content") or choice.get("text", "")
        for raw in r.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8")
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                chunk = json.loads(payload)
            except json.JSONDecodeError:
                continue
            for c in chunk.get("choices", []):
                out.append((c.get("delta") or {}).get("content") or c.get("text") or "")
    return "".join(out)


def chat(messages, temperature=0.2, backend=None):
    """Send messages to the model. Returns the reply as a string."""
    first = backend or BACKEND
    order = [first, "snowflake" if first == "ollama" else "ollama"]
    errors = []
    for b in order:
        try:
            fn = _chat_snowflake if b == "snowflake" else _chat_ollama
            return fn(messages, temperature)
        except Exception as e:  # try the other backend
            errors.append(f"{b}: {e}")
    raise RuntimeError("Both backends failed.\n  " + "\n  ".join(errors))


if __name__ == "__main__":
    print(chat([{"role": "user", "content": "Say hello in five words."}]))
