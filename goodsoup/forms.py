#-*- coding:utf-8 -*-
from flask.ext.wtf import Form,widgets
from wtforms import (
        widgets,
        TextField,
        TextAreaField, 
        SubmitField, 
        validators, 
        ValidationError, 
        PasswordField, 
        FileField, 
        RadioField, 
        SelectField, 
        SelectMultipleField, 
        BooleanField
        )
from models import db, User
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, current_app
import re

class Signup_form(Form):
    username    = TextField('username', [validators.Required(u'이름을 적어주세요')])
    email       = TextField('email', [validators.Required(u'이메일을 입력해주세요'),validators.Email(u'꼭 이메일 주소로 입력해주세요')])
    password    = PasswordField('password', [validators.Required(u'비밀번호를 입력해주세요')])
    password_check = PasswordField('password_check', [validators.Required(u'비밀번호를 확인해주세요')])
    address     = TextField('address',[validators.Required(u'나머지 주소를 입력해주세요')])
    tel         = TextField('tel',[validators.Required(u'전화번호를 입력해주세요'),validators.Regexp(r'[0-9]+-[0-9]+-[0-9]+')])

    def __init__(self, *args, **kargs):
        Form.__init__(self, *args, **kargs)

    def validate(self):
        if not Form.validate(self):
            return False
        if self.password.data != self.password_check.data:
            self.password_check.errors.append(u'비밀번호 확인이 틀리셨습니다.%s %s')
            return False
        user = User.query.filter_by(email=self.email.data.lower()).first()
        if user:
            self.email.errors.append(u'해당 이메일이 이미 존재합니다')
            return False
        else :
            return True

class Signin_form(Form):
    email       = TextField('email', [validators.Required(u'이메일을 입력해주세요'),validators.Email(u'꼭 이메일 주소로 입력해주세요')])
    password    = PasswordField('password', [validators.Required(u'비밀번호를 입력해주세요')])
    auto_login  = BooleanField('auto_login')

    def __init__(self, *args, **kargs):
        Form.__init__(self, *args, **kargs)

    def validate(self):
        if not Form.validate(self):
            return False
        user = User.query.filter_by(email=self.email.data.lower()).first()
        if user and user.check_password(self.password.data):
            return True
        else :
            self.email.errors.append(u'이메일 혹은 비밀번호가 틀렸습니다.')
            return False

class Board_create_form(Form):
    title       = TextField('title', [validators.Required(u'글 제목을 써주세요')])

    def __init__(self, *args, **kargs):
        Form.__init__(self, *args, **kargs)

    def validate(self):
        if not Form.validate(self):
            return False
        return True

class Comment_create_form(Form):
    body        = TextAreaField('comment', [validators.Required(u'댓글을 써주세요')])

    def __init__(self, *args, **kargs):
        Form.__init__(self, *args, **kargs)

    def validate(self):
        if not Form.validate(self):
            return False
        return True
