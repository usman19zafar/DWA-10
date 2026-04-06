# dwa10-memory

**Indestructible memory for Claude.** Stop losing context mid-conversation.

```bash
pip install dwa10-memory
```

---

## The problem

Claude forgets everything after ~20 messages. Long conversations lose critical facts. Every new session starts from zero.

## The solution

`dwa10-memory` wraps the Anthropic SDK with a priority-based anchor engine. Important facts survive the entire session — automatically.

```python
from dwa10 import DWASession

session = DWASession()  # uses ANTHROPIC_API_KEY env var

session.chat("My name is Sarah and my budget is $5,000")
session.chat("I prefer minimal, modern design")
# ... 40 messages later ...
response = session.chat("What laptop should I buy?")
# Claude STILL knows: Sarah, $5,000, minimal design ✓
```

---

## How it works

Every message runs a 3-step cycle:

1. **Pre-call** — decay old anchors, score by utility density, inject top-K into context
2. **Post-call** — extract new anchors from response (heuristic NER + patterns)
3. **Summary check** — compress low-priority anchors at message 15 or 70% window usage

### Anchor priority classes

| Class | Meaning | Decay |
|---|---|---|
| P0 | Critical — never forget | None |
| P1 | Important — keep active | Slow |
| P2 | Useful — archive when full | Fast |

---

## API

```python
from dwa10 import DWASession, Anchor

# Basic chat
session = DWASession(api_key="sk-...", model="claude-sonnet-4-20250514")
response = session.chat("Hello!")

# Manual anchoring (exact, always remembered)
session.anchor("User is a senior Python developer", class_="P0")
session.anchor("Project deadline: June 2026", class_="P1")

# Memory stats
print(session.memory_stats())
# {'core': 5, 'archival': 2, 'total': 7, 'message_count': 12}

# Export memory (on demand)
session.save("my_session")          # writes my_session.json + my_session.md
md = session.export_markdown()      # get markdown string
data = session.export_json()        # get dict

# Load memory into new session
new_session = DWASession()
new_session.load("my_session")      # restores all anchors
```

---

## What's free vs Pro

| Feature | Free (`dwa10-memory`) | Pro ([zulfr.com](https://zulfr.com/dwa10-pro)) |
|---|---|---|
| In-session anchor memory  | ✅ | ✅ |
| P0/P1/P2 priority classes | ✅ | ✅ |
| Utility-density context packing | ✅ | ✅ |
| Rolling summaries | ✅ | ✅ |
| Manual export/import | ✅ | ✅ |
| LLM-assisted extraction | ❌ | ✅ |
| Cross-session auto-persistence | ❌ | ✅ |
| Multi-agent memory sharing | ❌ | ✅ |
| Dependency graph | ❌ | ✅ |
| Audit logs + team memory | ❌ | ✅ (Corporate) |

---

## Requirements

- Python ≥ 3.9
- `anthropic` SDK ≥ 0.40.0
- Anthropic API key

---

## License

Apache 2.0 © 2026 Usman Zafar Ph.D 
www.zulfr.com
