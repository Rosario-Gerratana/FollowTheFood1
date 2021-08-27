from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from app import db, login_manager, app
from flask_login import UserMixin

"The database has been introduced through Flask-SQLAlchemy. It is an extension for Flask that adds support for "
"SQLAlchemy. "


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return "User ('{}', '{}', '{}')".format(self.username, self.email, self.image_file)


class Firm(db.Model):
    __tablename__ = 'firms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    logo = db.Column(db.String(20), nullable=False, default='default.jpg')
    content = db.Column(db.String(1000), nullable=False, unique=True)
    location = db.Column(db.String(64), nullable=False)
    products = db.relationship('Product', backref='producer', lazy=True)

    def __repr__(self):
        return "Firm ('{}')".format(self.name)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64), nullable=False)
    photo = db.Column(db.String(20), nullable=False, default='default.jpg')
    point_availability = db.Column(db.String(100))
    firm_producer = db.Column(db.Integer, db.ForeignKey('firms.id'), nullable=False)
    posts = db.relationship('Post', backref='products', lazy=True)

    def __repr__(self):
        return "Product ('{}', '{}', '{}')".format(self.name, self.image_file, self.point_availability)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    # firm_id = db.Column(db)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return "Post ('{}', '{}', '{}')".format(self.title, self.date_posted, self.content)
