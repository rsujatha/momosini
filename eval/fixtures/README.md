# Fixtures = recorded agent runs

Each `*.json` captures one run: the tool returns + the agent's output. The harness checks
that no developmental number in the output is absent from the tool returns. To add a case,
run the agent, save its tool calls + output here, and `pytest eval/`.
