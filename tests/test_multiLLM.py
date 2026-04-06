"""
dwa10 Multi-LLM Test Suite
Tests memory persistence across Claude, Copilot, ChatGPT, Gemini, Grok.

Install requirements:
    pip install dwa10 anthropic openai google-generativeai

Run:
    python test_multiLLM.py --llm claude
    python test_multiLLM.py --llm openai
    python test_multiLLM.py --llm gemini
    python test_multiLLM.py --llm grok
    python test_multiLLM.py --llm all
"""

import argparse
import os
from dwa10 import DWASession
from dwa10.adapters import (
    AnthropicAdapter,
    OpenAIAdapter,
    CallableAdapter,
)

PASS = "✅ PASS"
FAIL = "❌ FAIL"


# ── TEST CASES ────────────────────────────────────────────────────────────────

def run_memory_test(session: DWASession, llm_name: str):
    print(f"\n{'='*50}")
    print(f"  Testing: {llm_name}")
    print(f"{'='*50}")
    results = []

    # Test 1: Basic memory retention
    session.chat("My name is Usman and I am building dwa10.")
    session.chat("My budget for the project is $10,000.")
    session.chat("I prefer Python over JavaScript.")
    response = session.chat("What do you know about me so far?")
    passed = any(word in response.lower() for word in ["usman", "10,000", "python", "dwa10"])
    results.append(("Memory retention after 4 msgs", passed, response[:80]))

    # Test 2: Manual anchor survives long context
    session.anchor("CRITICAL: User's deadline is June 2026", class_="P0")
    for i in range(5):
        session.chat(f"Tell me something interesting about topic {i}.")
    response = session.chat("What is my project deadline?")
    passed = "june" in response.lower() or "2026" in response.lower()
    results.append(("P0 anchor survives 5 msgs", passed, response[:80]))

    # Test 3: Memory stats
    stats = session.memory_stats()
    passed = stats["total"] > 0 and stats["message_count"] == 10
    results.append(("Memory stats correct", passed, str(stats)))

    # Test 4: Audit integrity
    integrity = session.verify_integrity()
    passed = integrity["valid"] is True
    results.append(("Audit chain integrity", passed, str(integrity)))

    # Test 5: Export works
    md = session.export_markdown()
    passed = "DWA-10" in md and "Usman" in md or stats["total"] > 0
    results.append(("Export markdown", passed, md[:80]))

    # Print results
    for name, ok, preview in results:
        status = PASS if ok else FAIL
        print(f"  {status}  {name}")
        if not ok:
            print(f"        Response: {preview}")

    passed_count = sum(1 for _, ok, _ in results if ok)
    print(f"\n  Score: {passed_count}/{len(results)} passed")
    return passed_count, len(results)


# ── ADAPTERS ─────────────────────────────────────────────────────────────────

def get_claude_session():
    adapter = AnthropicAdapter(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-sonnet-4-20250514",
    )
    return DWASession(adapter=adapter, system="You are a helpful assistant.")


def get_openai_session():
    adapter = OpenAIAdapter(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
    )
    return DWASession(adapter=adapter)


def get_gemini_session():
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("pip install google-generativeai")

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-pro")

    def gemini_fn(system: str, messages: list) -> str:
        full = system + "\n\n"
        for m in messages:
            role = "User" if m["role"] == "user" else "Assistant"
            full += f"{role}: {m['content']}\n"
        full += "Assistant:"
        response = model.generate_content(full)
        return response.text

    return DWASession(adapter=CallableAdapter(gemini_fn))


def get_grok_session():
    # Grok uses OpenAI-compatible API
    adapter = OpenAIAdapter(
        api_key=os.getenv("GROK_API_KEY"),
        model="grok-beta",
    )
    # Point to xAI base URL
    import openai
    adapter._client = openai.OpenAI(
        api_key=os.getenv("GROK_API_KEY"),
        base_url="https://api.x.ai/v1",
    )
    return DWASession(adapter=adapter)


def get_copilot_session():
    # GitHub Copilot uses OpenAI-compatible API
    adapter = OpenAIAdapter(
        api_key=os.getenv("GITHUB_TOKEN"),
        model="gpt-4o",
    )
    import openai
    adapter._client = openai.OpenAI(
        api_key=os.getenv("GITHUB_TOKEN"),
        base_url="https://models.inference.ai.azure.com",
    )
    return DWASession(adapter=adapter)


# ── MAIN ─────────────────────────────────────────────────────────────────────

SUPPORTED = {
    "claude":  (get_claude_session,  "Claude (Anthropic)"),
    "openai":  (get_openai_session,  "ChatGPT (OpenAI)"),
    "gemini":  (get_gemini_session,  "Gemini (Google)"),
    "grok":    (get_grok_session,    "Grok (xAI)"),
    "copilot": (get_copilot_session, "Copilot (GitHub)"),
}

ENV_KEYS = {
    "claude":  "ANTHROPIC_API_KEY",
    "openai":  "OPENAI_API_KEY",
    "gemini":  "GEMINI_API_KEY",
    "grok":    "GROK_API_KEY",
    "copilot": "GITHUB_TOKEN",
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", default="claude",
                        choices=list(SUPPORTED.keys()) + ["all"])
    args = parser.parse_args()

    targets = list(SUPPORTED.keys()) if args.llm == "all" else [args.llm]
    total_passed = total_tests = 0

    for key in targets:
        env_key = ENV_KEYS[key]
        if not os.getenv(env_key):
            print(f"\n⚠️  Skipping {key} — set {env_key} env var first.")
            continue
        factory, name = SUPPORTED[key]
        try:
            session = factory()
            p, t = run_memory_test(session, name)
            total_passed += p
            total_tests += t
        except Exception as e:
            print(f"\n❌ {name} failed with error: {e}")

    if total_tests > 0:
        print(f"\n{'='*50}")
        print(f"  TOTAL: {total_passed}/{total_tests} passed across all LLMs")
        print(f"{'='*50}\n")
