#!/usr/bin/env python3
"""
CampusMail Conversation Transcript Exporter
Extracts the full development chat history and formats it into:
1. A standalone interactive HTML Chat Viewer (for desktop & mobile sharing)
2. A complete Markdown log in docs/CHAT_HISTORY.md for GitHub sharing
"""

import json
import os
import re
import html
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOG_PATH = Path(r"C:\Users\gunta\.gemini\antigravity\brain\b1deec12-9dc9-43d1-beaf-de9c67586fd1\.system_generated\logs\transcript_full.jsonl")
if not LOG_PATH.exists():
    LOG_PATH = Path(r"C:\Users\gunta\.gemini\antigravity\brain\b1deec12-9dc9-43d1-beaf-de9c67586fd1\.system_generated\logs\transcript.jsonl")

desktop_path = Path(r"C:\Users\gunta\Desktop")
docs_dir = BASE / "docs"
docs_dir.mkdir(parents=True, exist_ok=True)

def clean_user_text(raw_text: str) -> str:
    m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", raw_text, re.DOTALL)
    text = m.group(1).strip() if m else raw_text.strip()
    # Strip out any remaining internal xml tags
    text = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", text, flags=re.DOTALL).strip()
    return text

def parse_transcript():
    turns = []
    current_turn = {"turn": 1, "user": "", "assistant": "", "timestamp": ""}
    turn_counter = 1

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue

            source = item.get("source")
            msg_type = item.get("type")
            content = item.get("content", "")
            ts = item.get("created_at", "")

            if source == "USER_EXPLICIT" or msg_type == "USER_INPUT":
                user_msg = clean_user_text(content)
                if user_msg:
                    # If there's an ongoing turn with assistant reply, save it
                    if current_turn["user"] and current_turn["assistant"]:
                        turns.append(current_turn)
                        turn_counter += 1
                        current_turn = {"turn": turn_counter, "user": "", "assistant": "", "timestamp": ""}
                    elif current_turn["user"] and not current_turn["assistant"]:
                        # Merge multi-part user messages
                        user_msg = current_turn["user"] + "\n\n" + user_msg
                    
                    current_turn["user"] = user_msg
                    current_turn["timestamp"] = ts

            elif source == "MODEL" and msg_type == "PLANNER_RESPONSE":
                if content and not content.startswith("Created At:") and not content.startswith("Showing lines") and not content.startswith("**Waiting") and not content.startswith("**Testing") and not content.startswith("**Verifying") and not content.startswith("**Creating"):
                    if current_turn["assistant"]:
                        current_turn["assistant"] += "\n\n" + content.strip()
                    else:
                        current_turn["assistant"] = content.strip()

    if current_turn["user"]:
        turns.append(current_turn)

    return turns

def generate_markdown(turns):
    lines = [
        "# 💬 CampusMail — Complete End-to-End Development Transcript",
        "",
        "> **Project:** CampusMail (Intelligent University Email Classification & Dual-Head Phishing Shield)  ",
        "> **Student / Author:** Guntaas Singh (BE Second Year, TIET)  ",
        "> **GitHub Repository:** [https://github.com/guntaas0108-eng/Email_Classification](https://github.com/guntaas0108-eng/Email_Classification)  ",
        "> **Live Application:** [https://themes-televisions-learn-restore.trycloudflare.com](https://themes-televisions-learn-restore.trycloudflare.com)  ",
        "",
        "---",
        "",
        "This document contains the complete step-by-step chat history of how this project was designed, trained, customized, audited, and deployed from scratch.",
        "",
        "---",
        ""
    ]

    for t in turns:
        num = t["turn"]
        lines.append(f"## 👤 Step {num}: User Request")
        lines.append("")
        lines.append(t["user"])
        lines.append("")
        if t["assistant"]:
            lines.append("### 🤖 Antigravity AI Response & Implementation")
            lines.append("")
            lines.append(t["assistant"])
            lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)

