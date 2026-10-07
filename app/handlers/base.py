"""BaseHandler: auth, correlation id, body parsing, pagination parsing, error envelope."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from http import HTTPStatus
from typing import Any, Iterable, TypeVar

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from tornado import web

from app.core.errors import AppError, BadRequestError, NotFoundError, UnauthorizedError, ValidationFailedError
from app.core.logging_config import correlation_id_var
from app.core.pagination import SORT_ASC, SORT_DESC, Page, PageRequest
from app.core.unit_of_work import UnitOfWork
from app.schemas.common import ApiModel

logger = logging.getLogger(__name__)

SchemaT = TypeVar("SchemaT", bound=ApiModel)
ServiceT = TypeVar("ServiceT")


class BaseHandler(web.RequestHandler):
    """Thin entry layer base. Subclasses set ``public = True`` to skip JWT auth.

    Every handler gets the :class:`AppContext` via ``initialize(ctx=...)``.
    """

    public = False

    def initialize(self, ctx) -> None:  # noqa: D401 - tornado hook
        self.ctx = ctx
        self._uow: UnitOfWork | None = None
        self._user_id: int | None = None

    # ---------------------------------------------------------------- lifecycle
    async def prepare(self) -> None:
        correlation_id = (self.request.headers.get("X-Request-ID")
                          or self.request.headers.get("X-Correlation-ID")
                          or uuid.uuid4().hex)
        correlation_id_var.set(correlation_id)
        self.set_header("X-Request-ID", correlation_id)
        if not self.public:
            self._user_id = self._authenticate()

    async def _execute(self, transforms, *args, **kwargs):  # noqa: D401 - tornado hook
        """Run the request, then always release this request's DB session."""
        try:
            await super()._execute(transforms, *args, **kwargs)
        finally:
            await self._release_uow()

    async def _release_uow(self) -> None:
        if self._uow is not None:
            uow, self._uow = self._uow, None
            try:
                await uow.close()
            except Exception:  # noqa: BLE001 - boundary: closing must never fail the request
                logger.warning("Failed to close DB session", exc_info=True)

    def set_default_headers(self) -> None:
        self.set_header("Content-Type", "application/json; charset=UTF-8")

    def check_xsrf_cookie(self) -> None:  # API uses bearer tokens, not cookies
        return None

    # -------------------------------------------------------------------- auth
    def _authenticate(self) -> int:
        header = self.request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise UnauthorizedError("Missing or malformed Authorization header")
        return self.ctx.tokens.verify(token.strip())

    @property
    def current_user_id(self) -> int:
        if self._user_id is None:
            raise UnauthorizedError("Authentication required")
        return self._user_id

    # ---------------------------------------------------------- DI / services
    @property
    def uow(self) -> UnitOfWork:
        if self._uow is None:
            self._uow = self.ctx.new_uow()
        return self._uow

    def service(self, service_cls: type[ServiceT]) -> ServiceT:
        """Build a request-scoped service via the context's registry."""
        return self.ctx.registry.build(service_cls, self.uow)

    # ----------------------------------------------------------------- request
    def parse_json_object(self) -> dict[str, Any]:
        try:
            body = json.loads(self.request.body or b"", parse_float=Decimal)
        except (ValueError, UnicodeDecodeError) as exc:
            raise BadRequestError("Request body must be valid JSON") from exc
        if not isinstance(body, dict):
            raise BadRequestError("Request body must be a JSON object")
        return body

    def parse_body(self, schema: type[SchemaT]) -> SchemaT:
        """Parse the JSON body once and validate it; pydantic errors map to 422 centrally."""
        return schema.model_validate(self.parse_json_object())

    def page_request(self, sort_fields: Iterable[str], default_sort: str,
                     default_dir: str = SORT_ASC) -> PageRequest:
        settings = self.ctx.settings
        allowed = list(sort_fields)
        size = self._query_int("size", None)
        if size is None:
            size = self._query_int("limit", settings.default_page_size)
        page = self._query_int("page", 1)
        if size < 1 or page < 1:
            raise ValidationFailedError("page and size must be positive integers")
        size = min(size, settings.max_page_size)
        offset = self._query_int("offset", None)
        if offset is None:
            offset = (page - 1) * size
        elif offset < 0:
            raise ValidationFailedError("offset must not be negative")
        else:
            page = offset // size + 1
        sort_by = self.get_query_argument("sort", default_sort)
        if sort_by not in allowed:
            raise ValidationFailedError(f"sort must be one of: {', '.join(allowed)}")
        sort_dir = self.get_query_argument("order", default_dir).lower()
        if sort_dir not in (SORT_ASC, SORT_DESC):
            raise ValidationFailedError("order must be 'asc' or 'desc'")
        return PageRequest(page=page, size=size, offset=offset, sort_by=sort_by, sort_dir=sort_dir)

    def _query_int(self, name: str, default: int | None) -> int | None:
        raw = self.get_query_argument(name, None)
        if raw is None or raw == "":
            return default
        try:
            return int(raw)
        except ValueError as exc:
            raise ValidationFailedError(f"{name} must be an integer") from exc

    def query_enum(self, name: str, enum_cls) -> Any:
        """Optional enum filter; invalid value -> 422."""
        raw = self.get_query_argument(name, None)
        if raw is None or raw == "":
            return None
        try:
            return enum_cls(raw)
        except ValueError as exc:
            allowed = ", ".join(member.value for member in enum_cls)
            raise ValidationFailedError(f"{name} must be one of: {allowed}") from exc

    def query_date_range(self) -> tuple[date | None, date | None]:
        """``startDate`` / ``endDate`` (YYYY-MM-DD, inclusive). start > end -> 422."""
        start = self._query_date("startDate")
        end = self._query_date("endDate")
        if start and end and start > end:
            raise ValidationFailedError("startDate must not be after endDate")
        return start, end

    def _query_date(self, name: str) -> date | None:
        raw = self.get_query_argument(name, None)
        if raw is None or raw == "":
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc).date() \
                if "T" in raw else date.fromisoformat(raw)
        except ValueError as exc:
            raise ValidationFailedError(f"{name} must be an ISO date (YYYY-MM-DD)") from exc

    # ---------------------------------------------------------------- response
    def send_json(self, data: Any, status: int = 200) -> None:
        self.set_status(status)
        self.finish(json.dumps(data))

    def send_page(self, page: Page, item_schema: type[ApiModel]) -> None:
        items = [item_schema.model_validate(row).to_json() for row in page.items]
        self.send_json(page.to_envelope(items))

    def send_no_content(self) -> None:
        self.set_status(204)
        self.finish()

    # ------------------------------------------------------------------ errors
    def log_exception(self, typ, value, tb) -> None:  # noqa: D401 - logged once in write_error
        return None

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        exc = kwargs["exc_info"][1] if "exc_info" in kwargs else None
        status, message = self._classify(status_code, exc)
        error = HTTPStatus(status).phrase if status in HTTPStatus._value2member_map_ else "Error"
        self._log_failure(status, exc)
        self.set_status(status)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.finish(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": status,
            "error": error,
            "message": message,
            "path": self.request.path,
        }))

    @staticmethod
    def _classify(status_code: int, exc: BaseException | None) -> tuple[int, str]:
        if isinstance(exc, AppError):
            return exc.status_code, exc.message
        if isinstance(exc, ValidationError):
            return 422, _format_validation_errors(exc)
        if isinstance(exc, IntegrityError):
            return 409, "The request conflicts with existing data"
        if isinstance(exc, web.HTTPError):
            phrase = HTTPStatus(exc.status_code).phrase if exc.status_code in HTTPStatus._value2member_map_ else "Error"
            return exc.status_code, exc.log_message or phrase
        return 500, "An unexpected error occurred"

    def _log_failure(self, status: int, exc: BaseException | None) -> None:
        if status >= 500:
            logger.error("Unhandled error %s %s", self.request.method, self.request.path, exc_info=exc)
        else:
            logger.warning("%s %s -> %s %s", self.request.method, self.request.path, status, exc)


def _format_validation_errors(exc: ValidationError) -> str:
    parts = []
    for item in exc.errors(include_url=False, include_context=False, include_input=False):
        location = ".".join(str(piece) for piece in item["loc"]) or "body"
        parts.append(f"{location}: {item['msg']}")
    return "; ".join(parts)


class NotFoundHandler(BaseHandler):
    """Default handler for unmatched routes -> 404 envelope."""

    public = True

    async def prepare(self) -> None:
        await super().prepare()
        raise NotFoundError("Resource not found")
