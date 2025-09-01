# ticketing/app/routes.py

from flask import render_template, request, redirect, url_for, abort, flash
from flask_login import login_user, logout_user, login_required, current_user

# نمونه app را مستقیما از پکیج app (یعنی از فایل __init__.py) وارد می‌کنیم
from app import app
from .services import *
from .models import User, TicketStatus

# --- روت‌های احراز هویت ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('list_tickets'))
    if request.method == 'POST':
        user = get_user_by_username(request.form.get('username'))
        if user and user.check_password(request.form.get('password')):
            login_user(user, remember=request.form.get('remember'))
            flash('شما با موفقیت وارد شدید.', 'success')
            return redirect(url_for('list_tickets'))
        flash('نام کاربری یا رمز عبور اشتباه است.', 'danger')
    return render_template('login.html', title="ورود به سیستم")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('شما با موفقیت خارج شدید.', 'info')
    return redirect(url_for('login'))

# --- روت‌های اصلی تیکتینگ ---
@app.route('/')
@app.route('/tickets')
@login_required
def list_tickets():
    user_tickets = get_tickets_for_user(current_user)
    return render_template('tickets.html', tickets=user_tickets, title="لیست تیکت‌ها")

@app.route('/ticket/new', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if current_user.role != 'customer':
        abort(403)
    if request.method == 'POST':
        create_new_ticket(request.form['title'], request.form['content'], current_user)
        flash('تیکت شما با موفقیت ثبت شد.', 'success')
        return redirect(url_for('list_tickets'))
    return render_template('create_ticket.html', title="ایجاد تیکت جدید")

@app.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(ticket_id):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket or ticket not in get_tickets_for_user(current_user):
        abort(404)
    if request.method == 'POST':
        reply_content = request.form.get('reply_content')
        if reply_content:
            add_reply_to_ticket(ticket, current_user, reply_content)
            return redirect(url_for('ticket_detail', ticket_id=ticket.id))
    replies = get_replies_for_ticket(ticket_id)
    agents = get_all_agents() if current_user.role in ['admin', 'supervisor'] else None
    return render_template('ticket_detail.html', ticket=ticket, replies=replies, agents=agents, title=ticket.title)

@app.route('/ticket/<int:ticket_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket or (ticket.created_by != current_user and current_user.role not in ['admin', 'supervisor']):
        abort(403)
    if request.method == 'POST':
        edit_ticket_content(ticket, request.form['title'], request.form['content'], current_user)
        flash('تیکت با موفقیت ویرایش شد.', 'success')
        return redirect(url_for('ticket_detail', ticket_id=ticket.id))
    return render_template('edit_ticket.html', ticket=ticket, title="ویرایش تیکت")

@app.route('/ticket/<int:ticket_id>/delete', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    if current_user.role not in ['admin', 'supervisor']: abort(403)
    ticket = get_ticket_by_id(ticket_id)
    if ticket:
        delete_ticket_by_id(ticket, current_user)
        flash('تیکت با موفقیت حذف شد.', 'info')
    return redirect(url_for('list_tickets'))

@app.route('/ticket/<int:ticket_id>/assign', methods=['POST'])
@login_required
def assign_ticket(ticket_id):
    if current_user.role not in ['admin', 'supervisor']: abort(403)
    ticket = get_ticket_by_id(ticket_id)
    agent_id = request.form.get('agent_id')
    if not agent_id:
        flash("لطفاً یک کارشناس انتخاب کنید.", "warning")
        return redirect(url_for('ticket_detail', ticket_id=ticket.id))
    agent = get_user_by_id(int(agent_id))
    if ticket and agent:
        assign_ticket_to_agent(ticket, agent, current_user)
        flash(f"تیکت به {agent.username} تخصیص داده شد.", "success")
    return redirect(url_for('ticket_detail', ticket_id=ticket.id))

# --- روت‌های مدیریت و مانیتورینگ ---
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role not in ['admin', 'supervisor']: abort(403)
    stats = get_dashboard_stats()
    return render_template('dashboard.html', title="داشبورد مانیتورینگ", stats=stats)

@app.route('/users')
@login_required
def list_users():
    if current_user.role not in ['admin', 'supervisor']: abort(403)
    users = get_all_users()
    return render_template('admin/user_list.html', title="مدیریت کاربران", users=users)

@app.route('/users/new', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.role not in ['admin', 'supervisor']: abort(403)
    if request.method == 'POST':
        try:
            create_new_user(
                request.form['username'],
                request.form['password'],
                request.form['role']
            )
            flash(f"کاربر '{request.form['username']}' با موفقیت ایجاد شد.", "success")
            return redirect(url_for('list_users'))
        except ValueError as e:
            flash(str(e), "danger")
    return render_template('admin/user_form.html', title="افزودن کاربر جدید", user=None)

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role not in ['admin', 'supervisor']: abort(403)
    user = get_user_by_id(user_id)
    if not user: abort(404)

    if request.method == 'POST':
        try:
            update_user(
                user_id=user.id,
                new_username=request.form['username'],
                new_role=request.form['role'],
                new_password=request.form['password']
            )
            flash(f"اطلاعات کاربر '{user.username}' با موفقیت به‌روز شد.", "success")
            return redirect(url_for('list_users'))
        except ValueError as e:
            flash(str(e), "danger")
    
    return render_template('admin/user_form.html', title="ویرایش کاربر", user=user)

@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user_route(user_id):
    if current_user.role not in ['admin', 'supervisor']: abort(403)
    
    if user_id == current_user.id:
        flash("شما نمی‌توانید حساب کاربری خود را حذف کنید.", "danger")
        return redirect(url_for('list_users'))
        
    user = get_user_by_id(user_id)
    if user:
        delete_user(user_id)
        flash(f"کاربر '{user.username}' با موفقیت حذف شد.", "info")
    
    return redirect(url_for('list_users'))

# --- روت جدید برای بستن تیکت ---
@app.route('/ticket/<int:ticket_id>/close', methods=['POST'])
@login_required
def close_ticket(ticket_id):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        abort(404)
    
    if ticket.created_by != current_user and current_user.role not in ['admin', 'supervisor']:
        abort(403)
    
    if ticket.status != TicketStatus.CLOSED:
        ticket.status = TicketStatus.CLOSED
        update_ticket_status(ticket, current_user, TicketStatus.CLOSED)
        flash('تیکت با موفقیت بسته شد.', 'success')
    else:
        flash('این تیکت قبلاً بسته شده است.', 'info')
        
    return redirect(url_for('ticket_detail', ticket_id=ticket.id))
