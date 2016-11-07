#!/usr/bin/python
#-*- coding:utf-8 -*-
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__   = 'user'
    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(200))
    email           = db.Column(db.String(500), unique=True)
    password        = db.Column(db.String(200))
    created_at      = db.Column(db.DateTime)
    si              = db.Column(db.String(100))
    gu              = db.Column(db.String(100))
    dong            = db.Column(db.String(100))
    address         = db.Column(db.String(300))
    tel             = db.Column(db.String(200))

    def __init__(self, username, email, password, si, gu, dong, address, tel):
        self.username   = username
        self.email      = email
        self.set_password(password)
        self.created_at = datetime.now()
        self.si         = si
        self.gu         = gu
        self.dong       = dong
        self.address    = address
        self.tel        = tel

    def set_password(self, password):
        self.password   = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

class Image(db.Model):
    __tablename__   = 'image'    
    id              = db.Column(db.Integer, primary_key=True)
    image_path      = db.Column(db.String(1024))
    created_at      = db.Column(db.DateTime)
    user_id         = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, image_path, user_id):
        self.image_path = image_path
        self.created_at = datetime.now()
        self.user_id    = user_id

class Soup(db.Model):
    __tablename__   = 'soup'
    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(400))
    price           = db.Column(db.Integer)
    discounted_price= db.Column(db.Integer)
    description     = db.Column(db.String(1000))
    amount          = db.Column(db.Integer)
    is_special      = db.Column(db.SmallInteger)
    
    def __init__(self, name, price, discounted_price, description, amout=9999, is_special=0):
        self.name               = name
        self.price              = price
        self.discounted_price   = discounted_price
        self.description        = description
        self.amount             = amount
        self.is_special         = is_special

class Soup_has_image(db.Model):
    __tablename__   = 'soup_has_image'
    soup_id         = db.Column(db.Integer, primary_key=True)
    image_id        = db.Column(db.Integer, primary_key=True)

    def __init__(self, soup_id, image_id):
        self.soup_id    = soup_id
        self.image_id   = image_id

class Board(db.Model):
    __tablename__   = 'board'
    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(300))
    body            = db.Column(db.Text)
    created_at      = db.Column(db.DateTime)
    user_id         = db.Column(db.Integer, db.ForeignKey('user.id'))
    board_category_id   = db.Column(db.Integer, db.ForeignKey('board_category.id'))

    def __init__(self, title, body, user_id, board_category_id):
        self.title      = title
        self.body       = body
        self.created_at = datetime.now()
        self.user_id    = user_id
        self.board_category_id = board_category_id

class Board_category(db.Model):
    __tablename__   = 'board_category'
    id              = db.Column(db.Integer, primary_key=True)
    category_name   = db.Column(db.String(200))

    def __init__(self, category_name):
        self.category_name = category_name

class Board_comment(db.Model):
    __tablename__   = 'board_comment'
    id              = db.Column(db.Integer, primary_key=True)
    body            = db.Column(db.String(500))
    created_at      = db.Column(db.DateTime)
    board_id        = db.Column(db.Integer, db.ForeignKey('board.id'))
    user_id         = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, body, board_id, user_id):
        self.body       = body
        self.created_at = datetime.now()
        self.board_id   = board_id
        self.user_id    = user_id

class Payment(db.Model):
    __tablename__   = 'payment'
    id              = db.Column(db.Integer, primary_key=True)
    apply_num       = db.Column(db.Integer)
    state           = db.Column(db.Integer)
    created_at      = db.Column(db.DateTime)
    si              = db.Column(db.String(100))
    gu              = db.Column(db.String(100))
    dong            = db.Column(db.String(100))
    address         = db.Column(db.String(300))
    tel             = db.Column(db.String(200))
    imp_uid         = db.Column(db.Integer)
    paid_amout      = db.Column(db.Integer)

    def __init__(self, apply_num, si, gu, dong, address, tel, imp_uid, paid_amout, state=0):
        self.apply_num  = apply_num
        self.created_at = datetime.now()
        self.si         = si
        self.gu         = gu    
        self.dong       = dong
        self.address    = address
        self.tel        = tel
        self.imp_uid    = imp_uid
        self.paid_amout = paid_amout
        self.state      = state

class Payment_has_soup(db.Model):
    __tablename__   = 'payment_has_soup'
    payment_id      = db.Column(db.Integer, primary_key=True)
    soup_id         = db.Column(db.Integer, primary_key=True)

    def __init__(self, payment_id, soup_id):
        self.payment_id = payment_id
        self.soup_id    = soup_id
