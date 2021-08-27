import os
import random
import data
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from app import app, db, bcrypt, mail
from app.forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm, ContactForm, PostForm
from app.models import User, Post, Firm, Product
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

global data


@app.before_first_request
def setup_db():
    db.drop_all()
    db.create_all()
    data.fill_database()


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/layout')
def layout():
    return render_template('layout.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))


def save_picture(form_picture):
    random_hex = random.getrandbits(34)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = "{}{}".format(random_hex, f_ext)
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form, posts=posts)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('contact.html', form=form)
        else:
            flash('Form posted.')
            return redirect(url_for('index'))
    elif request.method == 'GET':
        return render_template('contact.html', form=form)


@app.route('/bloghome')
def bloghome():
    return render_template('bloghome.html')


@app.route("/firm/<string:name>")
def firm_page(name):
    firm = Firm.query.filter_by(name=name).first_or_404()
    products = Product.query.filter_by(producer=firm)
    return render_template('bloghome.html', products=products, firm=firm)


@app.route('/bloghome1')
def bloghome1():
    return render_template('blog-home-2.html')


@app.route("/product/<int:product_id>")
@login_required
def product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('productpage.html', type=product.type, product=product)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender=app.config['MAIL_USERNAME'], recipients=[user.email])
    msg.body = ('For reset password click the following link: ' + (url_for('reset_token', token=token, _external=True)))
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@app.route('/db-search')
def db_search():
    query = request.args.get('query')
    id = db.engine.execute("SELECT * FROM firms WHERE name=:param", {"param": query})
    id = id.fetchone()
    if id != None:
        id = str(id.name)
        return "/firm/" + id
    else:
        id = db.engine.execute("SELECT * FROM products WHERE type=:param", {"param": query})
        id = str(id.first().id)
        return "/product/" + id


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('new_post', post_id=post.id))
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('create_post.html', form=form, posts=posts)


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('post', post_id=post.id))

