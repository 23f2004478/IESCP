from main import app
from flask import render_template, request, redirect, session, url_for, flash, send_file, current_app
from models import db, User, Sponsor, Influencer, Campaign, Ad, Message, Transaction, Rating, SocialMedia
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os
import re
import csv
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import func

# Decorators -------------------------------------------------------------------------------------------

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("You need to login first")
            return redirect(url_for('login'))
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username')
            return redirect(url_for('login'))
        if not user.is_admin:
            flash("You are not authorized to visit this page")
            return redirect(url_for('home'))
        return func(*args, **kwargs)
    return wrapper

def sponsor_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("You need to login first", "error")
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username')
            flash("User not found", "error")
            return redirect(url_for('login'))
        
        if user.role != "sponsor" and not user.is_admin: # Admins are also authorized to do whatever sponsors can do
            flash("You are not authorized to visit this page", "error")
            return redirect(url_for('home'))
        
        return func(*args, **kwargs)
    
    return wrapper

def influencer_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("You need to login first")
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username')
            flash("User not found", "error")
            return redirect(url_for('login'))
        
        if user.role != "influencer" and not user.is_admin: # Admins are also authorized to do whatever influencers can do
            flash("You are not authorized to visit this page")
            return redirect(url_for('home'))
        return func(*args, **kwargs)
    return wrapper

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("You need to login first")
            return redirect(url_for('login'))
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

# Home / Dashboard Page -------------------------------------------------------------------------------------------

@app.route('/')
@login_required
def home():
    if 'username' not in session:
        flash("You need to login first")
        return redirect(url_for('login'))

    username=session['username']
    users = User.query.all()
    campaigns = Campaign.query.all()

    if session['role'] == 'admin':
        return render_template('admin/dashboard.html', username=username, users=users, campaigns=campaigns)

    if session['role'] == 'influencer':
        user = User.query.filter_by(username=session['username']).first()
        influencer = Influencer.query.filter_by(id=user.id).first()
        influencer_id = User.query.filter_by(username=session['username']).first().id
        ad_requests = Ad.query.filter_by(influencer_id=influencer_id).all()
        return render_template('influencer/dashboard.html', influencer=influencer, username=username, users=users, campaigns=campaigns, user=user, ad_requests=ad_requests)
    
    if session['role'] == 'sponsor':
        user = User.query.filter_by(username=session['username']).first()
        sponsor = Sponsor.query.filter_by(id=user.id).first()
        sponsor_id = User.query.filter_by(username=session['username']).first().id
        campaigns = Campaign.query.filter_by(sponsor_id=sponsor_id).all()
        current_date = datetime.utcnow().date()
        return render_template('sponsor/dashboard.html', sponsor=sponsor, username=username, users=users, campaigns=campaigns, user=user, current_date=current_date)

# User Settings ---------------------------------------------------------------------------------------- 

@app.route('/add_edit_delete_social_media', methods=['POST'])
@login_required
def add_edit_delete_social_media():
    platform = request.form.get('platform')
    link = request.form.get('link')
    followers_count = request.form.get('followers_count')
    social_media_id = request.form.get('social_media_id')
    delete_action = request.form.get('delete_action')
    current_user = User.query.filter_by(username=session['username']).first()

    if current_user.role == "influencer":
        influencer = Influencer.query.filter_by(id=current_user.id).first()
        
        if delete_action:  # Delete social media
            social_media = SocialMedia.query.filter_by(id=social_media_id, influencer_id=influencer.id).first()
            if social_media:
                db.session.delete(social_media)
                db.session.commit()
                flash("Social Media deleted successfully", 'success')
            else:
                flash("Social Media not found", 'error')
        elif social_media_id:  # Edit existing social media
            social_media = SocialMedia.query.filter_by(id=social_media_id, influencer_id=influencer.id).first()
            if social_media:
                social_media.platform = platform
                social_media.link = link
                social_media.followers_count = followers_count
                db.session.commit()
                flash("Social Media updated successfully", 'success')
            else:
                flash("Social Media not found", 'error')
        else:  # Add new social media
            new_social_media = SocialMedia(platform=platform, link=link, followers_count=followers_count, influencer_id=influencer.id)
            db.session.add(new_social_media)
            db.session.commit()
            flash("Social Media added successfully", 'success')
    
    return redirect(url_for('settings'))

@app.route('/user/settings')
@login_required
def settings():
    current_user = User.query.filter_by(username=session['username']).first()

    if current_user.role == "admin":
        return render_template('admin/settings.html', current_user=current_user)

    if current_user.role == "sponsor":
        sponsor = Sponsor.query.filter_by(id=current_user.id).first()
        name = sponsor.name
        industry = sponsor.industry
        return render_template('sponsor/settings.html', current_user=current_user, sponsor=sponsor, name=name, industry=industry)
    
    if current_user.role == "influencer":
        influencer = Influencer.query.filter_by(id=current_user.id).first()
        name = influencer.name
        category = influencer.category
        niche = influencer.niche

        social_media = SocialMedia.query.filter_by(influencer_id=influencer.id).all()

        return render_template('influencer/settings.html', current_user=current_user, influencer=influencer, name=name, category=category, niche=niche, social_media=social_media)

