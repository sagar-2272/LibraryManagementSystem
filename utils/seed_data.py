from models import db
from models.user import User
from models.book import Book
from models.transaction import Transaction, Reservation, Fine
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash

def create_dummy_data():
    """Create 50 users, 100 books, and sample transactions"""
    
    # Create Users (50 users)
    users = []
    roles = ['member'] * 45 + ['librarian'] * 4 + ['admin'] * 1
    
    for i in range(1, 51):
        user = User(
            username=f'user{i}',
            email=f'user{i}@library.com',
            password_hash=generate_password_hash('password123'),  # All users have same password for testing
            role=roles[i-1],
            first_name=f'First{i}',
            last_name=f'Last{i}',
            join_date=datetime.utcnow() - timedelta(days=random.randint(1, 365))
        )
        users.append(user)
        db.session.add(user)
    
    db.session.commit()
    print(f"Created {len(users)} users")
    
    # Create Books (100 books)
    books = []
    categories = ['Fiction', 'Science', 'Technology', 'History', 'Biography', 
                 'Mathematics', 'Physics', 'Computer Science', 'Literature', 'Art']
    
    authors = ['Author A', 'Author B', 'Author C', 'Author D', 'Author E',
              'Author F', 'Author G', 'Author H', 'Author I', 'Author J']
    
    for i in range(1, 101):
        category = random.choice(categories)
        author = random.choice(authors)
        
        book = Book(
            title=f'{category} Book {i}',
            author=author,
            isbn=f'978-{random.randint(1000000000, 9999999999)}',
            category=category,
            publisher=f'Publisher {(i % 5) + 1}',
            publication_year=random.randint(1990, 2023),
            total_copies=random.randint(1, 5),
            available_copies=random.randint(1, 5),
            location=f'Shelf {random.randint(1, 10)}-{random.randint(1, 50)}',
            description=f'This is a sample description for {category} Book {i}',
            status='available'
        )
        books.append(book)
        db.session.add(book)
    
    db.session.commit()
    print(f"Created {len(books)} books")
    
    # Create Transactions (borrow/return records)
    transactions = []
    
    # Create some borrowed books (30% of books are currently borrowed)
    member_users = [u for u in users if u.role == 'member']
    
    for i in range(30):  # 30 currently borrowed books
        user = random.choice(member_users)
        book = random.choice([b for b in books if b.available_copies > 0])
        
        if book.available_copies > 0:
            book.available_copies -= 1
            if book.available_copies == 0:
                book.status = 'checked_out'
            
            transaction = Transaction(
                user_id=user.id,
                book_id=book.id,
                borrow_date=datetime.utcnow() - timedelta(days=random.randint(1, 20)),
                due_date=datetime.utcnow() + timedelta(days=random.randint(1, 14)),
                status='borrowed'
            )
            transactions.append(transaction)
            db.session.add(transaction)
    
    # Create some returned books (past transactions)
    for i in range(50):  # 50 returned books
        user = random.choice(member_users)
        book = random.choice(books)
        
        borrow_date = datetime.utcnow() - timedelta(days=random.randint(30, 180))
        return_date = borrow_date + timedelta(days=random.randint(7, 21))
        
        transaction = Transaction(
            user_id=user.id,
            book_id=book.id,
            borrow_date=borrow_date,
            due_date=borrow_date + timedelta(days=14),
            return_date=return_date,
            status='returned'
        )
        transactions.append(transaction)
        db.session.add(transaction)
    
    db.session.commit()
    print(f"Created {len(transactions)} transactions")
    
    # Create Reservations (10 active reservations)
    reservations = []
    
    for i in range(10):
        user = random.choice(member_users)
        # Reserve books that are currently checked out
        borrowed_books = [t.book for t in Transaction.query.filter_by(status='borrowed').all()]
        if borrowed_books:
            book = random.choice(borrowed_books)
            
            reservation = Reservation(
                user_id=user.id,
                book_id=book.id,
                reserve_date=datetime.utcnow() - timedelta(days=random.randint(1, 10)),
                status='active'
            )
            reservations.append(reservation)
            db.session.add(reservation)
    
    db.session.commit()
    print(f"Created {len(reservations)} reservations")
    
    # Create Fines (some overdue fines)
    fines = []
    overdue_transactions = [t for t in Transaction.query.filter_by(status='borrowed').all() 
                          if t.due_date and t.due_date < datetime.utcnow()]
    
    for transaction in overdue_transactions[:15]:  # Create fines for 15 overdue books
        days_overdue = (datetime.utcnow() - transaction.due_date).days
        fine_amount = days_overdue * 0.50  # £0.50 per day
        
        fine = Fine(
            user_id=transaction.user_id,
            transaction_id=transaction.id,
            amount=round(fine_amount, 2),
            reason='overdue',
            issue_date=transaction.due_date + timedelta(days=1)
        )
        fines.append(fine)
        db.session.add(fine)
    
    # Mark some fines as paid
    for fine in fines[:5]:
        fine.status = 'paid'
        fine.paid_date = datetime.utcnow()
    
    db.session.commit()
    print(f"Created {len(fines)} fines")
    
    print("Dummy data creation completed!")