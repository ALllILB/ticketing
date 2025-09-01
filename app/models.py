# ticketing/app/models.py

import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from enum import Enum

# یک کلاس پایه برای مدیریت شناسه و زمان ایجاد به صورت خودکار
class Base:
    _id_counter = 0
    def __init__(self):
        Base._id_counter += 1
        self.id = Base._id_counter
        self.created_at = datetime.datetime.now()

# کلاس کاربر که از UserMixin برای سازگاری با Flask-Login ارث‌بری می‌کند
class User(Base, UserMixin):
    def __init__(self, username, password, role="customer"):
        super().__init__()
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

# تعریف Enum برای وضعیت‌های تیکت
class TicketStatus(Enum):
    OPEN = "درحال بررسی"
    IN_PROGRESS = "در حال انجام"
    ANSWERED = "پاسخ داده شده"
    CLOSED = "بسته شده"
    DELETED = "حذف شده"

# کلاس جدید برای دسته‌بندی‌های تیکت
class Category(Base):
    def __init__(self, name):
        super().__init__()
        self.name = name

class Ticket(Base):
    def __init__(self, title, content, created_by_user, category):
        super().__init__()
        self.title = title
        self.content = content
        self.created_by = created_by_user
        self.category = category  # اضافه کردن فیلد دسته‌بندی
        self.status = TicketStatus.OPEN
        self.assigned_to = None
        self.logs = []

    def assign_to(self, agent_user):
        if agent_user.role != "agent":
            raise ValueError("تیکت فقط می‌تواند به کارشناس (agent) تخصیص داده شود.")
        self.assigned_to = agent_user
        self.status = TicketStatus.IN_PROGRESS

class Reply(Base):
    def __init__(self, ticket, user, content):
        super().__init__()
        self.ticket = ticket
        self.user = user
        self.content = content

class LogEntry(Base):
    def __init__(self, ticket, user, action, details=""):
        super().__init__()
        self.ticket = ticket
        self.user = user
        self.action = action
        self.details = details
