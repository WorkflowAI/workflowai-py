from typing import Any, AsyncIterator, Literal, Optional, TypeVar, Union, overload

import httpx
from pydantic import BaseModel, TypeAdapter, ValidationError

from workflowai.core.client.utils import split_chunks
from workflowai.core.domain.errors import BaseError, ErrorResponse, WorkflowAIError

# A type for return values
_R = TypeVar("_R")
_M = TypeVar("_M", bound=BaseModel)


class APIClient:
    def __init__(self, endpoint: str, api_key: str, source_headers: Optional[dict[str, str]] = None):
        self.endpoint = endpoint
        self.api_key = api_key
        self.source_headers = source_headers or {}

        if not self.endpoint or not self.api_key:
            raise ValueError("Missing API URL or key")

    def _client(self) -> httpx.AsyncClient:
        client = httpx.AsyncClient(
            base_url=self.endpoint,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                **(self.source_headers or {}),
            },
            timeout=120.0,
        )
        return client

    async def get(self, path: str, returns: type[_R], query: Union[dict[str, Any], None] = None) -> _R:
        async with self._client() as client:
            response = await client.get(path, params=query)
            response.raise_for_status()
            return TypeAdapter(returns).validate_python(response.json())

    @overload
    async def post(self, path: str, data: BaseModel, returns: type[_R]) -> _R: ...

    @overload
    async def post(self, path: str, data: BaseModel) -> None: ...

    async def post(
        self,
        path: str,
        data: BaseModel,
        returns: Optional[type[_R]] = None,
    ) -> Optional[_R]:
        async with self._client() as client:
            response = await client.post(
                path,
                content=data.model_dump_json(exclude_none=True),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            if not returns:
                return None
            return TypeAdapter(returns).validate_python(response.json())

    @overload
    async def patch(self, path: str, data: BaseModel, returns: type[_R]) -> _R: ...

    @overload
    async def patch(self, path: str, data: BaseModel) -> None: ...

    async def patch(
        self,
        path: str,
        data: BaseModel,
        returns: Optional[type[_R]] = None,
    ) -> Optional[_R]:
        async with self._client() as client:
            response = await client.patch(
                path,
                content=data.model_dump_json(exclude_none=True),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            if not returns:
                return None
            return TypeAdapter(returns).validate_python(response.json())

    async def delete(self, path: str) -> None:
        async with self._client() as client:
            response = await client.delete(path)
            response.raise_for_status()

    def _extract_error(self, data: Union[bytes, str], exception: Optional[Exception] = None) -> WorkflowAIError:
        try:
            res = ErrorResponse.model_validate_json(data)
            return WorkflowAIError(res.error, task_run_id=res.task_run_id)
        except ValidationError:
            raise WorkflowAIError(
                error=BaseError(
                    message="Unknown error" if exception is None else str(exception),
                    details={
                        "raw": str(data),
                    },
                ),
            ) from exception

    async def stream(
        self,
        method: Literal["GET", "POST"],
        path: str,
        data: BaseModel,
        returns: type[_M],
    ) -> AsyncIterator[_M]:
        async with self._client() as client, client.stream(
            method,
            path,
            content=data.model_dump_json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        ) as response:
            async for chunk in response.aiter_bytes():
                payload = ""
                try:
                    for payload in split_chunks(chunk):
                        yield returns.model_validate_json(payload)
                except ValidationError as e:
                    raise self._extract_error(payload, e) from None
