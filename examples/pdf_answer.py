from pydantic import BaseModel, Field
import asyncio
import workflowai
from workflowai.core.domain.model import Model
from workflowai.fields import File
import os
from dotenv import load_dotenv
from workflowai import Run, WorkflowAIError
from typing import List

# Load environment variables from .env file
load_dotenv()

class PDFQuestionInput(BaseModel):
    pdf: File = Field(description="The PDF document to analyze")
    question: str = Field(description="The question to answer about the PDF content")

class PDFAnswerOutput(BaseModel):
    answer: str = Field(description="The answer to the question based on the PDF content")
    quotes: List[str] = Field(description="Relevant quotes from the PDF that support the answer")

@workflowai.agent(id="pdf-answer", model=Model.CLAUDE_3_5_SONNET_LATEST)
async def answer_pdf_question(input: PDFQuestionInput) -> Run[PDFAnswerOutput]:
    """
    Analyze the provided PDF document and answer the given question.
    Provide a clear and concise answer based on the content found in the PDF.
    
    Focus on:
    - Accurate information extraction from the PDF
    - Direct and relevant answers to the question
    - Context-aware responses that consider the full document
    - Citing specific sections or pages when relevant
    
    If the question cannot be answered based on the PDF content,
    provide a clear explanation of why the information is not available.
    """
    ...

async def run_pdf_answer():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(current_dir, "pdfs", "sec-form-4.pdf")
    
    with open(pdf_path, "rb") as pdf_file:
        import base64
        content = base64.b64encode(pdf_file.read()).decode("utf-8")
    
    pdf = File(content_type='application/pdf', data=content)
    question = "How many stocks were sold? What is the total amount in USD?"
    
    try:
        agent_run = await answer_pdf_question(
            PDFQuestionInput(pdf=pdf, question=question),
            use_cache="auto"
        )
    except WorkflowAIError as e:
        print(f"Failed to run task. Code: {e.error.code}. Message: {e.error.message}")
        return

    print("\n--------\nAgent output:\n", agent_run.output, "\n--------\n")
    print(f"Cost: ${agent_run.cost_usd:.10f}")
    print(f"Latency: {agent_run.duration_seconds:.2f}s")

    # # using URL for PDF
    # pdf_url = "https://example.com/sample.pdf"
    # pdf = File(url=pdf_url)
    # question = "What are the key findings in the conclusion?"
    # agent_run = await answer_pdf_question(
    #     PDFQuestionInput(pdf=pdf, question=question),
    #     use_cache="auto"
    # )

    # print("\n--------\nAgent output:\n", agent_run.output, "\n--------\n")
    # print(f"Cost: ${agent_run.cost_usd:.10f}")
    # print(f"Latency: {agent_run.duration_seconds:.2f}s")

if __name__ == "__main__":
    asyncio.run(run_pdf_answer()) 