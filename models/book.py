from sqlalchemy import CheckConstraint
from datetime import datetime

from . import db
class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(5), unique=True, nullable=False)  # Changed to 5 characters
    category = db.Column(db.String(50), nullable=False)
    publisher = db.Column(db.String(100))
    publication_year = db.Column(db.Integer)
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    location = db.Column(db.String(50))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='available')
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('length(isbn) = 5', name='isbn_length_check'),
        CheckConstraint('isbn ~ \'^[0-9]{5}$\'', name='isbn_numeric_check'),
    )