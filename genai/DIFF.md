---
lab3_genai_diff:
  instrumentation: "opentelemetry-instrumentation-genai-openai 1.2b0, with opentelemetry-sdk 1.45.0, opentelemetry-exporter-otlp-json-file 0.66b0 and openai 3.19.2"
  spec_ref: "semantic-conventions-genai@e57c543b4889619eb2a05702471937db5119165d"
  attributes:
    - {name: gen_ai.operation.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.provider.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.temperature, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.max_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.finish_reasons, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.id, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.input_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.output_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.reasoning.output_tokens, emitted: false, in_spec: true, stability: development}
    - {name: gen_ai.request.top_p, emitted: false, in_spec: true, stability: development}
    - {name: gen_ai.output.type, emitted: false, in_spec: true, stability: development}
---
<!-- ai-generated: 90% - Claude Code ran the call, read the spec's registry and spans model at the pinned commit, and wrote this; the author reviews it -->

# What the library emits, against the spec

**The call.** One chat completion to `gemini-3.8-flash` through Gemini's OpenAI-compatible endpoint, so the OpenAI client and
`opentelemetry-instrumentation-genai-openai` are used unchanged (`genai/trace_call.py`); the span went to `genai/spans.json`
as OTLP JSON. I compared it with `model/gen-ai/registry.yaml` and `model/gen-ai/spans.yaml` of the GenAI conventions
repository at commit `e57c543b4889619eb2a05702471937db5119165d`.

**What agrees.** All ten `gen_ai.*` keys the library put on the span are defined by the spec at that commit, and every one has
the stability `development`, so a dashboard that groups by them stands on attributes the spec itself calls unstable and may
rename again (the repository has had breaking changes since). The two attributes the spec requires on an inference span,
`gen_ai.operation.name` (`chat`) and `gen_ai.provider.name`, are there; so are the model as requested and as answered
(`gen_ai.request.model` and `gen_ai.response.model`, both `gemini-3.8-flash`), the response id, the finish reasons (`stop`, as
the spec's `string[]`) and the two token counts the spec recommends. The span name `chat gemini-3.8-flash` is the spec's
`{gen_ai.operation.name} {gen_ai.request.model}`, and the span kind is client, as the spec says. The request parameters I set,
the temperature and `max_tokens`, were recorded under the spec's names.

**What does not, or not quite.**

- `gen_ai.provider.name` is `openai`, but the call went to Google's endpoint. The spec allows this: the instrumentation sets the
  attribute "based on its best knowledge", which for an OpenAI client is the SDK's flavour, and it explicitly says a client
  configured against another provider may differ from the real one. The spec does define `gcp.gemini` for
  `generativelanguage.googleapis.com`, and `server.address` on the same span does say `generativelanguage.googleapis.com`, so the
  attributes contradict each other: a cost or latency dashboard grouped by provider would count Gemini calls as OpenAI.
- `gen_ai.usage.reasoning.output_tokens` is not emitted. Gemini 3.8 Flash is a thinking model, and on a first run with
  `max_tokens=400` the answer was cut after 12 visible tokens because the budget had gone into reasoning (`finish_reasons` was
  `length`); the library reports only `gen_ai.usage.output_tokens`, so the reasoning share of the bill, which the spec has an
  attribute for, is invisible. I raised `max_tokens` to 2000 for the recorded call, and its 71 output tokens end in `stop`.
- `gen_ai.request.top_p` and `gen_ai.output.type` are absent because my request did not set them, which is correct, not a
  gap: the library emits request attributes only for the parameters that were sent.
- The message content (`gen_ai.input.messages`, `gen_ai.output.messages`, the system instructions) is not on the span. The spec
  marks it opt-in, so this agrees with it, but a trace in this form cannot explain why a call was slow or wrong.
- The resource says `service.name: unknown_service:python` and the scope's `schemaUrl` is `https://opentelemetry.io/schemas/1.37.0`,
  an older schema than the repository I compared against; attributes can have moved between the two, which is why the
  comparison names a commit.

**What it means for a dashboard.** The attributes the library emits are enough for the three panels most teams build first -
calls by model, token usage, and latency by operation - and they match the spec's names, so a panel written against the spec
would work. Two things need care: group by `server.address` rather than by `gen_ai.provider.name` when the provider matters, and
treat every `gen_ai.*` name as something to re-check on the day of an upgrade, because the whole namespace is `development`.
