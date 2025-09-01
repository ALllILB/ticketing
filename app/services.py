# ticketing/app/services.py

from .models import User, Ticket, Reply, LogEntry, Category, TicketStatus
from collections import defaultdict
from datetime import date, datetime
from werkzeug.security import generate_password_hash

# پایگاه داده موقت (در حافظه)
DB = {
    "users": [], "tickets": [], "replies": [], "logs": [], "categories": []
}

# --- توابع مدیریت کاربران ---
def get_user_by_id(user_id):
    for user in DB["users"]:
        if user.id == user_id: return user
    return None

def get_user_by_username(username):
    for user in DB["users"]:
        if user.username == username: return user
    return None

def get_all_users():
    return DB.get("users", [])

def get_all_agents():
    return [u for u in DB.get("users", []) if u.role == 'agent']

def create_new_user(username, password, role):
    if get_user_by_username(username):
        raise ValueError(f"نام کاربری '{username}' قبلاً استفاده شده است.")
    new_user = User(username=username, password=password, role=role)
    DB["users"].append(new_user)
    return new_user

def update_user(user_id, new_username, new_role, new_password):
    user_to_update = get_user_by_id(user_id)
    if not user_to_update:
        raise ValueError("کاربر پیدا نشد.")
    existing_user = get_user_by_username(new_username)
    if existing_user and existing_user.id != user_id:
        raise ValueError(f"نام کاربری '{new_username}' قبلاً توسط کاربر دیگری استفاده شده است.")
    user_to_update.username = new_username
    user_to_update.role = new_role
    if new_password:
        user_to_update.password_hash = generate_password_hash(new_password)
    return user_to_update

def delete_user(user_id):
    user_to_delete = get_user_by_id(user_id)
    if user_to_delete:
        DB["users"].remove(user_to_delete)
        return True
    return False

# --- توابع مدیریت تیکت ---
def get_ticket_by_id(ticket_id):
    for ticket in DB["tickets"]:
        if ticket.id == ticket_id: return ticket
    return None

def get_tickets_for_user(user):
    if user.role in ['admin', 'supervisor']: return DB['tickets']
    if user.role == 'agent': return [t for t in DB['tickets'] if t.assigned_to == user or t.assigned_to is None]
    if user.role == 'customer': return [t for t in DB['tickets'] if t.created_by == user]
    return []

def create_new_ticket(title, content, creator_user, category):
    new_ticket = Ticket(title=title, content=content, created_by_user=creator_user, category=category)
    DB["tickets"].append(new_ticket)
    add_log_to_ticket(new_ticket, creator_user, "ایجاد تیکت")
    return new_ticket

def edit_ticket_content(ticket, new_title, new_content, editor_user):
    details = f"موضوع از '{ticket.title}' به '{new_title}' تغییر کرد."
    ticket.title = new_title
    ticket.content = new_content
    add_log_to_ticket(ticket, editor_user, "ویرایش تیکت", details)
    return True

def delete_ticket_by_id(ticket, deleter_user):
    if deleter_user.role not in ['admin', 'supervisor']:
        raise PermissionError("شما دسترسی لازم برای حذف تیکت را ندارید.")
    ticket.status = TicketStatus.DELETED
    add_log_to_ticket(ticket, deleter_user, "حذف تیکت")
    return True

def assign_ticket_to_agent(ticket, agent, assigner):
    if assigner.role not in ['admin', 'supervisor']:
        raise PermissionError("شما دسترسی لازم برای این کار را ندارید.")
    old_agent = ticket.assigned_to.username if ticket.assigned_to else "هیچکس"
    ticket.assign_to(agent)
    details = f"تیکت از '{old_agent}' به '{agent.username}' تخصیص داده شد."
    add_log_to_ticket(ticket, assigner, "تخصیص کارشناس", details)
    return True

def update_ticket_status(ticket, user, new_status):
    old_status = ticket.status
    ticket.status = new_status
    add_log_to_ticket(ticket, user, "تغییر وضعیت تیکت", f"وضعیت از '{old_status.value}' به '{new_status.value}' تغییر یافت.")

# --- توابع مدیریت پاسخ و لاگ ---
def add_reply_to_ticket(ticket, user, content):
    new_reply = Reply(ticket=ticket, user=user, content=content)
    DB["replies"].append(new_reply)
    if user.role != 'customer':
        if ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.ANSWERED
    add_log_to_ticket(ticket, user, "ثبت پاسخ", f'"{content[:30]}..."')
    return new_reply