@app.route('/user/settings', methods=['POST'])
def settings_post():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    current_user = User.query.filter_by(username=username).first()
    
    nusername = request.form.get('username')
    password = request.form.get('password')
    npassword = request.form.get('npassword')
    confirm = request.form.get('confirm')
    name = request.form.get('name')

    #sponsor specific
    industry = request.form.get('industry')
    
    #influencer specific
    category = request.form.get('category')
    niche = request.form.get('niche')

    # Change username if provided and valid
    if nusername:
        if nusername != current_user.username:
            quser = User.query.filter_by(username=nusername).first()
            if quser:
                flash("Username is already taken, please choose another username")
                return redirect(url_for('settings'))
            current_user.username = nusername
            flash(f"Username changed to {nusername}", category='success')
        else:
            flash("New username is the same as the current username", category='info')

    # Change password if provided and valid
    if password and npassword:
        if check_password_hash(current_user.passhash, password):
            if npassword != confirm:
                flash("Please check if new password and confirm new password are the same")
                return redirect(url_for('settings'))
            if not validate_password(npassword):
                flash("Password must be at least 8 characters long, contain a mix of uppercase and lowercase letters, numbers, and special characters, and must not include common words or patterns.", category='error')
                return redirect(url_for('settings'))
            current_user.passhash = generate_password_hash(npassword)
            flash("Password changed successfully", category='success')
        else:
            flash("Entered current password is incorrect")
            return redirect(url_for('settings'))

    # Update sponsor details (name, industry)
    if current_user.role == "sponsor":
        sponsor = Sponsor.query.filter_by(id=current_user.id).first()
        if name:
            sponsor.name = name
        if industry:
            sponsor.industry = industry

    # Update influencer details (name, category, niche)
    if current_user.role == "influencer":
        influencer = Influencer.query.filter_by(id=current_user.id).first()
        if name:
            influencer.name = name
        if category:
            influencer.category = category
        if niche:
            influencer.niche = niche

    db.session.commit()
    return redirect(url_for('settings'))

# Upload Profile Picture --------------------------------------------------------------------------------

# Define the directory where uploaded files will be stored
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'IESCP/static/exports')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure the upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/upload_profile_picture', methods=['POST'])
@login_required
def upload_profile_picture():
    current_user = User.query.filter_by(username=session['username']).first()

    if 'profile_picture' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['profile_picture']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # Delete the old profile picture if it's not the default
        if current_user.profile_picture != 'default_profile_picture.jpg':
            old_profile_picture_path = os.path.join(current_app.root_path, 'IESCP/static/uploads', current_user.profile_picture)
            if os.path.exists(old_profile_picture_path):
                os.remove(old_profile_picture_path)

        # Save the new profile picture
        filename = current_user.username + '_' + datetime.now().strftime('%Y%m%d%H%M%S') + '_' + file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure the directory exists before saving
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        file.save(file_path)
        current_user.profile_picture = filename
        db.session.commit()
        flash('Profile picture uploaded successfully', 'success')
        return redirect(url_for('profile', username=current_user.username))

    flash('Invalid file format. Allowed formats are PNG, JPG, JPEG, GIF')
    return redirect(url_for('settings'))

@app.route('/delete_profile_picture', methods=['POST'])
@login_required
def delete_profile_picture():
    current_user = User.query.filter_by(username=session['username']).first()

    # Define the path to the current profile picture
    profile_picture_path = os.path.join(current_app.root_path, 'IESCP/static/uploads', current_user.profile_picture)

    # Check if the current profile picture is not the default picture and if the file exists
    if current_user.profile_picture != 'default_profile_picture.jpg' and os.path.exists(profile_picture_path):
        os.remove(profile_picture_path)  # Delete the file

    current_user.profile_picture = 'default_profile_picture.jpg'
    db.session.commit()
    flash('Profile picture deleted successfully', 'success')
    return redirect(url_for('profile', username=current_user.username))

# User Login -------------------------------------------------------------------------------------------

def validate_password(password):
    if len(password) < 8:
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    if any(char.isspace() for char in password):
        return False
    common_patterns = ['password', 'qwerty', 'abcd']
    if any(pattern in password.lower() for pattern in common_patterns):
        return False
    return True


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if not username or not password:
        flash("Please fill all the mandatory fields", 'error')
        return redirect(url_for('login'))
    
    if not validate_password(password):
        flash("Password must be at least 8 characters long, contain a mix of uppercase and lowercase letters, numbers, and special characters, and must not include common words or patterns.", 'error')
        return redirect(url_for('login'))

    if not user or not check_password_hash(user.passhash, password) or user.role == "admin":
        flash("Username or password is incorrect")
        return redirect(url_for('login'))
    if user.is_deleted:
        flash("Your account has been deleted. Please contact support for assistance.", 'error')
        return redirect(url_for('login'))
    if user.is_flagged:
        flash("Your account has been flagged. Please contact support for assistance.", 'error')
        return redirect(url_for('login'))
    
    session['username'] = username
    session['role'] = user.role
    flash("Login Successful", 'success')
    return redirect(url_for('home'))

# Admin Login -------------------------------------------------------------------------------------------

@app.route('/secret-login')
def admin_login():
    return render_template('secret-login.html')

@app.route('/secret-login', methods=['POST'])
def admin_login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if not username or not password:
        flash("Please fill all the mandatory fields.", 'error')
        return redirect(url_for('admin_login'))
    
    if not validate_password(password):
        flash("Password must be at least 8 characters long, contain a mix of uppercase and lowercase letters, numbers, and special characters, and must not include common words or patterns.", 'error')
        return redirect(url_for('admin_login'))

    if not user or not check_password_hash(user.passhash, password):
        flash("Username or password is incorrect.", 'error')
        return redirect(url_for('admin_login'))
    
    if not user.is_admin:
        flash("Admin not found.", 'error')
        return redirect(url_for('admin_login'))
    
    session['username'] = username
    session['role'] = user.role
    flash("Admin Login Successful.", 'success')
    return redirect(url_for('home'))
    
# Sponsor Registration -----------------------------------------------------------------------------------

industries_list = [
    "Technology",
    "Health & Wellness",
    "Fashion & Beauty",
    "Food & Beverage",
    "Travel & Leisure",
    "Home & Garden",
    "Finance & Investment",
    "Education & Learning",
    "Entertainment",
    "Automotive",
    "Sports & Outdoors",
    "Pets",
    "Parenting & Family",
    "Arts & Crafts",
    "Business & Entrepreneurship",
    "Other"
]

