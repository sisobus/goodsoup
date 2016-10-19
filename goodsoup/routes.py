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

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    app.run(host='222.239.250.23',debug=True)