def get_replies_for_ticket(ticket_id):
    return [r for r in DB["replies"] if r.ticket.id == ticket_id]

def add_log_to_ticket(ticket, user, action, details=""):
    log = LogEntry(ticket=ticket, user=user, action=action, details=details)
    ticket.logs.append(log)
    DB["logs"].append(log)

# --- توابع مدیریت دسته‌بندی‌ها ---
def get_all_categories():
    return DB.get("categories", [])

def get_category_by_id(category_id):
    for category in DB["categories"]:
        if category.id == category_id:
            return category
    return None

def get_category_by_name(name):
    for category in DB["categories"]:
        if category.name == name:
            return category
    return None

def create_new_category(name):
    if get_category_by_name(name):
        raise ValueError("این دسته‌بندی قبلاً وجود دارد.")
    new_category = Category(name)
    DB["categories"].append(new_category)
    return new_category

def update_category(category_id, new_name):
    category = get_category_by_id(category_id)
    if not category:
        raise ValueError("دسته‌بندی یافت نشد.")
    if new_name and new_name != category.name and get_category_by_name(new_name):
        raise ValueError("نام دسته‌بندی قبلاً وجود دارد.")
    category.name = new_name
    return category

def delete_category(category_id):
    category_to_delete = get_category_by_id(category_id)
    if category_to_delete:
        DB["categories"].remove(category_to_delete)
        return True
    return False

# --- تابع داشبورد ---
def get_dashboard_stats():
    active_tickets = [t for t in DB.get("tickets", []) if t.status != TicketStatus.DELETED]
    status_counts = defaultdict(int)
    for ticket in active_tickets:
        status_counts[ticket.status] += 1
    today = date.today()
    new_tickets_today = sum(1 for t in active_tickets if t.created_at.date() == today)
    agent_workload = {agent.username: 0 for agent in get_all_agents()}
    for ticket in active_tickets:
        if ticket.assigned_to:
            if ticket.assigned_to.username in agent_workload:
                agent_workload[ticket.assigned_to.username] += 1
    def get_last_update(t):
        return max(log.created_at for log in t.logs) if t.logs else t.created_at
    recently_updated = sorted(active_tickets, key=get_last_update, reverse=True)[:5]
    return {
        "total_tickets": len(active_tickets),
        "open_tickets": status_counts.get(TicketStatus.OPEN, 0),
        "in_progress_tickets": status_counts.get(TicketStatus.IN_PROGRESS, 0),
        "answered_tickets": status_counts.get(TicketStatus.ANSWERED, 0),
        "new_tickets_today": new_tickets_today,
        "agent_workload": agent_workload,
        "recently_updated_tickets": recently_updated
    }

# --- ایجاد داده‌های اولیه برای تست ---
def create_initial_data():
    if DB["users"]: return
    admin = create_new_user("admin", "123", "admin")
    supervisor = create_new_user("supervisor", "123", "supervisor")
    agent1 = create_new_user("agent1", "123", "agent")
    agent2 = create_new_user("agent2", "123", "agent")
    customer1 = create_new_user("customer1", "123", "customer")

    # ایجاد دسته‌بندی‌های پیش‌فرض
    default_categories = [
        "سامانه", "غذا", "سیستم ورود و خروج", "اتوماسیون اداری",
        "چاپگر، اسکنر و فکس", "سخت افزاری", "نرم افزاری", "شبکه",
        "اینترنت و ایمیل", "دوربین‌ها و سیستم‌های امنیتی", "تلفن",
        "نرم افزار حسابداری", "درخواست راهنمایی", "ایستگاه کاری",
        "درخواست خرید کالا", "گرافیک و چاپ، ادیت فیلم", "انتقادات و پیشنهادات"
    ]
    for name in default_categories:
        create_new_category(name)

    # ایجاد تیکت نمونه
    cat_software = get_category_by_name("نرم افزاری")
    t1 = create_new_ticket("مشکل در ورود به نرم‌افزار", "نمی‌توانم وارد سیستم شوم.", customer1, cat_software)
    assign_ticket_to_agent(t1, agent1, supervisor)

create_initial_data()
