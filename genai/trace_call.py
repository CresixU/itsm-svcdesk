# ai-generated: 90% - Claude Code wrote this from HANDOUT.md, Stretch 1; the call itself is one chat completion to Gemini
"""One LLM call, instrumented with the OpenTelemetry GenAI instrumentation for OpenAI (Lab 3, Stretch 1).

Gemini is reached through its OpenAI-compatible endpoint, so the OpenAI client and its instrumentation are used
unchanged. The spans go to genai/spans.json as OTLP JSON, one batch per line (FileSpanExporter).

    docker run --rm --env-file <file with OPENAI_API_KEY=...> -v "$PWD":/work python:3.13-slim \
        bash -c "pip install -r /work/genai/requirements.txt && python /work/genai/trace_call.py"
"""
import os

from openai import OpenAI
from opentelemetry import trace
from opentelemetry.exporter.otlp.json.file import FileSpanExporter
from opentelemetry.instrumentation.genai.openai import OpenAIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

OUT = os.environ.get("GENAI_SPANS_PATH", "/work/genai/spans.json")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
MODEL = "gemini-3.8-flash"

if os.path.exists(OUT):
    os.remove(OUT)  # the exporter appends

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(FileSpanExporter(OUT)))
trace.set_tracer_provider(provider)
OpenAIInstrumentor().instrument()

client = OpenAI(base_url=BASE_URL, api_key=os.environ["OPENAI_API_KEY"])
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": "In two sentences: what does a p99 latency of 95 ms mean for a search endpoint that serves 40 requests per second?",
        }
    ],
    temperature=0.2,
    max_tokens=2000,
)
print(response.choices[0].message.content)

provider.shutdown()
