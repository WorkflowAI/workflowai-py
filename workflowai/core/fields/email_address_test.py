import pytest
from pydantic import BaseModel

from .email_address import EmailAddressStr


class _ModelWithEmail(BaseModel):
    email: EmailAddressStr


@pytest.mark.parametrize(
    "email",
    [
        "email@example.com",
        "firstname.lastname@example.com",
        "email@subdomain.example.com",
        "firstname+lastname@example.com",
        "1234567890@example.com",
        "email@example-one.com",
        "email@example.name",
        "email@example.museum",
        "email@example.co.jp",
        "firstname-lastname@example.com",
    ],
)
def test_email_validation_with_valid_emails(email: str) -> None:
    _ModelWithEmail(email=email)


@pytest.mark.parametrize(
    "email",
    [
        "plainaddress",
        "@no-local-part.com",
        "Outlook Contact <outlook_contact@domain.com>",
        "no-at-sign.com",
        "no-tld@domain",
        ";beginning-semicolon@domain.co.uk",
        "middle-semicolon@domain.co;uk",
        "trailing-semicolon@domain.com;",
        '"email-with-quotes"@domain.com',
        "spaces in local@domain.com",
        "email@domain.com (Joe Smith)",
        "email@domain@domain.com",
        ".email@domain.com",
        "email.@domain.com",
        "email..email@domain.com",
        "あいうえお@domain.com",
        "email@-domain.com",
        "email@domain..com",
    ],
)
def test_email_validation_with_invalid_emails(email: str) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        _ModelWithEmail(email=email)


def test_email_address_str_json_schema() -> None:
    schema = _ModelWithEmail.model_json_schema()
    assert schema == {
        "properties": {
            "email": {
                "examples": ["john.doe@example.com"],
                "format": "email",
                "title": "Email",
                "type": "string",
            },
        },
        "required": ["email"],
        "title": "_ModelWithEmail",
        "type": "object",
    }
