from . import db
from datetime import datetime, timedelta

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='borrowed')
    renewal_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Transaction User:{self.user_id} Book:{self.book_id}>'

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    reserve_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    notification_sent = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Reservation User:{self.user_id} Book:{self.book_id}>'

class Fine(db.Model):
    __tablename__ = 'fines'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    amount = db.Column(db.Float, default=0.0)
    reason = db.Column(db.String(100))
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    paid_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='unpaid')
    
    transaction = db.relationship('Transaction', backref='fine')
    
    def __repr__(self):
        return f'<Fine User:{self.user_id} Amount:{self.amount}>'