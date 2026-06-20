import base64
import json

import pytest

from app.services.firebase import _parse_credentials_json


def _sample_service_account() -> dict:
    return {
        "type": "service_account",
        "project_id": "demo-project",
        "private_key_id": "abc123",
        "private_key": "-----BEGIN PRIVATE KEY-----\nline1\nline2\n-----END PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk@test.iam.gserviceaccount.com",
        "client_id": "123",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }


def test_parse_credentials_json_single_line():
    payload = json.dumps(_sample_service_account())
    parsed = _parse_credentials_json(payload)
    assert parsed["project_id"] == "demo-project"


def test_parse_credentials_json_with_literal_private_key_newlines():
    creds = _sample_service_account()
    broken = json.dumps({k: v for k, v in creds.items() if k != "private_key"})
    broken = broken[:-1] + ', "private_key": "-----BEGIN PRIVATE KEY-----\nline1\nline2\n-----END PRIVATE KEY-----\n"}'
    parsed = _parse_credentials_json(broken)
    assert "BEGIN PRIVATE KEY" in parsed["private_key"]


def test_parse_credentials_json_base64_roundtrip():
    creds = _sample_service_account()
    encoded = base64.b64encode(json.dumps(creds).encode()).decode()
    decoded = json.loads(base64.b64decode(encoded))
    assert decoded["client_email"] == creds["client_email"]
