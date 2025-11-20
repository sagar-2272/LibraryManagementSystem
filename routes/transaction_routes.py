from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.book import Book
from models.transaction import Transaction, Reservation, Fine
from models.user import User
from datetime import datetime, timedelta

transaction_bp = Blueprint('transaction', __name__)

@transaction_bp.route('/borrow/<int:book_id>')
@login_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if book.available_copies <= 0:
        flash('No copies available for borrowing.', 'error')
        return redirect(url_for('books.book_details', book_id=book_id))
    
    # Check if user already has this book borrowed
    existing_loan = Transaction.query.filter_by(
        user_id=current_user.id, 
        book_id=book_id, 
        status='borrowed'
    ).first()
    
    if existing_loan:
        flash('You have already borrowed this book.', 'error')
        return redirect(url_for('books.book_details', book_id=book_id))
    
    # Create transaction
    transaction = Transaction(
        user_id=current_user.id,
        book_id=book_id,
        borrow_date=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=14),
        status='borrowed'
    )
    
    # Update book availability
    book.available_copies -= 1
    if book.available_copies == 0:
        book.status = 'checked_out'
    
    db.session.add(transaction)
    db.session.commit()
    
    flash(f'Book "{book.title}" borrowed successfully! Due date: {transaction.due_date.strftime("%Y-%m-%d")}', 'success')
    return redirect(url_for('member.dashboard'))

@transaction_bp.route('/return/<int:transaction_id>')
@login_required
def return_book(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    if transaction.user_id != current_user.id and current_user.role not in ['librarian', 'admin']:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    book = Book.query.get(transaction.book_id)
    
    # Update transaction
    transaction.return_date = datetime.utcnow()
    transaction.status = 'returned'
    
    # Update book availability
    book.available_copies += 1
    if book.status == 'checked_out':
        book.status = 'available'
    
    # Check for overdue and create fine if applicable
    if transaction.return_date > transaction.due_date:
        days_overdue = (transaction.return_date - transaction.due_date).days
        fine_amount = days_overdue * 0.50  # £0.50 per day
        
        fine = Fine(
            user_id=transaction.user_id,
            transaction_id=transaction.id,
            amount=round(fine_amount, 2),
            reason='overdue',
            issue_date=datetime.utcnow()
        )
        db.session.add(fine)
        flash(f'Book returned. Overdue fine: £{fine_amount:.2f}', 'warning')
    else:
        flash('Book returned successfully!', 'success')
    
    db.session.commit()
    return redirect(url_for('member.dashboard'))

@transaction_bp.route('/reserve/<int:book_id>')
@login_required
def reserve_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Check if book is available
    if book.available_copies > 0:
        flash('Book is available for borrowing directly.', 'info')
        return redirect(url_for('books.book_details', book_id=book_id))
    
    # Check if user already has active reservation
    existing_reservation = Reservation.query.filter_by(
        user_id=current_user.id, 
        book_id=book_id, 
        status='active'
    ).first()
    
    if existing_reservation:
        flash('You already have an active reservation for this book.', 'error')
        return redirect(url_for('books.book_details', book_id=book_id))
    
    # Create reservation
    reservation = Reservation(
        user_id=current_user.id,
        book_id=book_id,
        reserve_date=datetime.utcnow(),
        status='active'
    )
    
    db.session.add(reservation)
    db.session.commit()
    
    flash('Book reserved successfully! You will be notified when it becomes available.', 'success')
    return redirect(url_for('books.book_details', book_id=book_id))

@transaction_bp.route('/reservations')
@login_required
def view_reservations():
    active_reservations = Reservation.query.filter_by(
        user_id=current_user.id, 
        status='active'
    ).all()
    
    return render_template('transactions/reservations.html', 
                         reservations=active_reservations)

@transaction_bp.route('/fines')
@login_required
def view_fines():
    fines = Fine.query.filter_by(user_id=current_user.id).order_by(
        Fine.issue_date.desc()
    ).all()
    
    total_unpaid = sum(fine.amount for fine in fines if fine.status == 'unpaid')
    
    return render_template('transactions/fines.html', 
                         fines=fines, 
                         total_unpaid=total_unpaid)

@transaction_bp.route('/pay-fine/<int:fine_id>')
@login_required
def pay_fine(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    
    if fine.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    fine.status = 'paid'
    fine.paid_date = datetime.utcnow()
    
    db.session.commit()
    flash(f'Fine of £{fine.amount:.2f} paid successfully!', 'success')
    return redirect(url_for('transaction.view_fines'))