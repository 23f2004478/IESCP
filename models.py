from main import app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(64), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    profile_picture = db.Column(db.String(256), default='default_profile_picture.jpg')
    
    role = db.Column(db.Enum("admin", "sponsor", "influencer"), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_flagged = db.Column(db.Boolean, nullable=False, default=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    sponsors = db.relationship('Sponsor', backref='user', lazy=True, cascade='all, delete-orphan')
    influencers = db.relationship('Influencer', backref='user', lazy=True, cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True, cascade='all, delete-orphan')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True, cascade='all, delete-orphan')

class Sponsor(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=False)

    name = db.Column(db.String(64), nullable=False)
    industry = db.Column(db.String(64))
    spendings = db.Column(db.Integer, default=0)

    campaigns = db.relationship('Campaign', backref='sponsor', lazy=True, cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='sponsor', lazy=True, cascade='all, delete-orphan')

class Influencer(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=False)

    name = db.Column(db.String(64), nullable=False)
    category = db.Column(db.String(64))
    niche = db.Column(db.String(64))
    rating = db.Column(db.Integer, default=0)
    rating_count = db.Column(db.Integer, default=0)
    earnings = db.Column(db.Integer, default=0)

    social_media_handles = db.relationship('SocialMedia', backref='influencer', lazy=True, cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='influencer', lazy=True, cascade='all, delete-orphan')

class SocialMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(64), nullable=False)
    link = db.Column(db.String(256), nullable=False)
    followers_count = db.Column(db.Integer, nullable=False)

    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    remaining_budget = db.Column(db.Integer, nullable=False)
    visibility = db.Column(db.Enum("public", "private"), nullable=False)
    goals = db.Column(db.String(250))
    
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_flagged = db.Column(db.Boolean, nullable=False, default=False)
    
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)

    ads = db.relationship('Ad', backref='campaign', lazy=True, cascade='all, delete-orphan')

class Ad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    message = db.Column(db.String(250))
    requirements = db.Column(db.String(250))
    payment_amount = db.Column(db.Integer)
    status = db.Column(db.Enum("pending", "accepted", "rejected"), nullable=False, default="pending")
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    current_handler = db.Column(db.Enum("sponsor", "influencer"), nullable=False, default="sponsor") # used to differentiate whose gonna make a move next
    is_completed = db.Column(db.Boolean, nullable=False, default=False)
    is_paid = db.Column(db.Boolean, nullable=False, default=False)
    is_rated = db.Column(db.Boolean, nullable=False, default=False)

    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'))
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))
    rating_id = db.Column(db.Integer, db.ForeignKey('rating.id'))

    influencer = db.relationship('Influencer', backref='Ad', lazy=True)
    sponsor = db.relationship('Sponsor', backref='Ad', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ad_id = db.Column(db.Integer, db.ForeignKey('ad.id'))
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'))

    card_holder_name = db.Column(db.String(64), nullable=False)
    card_number = db.Column(db.String(16), nullable=False)
    card_expiry = db.Column(db.DateTime, nullable=False)
    card_cvv = db.Column(db.String(3), nullable=False)

    ad = db.relationship('Ad', backref='transactions', foreign_keys=[ad_id], lazy=True)
    sponsor = db.relationship('Sponsor', backref='transaction', lazy=True)
    influencer = db.relationship('Influencer', backref='transaction', lazy=True)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Float, nullable=False)
    review = db.Column(db.String(250))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    ad_id = db.Column(db.Integer, db.ForeignKey('ad.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'), nullable=False)

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        passhash = generate_password_hash('Admin@123')
        admin = User(username='admin', passhash=passhash, role="admin", is_admin=True)
        db.session.add(admin)
        db.session.commit()