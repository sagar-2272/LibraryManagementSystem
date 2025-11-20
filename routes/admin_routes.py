from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.book import Book
from models.transaction import Transaction, Fine
from datetime import datetime, timedelta
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/reports')
@login_required
def generate_reports():
    if current_user.role not in ['librarian', 'admin']:
        flash('Access denied. Librarian role required.', 'error')
        return redirect(url_for('index'))
    
    
    total_books = Book.query.count()
    total_members = User.query.filter_by(role='member').count()
    total_borrowed = Transaction.query.filter_by(status='borrowed').count()
    total_overdue = Transaction.query.filter(
        Transaction.status == 'borrowed',
        Transaction.due_date < datetime.utcnow()
    ).count()
    total_fines = Fine.query.filter_by(status='unpaid').count()
    total_fine_amount = db.session.query(func.sum(Fine.amount)).filter_by(status='unpaid').scalar() or 0
    
    popular_books = db.session.query(
        Book, 
        func.count(Transaction.id).label('borrow_count')
    ).join(Transaction).group_by(Book.id).order_by(
        func.count(Transaction.id).desc()
    ).limit(10).all()
    
    active_members = db.session.query(
        User,
        func.count(Transaction.id).label('borrow_count')
    ).join(Transaction).group_by(User.id).order_by(
        func.count(Transaction.id).desc()
    ).limit(10).all()
    
    overdue_books = Transaction.query.filter(
        Transaction.status == 'borrowed',
        Transaction.due_date < datetime.utcnow()
    ).all()
    
    return render_template('admin/reports.html',
                         total_books=total_books,
                         total_members=total_members,
                         total_borrowed=total_borrowed,
                         total_overdue=total_overdue,
                         total_fines=total_fines,
                         total_fine_amount=total_fine_amount,
                         popular_books=popular_books,
                         active_members=active_members,
                         overdue_books=overdue_books)

@admin_bp.route('/system-config')
@login_required
def system_config():
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    return render_template('admin/system_config.html')