@app.route('/register-sponsor')
def register_sponsor():
    return render_template('register-sponsor.html', industries_list=industries_list)

@app.route('/register-sponsor', methods=['POST'])
def register_sponsor_post():
    name = request.form.get('name')
    industry = request.form.get('industry')
    username = request.form.get('username')
    password = request.form.get('password')
    confirm = request.form.get('confirm')

    # all not nullable inputs are not empty
    if not username or not password or not confirm or not name or not industry:
        flash("Please fill all the mandatory fields", 'error')
        return redirect(url_for('register_sponsor'))

    if not validate_password(password):
        flash("Password must be at least 8 characters long, contain a mix of uppercase and lowercase letters, numbers, and special characters, and must not include common words or patterns.", category='error')
        return redirect(url_for('login'))
    
    # confirm and password should be same
    if not password == confirm:
        flash("Confirm and Password are not same", 'error')
        return redirect(url_for('register_sponsor'))

    # username should be unique
    user = User.query.filter_by(username=username).first()
    if user:
        flash("Please choose another username, selected username is taken", 'error')
        return redirect(url_for('register_sponsor'))
    
    passhash = generate_password_hash(password)

    user = User(username=username, passhash=passhash, role="sponsor")
    db.session.add(user)
    db.session.commit()

    sponsor = Sponsor(id=user.id, name=name, industry=industry)
    db.session.add(sponsor)
    db.session.commit()

    flash("Registration Successful, Please login to continue", category='success')
    return redirect(url_for('login'))

# Influencer Registration --------------------------------------------------------------------------------

# Dict of Cateogories and their niches

categories_dict = {
    "Technology": ["Gadgets", "Software", "Apps", "AI & Machine Learning", "Cybersecurity", "Wearables", "Smart Home Devices", "Virtual Reality", "Blockchain", "Drones"],
    "Health & Wellness": ["Fitness", "Nutrition", "Mental Health", "Skincare", "Supplements", "Yoga", "Meditation", "Alternative Medicine", "Health Apps", "Personal Training"],
    "Fashion & Beauty": ["Clothing", "Accessories", "Makeup", "Haircare", "Footwear", "Jewelry", "Skincare", "Fragrances", "Eyewear", "Sustainable Fashion"],
    "Food & Beverage": ["Restaurants", "Fast Food", "Organic Products", "Beverages", "Snacks", "Meal Kits", "Supplements", "Specialty Foods", "Cooking Equipment", "Catering"],
    "Travel & Leisure": ["Destinations", "Travel Gear", "Activities", "Accommodation", "Travel Agencies", "Cruises", "Adventure Travel", "Cultural Tours", "Travel Insurance", "Travel Apps"],
    "Home & Garden": ["Furniture", "Gardening Tools", "Home Decor", "Appliances", "Smart Home Devices", "Cleaning Supplies", "DIY Tools", "Outdoor Furniture", "Home Security", "Kitchenware"],
    "Finance & Investment": ["Personal Finance", "Cryptocurrency", "Real Estate", "Banking", "Insurance", "Financial Planning", "Stock Trading", "Retirement Planning", "Tax Services", "Investment Apps"],
    "Education & Learning": ["Online Courses", "Books", "Tutoring", "Educational Tools", "eLearning Platforms", "Test Preparation", "Language Learning", "Skill Development", "Academic Research", "Certifications"],
    "Entertainment": ["Movies", "Music", "Gaming", "Events", "Streaming Services", "Concerts", "Theater", "Comedy Shows", "Celebrity News", "Podcasts"],
    "Automotive": ["Cars", "Motorcycles", "Accessories", "Services", "Electric Vehicles", "Car Rentals", "Car Insurance", "Car Maintenance", "Auto Parts", "Car Dealerships"],
    "Sports & Outdoors": ["Outdoor Gear", "Fitness Equipment", "Team Sports", "Individual Sports", "Sportswear", "Outdoor Activities", "Camping Equipment", "Biking", "Fishing", "Hiking"],
    "Pets": ["Pet Food", "Pet Accessories", "Pet Healthcare", "Pet Training", "Pet Grooming", "Pet Toys", "Pet Insurance", "Pet Adoption", "Pet Travel", "Pet Services"],
    "Parenting & Family": ["Baby Products", "Parenting Tips", "Family Activities", "Educational Toys", "Childcare Services", "Family Health", "Parenting Apps", "Family Travel", "Family Finance", "Family Entertainment"],
    "Arts & Crafts": ["Art Supplies", "Craft Kits", "DIY Projects", "Sewing", "Knitting", "Painting", "Drawing", "Sculpture", "Pottery", "Art Classes"],
    "Business & Entrepreneurship": ["Startups", "Business Tools", "Marketing", "Networking", "Business Finance", "HR Solutions", "Office Supplies", "Business Consulting", "E-commerce", "Business Training"]
}

@app.route('/register-influencer', methods=['GET'])
def register_influencer():
    return render_template('register-influencer.html', categories_dict=categories_dict)


@app.route('/register-influencer', methods=['POST'])
def register_influencer_post():
    name = request.form.get('name')
    category = request.form.get('category')
    niche = request.form.get('niche')
    username = request.form.get('username')
    password = request.form.get('password')
    confirm = request.form.get('confirm')

    # all not nullable inputs are not empty
    if not username or not password or not confirm:
        flash("Please fill all the mandatory fields", 'error')
        return redirect(url_for('register_influencer'))

    if not validate_password(password):
        flash("Password must be at least 8 characters long, contain a mix of uppercase and lowercase letters, numbers, and special characters, and must not include common words or patterns.", category='error')
        return redirect(url_for('login'))
    
    # confirm and password should be same
    if not password == confirm:
        flash("Confirm and Password are not same")
        return redirect(url_for('register_influencer'))

    # username should be unique
    user = User.query.filter_by(username=username).first()
    if user:
        flash("Please choose another username, selected username is taken", 'error')
        return redirect(url_for('register_influencer'))
    
    passhash = generate_password_hash(password)

    user = User(username=username, passhash=passhash, role="influencer")
    db.session.add(user)
    db.session.commit()

    sponsor = Influencer(id=user.id, name=name, category=category, niche=niche)
    db.session.add(sponsor)
    db.session.commit()

    flash("Registration Successful, Please login to continue", category='success')
    return redirect(url_for('login'))

