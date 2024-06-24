import uuid

import workflowai
from examples.city_to_capital_task import CityToCapitalTask, CityToCapitalTaskInput
from workflowai.core.domain.task_version_reference import TaskVersionReference


async def test_deploy_task(wai: workflowai.Client):
    task = CityToCapitalTask(
        id=f"citytocapital-{uuid.uuid4()}",
        schema_id=0,
        version=TaskVersionReference.with_properties(model=""),
    )

    await wai.register(task)

    assert task.schema_id == 1

    # Run task with input
    task_run = await wai.run(task, task_input=CityToCapitalTaskInput(city="Osaka"))
    assert task_run.task_output.capital == "Tokyo"
    assert task_run.version.iteration == 1

    # Deploy group to dev environnment
    version = await wai.deploy_version(task, iteration=1, environment="dev")
    assert version.iteration == 1
    assert version.aliases == {"environment=dev"}

    # Run using the environment and the same input
    task_run2 = await wai.run(
        task, task_input=CityToCapitalTaskInput(city="Osaka"), environment="dev"
    )
    # IDs will match since we are using cache
    assert task_run.id == task_run2.id

    # Run using the environment and a different input
    task_run3 = await wai.run(
        task, task_input=CityToCapitalTaskInput(city="Toulouse"), environment="dev"
    )
    assert task_run3.task_output.capital == "Paris"
    assert task_run3.id != task_run2.id
