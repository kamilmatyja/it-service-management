---
lab3_genai_diff:
  instrumentation: "opentelemetry-instrumentation-genai-openai 1.2b0, opentelemetry-sdk 1.45.0"
  spec_ref: "semantic-conventions-genai@e57c543b4889619eb2a05702471937db5119165d"
  attributes:
    - {name: gen_ai.operation.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.provider.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.input_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.output_tokens, emitted: true, in_spec: true, stability: development}
---
<!-- ai-generated: 0% - Hand-written based on spec review -->

# What the library emits, against the spec
The library emits the core attributes matching the new `semantic-conventions-genai` repository precisely as intended in its development branch.