# Delete User -------------------------------------------------------------------------------------------

@app.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get(id)
    current_user = User.query.filter_by(username=session.get('username')).first()

    if not user:
        flash("User does not exist")
        return redirect(url_for('user_list'))

    if user.is_admin:
        flash("You cannot delete an admin")
        return redirect(url_for('user_list'))

    if user.username != session.get('username') and not current_user.is_admin:
        flash("You are not authorized to perform this action")
        return redirect(url_for('settings'))

    if user.is_deleted:  # If user is already deleted
        user.is_deleted = False
        db.session.commit()
        flash("User undeleted successfully", 'success')
    else:  # Mark user as deleted
        user.is_deleted = True
        db.session.commit()
        flash("User deleted successfully", 'success')

    if current_user.is_admin:
        return redirect(url_for('user_list'))
    else:
        return redirect(url_for('logout'))

    
# PERMANENTLY Delete User (admin access only) -------------------------------------------------------------------------------------------

@app.route('/users/<int:id>/permanently_delete', methods=['POST'])
@admin_required
def permanently_delete_user(id):
    user = User.query.get(id)

    if not user:
        flash("User does not exist")
        return redirect(url_for('user_list'))

    if user.role == "admin":
        flash("You cannot permanently delete an admin")
        return redirect(url_for('user_list'))

    db.session.delete(user)
    db.session.commit()
    flash("Permanently deleted user.", 'success')
    return redirect(url_for('user_list'))

# User Logout -------------------------------------------------------------------------------------------

@app.route('/logout')
def logout():
    current_user = User.query.filter_by(username=session['username']).first()
    session.pop('username')
    session.pop('role')
    if current_user.is_deleted:
        return redirect(url_for('login'))
    if current_user.is_admin:
        flash("Admin logged out successfully", 'success')
        return redirect(url_for('admin_login'))
    flash("Logged out successfully", 'success')
    return redirect(url_for('login'))
    

# Campaigns Section ------------------------------------------------------------------------------

@app.route('/campaigns')
def campaigns():
    if session['role'] == 'sponsor':
        user = User.query.filter_by(username=session['username']).first()
        sponsor_id = User.query.filter_by(username=session['username']).first().id
        campaigns = Campaign.query.filter_by(sponsor_id=sponsor_id)
        return render_template('campaigns.html', campaigns=campaigns, user=user)
    if session['role'] == 'admin':
        campaigns = Campaign.query.all()
        return render_template('campaigns.html', campaigns = campaigns)


# Add Campaign ------------------------------------------------------------------------------------------

@app.route('/campaigns/add')
def campaign_add():
    if session['role'] == 'sponsor':
        return render_template('sponsor/campaign/add.html')
    else:
        flash("The current user is not eligible for creating a new campaign.")
        return redirect(url_for('home'))

@app.route('/campaigns/add', methods=['POST'])
def campaign_add_post():
    name = request.form.get('name')
    description = request.form.get('description')
    goals = request.form.get('goals')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    budget = request.form.get('budget')
    visibility = request.form.get('visibility')
    remaining_budget = budget

    if not name:
        flash("Name is mandatory")
        return redirect(url_for('campaign_add'))
    
    campaign = Campaign.query.filter_by(name=name).first()
    if campaign:
        flash("Campaign with this name already exists", 'error')
        return redirect(url_for('campaign_add'))

    if len(name) > 64:
        flash("Campaign Name cannot be more than 64 characters", 'error')
        return redirect(url_for('campaign_add'))

    if len(description) > 250:
        flash("Campaign Description cannot be more than 250 characters", 'error')
        return redirect(url_for('campaign_add'))

    if len(goals) > 250:
        flash("Campaign Goals cannot be more than 250 characters", 'error')
        return redirect(url_for('campaign_add'))

    if start_date < datetime.now().strftime("%Y-%m-%d"):
        flash("Start Date cannot be in the past.", 'error')
        return redirect(url_for('campaign_add'))

    if start_date > end_date:
        flash("Start Date cannot be greater than End Date", 'error')
        return redirect(url_for('campaign_add'))
     
    if start_date:
        start_date = datetime.strptime(start_date,"%Y-%m-%d")
    else:
        start_date=None

    if end_date:
        end_date = datetime.strptime(end_date,"%Y-%m-%d")
    else:
        end_date=None
    
    user = User.query.filter_by(username=session['username']).first()
    campaign = Campaign(name=name, description=description, start_date=start_date, end_date=end_date, budget=budget, remaining_budget=remaining_budget, visibility=visibility, goals=goals, sponsor_id=user.id)
    db.session.add(campaign)
    db.session.commit()
    flash("Campaign added successfully", category='success')
    return redirect(url_for('campaigns'))

# Edit Campaign ------------------------------------------------------------------------------------------

@app.route('/campaigns/<int:id>/edit')
@sponsor_required
def campaign_edit(id):
    campaign = Campaign.query.get(id)
    return render_template('sponsor/campaign/edit.html', campaign=campaign)

