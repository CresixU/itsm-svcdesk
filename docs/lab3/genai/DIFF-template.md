---
lab3_genai_diff:
  instrumentation: ""           # TODO: the instrumentation package and its version, and the SDK's
  spec_ref: ""                  # TODO: exactly one of the two spec refs in HANDOUT.md, Stretch 1
  attributes:                   # at least five, none twice; every gen_ai.* key in genai/spans.json with emitted: true
    - {name: TODO, emitted: TODO, in_spec: TODO, stability: TODO}
    - {name: TODO, emitted: TODO, in_spec: TODO, stability: TODO}
    - {name: TODO, emitted: TODO, in_spec: TODO, stability: TODO}
    - {name: TODO, emitted: TODO, in_spec: TODO, stability: TODO}
    - {name: TODO, emitted: TODO, in_spec: TODO, stability: TODO}
---
<!-- ai-generated: ??% - TODO replace ?? with a number and say in one line how this file was written -->

# What the library emits, against the spec

Copy this file to `genai/DIFF.md`, next to `genai/spans.json` (Stretch 1, `L3-STRETCH-1`; MONITORING-SPEC.md M-28,
M-29). One entry per attribute:

- `name`: a `gen_ai.*` attribute key;
- `emitted`: `true` when the key appears in `genai/spans.json`, `false` when the spec defines it and your spans do
  not carry it. The `emitted: true` names must be exactly the `gen_ai.*` keys in your spans, no more and no fewer;
- `in_spec`: whether the spec ref you named defines the attribute;
- `stability`: only when `in_spec` is `true` - the attribute's stability in that ref, lower-case as the spec's model
  files write it (for example `development`), or `deprecated` for an attribute the ref marks as deprecated.

For example, `{name: gen_ai.request.model, emitted: true, in_spec: true, stability: development}`. Delete these
instructions when you write the file.

The prose below is yours: what agrees, what does not or not quite, and what that means for a dashboard built on
these attributes. Which ref you compare against, and whether the library matches it, is never graded; that your
claims agree with the ref and with your spans is.
