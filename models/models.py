# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from datetime import datetime
import os
from sqlalchemy import or_
from werkzeug.utils import secure_filename
import pytz

db = SQLAlchemy()
bcrypt = Bcrypt()



class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_filename = db.Column(db.String(100), nullable=True)

    signups = db.relationship('SignUp', back_populates='event', cascade="all, delete-orphan")
    organizer = db.relationship('User', back_populates='organized_events')
    
    UPLOAD_FOLDER = 'static/uploads'

    @staticmethod
    def get_all_upcoming():
        now = datetime.now(pytz.timezone('US/Eastern'))
        return Event.query.filter(
            (Event.date > now.date()) | 
            ((Event.date == now.date()) & (Event.time >= now.time()))
        ).order_by(Event.date, Event.time)


    def save(self):
        db.session.add(self)
        db.session.commit()


    def delete(self):
        db.session.delete(self)
        db.session.commit()

        
    def edit(self, name, description, type, date, time, location):
        self.name = name
        self.description = description
        self.type = type
        self.date = date
        self.time = time
        self.location = location
        db.session.commit()

        
    @staticmethod
    def search_events(query):
        now = datetime.now(pytz.timezone('US/Eastern'))
        return Event.query.filter(
            Event.name.contains(query) | Event.description.contains(query)
        ).order_by(
            or_(Event.date > now.date(), 
                (Event.date == now.date()) & (Event.time >= now.time())).desc(),
            Event.date,
            Event.time
        )
        
        
    @staticmethod
    def save_image(image):
        if image:
            filename = secure_filename(image.filename)
            upload_path = os.path.join(Event.UPLOAD_FOLDER, filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)  
            image.save(upload_path)
            return filename
        return None


    def update_image(self, image):
        if image and image.filename:
            self.remove_image()  
            saved_filename = Event.save_image(image)
            if saved_filename: 
                self.image_filename = saved_filename


    def remove_image(self):
        if self.image_filename:
            image_path = os.path.join(Event.UPLOAD_FOLDER, self.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
            self.image_filename = None  
            
            
    def __repr__(self):
        return f"<Event {self.name} on {self.date} at {self.time} in {self.location}>"



class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)  
    last_name = db.Column(db.String(50), nullable=False) 
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    profile_picture = db.Column(db.String(100), nullable=True) 
    organized_events = db.relationship('Event', back_populates='organizer', cascade="all, delete-orphan")
    signups = db.relationship('SignUp', back_populates='user', cascade="all, delete-orphan")


    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')


    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    
    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    
    @staticmethod
    def validate_registration_code(input_code, role):
        if role == 'event_creator' and input_code == '1234':
            return True
        return False

    
    def save_profile_picture(self, image):
        if image and image.filename:
            filename = secure_filename(image.filename)
            upload_path = os.path.join('static/uploads/profile_pictures', filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            image.save(upload_path)
            self.profile_picture = filename
            db.session.commit()
            
    
    def remove_profile_picture(self):
        if self.profile_picture:
            image_path = os.path.join('static/uploads/profile_pictures', self.profile_picture)
            if os.path.exists(image_path):
                os.remove(image_path)
            self.profile_picture = None
            db.session.commit()

    
    def delete(self):
        db.session.delete(self)
        db.session.commit()


    def save(self):
        db.session.add(self)
        db.session.commit()


    def __repr__(self):
        return f"<User {self.username}>"



class SignUp(db.Model):
    __tablename__ = 'signups'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event = db.relationship('Event', back_populates='signups')
    user = db.relationship('User', back_populates='signups')

    @classmethod
    def is_signed_up(cls, event_id, user_id):
        return cls.query.filter_by(event_id=event_id, user_id=user_id).first() is not None


    def save(self):
        db.session.add(self)
        db.session.commit()
        
        
    def delete(self):
        db.session.delete(self)
        db.session.commit()


    def __repr__(self):
        return f"<SignUp Event ID: {self.event_id}, User ID: {self.user_id}>"