@app.route('/campaigns/<int:id>/edit', methods=['POST'])
def campaign_edit_post(id):
    name = request.form.get('name')
    description = request.form.get('description')
    goals = request.form.get('goals')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    budget = request.form.get('budget')
    visibility = request.form.get('visibility')

    current_campaign = Campaign.query.get(id)
    campaign = Campaign.query.filter_by(name=name).first()

    # Validations

    if not name or not start_date or not end_date or not budget or not visibility:
        flash("The field is mandatory")
        return redirect(url_for('campaign_edit', id=f'{id}'))

    if campaign and campaign.id != current_campaign.id:
        flash("Category with this name already exists")
        return redirect(url_for('campaign_edit', id=f'{id}'))

    if len(name) > 64:
        flash("Category Name cannot be more than 64 characters")
        return redirect(url_for('campaign_edit', id=f'{id}'))

    if len(description) > 250:
        flash("Category Description cannot be more than 250 characters")
        return redirect(url_for('category_edit', id=f'{id}'))

    if start_date:
        start_date = datetime.strptime(start_date,"%Y-%m-%d")
    else:
        start_date=None

    if end_date:
        end_date = datetime.strptime(end_date,"%Y-%m-%d")
    else:
        end_date=None

    current_campaign.name = name
    current_campaign.description = description
    current_campaign.goals = goals
    current_campaign.start_date = start_date
    current_campaign.end_date = end_date
    current_campaign.budget = budget
    current_campaign.visibility = visibility

    db.session.commit()
    flash("Campaign edited successfully.", category="success")
    return redirect(url_for('campaigns'))

# Delete Campaign --------------------------------------------------------------------------------------

@app.route('/campaign/<int:id>/delete', methods=['POST'])
@sponsor_required
def campaign_delete(id):
    campaign = Campaign.query.get(id)
    print(campaign.id)
    if not campaign:
        flash("Campaign does not exist")
        return redirect(url_for('campaign_delete', id=f'{id}'))
    db.session.delete(campaign)
    db.session.commit()
    flash("Campaign deleted successfully", category='success')
    return redirect(url_for('campaigns'))

# Flag Campaign -----------------------------------------------------------------------------------------

@app.route('/campaigns/<int:id>/flag', methods=['POST'])
@admin_required
def flag_campaign(id):
    campaign = Campaign.query.get(id)
    if not campaign:
        flash("Campaign does not exist")
        return redirect(url_for('campaigns'))
    
    if campaign.is_flagged:
        campaign.is_flagged = False
        db.session.commit()
        flash("Campaign unflagged successfully", 'success')
        return redirect(url_for('campaigns'))
    
    campaign.is_flagged = True
    db.session.commit()
    flash("Campaign flagged successfully", 'success')
    return redirect(url_for('campaigns'))

# Ad Requests (for Sponsors) -------------------------------------------------------------------------------------

@app.route('/campaigns/<int:id>/ads')
@login_required
def ads(id):
    current_user = User.query.filter_by(username=session['username']).first()
    campaign = Campaign.query.get(id)

    if not campaign:
        flash("Campaign does not exist")
        return redirect(url_for('campaigns'))
    
    return render_template('sponsor/campaign/ads.html', campaign=campaign, current_user=current_user)

# Add Ad Request --------------------------------------------------------------------------------------------------

@app.route('/campaigns/<int:id>/ads/add')
@login_required
def ad_add(id):
    campaign = Campaign.query.get(id)
    influencers = Influencer.query.all()
    return render_template('sponsor/ad/add.html', campaign=campaign, influencers=influencers)

@app.route('/campaigns/<int:id>/ads/add', methods=['POST'])
@login_required
def ad_add_post(id):
    campaign = Campaign.query.get(id)
    if not campaign:
        flash("Campaign does not exist")
        return redirect(url_for('campaigns'))
    
    title = request.form.get('title')
    message = request.form.get('message')
    requirements = request.form.get('requirements')
    payment_amount = request.form.get('payment_amount')
    sponsor_id = Campaign.query.get(id).sponsor_id

    if session['role'] == 'sponsor':
        current_handler = 'influencer'
        influencer_id = request.form.get('influencer_id')
    elif session['role'] == 'influencer':
        current_handler = 'sponsor'
        influencer_id = User.query.filter_by(username=session['username']).first().id

    payment_amount = float(payment_amount)

    if not title or not message or not requirements or not payment_amount:
        flash("Please fill all the mandatory fields")
        return redirect(url_for('ad_add', id=f'{id}'))
    if len(title) > 64:
        flash("Title cannot be more than 64 characters")
        return redirect(url_for('ad_add', id=f'{id}'))
    if len(message) > 250:
        flash("Message cannot be more than 250 characters")
        return redirect(url_for('ad_add', id=f'{id}'))
    if len(requirements) > 250:
        flash("Requirements cannot be more than 250 characters")
        return redirect(url_for('ad_add', id=f'{id}'))
    if int(payment_amount) < 0:
        flash("Payment amount cannot be negative")
        return redirect(url_for('ad_add', id=f'{id}'))
    if int(payment_amount) > campaign.remaining_budget:
        flash("Payment amount cannot be greater than remaining budget")
        return redirect(url_for('ad_add', id=f'{id}'))
    
    ad = Ad(
        title=title, 
        message=message, 
        requirements=requirements, 
        payment_amount=payment_amount, 
        campaign_id=id,
        sponsor_id=sponsor_id,
        influencer_id=influencer_id,
        current_handler=current_handler
    )

    db.session.add(ad)
    db.session.commit()
    flash("Ad request added successfully", category='success')
    return redirect(url_for('ads', id=f'{id}'))

# Search Campaigns & Ads (temporary for testing) -------------------------------------------------------------------------------

