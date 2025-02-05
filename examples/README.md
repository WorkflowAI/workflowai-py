# WorkflowAI Examples

This directory contains example agents demonstrating different capabilities of the WorkflowAI SDK.

## Basic Examples

### 1. Basic Agent
[01_basic_agent.py](./01_basic_agent.py)

A simple agent that takes a city name and returns information about its country's capital. Demonstrates:
- Basic agent creation with input/output models
- Field descriptions and examples
- Cost and latency tracking

### 2. Agent with Tools
[02_agent_with_tools.py](./02_agent_with_tools.py)

Shows how to create agents that can use tools to enhance their capabilities:
- Using hosted tools (@browser-text, @search)
- Creating custom tools
- Handling tool responses

### 3. Caching Behavior
[03_caching.py](./03_caching.py)

Demonstrates different caching options in WorkflowAI using a medical SOAP notes extractor:
- 'auto' - Cache only when temperature is 0 (default)
- 'always' - Always use cache if available
- 'never' - Never use cache, always execute new runs

## Media Analysis Examples

### 4. Audio Analysis
[04_audio_classifier_agent.py](./04_audio_classifier_agent.py)

An agent that analyzes audio recordings for spam/robocall detection. Demonstrates:
- Using audio files as input
- Structured classification with confidence scores
- Detailed reasoning about audio content

Required asset:
- `assets/call.mp3` - Example audio file for spam detection

### 5. Browser Text Tool
[05_browser_text_uptime_agent.py](./05_browser_text_uptime_agent.py)

Demonstrates using the `@browser-text` tool to:
- Fetch content from status pages
- Extract uptime percentages
- Handle different page formats
- Process real-time web data

### 6. Streaming Example
[06_streaming_summary.py](./06_streaming_summary.py)

Shows how to use streaming to get real-time output from agents:
- Stream translations as they're generated
- Track progress with chunk numbers
- Access run metadata (cost, latency)

### 7. Image Analysis
[07_image_agent.py](./07_image_agent.py)

An agent that identifies cities from images. Given a photo of a city, it:
- Identifies the city and country
- Explains the reasoning behind the identification
- Lists key landmarks or architectural features
- Provides confidence level in the identification

Required asset:
- `assets/new-york-city.jpg` - Example city image for identification

### 8. PDF Analysis
[08_pdf_agent.py](./08_pdf_agent.py)

An agent that answers questions about PDF documents. Given a PDF and a question, it:
- Analyzes the PDF content
- Provides a clear and concise answer
- Includes relevant quotes from the document to support its answer

Required asset:
- `assets/sec-form-4.pdf` - Example SEC form for document analysis

## Workflow Pattern Examples

The [workflows](./workflows) directory contains examples of different workflow patterns for complex tasks:

1. **Chain of Agents** - Process long documents by breaking them into chunks
2. **Routing** - Direct queries to specialized agents based on type
3. **Parallel Processing** - Run multiple analyses concurrently
4. **Orchestrator-Worker** - Coordinate multiple agents for complex tasks

See [workflows/README.md](./workflows/README.md) for detailed information about each pattern.

## Asset Dependencies

All example assets should be placed in the `assets/` directory at the root of the project:

```
workflowai-py/
├── assets/
│   ├── call.mp3              # For audio classifier
│   ├── new-york-city.jpg     # For image agent
│   └── sec-form-4.pdf        # For PDF agent
├── examples/
│   ├── 01_basic_agent.py
│   ├── 02_agent_with_tools.py
│   └── ...
```

## Running the Examples

1. Make sure you have the required assets in the `assets/` directory
2. Set up your environment variables in `.env`:
   ```
   WORKFLOWAI_API_KEY=your_api_key
   ```
3. Run any example using Python:
   ```bash
   python examples/01_basic_agent.py
   ``` 