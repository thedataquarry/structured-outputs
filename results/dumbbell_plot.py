"""
Dumbbell plot comparing exact match scores across different methods.
The top score in the entire benchmark is chosen, and the other two methods'
corresponding scores are plotted alongside it for each dataset.
"""
import altair as alt
import polars as pl


DATA = [
    {
        "dataset": "Patient notes",
        "model": "openai/gpt-4.1",
        "BAML": 97.4,
        "DSPy default": 95.6,
        "DSPy + BAMLAdapter": 96.8,
    },
    {
        "dataset": "Financial NER",
        "model": "google/gemini-3-flash-preview",
        "BAML": 90.3,
        "DSPy default": 90.7,
        "DSPy + BAMLAdapter": 90.8,
    },
    {
        "dataset": "Insurance claims",
        "model": "openai/gpt-5.2",
        "BAML": 86.1,
        "DSPy default": 85.8,
        "DSPy + BAMLAdapter": 91.8,
    },
    {
        "dataset": "PII",
        "model": "google/gemini-3-flash-preview",
        "BAML": 96.7,
        "DSPy default": 97.9,
        "DSPy + BAMLAdapter": 96.9,
    },
]

METHODS = [
    ("BAML", "#1f77b4"),
    ("DSPy default", "#ff7f0e"),
    ("DSPy + BAMLAdapter", "#2ca02c"),
]


def main() -> None:
    records = []
    for item in DATA:
        for method, color in METHODS:
            records.append(
                {
                    "dataset": item["dataset"],
                    "model": item["model"],
                    "method": method,
                    "score": item[method],
                    "color": color,
                }
            )

    df = pl.DataFrame(records).with_columns(
        (pl.col("dataset")).alias("label")
    )

    lines = (
        alt.Chart(df)
        .mark_rule(color="#c6c6c6", strokeWidth=2)
        .encode(
            y=alt.Y("label:N", title=None, sort=None),
            x=alt.X(
                "min(score):Q",
                title="Exact match (%)",
                scale=alt.Scale(domain=[84, 99]),
            ),
            x2="max(score):Q",
        )
    )

    points = (
        alt.Chart(df)
        .mark_point(filled=True, size=280)
        .encode(
            y=alt.Y("label:N", sort=None),
            x="score:Q",
            color=alt.Color(
                "method:N",
                scale=alt.Scale(domain=[m[0] for m in METHODS], range=[m[1] for m in METHODS]),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            shape=alt.Shape(
                "method:N",
                scale=alt.Scale(
                    domain=[m[0] for m in METHODS],
                    range=["circle", "square", "diamond"],
                ),
                legend=None,
            ),
            tooltip=["dataset", "model", "method", alt.Tooltip("score:Q", format=".1f")],
        )
    )

    chart = (
        (lines + points)
        .properties(
            width=1150,
            height=650,
            title="",
        )
        .configure_view(stroke=None)
        .configure_axis(
            grid=True,
            gridDash=[4, 4],
            tickSize=0,
            labelFontSize=18,
            titleFontSize=18,
        )
        .configure_title(fontSize=20, anchor="start")
        .configure_legend(labelFontSize=16)
    )

    chart.save("dumbbell_benchmarks.html")


if __name__ == "__main__":
    main()