@app.route('/search')
@login_required
def search():
    current_user = User.query.filter_by(username=session['username']).first()

    search = request.args.get('search')
    budget = request.args.get('budget')
    category = request.args.get('category')
    niche = request.args.get('niche')

    campaigns, sponsors, influencers = [], [], []

    if search or budget or category or niche:
        campaign_query = Campaign.query.filter(Campaign.visibility == 'public')
        sponsor_query = Sponsor.query
        influencer_query = Influencer.query

        if search:
            search_filter = f"%{search}%"
            campaign_query = campaign_query.filter(Campaign.name.ilike(search_filter))
            sponsor_query = sponsor_query.filter(Sponsor.name.ilike(search_filter))
            influencer_query = influencer_query.filter(Influencer.name.ilike(search_filter))

        if budget:
            campaign_query = campaign_query.filter(Campaign.budget <= int(budget))

        if category:
            influencer_query = influencer_query.filter(Influencer.category.ilike(f"%{category}%"))

        if niche:
            influencer_query = influencer_query.filter(Influencer.niche.ilike(f"%{niche}%"))

        campaigns = campaign_query.all()
        sponsors = sponsor_query.all()
        influencers = influencer_query.all()

    return render_template('search.html', current_user=current_user, search=search, campaigns=campaigns, sponsors=sponsors, influencers=influencers, budget=budget, category=category, niche=niche)


# -----------------------------------------Profile------------------------------------------------------

@app.route('/<string:username>/profile')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first()
    current_user = User.query.filter_by(username=session['username']).first()

    if current_user.role == "admin":
        return render_template('admin/profile.html', user=user)
    
    if user.role == "sponsor":
        sponsor = Sponsor.query.filter_by(id=user.id).first()
        campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()
        current_date = datetime.utcnow().date()

        active_campaigns = [campaign for campaign in campaigns if current_date <= campaign.end_date]
        past_campaigns = [campaign for campaign in campaigns if current_date > campaign.end_date]

        return render_template('sponsor/profile.html', user=user, current_user=current_user, sponsor=sponsor, campaigns=campaigns, current_date=current_date, active_campaigns=active_campaigns, past_campaigns=past_campaigns)
    
    if user.role == "influencer":
        influencer = Influencer.query.filter_by(id=user.id).first()

        social_media = SocialMedia.query.filter_by(influencer_id=influencer.id).all()
        influencer.reach = sum(social.followers_count for social in social_media)

        unique_campaigns = (
            db.session.query(Campaign)
            .join(Ad)
            .filter(Ad.influencer_id == influencer.id)
            .distinct(Campaign.id)
            .options(joinedload(Campaign.ads))
            .all()
        )

        rating_counts = (
        db.session.query(Rating.rating, func.count(Rating.rating))
            .filter_by(influencer_id=influencer.id)
            .group_by(Rating.rating)
            .all()
        )
        
        rating_dict = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating, count in rating_counts:
            rating_dict[int(rating)] = count

        total_ratings = sum(rating_dict.values())

        social_links = {}
        for social_media in influencer.social_media_handles:
            social_links[social_media.platform] = social_media.link
        
        platforms = ['YouTube', 'Twitter', 'Facebook', 'Instagram', 'Twitch']
        for platform in platforms:
            if platform not in social_links:
                social_links[platform] = '#'

        return render_template('influencer/profile.html', user=user, current_user=current_user, influencer=influencer, campaigns=unique_campaigns, rating_dict=rating_dict, total_ratings=total_ratings, social_links=social_links)

# Chat ------------------------------------------------------------------------------------------------------------

@app.route('/mychats')
@login_required
def mychats():
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        return redirect(url_for('login'))

    messages = Message.query.filter(
        (Message.sender_id == current_user.id) |
        (Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp.desc()).all()

    latest_messages = {}
    for message in messages:
        contact_id = message.receiver_id if message.sender_id == current_user.id else message.sender_id
        if contact_id not in latest_messages or message.timestamp > latest_messages[contact_id].timestamp:
            latest_messages[contact_id] = message

    contacts = {}
    for contact_id in latest_messages:
        user = User.query.get(contact_id)
        if user:
            contact_type = None
            if Sponsor.query.get(contact_id):
                contact_type = 'sponsor'
            elif Influencer.query.get(contact_id):
                contact_type = 'influencer'
            else:
                contact_type = 'user'
            contacts[contact_id] = {
                'user': user,
                'type': contact_type
            }

    return render_template('myChats.html', latest_messages=latest_messages, contacts=contacts, current_user=current_user)

@app.route('/<string:username>/chat')
@login_required
def chat(username):
    user = User.query.filter_by(username=username).first()
    current_user = User.query.filter_by(username=session['username']).first()

    if user is None:
        flash('User does not exist.', 'danger')
        return redirect(url_for('home'))

    if user.id == current_user.id:
        flash('You cannot chat with yourself.', 'warning')
        return redirect(url_for('profile', username=username))

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user.id)) | 
        ((Message.sender_id == user.id) & (Message.receiver_id == current_user.id))
    ).all()
    return render_template('chat.html', user=user, messages=messages, current_user=current_user)

@app.route('/<string:username>/send_message', methods=['POST'])
@login_required
def send_message(username):
    receiver = User.query.filter_by(username=username).first()
    if receiver is None:
        flash('User does not exist.', 'danger')
        return redirect(url_for('chat', username=username))

    sender = User.query.filter_by(username=session['username']).first()
    if sender.id == receiver.id:
        flash('You cannot send a message to yourself.', 'warning')
        return redirect(url_for('chat', username=username))

    message_content = request.form['message']
    if not message_content:
        flash('Message cannot be empty.', 'warning')
        return redirect(url_for('chat', username=username))

    new_message = Message(
        sender_id=sender.id,
        receiver_id=receiver.id,
        content=message_content,
        timestamp=datetime.utcnow()
    )
    db.session.add(new_message)
    db.session.commit()
    
    return redirect(url_for('chat', username=username))


# Admin Dashboard (ADMIN SECTION) ----------------------------------------------------------------------------------------

@app.route('/users')
@admin_required
def user_list():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# Flag User ------------------------------------------------------------------------------------------------------------

@app.route('/users/<int:id>/flag', methods=['POST'])
@admin_required
def flag_user(id):
    user = User.query.get(id)
    if not user:
        flash("User does not exist")
        return redirect(url_for('user_list'))
    
    if user.is_flagged:
        user.is_flagged = False
        db.session.commit()
        flash("User unflagged successfully", 'success')
        return redirect(url_for('user_list'))
    
    user.is_flagged = True
    db.session.commit()
    flash("User flagged successfully", 'success')
    return redirect(url_for('user_list'))


