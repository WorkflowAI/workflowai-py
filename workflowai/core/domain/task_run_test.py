from typing import Optional

from pydantic import BaseModel

from workflowai.core.client.models import TaskRunResponse
from workflowai.core.domain.task import Task


class GenerateChangelogFromPropertiesTaskInput(BaseModel):
    temperature: Optional[float] = None


class GenerateChangelogFromPropertiesTaskOutput(BaseModel):
    changes: Optional[list[str]] = None


def test_task_run_model_validate():
    json_str = """{
    "id": "e3683ced-efd2-4b15-9ab4-aefdf17c4c19",
    "task_id": "generate-changelog-from-properties",
    "task_schema_id": 1,
    "task_input": {
        "temperature": 1
    },
    "task_input_hash": "6faebdc55135f380b00e7ada53f5cccc",
    "task_input_preview": "old_task_group: {properties: {temperature: 1, instructions: \\"Add 5 to the n",
    "task_output": {
        "changes": [
            "Temperature decreased from Creative to 0.73"
        ]
    },
    "task_output_hash": "d057c1f26fd8447c11cda7300e0f3717",
    "task_output_preview": "changes: [\\"Temperature decreased from Creative to 0.73\\"]",
    "group": {
        "id": "68eead780d01791ff2e09d39055ae6e8",
        "iteration": 36,
        "properties": {
            "model": "gemini-1.5-flash-002",
            "provider": "google",
            "temperature": 0,
            "instructions": "",
            "max_tokens": null,
            "runner_name": "WorkflowAI",
            "runner_version": "v0.1.0",
            "few_shot": null,
            "template_name": "v1",
            "task_variant_id": "fa546275ed8f6c801d6c6f174828d615"
        },
        "tags": [
            "model=gemini-1.5-flash-002",
            "provider=google",
            "temperature=0"
        ],
        "aliases": null,
        "is_external": null,
        "is_favorite": null,
        "notes": null,
        "similarity_hash": "",
        "benchmark_for_datasets": null
    },
    "status": "success",
    "error": null,
    "start_time": "2024-10-01T17:55:06.241000Z",
    "end_time": "2024-10-01T17:55:07.879000Z",
    "duration_seconds": 1.638103,
    "cost_usd": 0.00004651875,
    "created_at": "2024-10-01T17:55:07.879000Z",
    "updated_at": "2024-10-01T17:55:07.879000Z",
    "example_id": null,
    "corrections": null,
    "parent_task_ids": null,
    "scores": null,
    "labels": null,
    "metadata": {
        "used_alias": "environment=production"
    },
    "llm_completions": [
        {
            "messages": [
                {
                    "role": "system",
                    "content": ""
                },
                {
                    "role": "user",
                    "content": ""
                }
            ],
            "response": "{\\"changes\\": [\\"Temperature decreased from Creative to 0.73\\"]}",
            "usage": {
                "completion_token_count": 13.5,
                "completion_cost_usd": 0.00000405,
                "prompt_token_count": 566.25,
                "prompt_cost_usd": 0.00004246875
            }
        }
    ],
    "config_id": null,
    "dataset_benchmark_ids": null,
    "is_free": null,
    "author_tenant": null
}"""

    task_run = TaskRunResponse.model_validate_json(json_str).to_domain(
        Task(
            input_class=GenerateChangelogFromPropertiesTaskInput,
            output_class=GenerateChangelogFromPropertiesTaskOutput,
        ),
    )
    assert task_run.id == "e3683ced-efd2-4b15-9ab4-aefdf17c4c19"
