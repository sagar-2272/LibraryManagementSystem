from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db
from models.transaction import Transaction, Reservation, Fine
from datetime import datetime

member_bp = Blueprint('member', __name__)

@member_bp.route('/dashboard')
@login_required
def dashboard():
    # Current borrowed books
    current_loans = Transaction.query.filter_by(
        user_id=current_user.id, 
        status='borrowed'
    ).all()
    
    # Active reservations
    active_reservations = Reservation.query.filter_by(
        user_id=current_user.id, 
        status='active'
    ).all()
    
    # Unpaid fines
    unpaid_fines = Fine.query.filter_by(
        user_id=current_user.id, 
        status='unpaid'
    ).all()
    
    # Recent transactions (last 10)
    recent_transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.borrow_date.desc()).limit(10).all()
    
    total_fine = sum(fine.amount for fine in unpaid_fines)
    
    return render_template('members/dashboard.html',
                         current_loans=current_loans,
                         active_reservations=active_reservations,
                         unpaid_fines=unpaid_fines,
                         recent_transactions=recent_transactions,
                         total_fine=total_fine,
                         now=datetime.utcnow())

@member_bp.route('/borrowing-history')
@login_required
def borrowing_history():
    page = request.args.get('page', 1, type=int)
    
    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.borrow_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('members/borrowing_history.html', 
                         transactions=transactions)

@member_bp.route('/members')
@login_required
def manage_members():
    if current_user.role not in ['librarian', 'admin']:
        flash('Access denied. Librarian role required.', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    members = User.query.filter_by(role='member').order_by(
        User.join_date.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('members/manage_members.html', members=members)