def generate_html(turns):
    json_turns = json.dumps(turns)
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CampusMail - Full Development Chat History</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  :root {{
    --bg: #090a0f;
    --card: #111420;
    --border: rgba(255, 255, 255, 0.08);
    --text: #f1f5f9;
    --muted: #94a3b8;
    --accent: #6366f1;
    --accent-glow: rgba(99, 102, 241, 0.2);
    --user-bg: #1e1b4b;
    --user-border: rgba(99, 102, 241, 0.4);
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    font-size: 14px;
  }}
  header {{
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(9, 10, 15, 0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .logo {{
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .badge {{
    background: var(--accent);
    color: #fff;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
  }}
  .links a {{
    color: #818cf8;
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 600;
    margin-left: 16px;
    transition: color 0.15s ease;
  }}
  .links a:hover {{ color: #a5b4fc; text-decoration: underline; }}
  .container {{
    max-width: 960px;
    margin: 0 auto;
    padding: 32px 20px 80px;
  }}
  .intro-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 32px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
  }}
  .intro-card h2 {{
    margin: 0 0 8px;
    font-size: 1.4rem;
    font-weight: 800;
    color: #fff;
  }}
  .intro-card p {{
    margin: 4px 0 0;
    color: var(--muted);
    font-size: 0.92rem;
  }}
  .turn {{
    margin-bottom: 36px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}
  .user-bubble {{
    align-self: flex-end;
    max-width: 85%;
    background: var(--user-bg);
    border: 1px solid var(--user-border);
    border-radius: 16px 16px 4px 16px;
    padding: 14px 18px;
    color: #e0e7ff;
    font-size: 0.95rem;
    box-shadow: 0 4px 16px var(--accent-glow);
  }}
  .bubble-label {{
    font-size: 0.70rem;
    text-transform: uppercase;
    font-weight: 800;
    letter-spacing: 0.05em;
    color: #818cf8;
    margin-bottom: 4px;
  }}
  .ai-bubble {{
    align-self: flex-start;
    width: 100%;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px 16px 16px 4px;
    padding: 22px 26px;
    color: var(--text);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }}
  .ai-label {{
    font-size: 0.72rem;
    text-transform: uppercase;
    font-weight: 800;
    letter-spacing: 0.05em;
    color: #10b981;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .markdown-body pre {{
    background: #090a0f !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    padding: 14px !important;
    overflow-x: auto !important;
    color: #e2e8f0 !important;
    font-size: 0.88rem !important;
  }}
  .markdown-body code {{
    background: rgba(255, 255, 255, 0.08);
    padding: 2px 6px;
    border-radius: 4px;
    color: #a5b4fc;
    font-size: 0.88em;
  }}
  .markdown-body table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 0.88rem;
  }}
  .markdown-body th, .markdown-body td {{
    border: 1px solid var(--border);
    padding: 8px 12px;
    text-align: left;
  }}
  .markdown-body th {{ background: rgba(255,255,255,0.04); font-weight: 700; }}
  .markdown-body blockquote {{
    border-left: 4px solid var(--accent);
    margin: 12px 0;
    padding: 6px 16px;
    background: rgba(99, 102, 241, 0.08);
    color: #c7d2fe;
  }}
</style>
</head>
<body>
  <header>
    <div class="logo">
      <span>✉️ CampusMail</span>
      <span class="badge">Chat Log</span>
    </div>
    <div class="links">
      <a href="https://github.com/guntaas0108-eng/Email_Classification" target="_blank">💻 GitHub Repo</a>
      <a href="https://themes-televisions-learn-restore.trycloudflare.com" target="_blank">🌐 Live App</a>
    </div>
  </header>

  <div class="container">
    <div class="intro-card">
      <h2>🎓 CampusMail — Complete Development Transcript</h2>
      <p>This is the full conversation record of how CampusMail (University Email Classification & Dual-Head Cybersecurity Shield) was built step-by-step with Antigravity AI.</p>
    </div>

    <div id="chat-container"></div>
  </div>

  <script>
    const turns = {json_turns};
    const container = document.getElementById("chat-container");

    turns.forEach((t) => {{
      const turnDiv = document.createElement("div");
      turnDiv.className = "turn";

      if (t.user) {{
        const uBubble = document.createElement("div");
        uBubble.className = "user-bubble";
        uBubble.innerHTML = `<div class="bubble-label">👤 Guntaas Singh (Step ${{t.turn}})</div><div>${{marked.parse(t.user)}}</div>`;
        turnDiv.appendChild(uBubble);
      }}

      if (t.assistant) {{
        const aiBubble = document.createElement("div");
        aiBubble.className = "ai-bubble";
        aiBubble.innerHTML = `<div class="ai-label">🤖 Antigravity AI Assistant</div><div class="markdown-body">${{marked.parse(t.assistant)}}</div>`;
        turnDiv.appendChild(aiBubble);
      }}

      container.appendChild(turnDiv);
    }});
  </script>
</body>
</html>
"""
    return html_content

def main():
    print("Reading and parsing conversation transcript...")
    turns = parse_transcript()
    print(f"Parsed {len(turns)} complete turns.")

    # 1. Generate Markdown file for GitHub
    md_content = generate_markdown(turns)
    md_file = docs_dir / "CHAT_HISTORY.md"
    md_file.write_text(md_content, encoding="utf-8")
    print(f"Saved Markdown chat log to: {md_file}")

    # 2. Generate Interactive HTML Chat Viewer on Desktop
    html_content = generate_html(turns)
    html_file = desktop_path / "CampusMail_Chat_History.html"
    html_file.write_text(html_content, encoding="utf-8")
    print(f"Saved Interactive HTML Chat Viewer to: {html_file}")

    # 3. Also save a text/markdown copy on Desktop
    desktop_md = desktop_path / "CampusMail_Chat_History.md"
    desktop_md.write_text(md_content, encoding="utf-8")
    print(f"Saved Desktop Markdown transcript to: {desktop_md}")

if __name__ == "__main__":
    main()
