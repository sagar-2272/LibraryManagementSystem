from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.book import Book
from models.transaction import Transaction, Fine
from datetime import datetime
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

# ========== ADMIN DASHBOARD ==========
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

# ========== ADD BOOK ==========
@admin_bp.route('/admin/books/add', methods=['GET', 'POST'])
@login_required
def admin_add_book():
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            book = Book(
                title=request.form.get('title'),
                author=request.form.get('author'),
                isbn=request.form.get('isbn'),
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

# ========== EDIT BOOK ==========
@admin_bp.route('/admin/books/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_book(book_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        try:
            book.title = request.form.get('title')
            book.author = request.form.get('author')
            book.isbn = request.form.get('isbn')
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
@admin_bp.route('/admin/reports')
@login_required
def admin_reports():
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    return render_template('admin/reports.html')

# ========== MANAGE USERS ==========
@admin_bp.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access denied. Admin role required.', 'error')
        return redirect(url_for('index'))
    
    users = User.query.order_by(User.join_date.desc()).all()
    return render_template('admin/users.html', users=users)