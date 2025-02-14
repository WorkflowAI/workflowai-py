"""
This implementation is inspired by Google Research's Chain of Agents (CoA) framework:
https://research.google/blog/chain-of-agents-large-language-models-collaborating-on-long-context-tasks/

CoA is a training-free, task-agnostic framework for handling long-context tasks through LLM collaboration.
Instead of trying to fit everything into a single context window, it:
1. Breaks input into manageable chunks
2. Uses worker agents to process chunks sequentially, passing information forward
3. Uses a manager agent to synthesize the final answer

Key benefits of this approach:
- More efficient than full-context processing (O(nk) vs O(n²) complexity)
- Better performance than RAG for complex reasoning tasks
- Scales well with input length (performance improves with longer inputs)
- No training required, works with any LLM
"""

import asyncio

from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]

import workflowai
from workflowai import Model


class DocumentChunk(BaseModel):
    """A chunk of text from a long document."""

    content: str = Field(description="The content of this document chunk.")


class WorkerInput(BaseModel):
    """Input for a worker agent processing a document chunk."""

    chunk: DocumentChunk = Field(description="The current chunk to process.")
    query: str = Field(description="The query or task to be answered.")
    previous_findings: str = Field(
        default="",
        description="Accumulated findings from previous workers.",
    )


class WorkerOutput(BaseModel):
    """Output from a worker agent containing findings and evidence."""

    findings: str = Field(
        description="Key findings and information extracted from this chunk.",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Supporting evidence or quotes from the chunk.",
    )
    message_for_next: str = Field(
        description="Message to pass to the next worker with relevant context.",
    )


class ManagerInput(BaseModel):
    """Input for the manager agent to generate final response."""

    query: str = Field(description="The original query to answer.")
    accumulated_findings: str = Field(
        description="All findings accumulated through the worker chain.",
    )


class ManagerOutput(BaseModel):
    """Final output from the manager agent."""

    answer: str = Field(description="The final answer to the query.")
    reasoning: str = Field(description="Explanation of how the answer was derived.")
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="Key evidence supporting the answer.",
    )


@workflowai.agent(id="document-worker", model=Model.GPT_4O_MINI_LATEST)
async def worker_agent(_: WorkerInput) -> WorkerOutput:
    """
    Process your assigned document chunk to:
    1. Extract relevant information related to the query
    2. Build upon findings from previous workers
    3. Pass important context to the next worker

    Be concise but thorough in your analysis.
    Focus on information that could be relevant to the query.
    """
    ...


@workflowai.agent(id="document-manager", model=Model.CLAUDE_3_5_SONNET_LATEST)
async def manager_agent(_: ManagerInput) -> ManagerOutput:
    """
    Synthesize all findings from the worker agents to:
    1. Generate a comprehensive answer to the query
    2. Provide clear reasoning for your answer
    3. Include supporting evidence from the document

    Ensure your answer is well-supported by the accumulated findings.
    """
    ...


async def process_long_document(
    document: str,
    query: str,
    chunk_size: int = 2000,
) -> ManagerOutput:
    """
    Process a long document using Chain of Agents pattern:
    1. Split document into chunks
    2. Have worker agents process each chunk sequentially
    3. Pass findings through the chain
    4. Have manager agent synthesize final answer
    """
    # Split document into chunks
    chunks = [document[i : i + chunk_size] for i in range(0, len(document), chunk_size)]

    # Convert to DocumentChunk objects
    doc_chunks = [DocumentChunk(content=chunk) for chunk in chunks]

    # Initialize accumulator for findings
    accumulated_findings = ""

    # Process chunks sequentially through worker chain
    for chunk in doc_chunks:
        worker_input = WorkerInput(
            chunk=chunk,
            query=query,
            previous_findings=accumulated_findings,
        )

        # Get worker's output
        worker_output = await worker_agent(worker_input)

        # Accumulate findings
        if accumulated_findings:
            accumulated_findings += "\n\n"
        accumulated_findings += f"Findings:\n{worker_output.findings}"

        if worker_output.evidence:
            accumulated_findings += "\nEvidence:\n- "
            accumulated_findings += "\n- ".join(worker_output.evidence)

    # Have manager synthesize final answer
    manager_input = ManagerInput(
        query=query,
        accumulated_findings=accumulated_findings,
    )

    return await manager_agent(manager_input)


