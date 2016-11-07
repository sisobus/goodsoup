# -*- coding:utf-8 -*-
from flask import Flask, url_for
from flask.ext.paginate import Pagination
from flask import render_template, flash, redirect, session, url_for, request, g, jsonify
from flask import get_flashed_messages
from werkzeug import secure_filename
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.datastructures import FileStorage
from sqlalchemy import func

from config import (
        UPLOAD_FOLDER, 
        GS_DATABASE_URI, 
        GS_SECRET_KEY,
        GS_RESIZE_URL,
        GS_RESIZE_ROOT,
        GS_RESIZE_CACHE_DIR
        )
from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from datetime import datetime, timedelta
import os
import sys
import utils
import time
import json
import flask_resize

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']   = GS_DATABASE_URI
app.config['SECRET_KEY']                = GS_SECRET_KEY
app.config['UPLOAD_FOLDER']             = UPLOAD_FOLDER
app.config['RESIZE_URL']                = GS_RESIZE_URL
app.config['RESIZE_ROOT']               = GS_RESIZE_ROOT
app.config['RESIZE_CACHE_DIR']          = GS_RESIZE_CACHE_DIR
flask_resize.Resize(app)

from models import (
        db,
        User,
        Image,
        Soup,
        Soup_has_image,
        Board,
        Board_category,
        Board_comment,
        Payment,
        Payment_has_soup,
        )
from forms import (
        Signup_form,
        Signin_form,
        )

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

#
# address 
#
with open('/var/www/goodsoup/goodsoup/static/json/address.json','r') as fp:
    addresses = json.loads(fp.read())

@app.route('/json/address')
def address():
    """
    : search : route_address
    """
    return jsonify(results=addresses)
#
# address 
#

navbar_menus = utils.enum('HOME','SOUP','ABOUT','BOARD','LOGIN','CART')

@app.route('/test_user_db/<int:user_id>')
def test_user_db(user_id):
    user = User.query.filter_by(id=user_id).first()
    return jsonify(results={})

@app.route('/')
def home():
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.HOME,
            }
    return render_template('home.html',ret=ret)

@app.route('/soup')
def soup():
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.SOUP,
            }
    return render_template('soup.html',ret=ret)

@app.route('/about')
def about():
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.ABOUT,
            }
    return render_template('about.html',ret=ret)

@app.route('/board')
def board():
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.BOARD,
            }
    return render_template('board.html',ret=ret)

@app.route('/board_detail/<int:board_id>')
def board_detail(board_id):
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.BOARD,
            }
    return render_template('board_detail.html',ret=ret)

@app.route('/login')
def login():
    with app.app_context():
        signin_form = Signin_form()
        signup_form = Signup_form()
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.LOGIN,
            'signin_form': signin_form,
            'signup_form': signup_form,
            }
    return render_template('login.html',ret=ret)

@app.route('/signin',methods=['POST'])
def signin():
    with app.app_context():
        signin_form = Signin_form()
        signup_form = Signup_form()
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.LOGIN,
            'signin_form': signin_form,
            'signup_form': signup_form,
            }
    if request.method == 'POST':
        if not signin_form.validate():
            return render_template('login.html',ret=ret)
        email       = signin_form.email.data
        password    = signin_form.password.data
        auto_login  = signin_form.auto_login.data
        user        = User.query.filter_by(email=email.lower()).first()

        session['username'] = user.username
        session['email']    = user.email
        session['si']       = user.si
        session['gu']       = user.gu
        session['dong']     = user.dong
        session['address']  = user.address
        session['tel']      = user.tel
        session['user_id']  = user.id
        session['logged_in']= True

        return redirect(url_for('home'))
    elif request.method =='GET':
        return redirect(url_for('home'))
    return redirect(url_for('home'))

@app.route('/signup',methods=['POST'])
def signup():
    with app.app_context():
        signin_form = Signin_form()
        signup_form = Signup_form()
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.LOGIN,
            'signin_form': signin_form,
            'signup_form': signup_form,
            }
    if request.method == 'POST':
        if not signup_form.validate():
            return render_template('login.html',ret=ret)
        username    = signup_form.username.data
        email       = signup_form.email.data
        password    = signup_form.password.data
        si          = request.form.get('si')
        gu          = request.form.get('gu')
        dong        = request.form.get('dong')
        address     = signup_form.address.data
        tel         = signup_form.tel.data
        newuser     = User(username,email,password,si,gu,dong,address,tel)
        db.session.add(newuser)
        db.session.commit()

        session['username'] = username
        session['email']    = email
        session['si']       = si
        session['gu']       = gu
        session['dong']     = dong
        session['address']  = address
        session['tel']      = tel
        session['user_id']  = newuser.id
        session['logged_in']= True

        return redirect(url_for('home'))
    elif request.method == 'GET':
        return redirect('/')
    return redirect('/')

@app.route('/logout')
@login_required
def logout():
    if not 'logged_in' in session:
        return redirect(url_for('home'))
    session.pop('username',None)
    session.pop('email',None)
    session.pop('si',None)
    session.pop('gu',None)
    session.pop('dong',None)
    session.pop('address',None)
    session.pop('tel',None)
    session.pop('user_id',None)
    session.pop('logged_in',None)

    return redirect(url_for('home'))

@app.route('/cart')
def cart():
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.CART,
            }
    return render_template('cart.html',ret=ret)

@app.route('/soup_detail/<int:soup_id>')
def soup_detail(soup_id):
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.SOUP,
            }
    return render_template('soup_detail.html',ret=ret)

@app.route('/checkout')
def checkout():
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.SOUP,
            }
    return render_template('checkout.html',ret=ret)

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    app.run(host='222.239.250.23',debug=True)
