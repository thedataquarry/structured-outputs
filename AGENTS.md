# Instructions for agents

When running Python code, we have to cater to users of both pip and uv.

- Use 4 spaces to represent a tab (do not use tab characters)
- Always attempt to first run *any* Python code via the local virtual environment
  - Look for a local virtual environment (typically in `.venv` or `venv`)
  - Activate the environment, so that you can run multiple code exampes in the same environment
- Avoid using `uv run` directly, as you have issues running it in your sandbox
- Only fall back to the system `python3` to run code if the above steps don't work