# Structured outputs

Structured output benchmark that compares the results from modern tools like [BAML](https://docs.boundaryml.com/home)
and [DSPy](https://dspy.ai/). Both DSPy and BAML aim to solve the same problem: help developers build modular, reliable
AI systems with composable building blocks. However, there are nuanced differences in what
building blocks they use and how they are implemented. This repo aims to explore some of those and
study the performance on a benchmark dataset of clinical notes for a structured output extraction task.

## Data

See the respective directories in [src/](./src/) for the benchmarks tested.

## Setup

It's recommended to [install uv](https://docs.astral.sh/uv/getting-started/installation/) to manage the dependencies.

```bash
uv sync
```

Install any additional Python packages via `uv add <package_name>`.

See the evaluation results in the `./src/baml`  and `./src/dspy` directories for more information.

## Takeaways

The structured output benchmarks clearly show that BAML's schema representation in the prompt sent to the LLM is more
concise and token-efficient compared to DSPy's default JSON schema (far more verbose and messy for
LLMs to reason about). However, DSPy allows users to define [custom adapters](https://dspy.ai/learn/programming/language_models/?h=adapter#advanced-building-custom-lms-and-writing-your-own-adapters),
which is very helpful -- we can then compare the effect of the schema representation by
writing a custom [`BAMLAdapter`](./src/dspy/baml_adapter.py) for DSPy that achieves a similar level of performance.

See below for a comparison of the two schema representations.
![](./assets/json-schema-vs-baml.png)

The results for experiments that use the BAML adapter are shown in the [src/dspy](./src/dspy) directory.