# View Ad Requests (for influencers & sponsors) -----------------------------------------------------------------------------------

@app.route('/adrequest/<int:id>/view')
@login_required
def view_ad_request(id):
    ad = Ad.query.get(id)
    return render_template('view_ad_request.html', ad=ad)


# Ad Request Update Status ------------------------------------------------------------------------------------------

@app.route('/update_status/<int:id>/<string:status>', methods=['POST'])
@login_required
def update_status(id, status):
    ad = Ad.query.get(id)
    if ad:
        if status in ['accepted', 'rejected']:
            ad.status = status
            if status == 'accepted':
                ad.campaign.remaining_budget = ad.campaign.remaining_budget - ad.payment_amount
            db.session.commit()
            return redirect(url_for('view_ad_request', id=id))
        else:
            return "Invalid status", 400
    else:
        return "Ad not found", 404
    
# Ad Request Mark as Completed ------------------------------------------------------------------------------------------
    
@app.route('/mark_completed/<int:id>', methods=['POST'])
@login_required
def mark_completed(id):
    ad = Ad.query.get(id)
    if ad:
        ad.is_completed = True
        db.session.commit()
        return redirect(url_for('view_ad_request', id=id))
    
# Ad Payment Gateway --------------------------------------------------------------------------------------------------

@app.route('/pay/<int:id>')
@sponsor_required
def pay(id):
    ad = Ad.query.get(id)
    return render_template('transaction.html', ad=ad)

@app.route('/pay/<int:id>', methods=['POST'])
@sponsor_required
def pay_post(id):
    ad = Ad.query.get(id)
    if not ad:
        flash('Ad not found', 'danger')
        return redirect(url_for('pay', id=id)), 404

    if ad.status != 'accepted':
        flash('Ad request is not accepted', 'danger')
        return redirect(url_for('pay', id=id)), 400

    if ad.is_paid:
        flash('Ad request is already paid for', 'danger')
        return redirect(url_for('pay', id=id)), 400

    card_holder_name = request.form.get('card_holder_name')
    card_number = request.form.get('card_number')
    card_expiry = request.form.get('card_expiry')
    card_cvv = request.form.get('card_cvv')
    
    # Validation
    if not card_holder_name:
        flash('Card holder name is mandatory', 'danger')
        return redirect(url_for('pay', id=id)), 400
    
    if card_cvv and (not card_cvv.isdigit() or len(card_cvv) != 3):
        flash('Invalid CVV', 'danger')
        return redirect(url_for('pay', id=id)), 400
    
    if card_number and (not card_number.isdigit() or len(card_number) != 16):
        flash('Invalid card number', 'danger')
        return redirect(url_for('pay', id=id)), 400
    
    if card_expiry:
        try:
            card_expiry = datetime.strptime(card_expiry, '%Y-%m')
        except ValueError:
            flash('Invalid card expiry format', 'danger')
            return redirect(url_for('pay', id=id)), 400
    else:
        flash('Card expiry is mandatory', 'danger')
        return redirect(url_for('pay', id=id)), 400
    
    if card_expiry < datetime.utcnow():
        flash('Card has expired', 'danger')
        return redirect(url_for('pay', id=id)), 400

    ad.is_paid = True
    influencer = Influencer.query.get(ad.influencer_id)
    influencer.earnings = influencer.earnings + ad.payment_amount
    sponsor = Sponsor.query.get(ad.sponsor_id)
    sponsor.spendings = sponsor.spendings + ad.payment_amount

    transaction = Transaction(
        amount=ad.payment_amount,
        date_created=datetime.utcnow(),
        ad_id=ad.id,
        sponsor_id=ad.sponsor_id,
        influencer_id=ad.influencer_id,
        card_holder_name=card_holder_name,
        card_number=card_number,
        card_expiry=card_expiry,
        card_cvv=card_cvv
    )

    try:
        db.session.add(transaction)
        db.session.commit()

        ad.transaction_id = transaction.id
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        flash('Transaction could not be completed. Please try again.', 'danger')
        return redirect(url_for('pay', id=id))

    flash('Payment successful', 'success')
    return redirect(url_for('view_ad_request', id=id))

# View a Transaction--------------------------------------------------------------------------------------------------

@app.route('/transaction/<int:id>')
@login_required
def view_transaction(id):
    transaction = Transaction.query.get(id)
    return render_template('view_a_transaction.html', transaction=transaction)

# Edit Ad Request --------------------------------------------------------------------------------------------------

@app.route('/ads/<int:id>/edit')
@sponsor_required
def ad_edit(id):
    ad = Ad.query.get(id)
    if not ad:
        flash("Ad Request does not exist")
        return redirect(url_for('ads'))
    return render_template('sponsor/ad/edit.html', ad=ad)

# Delete Ad Request --------------------------------------------------------------------------------------------------

@app.route('/ads/<int:id>/delete', methods=['POST'])
@sponsor_required
def ad_delete(id):
    ad = Ad.query.get(id)
    if not ad:
        flash("Ad Request does not exist")
        return redirect(url_for('ads'))
    db.session.delete(ad)
    db.session.commit()
    flash("Ad Request deleted successfully", 'success')
    return redirect(url_for('ads', id=ad.campaign_id))

# Ad Request Negotiate ----------------------------------------------------------------------------------------------

