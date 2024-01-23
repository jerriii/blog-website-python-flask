from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    preferences = db.Column(db.String(255), nullable=True)
    topics = db.Column(db.String(255), nullable=True)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    tagline = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=True)
    img_file = db.Column(db.String(100), nullable=True)
    overall_rating = db.Column(db.Float, default=0.0)
    isVerified = db.Column(db.Boolean, default=False)
    isProfane = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('Users', backref=db.backref('posts', lazy=True))


class Ratings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.sno'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('Users', backref=db.backref('ratings', lazy=True))
    post = db.relationship('Posts', backref=db.backref('ratings', lazy=True))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)


class UserTimeSpent(db.Model):
    __tablename__ = 'user_time_spent'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.sno'), nullable=False)
    time = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship('Users', backref=db.backref('time_spent', lazy=True))
    post = db.relationship('Posts', backref=db.backref('time_spent', lazy=True))
