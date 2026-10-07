"""Generic repository: lookup, add, delete, and a paginated select helper."""
from __future__ import annotations

from typing import Generic, Mapping, TypeVar

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.core.pagination import SORT_DESC, Page, PageRequest

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Data-access base. Subclasses set ``model`` and add domain queries."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, entity_id: int) -> ModelT | None:
        return await self._session.get(self.model, entity_id)

    async def add(self, entity: ModelT) -> ModelT:
        """Insert and flush so ``entity.id`` is populated (commit is the UoW's job)."""
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def flush(self) -> None:
        await self._session.flush()

    async def delete(self, entity_id: int) -> None:
        """Delete by primary key with a Core DELETE (DB-level cascades handle children)."""
        await self._session.execute(delete(self.model).where(self.model.id == entity_id))

    async def paginate(
        self,
        stmt: Select,
        request: PageRequest,
        sort_columns: Mapping[str, InstrumentedAttribute],
    ) -> Page[ModelT]:
        """Run count query + ordered/limited query. ``sort_columns`` is the sort allowlist."""
        total = (await self._session.execute(
            select(func.count()).select_from(stmt.order_by(None).subquery())
        )).scalar_one()
        column = sort_columns[request.sort_by]
        ordering = column.desc() if request.sort_dir == SORT_DESC else column.asc()
        rows = (await self._session.execute(
            stmt.order_by(ordering, self.model.id.asc()).limit(request.size).offset(request.offset)
        )).scalars().all()
        return Page(items=rows, total=total, request=request)