@app.route('/negotiate/<int:id>', methods=['POST'])
@login_required
def negotiate(id):
    ad = Ad.query.get(id)
    if not ad:
        flash('Ad not found', 'danger')
        return "Ad not found", 404

    payment_amount = request.form.get('payment_amount')
    requirements = request.form.get('requirements')

    # Validation
    if not payment_amount:
        flash('Payment amount is mandatory', 'danger')
        return redirect(url_for('view_ad_request', id=id)), 400
    
    if not payment_amount.replace('.', '', 1).isdigit() or float(payment_amount) <= 0:
        flash('Payment amount must be a valid positive number', 'danger')
        return redirect(url_for('view_ad_request', id=id)), 400
    
    if len(requirements) > 250:
        flash("Requirements cannot be more than 250 characters")
        return redirect(url_for('ad_edit', id=f'{id}')), 400

    payment_amount = float(payment_amount)

    if payment_amount == ad.payment_amount and requirements == ad.requirements:
        flash('No changes detected in the negotiation request', 'warning')
        return redirect(url_for('view_ad_request', id=id))

    if session['role'] == 'sponsor':
        current_handler = 'influencer'
    elif session['role'] == 'influencer':
        current_handler = 'sponsor'
    
    # Update Ad
    ad.requirements = requirements
    ad.payment_amount = payment_amount
    ad.current_handler = current_handler
    ad.status = 'pending'
    db.session.commit()
    flash('Negotiation request submitted successfully!', 'success')
    return redirect(url_for('view_ad_request', id=id))

# Exporting Data (for ADMIN only) ------------------------------------------------------------------------------------------------
EXPORT_FOLDER = os.path.join(os.getcwd(), 'IESCP/static/exports')
app.config['EXPORT_FOLDER'] = EXPORT_FOLDER

# Export Campaigns Data (in CSV) ------------------------------------------------------------------------------------------------------------

@app.route('/export-campaigns-csv')
@admin_required
def export_campaigns_csv():
    campaigns = Campaign.query.all()
    current_user = User.query.filter_by(username=session['username']).first()
    filename = f"{current_user.username}_{datetime.now().strftime('%Y%m%d%H%M%S')}_campaigns_data.csv"
    path = os.path.join(app.config['EXPORT_FOLDER'], filename)
    
    with open(path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"')
        csvwriter.writerow(["ID", "Name", "Description", "Start Date", "End Date", "Budget", "Visibility", "Goals", "Date Created", "Sponsor ID"])
        for campaign in campaigns:
            csvwriter.writerow([campaign.id, campaign.name, campaign.description, campaign.start_date, campaign.end_date, campaign.budget, campaign.visibility, campaign.goals, campaign.date_created, campaign.sponsor_id])
    
    return send_file(path, as_attachment=True, download_name=filename)

# Export Users Data (in CSV) ------------------------------------------------------------------------------------------------------------

@app.route('/export-users-csv')
@admin_required
def export_users_csv():
    users = User.query.all()
    current_user = User.query.filter_by(username=session['username']).first()
    filename = current_user.username + '_' + datetime.now().strftime('%Y%m%d%H%M%S') + '_users_data.csv'
    path = os.path.join(app.config['EXPORT_FOLDER'], filename)
    
    with open(path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"')
        csvwriter.writerow(["ID", "Username", "Role", "Is Admin", "Is Flagged", "Is Deleted"])
        for user in users:
            csvwriter.writerow([user.id, user.username, user.role, user.is_admin, user.is_flagged, user.is_deleted])
    
    return send_file(path, as_attachment=True, download_name=filename)

# Export Ads Data (in CSV) ------------------------------------------------------------------------------------------------------------

@app.route('/export-ads-csv')
@admin_required
def export_ads_csv():
    ads = Ad.query.all()
    current_user = User.query.filter_by(username=session['username']).first()
    filename = current_user.username + '_' + datetime.now().strftime('%Y%m%d%H%M%S') + '_ads_data.csv'
    path = os.path.join(app.config['EXPORT_FOLDER'], filename)
    
    with open(path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"')
        csvwriter.writerow(["ID", "Title", "Message", "Requirements", "Payment Amount", "Status", "Date Created", "Campaign ID", "Sponsor ID", "Influencer ID"])
        for ad in ads:
            csvwriter.writerow([ad.id, ad.title, ad.message, ad.requirements, ad.payment_amount, ad.status, ad.date_created, ad.campaign_id, ad.sponsor_id, ad.influencer_id])
    
    return send_file(path, as_attachment=True, download_name=filename)


# Rating for an Ad Request after payment ------------------------------------------------------------------------------------------------

@app.route('/rate/<int:id>')
@sponsor_required
def rate(id):
    ad = Ad.query.get(id)
    return render_template('influencer/rating.html', ad=ad)

@app.route('/rate/<int:id>', methods=['POST'])
@sponsor_required
def rate_post(id):
    ad = Ad.query.get(id)
    if not ad:
        flash('Ad not found', 'danger')
        return "Ad not found", 404

    rating = request.form.get('rating')
    review = request.form.get('review')

    rating = float(rating)

    # Validation
    if not rating:
        flash('Rating is mandatory', 'danger')
        return redirect(url_for('rate', id=id)), 400
    
    if rating < 1 or rating > 5:
        flash('Rating is invalid', 'danger')
        return redirect(url_for('rate', id=id)), 400
    
    if len(review) > 250:
        flash("Review cannot be more than 250 characters", 'danger')
        return redirect(url_for('rate', id=id)), 400
    
    influencer = Influencer.query.get(ad.influencer_id)
    influencer.rating = (influencer.rating * influencer.rating_count + rating) / (influencer.rating_count + 1)
    influencer.rating_count += 1
    db.session.commit()

    new_rating = Rating(
        rating=rating,
        review=review,
        date_created=datetime.utcnow(),
        ad_id=id,
        sponsor_id=ad.sponsor_id,
        influencer_id=ad.influencer_id,
        transaction_id=ad.transaction_id
    )

    try:
        db.session.add(new_rating)
        db.session.commit()

        ad.is_rated = True
        ad.rating_id = new_rating.id
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        flash('Rating could not be completed. Please try again.', 'danger')
        return redirect(url_for('rate', id=id))

    flash('Rating submitted successfully!', 'success')
    return redirect(url_for('view_ad_request', id=id))
