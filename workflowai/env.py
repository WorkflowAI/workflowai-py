"""A file to describe all environment variables"""

import os

WORKFLOWAI_APP_URL = os.getenv("WORKFLOWAI_APP_URL", "workflowai.com")

WORKFLOWAI_DEFAULT_MODEL = os.getenv("WORKFLOWAI_DEFAULT_MODEL", "gemini-1.5-pro-latest")

WORKFLOWAI_API_URL = os.getenv("WORKFLOWAI_API_URL")

WORKFLOWAI_API_KEY = os.getenv("WORKFLOWAI_API_KEY", "")
