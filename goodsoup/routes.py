# -*- coding:utf-8 -*-
from flask import Flask, url_for
from flask.ext.paginate import Pagination
from flask import render_template, flash, redirect, session, url_for, request, g, jsonify
from flask import get_flashed_messages
from werkzeug import secure_filename
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.datastructures import FileStorage
from sqlalchemy import func

from config import UPLOAD_FOLDER, GS_DATABASE_URI, GS_SECRET_KEY

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI']   = GS_DATABASE_URI
#app.config['SECRET_KEY']                = GS_SECRET_KEY
#app.config['UPLOAD_FOLDER']             = UPLOAD_FOLDER

import os
import sys
import utils
navbar_menus = utils.enum('HOME','SOUP','ABOUT','BOARD','LOGIN','CART')

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

@app.route('/login')
def login():
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.LOGIN,
            }
    return render_template('login.html',ret=ret)

@app.route('/cart')
def cart():
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.CART,
            }
    return render_template('/cart.html',ret=ret)

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    app.run(host='222.239.250.23',debug=True)
