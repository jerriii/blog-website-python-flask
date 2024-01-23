import math
import os

from flask import Flask, render_template, url_for, request, redirect, jsonify, flash, make_response, abort
from flask_wtf import CSRFProtect
from spacy.tokens import Token
from sqlalchemy import and_, func
from werkzeug.security import check_password_hash, generate_password_hash

from datetime import datetime

from algorithm import recommend_post
from helpers import UPLOAD_FOLDER, content_type_options, parameters
from image_utils import allowed_file, save_image_file
from models import Posts, db, Users, Ratings, UserTimeSpent
from profanity_checker import set_profane_extension, pf
from utils import get_current_user, session, is_user_logged_in, set_user_in_session

app = Flask(__name__)
app.debug = True
app.secret_key = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = parameters['local_uri']

db.init_app(app)
csrf = CSRFProtect(app)


@app.context_processor
def inject():
    return dict(parameters=parameters, current_user=get_current_user())


@app.before_request
def before_request_handler():
    user = get_current_user()
    if user and not request.path.startswith('/static/'):
        if user.preferences is None:
            if request.path != '/select_preferences':
                flash('Please select preferences', 'error')
                return redirect('/select_preferences')


@app.route('/select_preferences', methods=['GET', 'POST'])
def select():
    if request.method == 'POST':
        user = get_current_user()
        user.preferences = request.form.get('content_type')
        user.topics = ",".join([topic.strip() for topic in request.form.get('preferences').split(',')])
        db.session.commit()
        return redirect('/')
    return render_template('select_preferences.html', content_type_options=content_type_options)


@app.route("/report_time_spent", methods=['POST'])
@csrf.exempt
def report_time_spent():
    post_id = request.json.get('post_id')
    time_spent = request.json.get('time_spent')
    if get_current_user() and post_id and time_spent:
        user = get_current_user()
        UserTimeSpent.query.filter_by(user_id=user.id, post_id=post_id).first().time += int(time_spent)
        db.session.commit()
    return {"success": True}