async def main():
    # Example long document
    document = """
    The Industrial Revolution was a period of major industrialization and innovation during the late 18th and early 19th centuries. It began in Britain and later spread to other parts of the world. This era marked a major turning point in human history, fundamentally changing economic and social organization. Steam power, mechanization, and new manufacturing processes revolutionized production methods. The introduction of new technologies and manufacturing techniques led to unprecedented increases in productivity and efficiency.

    The development of new manufacturing processes led to significant changes in how goods were produced. The factory system replaced cottage industries, bringing workers into centralized locations. New iron production processes using coke instead of charcoal dramatically increased output. Textile manufacturing was transformed by inventions like the spinning jenny and power loom. These changes enabled mass production of goods at unprecedented scales. The mechanization of agriculture through innovations like the seed drill and threshing machine reduced the labor needed for farming while increasing food production.

    Social and economic impacts were profound, affecting both urban and rural life. Cities grew rapidly as people moved from rural areas to work in factories. Working conditions were often harsh, with long hours, dangerous conditions, and child labor being common. A new middle class emerged, while traditional skilled craftsmen often struggled. Living conditions in industrial cities were frequently overcrowded and unsanitary, leading to disease outbreaks. The rise of labor movements and trade unions began in response to poor working conditions and low wages. Education systems were developed to provide workers with basic literacy and numeracy skills needed in the new industrial economy.

    Environmental consequences became apparent as industrialization progressed. Coal burning led to severe air pollution in industrial cities, creating smog and respiratory problems. Rivers became contaminated with industrial waste and raw sewage. Deforestation increased as wood was needed for construction and fuel. The landscape was transformed by mines, factories, and expanding urban areas. These changes marked the beginning of large-scale human impact on the environment, leading to problems that would only be recognized and addressed much later.

    Transportation and communication systems underwent revolutionary changes during this period. The development of railways, steam-powered ships, and improved road networks facilitated the movement of goods and people. The telegraph enabled rapid long-distance communication for the first time. These advances in transportation and communication helped create larger markets and more integrated economies.

    The Industrial Revolution also had significant cultural and intellectual impacts. Scientific and technological progress led to increased faith in human capability and reason. The Enlightenment ideals of progress and rationality found practical expression in industrial innovations. New forms of urban culture emerged, while traditional rural ways of life declined. The period saw the rise of new philosophical and political movements, including socialism, in response to industrial conditions.

    Public health and medicine saw both challenges and advances during this period. The concentration of population in cities led to serious health problems, including cholera epidemics and tuberculosis outbreaks. However, these challenges eventually spurred improvements in urban sanitation and medical knowledge. The development of public health systems and modern medical practices can be traced to this era.

    The Industrial Revolution's impact on agriculture extended beyond mechanization. New farming techniques and crop rotation methods increased agricultural productivity. The application of scientific principles to farming led to improved livestock breeding and crop yields. These agricultural advances were necessary to feed growing urban populations and free up labor for industrial work.

    The financial and business systems also evolved significantly. New forms of business organization, such as joint-stock companies, emerged to handle larger-scale industrial operations. Banking and credit systems expanded to provide capital for industrial growth. Insurance companies developed to manage the risks of industrial enterprises. These financial innovations helped fuel continued industrial expansion.

    The role of women in society began to change during this period. While many women worked in factories under difficult conditions, the Industrial Revolution also created new opportunities for women's employment in sectors like textile manufacturing. Middle-class women often found themselves managing increasingly complex households. The seeds of women's rights movements were planted during this era.

    The global impact of the Industrial Revolution was profound and long-lasting. As industrialization spread from Britain to other countries, it created new patterns of international trade and competition. Colonial empires expanded as industrial nations sought raw materials and markets. The technological and economic gaps between industrialized and non-industrialized regions grew, shaping global relationships that persist to the present day.

    The Industrial Revolution's legacy continues to influence modern society. Many current environmental challenges, including climate change, can be traced to the industrial practices established during this period. Modern labor laws, education systems, and urban planning still reflect responses to Industrial Revolution conditions. Understanding this transformative period helps explain many aspects of contemporary life and the ongoing challenges we face.
    """  # noqa: E501

    query = "What were the major environmental impacts of the Industrial Revolution?"

    run = await process_long_document(document, query)

    print("\n=== Query ===")
    print(query)

    print("\n=== Answer ===")
    print(run.answer)

    print("\n=== Reasoning ===")
    print(run.reasoning)

    if run.supporting_evidence:
        print("\n=== Supporting Evidence ===")
        for evidence in run.supporting_evidence:
            print(f"- {evidence}")


if __name__ == "__main__":
    asyncio.run(main())
