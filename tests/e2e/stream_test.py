from typing import Optional

import pytest
from pydantic import BaseModel

import workflowai
from workflowai.core.domain.task import Task


class ImprovePromptTaskInput(BaseModel):
    original_prompt: Optional[str] = None
    prompt_input: Optional[str] = None
    prompt_output: Optional[str] = None
    user_evaluation: Optional[str] = None


class ImprovePromptTaskOutput(BaseModel):
    improved_prompt: Optional[str] = None
    changelog: Optional[str] = None


class ImprovePromptTask(Task[ImprovePromptTaskInput, ImprovePromptTaskOutput]):
    id: str = "improve-prompt"
    schema_id: int = 3
    input_class: type[ImprovePromptTaskInput] = ImprovePromptTaskInput
    output_class: type[ImprovePromptTaskOutput] = ImprovePromptTaskOutput


@pytest.mark.skip("This hits the API")
async def test_stream_task(wai: workflowai.Client):
    task = ImprovePromptTask()

    task_input = ImprovePromptTaskInput(
        original_prompt="Say hello to the guest",
        prompt_input='{"guest": "John", "language": "French"}',
        prompt_output='{"greeting": "Hello John"}',
        user_evaluation="Not in the right language",
    )

    streamed = await wai.run(task, task_input=task_input, stream=True, use_cache="never")
    chunks = [chunk async for chunk in streamed]

    assert len(chunks) > 1