@app.route("/")
def home():
    posts = recommend_post(get_current_user(), Posts.query.filter(and_(Posts.isVerified == 1, Posts.isProfane == 0)) \
                           .order_by(Posts.date.desc()).all())
    last = math.ceil(len(posts) / int(parameters['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(parameters['no_of_posts']): (page - 1) * int(parameters['no_of_posts']) + int(
        parameters['no_of_posts'])]

    # Fetch usernames from user_ids
    usernames = {}
    for post in posts:
        user = Users.query.get(post.user_id)
        if user:
            usernames[post.user_id] = user.username
        else:
            usernames[post.user_id] = "Unknown"  # Default username if user is not found
    #
    if page == 1:
        prev = "#"
        nxt = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        nxt = "#"
    else:
        prev = "/?page=" + str(page - 1)
        nxt = "/?page=" + str(page + 1)

    home_bg_url = url_for('static', filename='assets/img/home-bg.jpg')
    return render_template('index.html', home_bg_url=home_bg_url, posts=posts, prev=prev, next=nxt,
                           usernames=usernames)


@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if is_user_logged_in():
        return redirect(url_for('user_post'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = Users.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            set_user_in_session(user_id=user.id)
            session.pop('user', None)

            flash('Login successful.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.', 'error')

    validation_js = url_for('static', filename='js/validation.js')
    sign_in = url_for('static', filename='css/sign-in.css')
    return render_template('user_login.html', sign_in=sign_in, validation_js=validation_js)


@app.route('/user_register', methods=['GET', 'POST'])
def user_register():
    if is_user_logged_in():
        return redirect(url_for('user_post'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']

        hashed_password = generate_password_hash(password)
        new_user = Users(username=username, password=hashed_password, email=email, phone=phone)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('user_login'))

    validation_js = url_for('static', filename='js/validation.js')
    sign_in = url_for('static', filename='css/sign-in.css')
    return render_template('user_register.html', sign_in=sign_in, validation_js=validation_js)


@app.route('/user_post', methods=['GET', 'POST'])
def user_post():
    if not is_user_logged_in():
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        title = request.form['title']
        tagline = request.form['tagline']
        slug = request.form['slug']
        content = request.form['content']
        content_type = request.form['content_type']
        date = datetime.now()
        img_file = request.files['img_file']

        errors = {}

        if not title:
            errors['title'] = 'A title is required.'
        if not tagline:
            errors['tagline'] = 'A tagline is required.'
        if not slug:
            errors['slug'] = 'Slug is required.'
        if not content:
            errors['content'] = 'Content is required.'
        if not content_type:
            errors['content_type'] = 'Content Type is required.'
        if not img_file:
            errors['img_file'] = 'Image File is required.'
        elif not allowed_file(img_file.filename):
            errors['img_file'] = 'Invalid file type. Only .jpg, .jpeg, and .png images are supported.'

        if errors:
            for key, value in errors.items():
                flash(value, 'error')
            session['post_form_data'] = request.form
            return redirect(url_for('user_post'))

        # Check if the image file was successfully saved
        filename = save_image_file(img_file)
        if not filename:
            flash('Error saving the image file. Please try again.', 'error')
            session['post_form_data'] = request.form
            return redirect(url_for('user_post'))

        user_id = session.get('user_id')

        Token.set_extension('is_profane', getter=set_profane_extension, force=True)  # type: ignore

        if pf.is_profane(title) or pf.is_profane(tagline) or pf.is_profane(slug) or pf.is_profane(content):
            is_profane = True

            flash('Post contains inappropriate content so it may not be published.', 'warning')
        else:
            is_profane = False
            flash('Post submitted successfully.', 'success')

        new_post = Posts(title=title,
                         tagline=tagline,
                         slug=slug,
                         content=content,
                         content_type=content_type,
                         date=date,
                         img_file=filename,
                         user_id=user_id,
                         isVerified=False,
                         isProfane=is_profane)
        db.session.add(new_post)
        db.session.commit()
        session.pop('post_form_data', None)

    about_bg_url = url_for('static', filename="assets/img/about-bg.jpg")
    return render_template('user_post.html', errors={}, about_bg_url=about_bg_url,
                           content_type_options=content_type_options)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    post_id = post.sno
    file_path = 'assets/img/' + post.img_file
    post_bg_url = url_for('static', filename=file_path)
    user_id = session.get('user_id')

    if get_current_user() and not UserTimeSpent.query.filter_by(user_id=user_id, post_id=post_id).first():
        db.session.add(UserTimeSpent(user_id=user_id, post_id=post_id))
        db.session.commit()

    ratings = Ratings.query.filter_by(post_id=post_id).join(Users).all()
    recommended_posts = recommend_post(get_current_user(), Posts.query.all())
    items_per_page = 3
    page = request.args.get('page', 1, type=int)
    total_posts = len(recommended_posts)
    total_pages = (total_posts + items_per_page - 1) // items_per_page

    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    current_posts = recommended_posts[start_idx:end_idx]

    return render_template('post.html', post_bg_url=post_bg_url, post=post, post_id=post_id, user_id=user_id,
                           ratings=ratings, current_posts=current_posts, total_pages=total_pages, current_page=page)


@app.route("/submit_rating_comment", methods=["POST"])
def submit_rating_comment():
    if request.method == "POST":
        user_id = session.get("user_id")
        post_id = request.json.get("post_id")
        rating = request.json.get("rating")
        comment = request.json.get("comment")

        if user_id and post_id and rating:
            existing_rating = Ratings.query.filter_by(post_id=post_id, user_id=user_id).first()
            if existing_rating:
                existing_rating.rating = rating
                existing_rating.comment = comment
            else:
                new_rating = Ratings(post_id=post_id, user_id=user_id, rating=rating, comment=comment)
                db.session.add(new_rating)

            db.session.commit()

            ratings = Ratings.query.filter_by(post_id=post_id).all()
            total_ratings = sum(rating.rating for rating in ratings)
            overall_rating = total_ratings / len(ratings)
            post_obj = Posts.query.get(post_id)
            post_obj.overall_rating = overall_rating
            db.session.commit()

            response_data = {"success": True, "message": "Rating and comment submitted successfully."}
            return jsonify(response_data)
        else:
            flash("Invalid data.", "error")
            return {"message": "Invalid data."}, 400


@app.route('/check_slug')
def check_slug():
    entered_slug = request.args.get('slug')

    # Check if the entered slug already exists in the database
    existing_post = Posts.query.filter_by(slug=entered_slug).first()
    if existing_post:
        return {'exists': True}
    else:
        return {'exists': False}


@app.route("/about")
def about():
    about_bg_url = url_for('static', filename='assets/img/about-bg.jpg')
    return render_template('about.html', about_bg_url=about_bg_url)


@app.route("/users")
def users():
    user = Users.query.all()
    home_bg_url = url_for('static', filename='assets/img/home-bg.jpg')
    return render_template('users.html', home_bg_url=home_bg_url, user=user)


@app.route("/profile")
def profile():
    user_id = session.get('user_id')

    user = None
    post = None

    if user_id:
        user = Users.query.filter_by(id=user_id).first()
        post = Posts.query.filter_by(user_id=user_id).all()

    about_bg_url = url_for('static', filename='assets/img/about-bg.jpg')
    return render_template('profile.html', about_bg_url=about_bg_url, user=user, post=post)


@app.route("/dashboard", methods=['POST', 'GET'])
def dashboard():
    if 'user' in session and session['user'] == parameters['admin_user']:
        post = Posts.query.all()
        home_bg_url = url_for('static', filename='assets/img/home-bg.jpg')
        return render_template('dashboard.html', home_bg_url=home_bg_url, post=post)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('upass')
        if username == parameters['admin_user'] and userpass == parameters['admin_password']:
            session['user'] = username
            post = Posts.query.all()
            home_bg_url = url_for('static', filename='assets/img/home-bg.jpg')
            return render_template('dashboard.html', post=post, home_bg_url=home_bg_url)

    sign_in = url_for('static', filename='css/sign-in.css')
    return render_template('login.html', sign_in=sign_in)


@app.route("/approve_post", methods=['GET'])
def approve_posts():
    if 'user' in session and session['user'] == parameters['admin_user']:
        posts = Posts.query.filter(Posts.isVerified == 0).all()

        home_bg_url = url_for('static', filename='assets/img/home-bg.jpg')
        return render_template('approve_post.html', posts=posts, home_bg_url=home_bg_url)
    else:
        flash('You need to log in as an admin to access this page.', 'warning')
        return redirect('/dashboard')


@app.route("/check/<int:post_id>", methods=['GET', 'POST'])
def check(post_id):
    if 'user' in session and session['user'] == parameters['admin_user']:
        posts = Posts.query.get_or_404(post_id)

        if request.method == 'POST' and 'delete' in request.form:
            if posts.sno is not None:
                UserTimeSpent.query.filter_by(post_id=posts.sno).delete()
            db.session.delete(posts)
            db.session.commit()

            flash('Post deleted successfully', 'success')
            return redirect('/dashboard')

        if request.method == 'POST' and 'approve' in request.form:
            # Get the data from the UserPosts and add it to Posts database
            title = posts.title
            tagline = posts.tagline
            slug = posts.slug
            content = posts.content
            content_type = posts.content_type
            date = datetime.now().strftime('%Y-%m-%d')
            img_file = posts.img_file
            user_id = posts.user_id

            is_verified = 1

            post = Posts(title=title, tagline=tagline, slug=slug, content=content, content_type=content_type, date=date,
                         img_file=img_file, isVerified=is_verified, user_id=user_id)
            db.session.add(post)
            db.session.commit()

            # Delete the entry from UserPosts after approval
            db.session.delete(posts)
            db.session.commit()

            flash('Post approved and added to Posts database.', 'success')
            return redirect('/dashboard')

        return render_template('check.html', posts=posts)
    else:
        flash('You need to log in as an admin to access this page.', 'warning')
        return redirect('/dashboard')


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/')


@app.route('/user_logout')
def user_logout():
    set_user_in_session(logout=True)
    session.clear()
    response = make_response(redirect(url_for('home')))
    response.headers['Cache-Control'] = 'no-store, must-revalidate, max-age=0, no-cache, private'

    flash('You have been logged out.', 'success')
    return response


@app.after_request
def add_cache_control(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/edit/<string:sno>", methods=['POST', 'GET'])
def edit(sno):
    if is_user_logged_in():
        if request.method == 'POST':
            title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            content_type = request.form.get('content_type')
            img_file = request.files['img_file']

            if sno == '0':
                flash('You cannot add post', 'warning')
                return redirect('/profile')

            post = Posts.query.filter_by(sno=sno).first()
            post.title = title
            post.slug = slug
            post.content = content
            post.content_type = content_type
            post.tagline = tagline

            if img_file:
                new_filename = save_image_file(img_file)
                if new_filename:
                    old_img_path = os.path.join(UPLOAD_FOLDER, post.img_file)
                    if os.path.exists(old_img_path):
                        os.remove(old_img_path)
                    post.img_file = new_filename

            db.session.commit()
            return redirect('/profile')

        home_bg_url = url_for('static', filename='/assets/img/home-bg.jpg')
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', sno=sno, post=post, home_bg_url=home_bg_url,
                               content_type_options=content_type_options)


@app.route('/edit_account', methods=['GET', 'POST'])
def edit_account():
    current_user = get_current_user()

    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        current_user.phone = request.form['phone']
        old_password = request.form['old_password']

        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password and confirm_password:
            if check_password_hash(current_user.password, old_password):
                if new_password == confirm_password:
                    current_user.password = generate_password_hash(new_password)
                    flash('Password updated successfully!', 'success')
                else:
                    flash('New password and confirm password do not match.', 'error')
            else:
                flash('Old password is incorrect.', 'error')

        db.session.commit()
        flash('Changes saved successfully!', 'success')
        return redirect(url_for('profile'))
    sign_in = url_for('static', filename='css/sign-in.css')
    return render_template('edit_account.html', current_user=current_user, sign_in=sign_in)


@app.route("/cancel")
def cancel():
    return redirect("/profile")


@app.route("/delete/<string:sno>", methods=['POST', 'GET'])
def delete(sno):
    if 'user' in session and session['user'] == parameters['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()

        # Delete UserTimeSpent entries
        UserTimeSpent.query.filter_by(post_id=post.sno).delete()

        # Delete ratings entries referencing the post
        ratings_entries = Ratings.query.filter_by(post_id=post.sno).all()
        for entry in ratings_entries:
            db.session.delete(entry)

        # Delete the post
        db.session.delete(post)
        db.session.commit()

        return redirect('/dashboard')
    elif is_user_logged_in():
        post = Posts.query.filter_by(sno=sno).first()

        # Delete UserTimeSpent entries
        UserTimeSpent.query.filter_by(post_id=post.sno).delete()

        # Delete ratings entries referencing the post
        ratings_entries = Ratings.query.filter_by(post_id=post.sno).all()
        for entry in ratings_entries:
            db.session.delete(entry)

        # Delete the post
        db.session.delete(post)
        db.session.commit()

        return redirect('/profile')
    else:
        abort(403)


def update_remaining_post_ratings():
    subquery = db.session.query(
        Ratings.post_id,
        func.avg(Ratings.rating).label('avg_rating')
    ).group_by(Ratings.post_id).subquery()

    posts = db.session.query(Posts, subquery.c.avg_rating). \
        outerjoin(subquery, Posts.sno == subquery.c.post_id).all()

    for post, avg_rating in posts:
        post.overall_rating = avg_rating or 0.0  # Handle the case when there are no ratings

    # Commit the changes to the database
    db.session.commit()


@app.route("/delete_user/<int:user_id>", methods=['POST', 'GET'])
def delete_user(user_id):
    if 'user' in session and session['user'] == parameters['admin_user']:
        session.pop('user_id', None)

        UserTimeSpent.query.filter_by(user_id=user_id).delete()
        user = Users.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()

            update_remaining_post_ratings()

            flash('User and related data deleted successfully.', 'message')
            return redirect(url_for("users"))
        else:
            flash('User not found.', 'message')
            return redirect(url_for("users"))
    else:
        flash('Unauthorized', 'message')
        return redirect(url_for("users"))


@app.route("/delete_account", methods=['POST', 'GET'])
def delete_account():
    user_id_to_delete = session.get('user_id')

    session.pop('user_id', None)
    UserTimeSpent.query.filter_by(user_id=user_id_to_delete).delete()
    # Delete user-related data
    user_main_posts = Posts.query.filter_by(user_id=user_id_to_delete).all()
    for post in user_main_posts:
        Ratings.query.filter_by(post_id=post.sno).delete()
    Posts.query.filter_by(user_id=user_id_to_delete).delete()

    # Commit the changes to the database to delete user-related data
    db.session.commit()

    # Update overall_rating for remaining posts
    update_remaining_post_ratings()

    # Delete the user
    Users.query.filter_by(id=user_id_to_delete).delete()

    # Commit the changes to the database to delete the user
    db.session.commit()

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)
