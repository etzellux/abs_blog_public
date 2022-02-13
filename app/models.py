from datetime import datetime
from flask_login.mixins import AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask_login import UserMixin
from markdown import markdown
import bleach
from . import db, login_manager

class Permission:
    COMMENT = 1
    WRITE = 2
    MOD = 4
    ADMIN = 8


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(64), nullable=False, unique=True)
    username = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(128))
    regdate = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed = db.Column(db.Boolean, default=False)
    #foreign key
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), default=1)
    #relationship
    posts = db.relationship("Post", backref="author")
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError("password is not a readible attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.role.has_permission(Permission.ADMIN)
    
    def __repr__(self):
        return "<User %r>" % self.id

class AnonymousUser(AnonymousUserMixin):
    def can(self, perm):
        return False
    
    def is_administrator(self):
        return False

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(40), nullable=False)
    permissions = db.Column(db.Integer, nullable=False, default=0)
    #relationship
    users = db.relationship("User", backref="role")

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions -= perm

    def reset_permission(self):
        self.permissions = 0

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    header = db.Column(db.String(100))
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    last_edited = db.Column(db.DateTime, default=datetime.utcnow())
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    tagging = db.relationship("Tagging", backref="post", uselist=False)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'img', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p', 'table', 'tr', 'td']
        allowed_attr = {"a":["href"], "img":["src"]}
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format="html"),
                                        tags=allowed_tags, attributes=allowed_attr, strip=True))
db.event.listen(Post.body, "set", Post.on_changed_body)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'img', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        allowed_attr = {"a":["href"], "img":["src"]}
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format="html"),
                                        tags=allowed_tags, attributes=allowed_attr, strip=True))
db.event.listen(Comment.body, "set", Comment.on_changed_body)

class Tag(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False, unique=True)

class Tagging(db.Model):
    __tablename__ = "taggings"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    tag1_id = db.Column(db.Integer, nullable=False)
    tag2_id = db.Column(db.Integer, nullable=False)
    tag3_id = db.Column(db.Integer, nullable=False)

    def update(self, tagging : list()):
        if len(tagging) != 3:
            raise TypeError("Parameter must be a list with 3 elements")
        self.tag1_id = tagging[0]
        self.tag2_id = tagging[1]
        self.tag3_id = tagging[2]
    

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.anonymous_user = AnonymousUser 