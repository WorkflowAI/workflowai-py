import os

from workflowai import fields


def test_exported_fields_match_core_fields():
    # Get the number of exported fields in fields.py
    exported_fields = {attr for attr in dir(fields) if not attr.startswith("_")}

    # Get the number of files in workflowai/core/fields
    core_fields_dir = os.path.join(os.path.dirname(__file__), "core", "fields")
    core_field_files = {
        "".join(word.capitalize() for word in f.removesuffix(".py").split("_"))
        for f in os.listdir(core_fields_dir)
        if f.endswith(".py") and f != "__init__.py" and not f.endswith("_test.py")
    }

    assert len(core_field_files) == len(exported_fields)
