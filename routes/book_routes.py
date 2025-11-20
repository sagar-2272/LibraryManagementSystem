from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from models import db
from models.book import Book
from models.transaction import Transaction, Reservation
from sqlalchemy import or_

book_bp = Blueprint('books', __name__)

@book_bp.route('/books')
def book_catalog():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = Book.query
    
    if category:
        query = query.filter(Book.category == category)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Book.title.ilike(search_term),
                Book.author.ilike(search_term),
                Book.isbn.ilike(search_term),
                Book.category.ilike(search_term)
            )
        )
    
    books = query.order_by(Book.title).paginate(page=page, per_page=12, error_out=False)
    
    categories = db.session.query(Book.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('books/catalog.html', 
                         books=books, 
                         categories=categories,
                         current_category=category,
                         search_term=search)

@book_bp.route('/books/<int:book_id>')
def book_details(book_id):
    book = Book.query.get_or_404(book_id)
    user_reservation = None
    if current_user.is_authenticated:
        user_reservation = Reservation.query.filter_by(
            user_id=current_user.id, 
            book_id=book_id, 
            status='active'
        ).first()
    
    reservation_count = Reservation.query.filter_by(
        book_id=book_id, 
        status='active'
    ).count()
    
    return render_template('books/book_detail.html', 
                         book=book, 
                         user_reservation=user_reservation,
                         reservation_count=reservation_count)

@book_bp.route('/books/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if current_user.role not in ['librarian', 'admin']:
        flash('Access denied. Librarian role required.', 'error')
        return redirect(url_for('books.book_catalog'))
    
    if request.method == 'POST':
        book = Book(
            title=request.form.get('title'),
            author=request.form.get('author'),
            isbn=request.form.get('isbn'),
            category=request.form.get('category'),
            publisher=request.form.get('publisher'),
            publication_year=request.form.get('publication_year'),
            total_copies=int(request.form.get('total_copies', 1)),
            available_copies=int(request.form.get('total_copies', 1)),
            location=request.form.get('location'),
            description=request.form.get('description')
        )
        
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('books.book_details', book_id=book.id))
    
    return render_template('books/manage_books.html', book=None)

@book_bp.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    if current_user.role not in ['librarian', 'admin']:
        flash('Access denied. Librarian role required.', 'error')
        return redirect(url_for('books.book_catalog'))
    
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.isbn = request.form.get('isbn')
        book.category = request.form.get('category')
        book.publisher = request.form.get('publisher')
        book.publication_year = request.form.get('publication_year')
        book.location = request.form.get('location')
        book.description = request.form.get('description')
        
        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('books.book_details', book_id=book.id))
    
    return render_template('books/manage_books.html', book=book)