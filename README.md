# LLMAssistedUse
A barebone adaptation of Anthropic Computer use with Agent and MCP. Developed using langgraph, Ollama and qwen2.5. This works for the sake of working and needs more improvement which will follow in upcoming commits.

## Prerequisites
Ollama is required to run this as of now, in upcoming iterations I will include feature for online LLMs
<br/>
<code>ollama pull qwen2.5</code>
<br/>
<code>ollama serve</code>

## How to Run it
Install the python packages and run agent.py
<br/>
<code>pip install -r requirements.txt</code>
<br/>
<code>python agent.py</code>

## Upcoming Changes
<li>Integrate other MCP Servers on the fly</li>
<li>Make the application configurable</li>
