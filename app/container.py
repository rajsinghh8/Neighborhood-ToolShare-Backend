"""Composition root: builds the AppContext and the service registry (manual DI)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from app.config import Settings
from app.core.security import PasswordHasher, TokenService
from app.core.unit_of_work import UnitOfWork
from app.db.database import Database
from app.events.publisher import EventPublisher

T = TypeVar("T")
ServiceFactory = Callable[[UnitOfWork], Any]


class ServiceRegistry:
    """Maps a service class to a factory taking the request's UnitOfWork."""

    def __init__(self) -> None:
        self._factories: dict[type, ServiceFactory] = {}

    def register(self, service_cls: type[T], factory: Callable[[UnitOfWork], T]) -> None:
        self._factories[service_cls] = factory

    def build(self, service_cls: type[T], uow: UnitOfWork) -> T:
        return self._factories[service_cls](uow)


@dataclass
class AppContext:
    """Everything handlers and the scheduler need; created once at startup."""

    settings: Settings
    database: Database
    publisher: EventPublisher
    hasher: PasswordHasher
    tokens: TokenService
    registry: ServiceRegistry

    def new_uow(self) -> UnitOfWork:
        return UnitOfWork(self.database, self.publisher)


def build_registry(settings: Settings, hasher: PasswordHasher, tokens: TokenService) -> ServiceRegistry:
    """Wire every service. Constructor contracts are fixed in checkpoint.md."""
    from app.services.audit_log_service import AuditLogService
    from app.services.audit_recorder import AuditRecorder
    from app.services.auth_service import AuthService
    from app.services.budget_category_service import BudgetCategoryService
    from app.services.event_access import EventAccess
    from app.services.event_service import EventService
    from app.services.expense_service import ExpenseService
    from app.services.guest_service import GuestService
    from app.services.notification_recorder import NotificationRecorder
    from app.services.notification_service import NotificationService
    from app.services.schedule_item_service import ScheduleItemService
    from app.services.task_service import TaskService
    from app.services.vendor_payment_service import VendorPaymentService
    from app.services.vendor_service import VendorService

    def audit(uow: UnitOfWork) -> AuditRecorder:
        return AuditRecorder(uow, settings.kafka_audit_topic)

    def notifier(uow: UnitOfWork) -> NotificationRecorder:
        return NotificationRecorder(uow, settings.kafka_notification_topic)

    registry = ServiceRegistry()
    registry.register(AuthService, lambda uow: AuthService(uow, hasher, tokens))
    registry.register(EventService, lambda uow: EventService(uow, EventAccess(uow)))
    registry.register(TaskService, lambda uow: TaskService(uow, EventAccess(uow), audit(uow)))
    registry.register(GuestService, lambda uow: GuestService(uow, EventAccess(uow), audit(uow), notifier(uow)))
    registry.register(BudgetCategoryService, lambda uow: BudgetCategoryService(uow, EventAccess(uow), audit(uow)))
    registry.register(ExpenseService, lambda uow: ExpenseService(uow, EventAccess(uow), audit(uow)))
    registry.register(ScheduleItemService, lambda uow: ScheduleItemService(uow, EventAccess(uow), audit(uow)))
    registry.register(VendorService, lambda uow: VendorService(uow, EventAccess(uow), audit(uow)))
    registry.register(VendorPaymentService, lambda uow: VendorPaymentService(uow, EventAccess(uow), audit(uow)))
    registry.register(NotificationService, lambda uow: NotificationService(uow))
    registry.register(AuditLogService, lambda uow: AuditLogService(uow, EventAccess(uow)))
    return registry


def build_context(settings: Settings, publisher: EventPublisher, database: Database | None = None) -> AppContext:
    """Create the long-lived collaborators and wire them together."""
    hasher = PasswordHasher()
    tokens = TokenService(settings.jwt_secret, settings.jwt_algorithm, settings.jwt_expire_minutes)
    return AppContext(
        settings=settings,
        database=database or Database(settings.database_url, settings.db_connect_retries),
        publisher=publisher,
        hasher=hasher,
        tokens=tokens,
        registry=build_registry(settings, hasher, tokens),
    )
