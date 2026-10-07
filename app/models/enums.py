"""Enumerations stored as plain strings (portable across MySQL/SQLite)."""
from __future__ import annotations

import enum


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InvitationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    STATUS_CHANGE = "status_change"


class NotificationType(str, enum.Enum):
    GUEST_INVITATION_STATUS = "guest_invitation_status"
    TASK_DUE_SOON = "task_due_soon"
    TASK_OVERDUE = "task_overdue"
    BUDGET_THRESHOLD = "budget_threshold"


class AuditEntityType(str, enum.Enum):
    TASK = "task"
    GUEST = "guest"
    BUDGET_CATEGORY = "budget_category"
    EXPENSE = "expense"
    SCHEDULE_ITEM = "schedule_item"
    VENDOR = "vendor"
    VENDOR_PAYMENT = "vendor_payment"
