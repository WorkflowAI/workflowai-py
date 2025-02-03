import workflowai
from workflowai import Model
from pydantic import BaseModel, Field
import asyncio
from enum import Enum
from typing import List, TypedDict


class ChangeType(str, Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class ComplexityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FileChange(BaseModel):
    """Describes a planned change to a file."""
    purpose: str = Field(description="Purpose of the change in the context of the feature.")
    file_path: str = Field(description="Path to the file to be changed.")
    change_type: ChangeType = Field(description="Type of change to be made.")


class ImplementationPlanInput(BaseModel):
    """Input for generating an implementation plan."""
    feature_request: str = Field(description="The feature request to implement.")


class ImplementationPlanOutput(BaseModel):
    """Output containing the implementation plan."""
    files: List[FileChange] = Field(description="List of files to be changed.")
    estimated_complexity: ComplexityLevel = Field(description="Estimated complexity of the implementation.")


# Uses O1 for its strong architectural planning capabilities
@workflowai.agent(id='implementation-planner', model=Model.O1_2024_12_17_HIGH_REASONING_EFFORT)
async def plan_implementation_agent(
    input: ImplementationPlanInput
) -> ImplementationPlanOutput:
    """
    Senior software architect planning feature implementations.
    Analyze feature requests and create detailed implementation plans.
    """
    ...


class FileImplementationInput(BaseModel):
    """Input for implementing file changes."""
    file_path: str = Field(description="Path to the file being changed.")
    purpose: str = Field(description="Purpose of the change.")
    feature_request: str = Field(description="Overall feature context.")
    change_type: ChangeType = Field(description="Type of change being made.")


class FileImplementationOutput(BaseModel):
    """Output containing the implemented changes."""
    explanation: str = Field(description="Explanation of the implemented changes.")
    code: str = Field(description="The implemented code changes.")


# Uses GPT-4O for its strong code generation and modification capabilities
@workflowai.agent(id='file-implementer', model=Model.GPT_4O_LATEST)
async def implement_file_changes_agent(
    input: FileImplementationInput
) -> FileImplementationOutput:
    """
    Expert at implementing code changes based on the change type:
    - CREATE: Implement new files following best practices and project patterns
    - MODIFY: Modify existing code while maintaining consistency
    - DELETE: Safely remove code while ensuring no breaking changes
    """
    ...


class ImplementationChange(TypedDict):
    file: FileChange
    implementation: FileImplementationOutput


class FeatureImplementationResult(TypedDict):
    plan: ImplementationPlanOutput
    changes: List[ImplementationChange]


async def implement_feature(feature_request: str) -> FeatureImplementationResult:
    """
    Implement a feature using an orchestrator-worker pattern:
    1. Orchestrator (planner) analyzes the request and creates an implementation plan
    2. Workers execute the planned changes in parallel
    3. Return both the plan and implemented changes
    """
    # Orchestrator: Plan the implementation
    implementation_plan = await plan_implementation_agent(
        ImplementationPlanInput(feature_request=feature_request)
    )

    # Workers: Execute the planned changes in parallel
    file_changes = await asyncio.gather(*[
        implement_file_changes_agent(
            FileImplementationInput(
                file_path=file.file_path,
                purpose=file.purpose,
                feature_request=feature_request,
                change_type=file.change_type
            )
        ) for file in implementation_plan.files
    ])

    # Combine results
    changes: List[ImplementationChange] = [
        {
            "file": implementation_plan.files[i],
            "implementation": change
        }
        for i, change in enumerate(file_changes)
    ]

    return {
        "plan": implementation_plan,
        "changes": changes
    }


if __name__ == "__main__":
    # Example feature request
    feature_request = """
    Add a new user authentication endpoint that:
    1. Accepts username/password
    2. Validates credentials
    3. Returns a JWT token
    4. Includes rate limiting
    """

    result = asyncio.run(implement_feature(feature_request))
    
    print("\n=== Implementation Plan ===")
    print(f"Estimated Complexity: {result['plan'].estimated_complexity}")
    print("\nPlanned Changes:")
    for file in result['plan'].files:
        print(f"\n- {file.change_type.upper()}: {file.file_path}")
        print(f"  Purpose: {file.purpose}")
    
    print("\n=== Implemented Changes ===")
    for change in result['changes']:
        file = change['file']
        impl = change['implementation']
        
        print(f"\n=== {file.change_type.upper()}: {file.file_path} ===")
        print("\nPurpose:")
        print(file.purpose)
        print("\nExplanation:")
        print(impl.explanation)
        print("\nCode:")
        print(impl.code)
    print() 