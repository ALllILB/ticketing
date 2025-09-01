# ticketing/app/services.py

from .models import User, Ticket, Reply, LogEntry, TicketStatus
from .data import users_db, tickets_db, replies_db

def get_user_by_id(user_id):
    """برگرداندن یک کاربر بر اساس شناسه."""
    return next((u for u in users_db if u.id == user_id), None)

def get_user_by_username(username):
    """برگرداندن یک کاربر بر اساس نام کاربری."""
    return next((u for u in users_db if u.username == username), None)

def create_new_user(username, password, role):
    """ایجاد یک کاربر جدید و اضافه کردن آن به دیتابیس."""
    if get_user_by_username(username):
        raise ValueError("نام کاربری قبلاً وجود دارد.")
    new_user = User(username, password, role)
    users_db.append(new_user)
    return new_user

def get_all_users():
    """برگرداندن لیست تمام کاربران."""
    return users_db

def update_user(user_id, new_username, new_role, new_password):
    """به‌روزرسانی اطلاعات یک کاربر."""
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("کاربر یافت نشد.")
    if new_username and new_username != user.username and get_user_by_username(new_username):
        raise ValueError("نام کاربری قبلاً وجود دارد.")
    
    if new_username:
        user.username = new_username
    if new_role:
        user.role = new_role
    if new_password:
        user.password_hash = User(new_username, new_password).password_hash
    return user

def delete_user(user_id):
    """حذف یک کاربر."""
    global users_db
    users_db = [user for user in users_db if user.id != user_id]

# --- توابع مدیریت تیکت‌ها ---

def get_ticket_by_id(ticket_id):
    """برگرداندن یک تیکت بر اساس شناسه."""
    return next((t for t in tickets_db if t.id == ticket_id), None)

def get_tickets_for_user(user):
    """برگرداندن تیکت‌های مرتبط با کاربر."""
    if user.role == 'customer':
        return [t for t in tickets_db if t.created_by.id == user.id]
    elif user.role in ['admin', 'supervisor']:
        return tickets_db
    elif user.role == 'agent':
        return [t for t in tickets_db if t.assigned_to and t.assigned_to.id == user.id]
    return []

def create_new_ticket(title, content, created_by_user):
    """ایجاد یک تیکت جدید."""
    new_ticket = Ticket(title, content, created_by_user)
    tickets_db.append(new_ticket)
    
    # ثبت رویداد در لاگ تیکت
    log_entry = LogEntry(new_ticket, created_by_user, "ایجاد تیکت")
    new_ticket.logs.append(log_entry)
    return new_ticket

def add_reply_to_ticket(ticket, user, content):
    """اضافه کردن یک پاسخ به تیکت."""
    new_reply = Reply(ticket, user, content)
    replies_db.append(new_reply)
    
    # به‌روزرسانی وضعیت تیکت و ثبت در لاگ
    if ticket.status == TicketStatus.OPEN and user.role != 'customer':
        ticket.status = TicketStatus.ANSWERED
        log_entry = LogEntry(ticket, user, "پاسخ داده شد")
        ticket.logs.append(log_entry)
    
    if user.role == 'customer' and ticket.status == TicketStatus.ANSWERED:
        ticket.status = TicketStatus.OPEN
        log_entry = LogEntry(ticket, user, "پاسخ کاربر")
        ticket.logs.append(log_entry)
        
    return new_reply

def edit_ticket_content(ticket, new_title, new_content, user):
    """ویرایش محتوای تیکت و ثبت آن در لاگ."""
    old_title = ticket.title
    old_content = ticket.content
    ticket.title = new_title
    ticket.content = new_content
    
    log_entry = LogEntry(ticket, user, "ویرایش تیکت", f"موضوع از '{old_title}' به '{new_title}' تغییر یافت.")
    ticket.logs.append(log_entry)
    return ticket

def delete_ticket_by_id(ticket, user):
    """حذف یک تیکت با تغییر وضعیت آن."""
    ticket.status = TicketStatus.DELETED
    log_entry = LogEntry(ticket, user, "حذف تیکت")
    ticket.logs.append(log_entry)
    
def assign_ticket_to_agent(ticket, agent, user):
    """تخصیص تیکت به یک کارشناس و ثبت آن در لاگ."""
    old_agent_name = ticket.assigned_to.username if ticket.assigned_to else 'هیچکس'
    ticket.assign_to(agent)
    log_entry = LogEntry(ticket, user, "تخصیص تیکت", f"تیکت از '{old_agent_name}' به '{agent.username}' تخصیص داده شد.")
    ticket.logs.append(log_entry)
    return ticket
    
def get_replies_for_ticket(ticket_id):
    """برگرداندن پاسخ‌های مربوط به یک تیکت."""
    return [r for r in replies_db if r.ticket.id == ticket_id]

def get_all_agents():
    """برگرداندن لیست تمام کارشناسان."""
    return [u for u in users_db if u.role == 'agent']

def get_dashboard_stats():
    """محاسبه آمار داشبورد."""
    stats = {}
    stats['total_tickets'] = len(tickets_db)
    stats['open_tickets'] = len([t for t in tickets_db if t.status == TicketStatus.OPEN])
    stats['in_progress_tickets'] = len([t for t in tickets_db if t.status != TicketStatus.OPEN and t.status != TicketStatus.CLOSED and t.status != TicketStatus.DELETED])
    stats['new_tickets_today'] = len([t for t in tickets_db if t.created_at.date() == datetime.date.today()])
    
    # محاسبه بار کاری کارشناسان
    agent_workload = {}
    for agent in get_all_agents():
        agent_workload[agent.username] = len([t for t in tickets_db if t.assigned_to and t.assigned_to.id == agent.id and t.status != TicketStatus.CLOSED])
    stats['agent_workload'] = agent_workload
    
    # آخرین تیکت‌های به‌روز شده
    recently_updated = sorted(tickets_db, key=lambda t: t.logs[-1].created_at if t.logs else t.created_at, reverse=True)
    stats['recently_updated_tickets'] = recently_updated[:10]
    
    return stats

def update_ticket_status(ticket, user, new_status):
    """به‌روزرسانی وضعیت تیکت و ثبت در لاگ."""
    old_status = ticket.status
    ticket.status = new_status
    log_entry = LogEntry(ticket, user, "تغییر وضعیت تیکت", f"وضعیت از '{old_status.value}' به '{new_status.value}' تغییر یافت.")
    ticket.logs.append(log_entry)
