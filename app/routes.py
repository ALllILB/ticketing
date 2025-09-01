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

# تعریف وضعیت‌های ممکن برای تیکت
class TicketStatus(Enum):
    OPEN = "در حال بررسی"
    IN_PROGRESS = "درحال بررسی"
    ANSWERED = "پاسخ داده شده"
    CLOSED = "بسته شده"

# کلاس کاربر که از UserMixin برای سازگاری با Flask-Login ارث‌بری می‌کند
class User(Base, UserMixin):
    def __init__(self, username, password, role="customer"):
        super().__init__()
        self.username = username
        # رمز عبور به صورت هش شده ذخیره می‌شود
        self.password_hash = generate_password_hash(password)
        self.role = role

    def check_password(self, password):
        """بررسی می‌کند که آیا رمز عبور ورودی با هش ذخیره شده مطابقت دارد یا خیر."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

class Ticket(Base):
    def __init__(self, title, content, created_by_user):
        super().__init__()
        self.title = title
        self.content = content
        self.created_by = created_by_user
        # وضعیت پیش‌فرض تیکت در زمان ایجاد
        self.status = TicketStatus.OPEN
        self.assigned_to = None
        self.logs = []  # لیستی برای نگهداری تاریخچه تغییرات تیکت

    def assign_to(self, agent_user):
        if agent_user.role != "agent":
            raise ValueError("تیکت فقط می‌تواند به کارشناس (agent) تخصیص داده شود.")
        self.assigned_to = agent_user
        self.status = TicketStatus.IN_PROGRESS

    def close_ticket(self):
        """متدی برای تغییر وضعیت تیکت به بسته شده."""
        self.status = TicketStatus.CLOSED

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
        self.action = action  # مثلا: 'ایجاد', 'ویرایش', 'تخصیص'
        self.details = details # توضیحات بیشتر
