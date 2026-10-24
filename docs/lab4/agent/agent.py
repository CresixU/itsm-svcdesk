# ai-generated: 100% - Claude Code (Opus 5.5) adapted this loop from the course's tool research (C.5); the lecturer reviews it
"""A minimal investigator for Lab 4: any OpenAI-compatible model + the course's Prometheus MCP server.

    python agent.py "Checkout errors paged at 10:44:30Z on 2026-10-24. Investigate 10:30Z to 11:10Z. What is the cause?"

Environment:
    BASE_URL   the model's OpenAI-compatible endpoint: Ollama http://localhost:11434/v1 (default), or Gemini
               https://generativelanguage.googleapis.com/v1beta/openai/ with API_KEY=<your AI Studio key>
    API_KEY    the key (Ollama ignores it)
    MODEL      qwen3:1.7b (default), gemini-3.8-flash, gemini-3.5-flash-lite, ...
    PROMETHEUS_URL  the Prometheus to investigate (default http://localhost:9090)
    MAX_STEPS  model calls before it must answer (default 8)
    TRANSCRIPT the transcript file (default ai-rca/transcript.md); a JSON-lines twin is written next to it

The transcript is what the ledger quotes: every model message verbatim, every tool call with its arguments and
(cut) result. The agent never sees the answer: it reads only what Prometheus holds.
"""

import asyncio
import json
import os
import shlex
import sys
import time
from pathlib import Path

from mcp import Client, StdioServerParameters
from openai import AsyncOpenAI

HERE = Path(__file__).resolve().parent
BASE_URL = os.environ.get("BASE_URL", "http://localhost:11434/v1")
API_KEY = os.environ.get("API_KEY", "ollama")
MODEL = os.environ.get("MODEL", "qwen3:1.7b")
MCP_CMD = shlex.split(os.environ.get("MCP_CMD", f"{shlex.quote(sys.executable)} {shlex.quote(str(HERE / 'prom_mcp.py'))}"))
MAX_STEPS = int(os.environ.get("MAX_STEPS", "8"))
EFFORT = os.environ.get("REASONING_EFFORT")
TRANSCRIPT = Path(os.environ.get("TRANSCRIPT", "ai-rca/transcript.md"))
SYSTEM = ("You are an on-call SRE assistant with read-only access to Prometheus through tools. The shop's services "
          "export span metrics: traces_span_metrics_calls_total and traces_span_metrics_duration_milliseconds_bucket, "
          "with labels service_name, span_name, span_kind, status_code (STATUS_CODE_ERROR marks failures). Always pass an "
          "explicit time inside the incident window. Gather evidence with the tools before answering, and state each "
          "hypothesis about the cause as a separate sentence, with the query that supports it.")
FINAL = ("You have no tool calls left. Answer now from the evidence you gathered: which services are failing or slow, "
         "and what is the most likely cause? State each hypothesis as a separate sentence, with the query behind it.")


def write(text: str, event: dict) -> None:
    TRANSCRIPT.parent.mkdir(parents=True, exist_ok=True)
    with TRANSCRIPT.open("a", encoding="utf-8") as md:
        md.write(text + "\n\n")
    with TRANSCRIPT.with_suffix(".jsonl").open("a", encoding="utf-8") as jl:
        jl.write(json.dumps({"ts": round(time.time(), 3), **event}, default=str) + "\n")


async def call_tool(mcp, name, raw):
    try:
        args = json.loads(raw or "{}")
        if not isinstance(args, dict):
            raise ValueError("arguments must be a JSON object")
        result = await mcp.call_tool(name, args)
        text = "\n".join(c.text for c in result.content if getattr(c, "type", "") == "text")
        return args, ("ERROR: " + text) if result.is_error else text
    except Exception as exc:  # bad JSON, unknown tool: tell the model and go on
        return raw, f"ERROR: {type(exc).__name__}: {exc}"


async def main(question: str) -> int:
    llm = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
    env = {**os.environ, "PROMETHEUS_URL": os.environ.get("PROMETHEUS_URL", "http://localhost:9090")}
    async with Client(StdioServerParameters(command=MCP_CMD[0], args=MCP_CMD[1:], env=env)) as mcp:
        tools = [{"type": "function", "function": {"name": t.name, "description": t.description or "",
                                                   "parameters": t.input_schema}}
                 for t in (await mcp.list_tools()).tools]
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
        write(f"# Investigation transcript\n\nmodel: {MODEL} at {BASE_URL}\n\n## Question\n\n{question}",
              {"event": "start", "model": MODEL, "base_url": BASE_URL, "question": question})
        for step in range(MAX_STEPS):
            extra = {"reasoning_effort": EFFORT} if EFFORT else {}
            last = step == MAX_STEPS - 1
            if last:                    # the last call has no tools: the model must answer with what it has
                messages.append({"role": "user", "content": FINAL})
                write(f"## The step limit\n\n{FINAL}", {"event": "final_request", "step": step, "content": FINAL})
            started = time.time()
            resp = await llm.chat.completions.create(model=MODEL, messages=messages, **({} if last else {"tools": tools}),
                                                     **extra)
            msg = resp.choices[0].message
            calls = msg.tool_calls or []
            write(f"## Step {step + 1}: the model ({time.time() - started:.0f} s)\n\n{msg.content or '(no text)'}",
                  {"event": "model", "step": step, "content": msg.content,
                   "tool_calls": [{"name": c.function.name, "arguments": c.function.arguments} for c in calls]})
            if not calls:
                print(msg.content)
                return 0
            # send the model's message back exactly as it came, provider fields included: Gemini 3 models refuse a
            # conversation whose tool calls lost the `thought_signature` they were returned with (HTTP 400)
            turn = msg.model_dump(exclude_none=True)
            turn.setdefault("content", "")
            messages.append(turn)
            for c in calls:
                args, text = await call_tool(mcp, c.function.name, c.function.arguments)
                write(f"### Tool `{c.function.name}`\n\n```\n{json.dumps(args)}\n```\n\n```\n{text[:3000]}\n```",
                      {"event": "tool", "step": step, "name": c.function.name, "arguments": args, "result": text[:4000]})
                messages.append({"role": "tool", "tool_call_id": c.id, "content": text})
        write(f"(no final answer after {MAX_STEPS} model calls)", {"event": "step_limit"})
        return 1                        # the last call still asked for a tool, or MAX_STEPS < 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main(" ".join(sys.argv[1:]) or "Which shop services fail most right now?")))
