from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.book import Book
from models.transaction import Transaction, Fine
from datetime import datetime
from sqlalchemy import func
from sqlalchemy import not_


admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    # Basic statistics
    total_books = Book.query.count()
    total_members = User.query.filter_by(role='member').count()
    total_librarians = User.query.filter_by(role='librarian').count()
    total_borrowed = Transaction.query.filter_by(status='borrowed').count()
    
    # Books by category
    books_by_category = db.session.query(
        Book.category, 
        func.count(Book.id).label('count')
    ).group_by(Book.category).all()
    
    # Recent books added
    recent_books = Book.query.order_by(Book.created_date.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_books=total_books,
                         total_members=total_members,
                         total_librarians=total_librarians,
                         total_borrowed=total_borrowed,
                         books_by_category=books_by_category,
                         recent_books=recent_books)

# ========== MANAGE BOOKS ==========
@admin_bp.route('/admin/books')
@login_required
def admin_books():
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Book.query
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Book.title.ilike(search_term) | 
            Book.author.ilike(search_term) |
            Book.isbn.ilike(search_term)
        )
    
    books = query.order_by(Book.title).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/books.html',
                         books=books,
                         search=search)
@admin_bp.route('/admin/books/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_book(book_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        try:
            new_isbn = request.form.get('isbn', '').strip()
            
            # Validate ISBN: exactly 5 digits
            if len(new_isbn) != 5:
                flash('ISBN must be exactly 5 characters', 'error')
                return redirect(url_for('admin.admin_edit_book', book_id=book_id))
            
            if not new_isbn.isdigit():
                flash('ISBN must contain only digits (0-9)', 'error')
                return redirect(url_for('admin.admin_edit_book', book_id=book_id))
            
            # Check if ISBN already exists (excluding current book)
            if new_isbn != book.isbn:
                existing_book = Book.query.filter_by(isbn=new_isbn).first()
                if existing_book:
                    flash(f'ISBN {new_isbn} already exists for book: {existing_book.title}', 'error')
                    return redirect(url_for('admin.admin_edit_book', book_id=book_id))
            
            book.title = request.form.get('title')
            book.author = request.form.get('author')
            book.isbn = new_isbn
            book.category = request.form.get('category')
            book.publisher = request.form.get('publisher')
            book.publication_year = int(request.form.get('publication_year')) if request.form.get('publication_year') else None
            book.location = request.form.get('location')
            book.description = request.form.get('description')
            
            db.session.commit()
            flash(f'Book "{book.title}" updated successfully!', 'success')
            return redirect(url_for('admin.admin_books'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating book: {str(e)}', 'error')
    
    return render_template('admin/edit_book.html', book=book)

# ========== DELETE BOOK ==========
@admin_bp.route('/admin/books/<int:book_id>/delete', methods=['POST'])
@login_required
def admin_delete_book(book_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    book = Book.query.get_or_404(book_id)
    book_title = book.title
    
    try:
        db.session.delete(book)
        db.session.commit()
        flash(f'Book "{book_title}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting book: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_books'))

# ========== REPORTS ==========
# @admin_bp.route('/admin/reports')
# @login_required
# def admin_reports():
#     if current_user.role != 'admin':
#         flash('Access denied. Admin role required.', 'error')
#         return redirect(url_for('index'))
    
#     return render_template('admin/reports.html')

# ========== MANAGE USERS ==========
@admin_bp.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    
    # Show only members (not admins or librarians)
    users = User.query.filter_by(role='member').order_by(
        User.join_date.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    # Get user statistics
    total_members = User.query.filter_by(role='member').count()
    total_librarians = User.query.filter_by(role='librarian').count()
    total_admins = User.query.filter_by(role='admin').count()
    
    return render_template('admin/users.html', 
                         users=users,
                         total_members=total_members,
                         total_librarians=total_librarians,
                         total_admins=total_admins)


@admin_bp.route('/admin/users/<int:user_id>/deactivate', methods=['POST'])
@login_required
def deactivate_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    if user_id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.admin_users'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    
    db.session.commit()
    
    action = "deactivated" if not user.is_active else "reactivated"
    flash(f'User {user.username} has been {action}.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.admin_users'))
    
    user = User.query.get_or_404(user_id)
    username = user.username
    
    active_transactions = Transaction.query.filter_by(
        user_id=user_id, 
        status='borrowed'
    ).count()
    
    if active_transactions > 0:
        flash(f'Cannot delete {username} - they have {active_transactions} active book borrowings.', 'error')
        return redirect(url_for('admin.admin_users'))
    
    
    Fine.query.filter_by(user_id=user_id).delete()
    
    Reservation.query.filter_by(user_id=user_id).delete()
    
    Transaction.query.filter_by(user_id=user_id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been permanently deleted.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/users/delete-all-members', methods=['POST'])
@login_required
def delete_all_members():
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))

    members = User.query.filter_by(role='member').all()
    member_count = len(members)
    
    if member_count == 0:
        flash('No member users to delete.', 'info')
        return redirect(url_for('admin.admin_users'))
    
    try:
        for member in members:
            
            if member.id == current_user.id:
                continue
            
        
            Fine.query.filter_by(user_id=member.id).delete()
            
            Reservation.query.filter_by(user_id=member.id).delete()
            

            Transaction.query.filter_by(user_id=member.id).delete()
            
            # Delete the user
            db.session.delete(member)
        
        db.session.commit()
        flash(f'Successfully deleted {member_count} member users.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting users: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/users/delete-all', methods=['POST'])
@login_required
def delete_all_users():
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    users = User.query.filter(User.id != current_user.id).all()
    user_count = len(users)
    
    if user_count == 0:
        flash('No users to delete.', 'info')
        return redirect(url_for('admin.admin_users'))
    
    try:
        for user in users:
            Fine.query.filter_by(user_id=user.id).delete()
            
            Reservation.query.filter_by(user_id=user.id).delete()
            
            Transaction.query.filter_by(user_id=user.id).delete()
            
            db.session.delete(user)
        
        db.session.commit()
        flash(f'Successfully deleted {user_count} users (all except yourself).', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting users: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/books/add', methods=['GET', 'POST'])
@login_required
def admin_add_book():
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            isbn = request.form.get('isbn', '').strip()
            
            if len(isbn) != 5 or not isbn.isdigit():
                flash('ISBN must be exactly 5 digits (e.g., 12345)', 'error')
                return redirect(url_for('admin.admin_add_book'))
            
            existing_book = Book.query.filter_by(isbn=isbn).first()
            if existing_book:
                flash(f'ISBN {isbn} already exists for book: {existing_book.title}', 'error')
                return redirect(url_for('admin.admin_add_book'))
            
            book = Book(
                title=request.form.get('title'),
                author=request.form.get('author'),
                isbn=isbn,
                category=request.form.get('category'),
                publisher=request.form.get('publisher'),
                publication_year=int(request.form.get('publication_year')) if request.form.get('publication_year') else None,
                total_copies=int(request.form.get('total_copies', 1)),
                available_copies=int(request.form.get('total_copies', 1)),
                location=request.form.get('location'),
                description=request.form.get('description'),
                status='available'
            )
            
            db.session.add(book)
            db.session.commit()
            flash(f'Book "{book.title}" added successfully!', 'success')
            return redirect(url_for('admin.admin_books'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding book: {str(e)}', 'error')
    
    return render_template('admin/add_book.html', book=None)

@admin_bp.route('/admin/reports')
@login_required
def admin_reports():
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    total_books = Book.query.count()
    total_members = User.query.filter_by(role='member').count()
    total_librarians = User.query.filter_by(role='librarian').count()
    total_borrowed = Transaction.query.filter_by(status='borrowed').count()
    total_overdue = Transaction.query.filter(
        Transaction.status == 'borrowed',
        Transaction.due_date < datetime.utcnow()
    ).count()
    
    total_fine_amount = db.session.query(func.sum(Fine.amount)).filter_by(status='unpaid').scalar()
    if total_fine_amount is None:
        total_fine_amount = 0.0
    
    total_fines = Fine.query.filter_by(status='unpaid').count()
    
    popular_books = db.session.query(
        Book, 
        func.count(Transaction.id).label('borrow_count')
    ).join(Transaction).group_by(Book.id).order_by(
        func.count(Transaction.id).desc()
    ).limit(5).all()
    
    active_members = db.session.query(
        User,
        func.count(Transaction.id).label('borrow_count')
    ).join(Transaction).filter(User.role == 'member').group_by(User.id).order_by(
        func.count(Transaction.id).desc()
    ).limit(5).all()
    
    overdue_books = db.session.query(Transaction, Book, User).join(
        Book, Transaction.book_id == Book.id
    ).join(
        User, Transaction.user_id == User.id
    ).filter(
        Transaction.status == 'borrowed',
        Transaction.due_date < datetime.utcnow()
    ).all()
    
    return render_template('admin/reports.html',
                         total_books=total_books,
                         total_members=total_members,
                         total_librarians=total_librarians,
                         total_borrowed=total_borrowed,
                         total_overdue=total_overdue,
                         total_fines=total_fines,
                         total_fine_amount=total_fine_amount,
                         popular_books=popular_books,
                         active_members=active_members,
                         overdue_books=overdue_books,
                         now=datetime.utcnow())