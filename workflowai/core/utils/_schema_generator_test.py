from pydantic import BaseModel

from workflowai.core.utils._schema_generator import JsonSchemaGenerator


class TestJsonSchemaGenerator:
    def test_generate(self):
        class TestModel(BaseModel):
            name: str

        schema = TestModel.model_json_schema(schema_generator=JsonSchemaGenerator)
        assert schema == {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
