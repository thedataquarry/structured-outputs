# Structured outputs

Structured output benchmark that compares the results from modern tools like [BAML](https://docs.boundaryml.com/home)
and [DSPy](https://dspy.ai/). Both DSPy and BAML have largely similar goals: help developers build modular, reliable
AI systems with composable building blocks, and a strong emphasis on evaluation and testing.
However, there are nuanced differences in what building blocks they use and how they are implemented. This repo
aims to explore some of those differences and compare their performance on multiple structured output benchmarks.

## Data

See the respective directories in [src/](./src/) for the benchmarks tested. The datasets used in `src/*/data` are
summarized below. The first one is a healthcare dataset of clinical notes, while the others are from the
Cleanlab [structured output benchmarks](https://github.com/cleanlab/structured-output-benchmark).

Dataset | Task | Source | Input | Output | Records | Notes
--- | --- | --- | --- | --- | --- | ---
Patient notes | Extract structured fields from unstructured patient notes | [FHIR patient records](https://huggingface.co/datasets/kishanbodybrain/test-fhir/tree/main/data) | Plain text | Nested JSON | 2,726 | Gold data derived from `data/raw_fhir.json` to `gold.json`
Financial entities | Extract financial and contextual entities from business text | [Cleanlab fire-financial-ner-extraction](https://huggingface.co/datasets/Cleanlab/fire-financial-ner-extraction) | Parquet | Nested JSON | 100 | From Cleanlab structured outputs benchmark
Insurance claims | Extract structured fields from insurance claim records | [Cleanlab insurance-claims-extraction](https://huggingface.co/datasets/Cleanlab/insurance-claims-extraction) | Parquet | Nested JSON | 30 | From Cleanlab structured outputs benchmark
PII | Extract and classify PII from unstructured text | [Cleanlab pii-extraction](https://huggingface.co/datasets/Cleanlab/pii-extraction) | Parquet | Nested JSON | 100 | From Cleanlab structured outputs benchmark

Many thanks to the Cleanlab authors for publishing high-quality benchmarks for structured outputs with
human-annotated data. See their blog post on why pre-existing structured output benchmarks were riddled with
mistakes [here](https://cleanlab.ai/blog/structured-output-benchmark/).

## Setup

It's recommended to [install uv](https://docs.astral.sh/uv/getting-started/installation/) to manage the dependencies.

```bash
uv sync
```

Install any additional Python packages via `uv add <package_name>`.

See the evaluation results in the `./src/baml`  and `./src/dspy` directories for more information.

## Takeaways

- BAML performs better than DSPy for structured outputs when using smaller, less capable models and when the output is nested beyond one level. In such conditions, due to the complexity of the task, BAML's parser can help fix mistakes from the LLM's output.
- DSPy uses structured prompt templates, which add verbosity compared to a minimal BAML prompt; that extra token cost can pay off with larger, more capable models that handle longer prompts more effectively.
- DSPy with the custom [`BAMLAdapter`](./src/dspy/baml_adapter.py) + a larger, more capable model outperforms BAML because the combination of the model's enhanced reasoning ability + the richness of its structured prompts helps the model perform the task better.

In DSPy, the `BAMLAdapter` improves on the default `ChatAdapter`'s schema formatting as shown below.
![](./assets/json-schema-vs-baml.png)

The difference in readability explains the stark improvement in performance when outputting nested JSON data
that's more than one level deep. On the other hand, the improvement with `BAMLAdapter` is not as significant
when working with schemas that are flatter and simpler.

## Bottom line

- If token budget and using small, cheap models are a priority, BAML is the better option for structured outputs.
- If you have access to larger, more capable models and you're dealing with nested JSON data in your schema,
DSPy + `BAMLAdapter` is useful.
- If you have access to larger, more capable models and you're dealing with flat structures and simple schemas,
either BAML or DSPy would work more or less just as well.

> [!NOTE]
> All approaches (BAML or DSPy) will work better with optimized prompts. When you optimize the baseline prompt,
> it's more than likely that most of the gains come from better-specified instructions to the LLM, not the
> schema format.

> 🚩 Focus on prompt optimization to get the most out of either BAML or DSPy for any task. 🚩