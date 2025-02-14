# Workflows Patterns

This README describes the five main patterns used in our workflows built using the WorkflowAI SDK. These patterns provide a structured method for composing complex AI tasks from simpler components, and allow you to balance flexibility and control in your AI applications.

## 1. Sequential Processing (Chains)
In this pattern, tasks are executed in a fixed sequence, where the output of one step becomes the input for the next. This is ideal for linear processes such as content generation, data transformation, or any task that benefits from a clear, step-by-step flow.

**Example:**
- Generate an initial result (e.g., marketing copy).
- Evaluate and refine that result through subsequent steps.

For an implementation example, see [chain.py](chain.py).

## 2. Routing
The routing pattern directs work based on intermediate results. An initial decision or classification determines which specialized agent should handle the next part of the workflow. This allows the system to adapt its behavior based on context (for instance, routing customer queries to different support teams).

**Example:**
- Classify a customer query (e.g., as general, refund, or technical).
- Route the query to a specialized agent that handles that particular type.

For an implementation example, see [routing.py](routing.py).

## 3. Parallel Processing
Parallel processing splits work into independent subtasks that run concurrently. This pattern is used when different aspects of an input can be handled independently, leading to faster overall processing times.

**Example:**
- Perform security, performance, and maintainability reviews on code simultaneously.
- Collect and aggregate the results after all tasks complete.

For an implementation example, see [parallel_processing.py](parallel_processing.py).

## 4. Orchestrator-Worker
In the orchestrator-worker pattern, one agent (the orchestrator) plans and coordinates the work, while multiple worker agents execute the individual parts of the plan in parallel. This pattern is particularly useful when a task can be decomposed into distinct planning and execution phases.

**Example:**
- An orchestrator analyzes a feature request and generates an implementation plan with details on file changes.
- Worker agents then execute the planned changes concurrently.

For an implementation example, see [orchestrator_worker.py](orchestrator_worker.py).

## 5. Evaluator-Optimizer
The evaluator-optimizer pattern employs an iterative feedback loop. An initial output is evaluated for quality, and based on the feedback, improvements are made. This cycle is repeated until the output reaches the desired quality, or a maximum number of iterations is met.

**Example:**
- Translate text using a fast initial model.
- Evaluate the translation's quality, tone, nuance, and cultural accuracy.
- If needed, refine the translation based on detailed feedback and repeat the process.

For an implementation example, see [evaluator_optimizer.py](evaluator_optimizer.py).

## 6. Chain of Agents (Long Context Processing)
The Chain of Agents pattern is designed for processing long documents or complex tasks that exceed the context window of a single model. In this pattern, multiple worker agents process different chunks of the input sequentially, passing their findings through the chain, while a manager agent synthesizes the final output.

**Example:**
- Split a long document into manageable chunks
- Worker agents process each chunk sequentially, building upon previous findings
- A manager agent synthesizes all findings into a final, coherent response

For an implementation example, see [chain_of_agents.py](chain_of_agents.py).

## 7. Agent Delegation
The Agent Delegation pattern enables dynamic and flexible workflows where one agent can invoke other agents through tools. This pattern is particularly useful when you want an agent to dynamically choose which specialized agents to use based on the task at hand, rather than having a fixed sequence or structure.

**Key Features:**
- Dynamic model selection based on task requirements
- Flexible workflow that adapts based on initial responses
- Ability to track which agents were used and why
- Built-in confidence scoring for quality control

**Example:**
- An orchestrator agent receives a complex task (e.g., system architecture design)
- It breaks down the task into smaller components
- For each component, it:
  - Chooses the most appropriate model (e.g., GPT-4 for reasoning, Claude for analysis)
  - Delegates the work through a tool
  - Evaluates the response and confidence level
  - Requests additional work if needed
- Finally, it synthesizes all responses into a coherent solution

For an implementation example, see [agent_delegation.py](agent_delegation.py).

---

These patterns were inspired by the workflow patterns described in the [Vercel AI SDK Documentation](https://sdk.vercel.ai/docs/foundations/agents#patterns-with-examples) and research from organizations like [Google Research](https://research.google/blog/chain-of-agents-large-language-models-collaborating-on-long-context-tasks/).

This README should serve as a high-level guide to understanding and using the different patterns available in our workflows.
