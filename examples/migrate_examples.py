import asyncio
from typing import Callable, TypeVar

from pydantic import BaseModel

import workflowai
from examples.schemas import schema_13, schema_19
from workflowai import Client, Task
from workflowai.core.domain.task_example import TaskExample

_FromTaskInput = TypeVar("_FromTaskInput", bound=BaseModel)
_ToTaskInput = TypeVar("_ToTaskInput", bound=BaseModel)
_FromTaskOutput = TypeVar("_FromTaskOutput", bound=BaseModel)
_ToTaskOutput = TypeVar("_ToTaskOutput", bound=BaseModel)

Migrator = Callable[
    [_FromTaskInput, _FromTaskOutput], tuple[_ToTaskInput, _ToTaskOutput]
]


async def migrate_examples(
    client: Client,
    from_task: Task[_FromTaskInput, _FromTaskOutput],
    to_task: Task[_ToTaskInput, _ToTaskOutput],
    migrate_fn: Migrator[_FromTaskInput, _FromTaskOutput, _ToTaskInput, _ToTaskOutput],
):
    examples = await client.list_examples(from_task)
    print(f"Found {len(examples.items)} examples to migrate")  # noqa T001

    existing_examples = await client.list_examples(to_task)
    existing_example_hashes = {
        example.task_input_hash for example in existing_examples.items
    }

    print(f"Found {len(existing_examples.items)} existing examples")  # noqa T001

    for example in examples.items:
        if example.task_input_hash in existing_example_hashes:
            print(  # noqa T001
                f"Skipping example {example.id} as it already exists in the target task"
            )
            continue

        to_input, to_output = migrate_fn(example.task_input, example.task_output)
        print("Importing example", example.id)  # noqa T001
        await client.import_example(
            TaskExample(
                task=to_task,
                task_input=to_input,
                task_output=to_output,
            )
        )


def _default_migrate_fn(from_input: BaseModel, to: type[_ToTaskInput]):
    return to.model_validate(from_input.model_dump(mode="json"))


_LINE_ITEM_SYSTEM_MAP = {
    schema_13.LineItemSystem.CPT: schema_19.LineItemSystem.CPT,
    schema_13.LineItemSystem.ICD: schema_19.LineItemSystem.ICD_10,
    schema_13.LineItemSystem.HCPCS: schema_19.LineItemSystem.HCPCS,
    schema_13.LineItemSystem.OTHER: schema_19.LineItemSystem.OTHER,
}


def _migrade_line_item(from_line_item: schema_13.LineItem):
    return schema_19.LineItem(
        line_item_sequence=from_line_item.line_item_sequence,
        line_item_code=from_line_item.line_item_code,
        line_item_service_description=from_line_item.line_item_service_description,
        line_item_occurrence_date=from_line_item.line_item_occurrence_date,
        line_item_type=schema_19.LineItemType(from_line_item.line_item_type.value),
        line_item_amount=from_line_item.line_item_amount,
        line_item_system=_LINE_ITEM_SYSTEM_MAP[from_line_item.line_item_system],
    )


def _migrate_billing_period(from_billing_period: schema_13.BillingPeriod):
    return schema_19.BillingPeriod(
        start_date=from_billing_period.start_date.date(),
        end_date=from_billing_period.end_date.date(),
    )


def medical_invoice_migrate_fn(
    from_input: schema_13.MedicalInvoiceImageExtractionTaskInput,
    from_output: schema_13.MedicalInvoiceImageExtractionTaskOutput,
):
    to_input = _default_migrate_fn(
        from_input, schema_19.MedicalInvoiceImageExtractionTaskInput
    )

    to_output = schema_19.MedicalInvoiceImageExtractionTaskOutput(
        issuer=_default_migrate_fn(from_output.issuer, schema_19.Issuer),
        recipient=_default_migrate_fn(from_output.recipient, schema_19.Recipient),
        creation_date=from_output.creation_date,
        status=schema_19.Status(from_output.status.value),
        isPaid=from_output.isPaid,
        subject=_default_migrate_fn(from_output.subject, schema_19.Subject),
        billing_period=_migrate_billing_period(from_output.billing_period),
        invoice_identifier=from_output.invoice_identifier,
        line_items=[_migrade_line_item(item) for item in from_output.line_items],
        total_net_amount=from_output.total_net_amount,
        total_gross_amount=from_output.total_gross_amount,
        payment_notes=from_output.payment_notes,
        payment_terms=from_output.payment_terms,
        practitioner=_default_migrate_fn(
            from_output.practitioner, schema_19.Practitioner
        ),
        service_date=from_output.service_date,
    )
    return to_input, to_output


if __name__ == "__main__":
    client = workflowai.start()

    from_task = schema_13.MedicalInvoiceImageExtractionTask()
    to_task = schema_19.MedicalInvoiceImageExtractionTask()

    asyncio.run(
        migrate_examples(client, from_task, to_task, medical_invoice_migrate_fn)
    )
