# controllers.py
from flask_login import login_user, logout_user
from flask import session
import requests
from datetime import timedelta
from models.models import db, Event, User, SignUp
from datetime import datetime
import pytz

class UserController:
    
    @staticmethod
    def login_user_controller(username, password):
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            session.permanent = True 
            return True
        return False


    @staticmethod
    def logout_user_controller():
        logout_user()
    
    
    @staticmethod
    def register_user(username, password, email, first_name, last_name, role, registration_code=None):
        if role == 'event_creator' and not User.validate_registration_code(registration_code, role):
            raise ValueError("Invalid registration code for Event Creator role")

        user = User(username=username, email=email, first_name=first_name, last_name=last_name, role=role)
        user.set_password(password)
        user.save()
        return user
    
    
    @staticmethod
    def get_user_info(user_id):
        return User.query.get(user_id)
    
    
    @staticmethod
    def update_user_profile(user_id, first_name, last_name, email):
        user = User.query.get(user_id)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
    
    
    @staticmethod
    def update_user_profile_picture(user_id, profile_picture):
        user = User.query.get(user_id)
        if profile_picture:
            user.save_profile_picture(profile_picture)
            
    @staticmethod
    def remove_profile_picture(user_id):
        user = User.query.get(user_id)
        user.remove_profile_picture()

    
    @staticmethod
    def check_password(user_id, password):
        user = User.query.get(user_id)
        return user.check_password(password)
    
    
    @staticmethod
    def change_password(user_id, password):
        user = User.query.get(user_id)
        user.set_password(password)
        user.save()
    
        
    @staticmethod
    def get_user_by_email(email):
        return User.find_by_email(email)

    
    @staticmethod
    def get_user_by_id(user_id):
        """Retrieve a user by their ID."""
        return User.query.get(int(user_id))

        
    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if user.role == 'event_creator':
            events = Event.query.filter_by(organizer_id=user_id).all()
            for event in events:
                event.delete()
        user.delete()
    
        
    @staticmethod
    def get_user_type(user_id):
        user = User.query.get(user_id)
        return user.role
    
    
    @staticmethod
    def get_user_by_email(email):
        return User.query.filter_by(email=email).first()
    
    


class EventController:
    
    @staticmethod
    def add_event(name, description, event_type, date, time, location, organizer_id, image=None):

        image_filename = Event.save_image(image)        
        new_event = Event(
            name=name,
            description=description,
            type=event_type,
            date=date,
            time=time,
            location=location,
            organizer_id=organizer_id,
            image_filename=image_filename
        )
        new_event.save()


    @staticmethod
    def get_all_events():
        return Event.get_all_upcoming()


    @staticmethod
    def get_event(event_id):
        return Event.query.get(event_id)


    @staticmethod
    def search_events(query, filter_category=None):
        now = datetime.now(pytz.timezone('US/Eastern'))
        base_query = Event.query.filter(
            Event.name.contains(query) | Event.description.contains(query)
        )

        if filter_category == "type":
            base_query = base_query.filter(Event.type.contains(query))
        elif filter_category == "time":
            base_query = base_query.filter((Event.date > now.date()) | ((Event.date == now.date()) & (Event.time >= now.time())))
        elif filter_category == "location":
            base_query = base_query.filter(Event.location.contains(query))

        return base_query.order_by(Event.date, Event.time)


    @staticmethod
    def get_user_events(user_id):
        return Event.query.filter_by(organizer_id=user_id).all()


    @staticmethod
    def delete_event(event_id):
        event = Event.query.get(event_id)
        if event:
            event.delete()



    @staticmethod
    def edit_event(event_id, name, description, event_type, date, time, location, image=None, remove_image=False):
        event = Event.query.get(event_id)
        
        event.name = name
        event.description = description
        event.type = event_type
        event.date = date
        event.time = time
        event.location = location
        
        if remove_image:
            event.remove_image()
        elif image and image.filename:
            event.update_image(image)
        
        db.session.commit()
        
        

    @staticmethod
    def get_signup_count(event_id):
        return SignUp.query.filter_by(event_id=event_id).count()

        

class SignUpController:
    @staticmethod
    def add_sign_up(event_id, user_id):
        if not SignUp.is_signed_up(event_id, user_id):
            sign_up = SignUp(event_id=event_id, user_id=user_id)
            sign_up.save()
            return "Signed up successfully"
        return "Already signed up"


    @staticmethod
    def check_for_signup(event_id, user_id):
        return SignUp.is_signed_up(event_id, user_id)


    @staticmethod
    def get_signups_for_event(event_id):
        event = Event.query.get(event_id)
        return event.signups if event else None

    
    @staticmethod
    def get_events_for_user(user_id):
        signups = SignUp.query.filter_by(user_id=user_id).all()
        events = [Event.query.get(signup.event_id) for signup in signups]
        return events

    
    @staticmethod
    def remove_sign_up(event_id, user_id):
        signup = SignUp.query.filter_by(event_id=event_id, user_id=user_id).first()
        if signup:
            signup.delete()
            return "Unsign successful"
        return "Not signed up"
    
    
    @staticmethod
    def get_signups_for_event(event_id):
        signups = SignUp.query.filter_by(event_id=event_id).all()
        user_details = [
            {
                'username': signup.user.username,
                'first_name': signup.user.first_name,
                'last_name': signup.user.last_name,
                'email': signup.user.email,
                'profile_picture': signup.user.profile_picture,
            }
            for signup in signups
        ]
        return user_details
