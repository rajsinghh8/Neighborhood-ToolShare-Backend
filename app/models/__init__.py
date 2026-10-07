"""Importing this package registers every model on ``Base.metadata``."""
from app.models.audit import AuditLog
from app.models.budget import BudgetCategory, Expense
from app.models.event import Event
from app.models.guest import Guest
from app.models.notification import Notification
from app.models.schedule import ScheduleItem
from app.models.task import Task
from app.models.user import User
from app.models.vendor import Vendor, VendorPayment

__all__ = [
    "AuditLog", "BudgetCategory", "Event", "Expense", "Guest", "Notification",
    "ScheduleItem", "Task", "User", "Vendor", "VendorPayment",
]
