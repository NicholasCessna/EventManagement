# flask_routes.py
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from controllers.controllers import UserController, EventController, SignUpController
from utils.email_verifier import EmailVerifier
from datetime import datetime
import pytz

def register_routes(app):
    
    @app.route('/', methods=['GET', 'POST'])
    def events():
        page = request.args.get('page', 1, type=int)
        per_page = 20

        search_query = request.form.get('search') if request.method == 'POST' else None
        filter_category = request.form.get('filter_category') if request.method == 'POST' else None

        events_query = EventController.search_events(search_query, filter_category) if search_query else EventController.get_all_events()

        pagination = events_query.paginate(page=page, per_page=per_page)

        event_signup_status = {}
        event_signup_counts = {}
        if current_user.is_authenticated:
            for event in pagination.items:
                event_signup_status[event.id] = SignUpController.check_for_signup(event.id, current_user.id)
                event_signup_counts[event.id] = EventController.get_signup_count(event.id)

        tz = pytz.timezone('US/Eastern')
        now = datetime.now(tz)
        current_date = now.date()
        current_time = now.time()

        return render_template(
            'events.html',
            events=pagination.items,
            event_signup_status=event_signup_status,
            event_signup_counts=event_signup_counts,
            prev_page=pagination.prev_num if pagination.has_prev else None,
            next_page=pagination.next_num if pagination.has_next else None,
            current_date=current_date,
            current_time=current_time
        )




    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if request.method == 'POST':
            if 'update_profile' in request.form:

                first_name = request.form.get('first_name')
                last_name = request.form.get('last_name')
                email = request.form.get('email')

                try:
                    UserController.update_user_profile(current_user.id, first_name, last_name, email)
                    flash('Your profile details have been updated successfully.', 'success')
                except Exception as e:
                    flash(f'Failed to update profile details: {str(e)}', 'error')

            if 'profile_picture' in request.files:
                profile_picture = request.files['profile_picture']
                try:
                    if profile_picture:
                        UserController.update_user_profile_picture(current_user.id, profile_picture)
                        flash('Your profile picture has been updated.', 'success')
                except Exception as e:
                    flash(f'Failed to update profile picture: {str(e)}', 'error')

            if 'change_password' in request.form:
                old_password = request.form.get('old_password')
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')

                if not UserController.check_password(current_user.id, old_password):
                    flash('Incorrect old password.', 'error')
                elif new_password != confirm_password:
                    flash('Passwords do not match.', 'error')
                else:
                    try:
                        UserController.change_password(current_user.id, new_password)
                        flash('Password changed successfully.', 'success')
                    except Exception as e:
                        flash(f'Failed to change password: {str(e)}', 'error')

            if 'delete_account' in request.form:
                try:
                    UserController.delete_user(current_user.id)
                    UserController.logout_user_controller()
                    flash('Your account has been deleted.', 'success')
                    return redirect(url_for('events'))
                except Exception as e:
                    flash(f'Failed to delete account: {str(e)}', 'error')

            return redirect(url_for('profile'))

        # Render profile with current data
        events_for_user = SignUpController.get_events_for_user(current_user.id)
        created_events = []
        if UserController.get_user_type(current_user.id) == 'event_creator':
            created_events = EventController.get_user_events(current_user.id)

        return render_template(
            'profile.html',
            user=current_user,
            events_for_user=events_for_user,
            created_events=created_events,
            current_date=datetime.now().date(),
            current_time=datetime.now().time(),
        )


                 
    @app.route('/event/<int:event_id>')
    def event_detail(event_id):
        event = EventController.get_event(event_id)
        signup_status = False
        signup_count = EventController.get_signup_count(event_id)
        if current_user.is_authenticated:
            signup_status = SignUpController.check_for_signup(event_id, current_user.id)

        tz = pytz.timezone('US/Eastern')
        now = datetime.now(tz)
        current_date = now.date()
        current_time = now.time()

        return render_template(
            'event_detail.html',
            event=event,
            signup_status=signup_status,
            signup_count=signup_count,
            current_date=current_date,
            current_time=current_time
        )

    
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            try:
                first_name = request.form['first_name']
                last_name = request.form['last_name']
                username = request.form['username']
                password = request.form['password']
                confirm_password = request.form['confirm_password']
                email = request.form['email']
                role = request.form['role']
                registration_code = request.form.get('registration_code')
                profile_picture = request.files.get('profile_picture')

                if password != confirm_password:
                    flash('Passwords do not match', 'error')
                    return redirect(url_for('register'))

                if UserController.get_user_info(username):
                    flash('Username already exists', 'error')
                    return redirect(url_for('register'))

                if UserController.get_user_by_email(email):
                    flash('Email is already registered', 'error')
                    return redirect(url_for('register'))

                if not EmailVerifier.verify(email):
                    flash('Email verification failed.', 'error')
                    return redirect(url_for('register'))

                user = UserController.register_user(
                    username, password, email, first_name, last_name, role, registration_code
                )

                if profile_picture:
                    UserController.update_user_profile_picture(user.id, profile_picture)

                flash('Registration successful! Please log in.')
                return redirect(url_for('login'))
            except Exception as e:
                flash('An error occurred during registration.', 'error')
                print(f"Error: {e}")
                return redirect(url_for('register'))
        return render_template('register.html')


    @app.route('/event/<int:event_id>/signups', methods=['GET'])
    @login_required
    def view_signups(event_id):
        event = EventController.get_event(event_id)
        
        if event.organizer_id != current_user.id:
            flash("You do not have permission to view signups for this event.", "error")
            return redirect(url_for('profile'))

        signups = SignUpController.get_signups_for_event(event_id)
        total_signups = len(signups)

        return render_template(
            'view_signups.html',
            event=event,
            signups=signups,
            total_signups=total_signups
        )


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if UserController.login_user_controller(username, password):
                flash('Logged in successfully!', 'success')
                return redirect(url_for('events'))
            flash('Invalid username or password', 'error')
        return render_template('login.html')


    @app.route('/logout')
    @login_required
    def logout():
        UserController.logout_user_controller()
        flash('Logged out successfully', 'success')
        return redirect(url_for('login'))


    @app.route('/add_event', methods=['GET', 'POST'])
    @login_required
    def add_event_route():
        if current_user.role != 'event_creator':
            flash("You don't have permission to add events.")
            return redirect(url_for('events'))

        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            event_type = request.form['event_type']
            date_str = request.form['date']
            time_str = request.form['time']
            location = request.form['location']
            image = request.files.get('image')

            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            time = datetime.strptime(time_str, '%H:%M').time()

            EventController.add_event(name, description, event_type, date, time, location, current_user.id, image)
            flash('Event added successfully!')
            return redirect(url_for('events'))
        return render_template('add_event.html')


    @app.route('/event/<int:event_id>/signup', methods=['GET', 'POST'])
    @login_required
    def signup(event_id):
        if request.method == 'POST':
            message = SignUpController.add_sign_up(event_id, current_user.id)
            flash(message)
            return redirect(url_for('event_detail', event_id=event_id))
        event = EventController.get_event(event_id)
        return render_template('signup.html', event=event)


    @app.route('/event/<int:event_id>/delete', methods=['POST'])
    @login_required
    def delete_event(event_id):
        EventController.delete_event(event_id)
        flash('Event deleted successfully')
        return redirect(url_for('profile'))
    
        
    @app.route('/event/<int:event_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_event(event_id):
        event = EventController.get_event(event_id)

        if request.method == 'POST':
            # Collect form data
            name = request.form['name']
            description = request.form['description']
            event_type = request.form['event_type']  # Added event type
            date_str = request.form['date']
            time_str = request.form['time']
            location = request.form['location']
            remove_image = request.form.get('remove_image', None) == "yes"
            image = request.files.get('image')

            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            time = datetime.strptime(time_str, '%H:%M').time()
            
            EventController.edit_event(event_id, name, description, event_type, date, time, location, image, remove_image)
            flash('Event updated successfully!')
            return redirect(url_for('profile'))

        return render_template('edit_event.html', event=event)
    
    
    @app.route('/event/<int:event_id>/unsign', methods=['POST'])
    @login_required
    def unsign_event(event_id):
        message = SignUpController.remove_sign_up(event_id, current_user.id)
        flash(message)
        return redirect(url_for('profile'))
