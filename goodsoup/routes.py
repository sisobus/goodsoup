# -*- coding:utf-8 -*-
from flask import Flask, url_for
from flask.ext.paginate import Pagination
from flask import render_template, flash, redirect, session, url_for, request, g, jsonify
from flask import get_flashed_messages
from flask_mail import Mail, Message
from werkzeug import secure_filename
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.datastructures import FileStorage
from sqlalchemy import *

from config import (
        UPLOAD_FOLDER, 
        GS_DATABASE_URI, 
        GS_SECRET_KEY,
        GS_RESIZE_URL,
        GS_RESIZE_ROOT,
        GS_RESIZE_CACHE_DIR,
        GS_IMP_TEST_KEY,
        GS_IMP_TEST_API_KEY,
        GS_IMP_TEST_SECRET_KEY,
        MAIL_SERVER,
        MAIL_PORT,
        MAIL_USE_TLS,
        MAIL_USE_SSL,
        MAIL_USERNAME,
        MAIL_PASSWORD,
        )
from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from datetime import datetime, timedelta
import os
import sys
import utils
import time
import json
import flask_resize
import string
import random
from decorators import async
from iamport import Iamport

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']   = GS_DATABASE_URI
app.config['SECRET_KEY']                = GS_SECRET_KEY
app.config['UPLOAD_FOLDER']             = UPLOAD_FOLDER
app.config['RESIZE_URL']                = GS_RESIZE_URL
app.config['RESIZE_ROOT']               = GS_RESIZE_ROOT
app.config['RESIZE_CACHE_DIR']          = GS_RESIZE_CACHE_DIR
app.config["MAIL_SERVER"] = MAIL_SERVER
app.config["MAIL_PORT"] = MAIL_PORT
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = MAIL_USERNAME 
app.config["MAIL_PASSWORD"] = MAIL_PASSWORD
flask_resize.Resize(app)
mail = Mail(app)

iamport = Iamport(imp_key=GS_IMP_TEST_API_KEY,imp_secret=GS_IMP_TEST_SECRET_KEY)

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
        Soup_image,
        )
from forms import (
        Signup_form,
        Signin_form,
        Board_create_form,
        Comment_create_form,
        Soup_create_form,
        Update_user_form,
        Update_password_form,
        Find_password_form,
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

navbar_menus = utils.enum('HOME','SOUP','ABOUT','BOARD','STORE','LOGIN','CART','CHECK','MYPAGE','ADMIN')

### EMAIL
def generate_temp_password():
    alphabet     = list(string.ascii_uppercase)+list(string.ascii_lowercase)
    ret = ''
    for i in xrange(20):
        ret += alphabet[random.randint(0,len(alphabet)-1)]
    return ret

@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(app,msg)

### CREATE
@app.route('/save_board',methods=['POST'])
@login_required
def save_board():
    with app.app_context():
        board_create_form  = Board_create_form()
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.BOARD,
            'board_create_form': board_create_form,
            }
    if request.method == 'POST':
        if not board_create_form.validate_on_submit():
            return render_template('board_create.html',ret=ret)
        title               = board_create_form.title.data
        user_id             = session['user_id']
        board_category_id   = request.form.get('category')
        body                = request.form['board_body'].strip()
        new_board           = Board(title,body,user_id,board_category_id)
        db.session.add(new_board)
        db.session.commit()

        board_id = new_board.id
        return redirect(url_for('board_detail',board_id=board_id))
    elif request.method == 'GET':
        return redirect('/')
    return redirect('/')

@app.route('/save_comment/<int:board_id>',methods=['POST'])
@login_required
def save_comment(board_id):
    with app.app_context():
        comment_create_form = Comment_create_form()
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.BOARD,
            'comment_create_form': comment_create_form,
            }
    if request.method == 'POST':
        body    = comment_create_form.body.data
        board_id= board_id
        user_id = session['user_id']
        new_comment = Board_comment(body,board_id,user_id)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('board_detail',board_id=board_id))

    elif request.method == 'GET':
        return redirect('/')
    return redirect('/')

@app.route('/save_soup_image',methods=['POST'])
@login_required
def save_soup_image():
    if request.method == 'POST':
        if request.files:
            files = request.files
            for file_key in files:
                file = request.files[file_key]
                filename = secure_filename(file.filename)
                directory_name = utils.convert_email_to_directory_name(session['email'])
                directory_url = os.path.join(app.config['UPLOAD_FOLDER'],directory_name)
                utils.createDirectory(directory_url)
                file_path = os.path.join(directory_url,filename.split('.')[0]+'-'+str(datetime.now()).replace(' ','-')+'.'+filename.split('.')[-1])
                file.save(file_path)
                new_soup_image = Soup_image(file_path,1,session['user_id'])
                db.session.add(new_soup_image)
                db.session.commit()
                return json.dumps({'message': 'upload success'})
        return json.dumps({'message':'error'})
    return json.dumps({'message': 'upload success'})

@app.route('/save_soup',methods=['POST'])
def save_soup():
    with app.app_context():
        soup_create_form = Soup_create_form()

    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.SOUP,
            'soup_create_form': soup_create_form,
            }

    if request.method == 'POST':
        if not soup_create_form.validate():
            soup_images = Soup_image.query.filter_by(soup_id=1).all()
            for soup_image in soup_images:
                db.session.delete(soup_image)
                db.session.commit()
            return render_template('soup_create.html',ret=ret)
        name                = soup_create_form.name.data
        price               = int(soup_create_form.price.data.replace(',',''))
        discounted_price    = int(soup_create_form.discounted_price.data.replace(',',''))
        description         = soup_create_form.description.data
        amount              = int(soup_create_form.amount.data.replace(',',''))
        is_special          = soup_create_form.is_special.data
        if is_special:
            t = 1
        else :
            t = 0
        new_soup            = Soup(name,price,discounted_price,description,amount,t)
        db.session.add(new_soup)
        db.session.commit()
        soup_id             = new_soup.id
        soup_images         = Soup_image.query.filter_by(soup_id=1).all()
        for soup_image in soup_images:
            soup_image.soup_id  = soup_id
            db.session.commit()
        return redirect(url_for('soup_detail',soup_id=soup_id))
    elif request.method == 'GET':
        return redirect('/')
    return redirect('/')
###

### READ 
def get_board_categories():
    board_categories = Board_category.query.order_by(Board_category.id.asc())
    ret = {}
    for board_category in board_categories:
        ret[int(board_category.id)] = str(board_category.category_name)
    return ret

def get_board_information(boards):
    ret = []
    for board in boards:
        user = User.query.filter_by(id=board.user_id).first()
        number_of_comments = Board_comment.query.filter_by(board_id=board.id).count()
        d = {
            'id': board.id,
            'title': board.title,
            'body': board.body,
            'created_at': board.created_at,
            'user_id': board.user_id,
            'user': user,
            'board_category_id': board.board_category_id,
            'board_category_name': get_board_categories()[int(board.board_category_id)],
            'number_of_comments': number_of_comments,
            }
        ret.append(d)
    return ret

def get_board_by_board_id(board_id):
    board = Board.query.filter_by(id=board_id).first()
    user = User.query.filter_by(id=board.user_id).first()
    ret = {
        'id': board.id,
        'title': board.title,
        'body': board.body,
        'created_at': board.created_at,
        'user_id': board.user_id,
        'user': user,
        'board_category_id': board.board_category_id,
        'board_category_name': get_board_categories()[int(board.board_category_id)],
            }
    return ret

def get_comments_by_board_id(board_id):
    comments = Board_comment.query.filter_by(board_id=board_id).order_by(Board_comment.created_at.asc())
    ret = []
    for comment in comments:
        user = User.query.filter_by(id=comment.user_id).first()
        d = {
            'id': comment.id,
            'body': comment.body,
            'created_at': comment.created_at,
            'board_id': comment.board_id,
            'user_id': comment.user_id,
            'user': user,
                }
        ret.append(d)
    return ret

def get_soup_image_information(soup_images):
    ret = []
    for soup_image in soup_images:
        d = {
                'id': soup_image.id,
                'image_path': utils.get_image_path(soup_image.image_path),
                'created_at': soup_image.created_at,
                'soup_id': soup_image.soup_id,
                'user_id': soup_image.user_id,
                }
        ret.append(d)
    return ret

def get_soup_information(soups):
    ret = []
    for soup in soups:
        if soup.id == 1:
            continue
        payments = Payment.query.order_by(Payment.created_at.desc()).filter(Payment.created_at >= datetime.today().strftime('%Y-%m-%d'))
        today_paid_cnt = 0
        for payment in payments:
            payment_has_soup = Payment_has_soup.query.filter(and_(Payment_has_soup.payment_id==payment.id,Payment_has_soup.soup_id==soup.id)).first()
            if payment_has_soup:
                today_paid_cnt += payment_has_soup.soup_cnt


        soup_images = Soup_image.query.filter_by(soup_id=soup.id).order_by(Soup_image.created_at.asc())
        soup_images = get_soup_image_information(soup_images)
        d = {
                'id': soup.id,
                'name': soup.name,
                'price': soup.price,
                'discounted_price': soup.discounted_price,
                'description': soup.description,
                'amount': max(0,soup.amount-today_paid_cnt),
                'is_special': soup.is_special,
                'soup_images': soup_images,
                }
        ret.append(d)
    return ret

def get_payment_information(payments):
    ret = []
    for payment in payments:
        payment_has_soup = Payment_has_soup.query.filter_by(payment_id=payment.id).all()
        soups = []
        for phs in payment_has_soup:
            soup_id = phs.soup_id
            soup_cnt = phs.soup_cnt
            soup = Soup.query.filter_by(id=soup_id).first()
            soup = get_soup_information([soup])[0]
            soup['soup_cnt'] = soup_cnt
            soups.append(soup)
        user = User.query.filter_by(id=payment.user_id).first()

        d = {
                'id': payment.id,
                'created_at': payment.created_at,
                'address': payment.address,
                'tel': payment.tel,
                'imp_uid': payment.imp_uid,
                'paid_amount': payment.paid_amount,
                'apply_num': payment.apply_num,
                'state': payment.state,
                'soups': soups,
                'user': user,
                }
        ret.append(d)
    return ret


###

### UPDATE 
@app.route('/update_board/<int:board_id>',methods=['POST'])
@login_required
def update_board(board_id):
    with app.app_context():
        board_create_form  = Board_create_form()
    board = Board.query.filter_by(id=board_id).first()
    if not (session['user_id'] == board.user_id or session['level'] == 99):
        return redirect(url_for('home'))
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.BOARD,
            'board_create_form': board_create_form,
            'board': board,
            }
    if request.method == 'POST':
        if not board_create_form.validate_on_submit():
            return render_template('board_create',ret=ret)

        board.title               = board_create_form.title.data
        board.board_category_id   = request.form.get('category')
        board.body                = request.form['board_body'].strip()
        db.session.commit()

        return redirect(url_for('board_detail',board_id=board_id))
    elif request.method == 'GET':
        return redirect('/')
    return redirect('/')

@app.route('/update_soup/<int:soup_id>',methods=['POST'])
@login_required
def update_soup(soup_id):
    with app.app_context():
        soup_create_form = Soup_create_form()
    soup = Soup.query.filter_by(id=soup_id).first()
    
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.SOUP,
            'soup_create_form': soup_create_form,
            'soup': soup,
            }

    if request.method == 'POST':
        if not soup_create_form.validate():
            return render_template('soup_create.html',ret=ret)
        soup.name                = soup_create_form.name.data
        soup.price               = int(soup_create_form.price.data.replace(',',''))
        soup.discounted_price    = int(soup_create_form.discounted_price.data.replace(',',''))
        soup.description         = soup_create_form.description.data
        soup.amount              = int(soup_create_form.amount.data.replace(',',''))
        is_special          = soup_create_form.is_special.data
        if is_special:
            soup.is_special = 1
        else :
            soup.is_special = 0
        db.session.commit()
        return redirect(url_for('soup_detail',soup_id=soup_id))
    elif request.method == 'GET':
        return redirect('/')
    return redirect('/')

@app.route('/add_cart',methods=['POST'])
def add_cart():
    if request.method == 'POST':
        soup_id = request.form['soup_id']
        soup_cnt = request.form['soup_cnt']
        next_cart_list = []
        for item in session['cart_list']:
            if item['soup_id'] == soup_id:
                continue
            next_cart_list.append(item)
        next_cart_list.append({
            'soup_id': soup_id,
            'soup_cnt': soup_cnt
            });
        session['cart_list'] = next_cart_list
        return json.dumps({'message': 'add cart success'})

@app.route('/update_cart',methods=['POST'])
def update_cart():
    if request.method == 'POST':
        soup_id = request.form['soup_id']
        soup_cnt = request.form['soup_cnt']
        next_cart_list = []
        for item in session['cart_list']:
            if int(item['soup_id']) == int(soup_id):
                item['soup_cnt'] = soup_cnt
            next_cart_list.append(item)
        session['cart_list'] = next_cart_list
        return json.dumps({'message': 'update cart success'})


@app.route('/update_user',methods=['POST'])
@login_required
def update_user():
    with app.app_context():
        update_user_form = Update_user_form()
    user_id = session['user_id']
    user = User.query.filter_by(id=user_id).first()
    ret = {
        'navbar_menus': navbar_menus,
        'selected_navbar_index': navbar_menus.MYPAGE,
        'user': user
        }
    if not update_user_form.validate():
        ret['update_user_form']          = update_user_form 
        ret['si']                   = user.si
        ret['gu']                   = user.gu
        ret['dong']                 = user.dong
        return render_template('mypage_update_user.html',ret=ret)
    user.si = request.form.get('si')
    user.gu = request.form.get('gu')
    user.dong = request.form.get('dong')
    user.address = update_user_form.address.data
    user.tel = update_user_form.tel.data
    session['si']       = user.si
    session['gu']       = user.gu
    session['dong']     = user.dong
    session['address']  = user.address
    session['tel']      = user.tel
    db.session.commit()
    return redirect('/mypage/0')

@app.route('/update_password',methods=['POST'])
@login_required
def update_password():
    with app.app_context():
        update_password_form = Update_password_form()
    user = User.query.filter_by(id=session['user_id']).first()
    ret = {
        'navbar_menus': navbar_menus,
        'selected_navbar_index': navbar_menus.MYPAGE,
        'user': user
        }
    if not update_password_form.validate():
        ret['update_password_form'] = update_password_form
        return render_template('mypage_update_password.html',ret=ret)
    if not user.check_password(update_password_form.cur_password.data):
        ret['update_password_form'] = update_password_form
        update_password_form.cur_password.errors.append(u'기존 비밀번호가 틀렸습니다')
        return render_template('mypage_update_password.html',ret=ret)

    user.set_password(update_password_form.password.data)
    db.session.commit()
    return redirect('/mypage/0')

###

### DELETE 
@app.route('/delete_comment/<int:comment_id>',methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Board_comment.query.filter_by(id=comment_id).first()
    db.session.delete(comment)
    db.session.commit()
    return json.dumps({'message': 'delete success'})

@app.route('/delete_board/<int:board_id>',methods=['POST'])
@login_required
def delete_board(board_id):
    board = Board.query.filter_by(id=board_id).first()
    comments = Board_comment.query.filter_by(board_id=board.id).all()
    for comment in comments:
        db.session.delete(comment)
        db.session.commit()
    db.session.delete(board)
    db.session.commit()
    return json.dumps({'message': 'delete success'})

@app.route('/delete_image',methods=['POST'])
@login_required
def delete_image():
    if request.method == 'POST':
        filename = request.form.get('id')
        filename = secure_filename(filename)
        print filename
        only_filename = filename.split('.')[0]
        soup_image = Soup_image.query.filter(Soup_image.image_path.like('%'+only_filename+'%')).order_by(Soup_image.created_at.desc()).first()
        db.session.delete(soup_image)
        db.session.commit()
    return json.dumps({'message': 'delete success'})

@app.route('/delete_soup/<int:soup_id>',methods=['POST'])
@login_required
def delete_soup(soup_id):
    if request.method == 'POST':
        soup = Soup.query.filter_by(id=soup_id).first()
        soup_images = Soup_image.query.filter_by(soup_id=soup_id).all()
        for soup_image in soup_images:
            db.session.delete(soup_image)
            db.session.commit()
        payment_has_soups = Payment_has_soup.query.filter_by(soup_id=soup.id).all()
        for payment_has_soup in payment_has_soups:
            db.session.delete(payment_has_soup)
            db.session.commit()
        db.session.delete(soup)
        db.session.commit()
        return json.dumps({'message': 'delete success'})

    elif request.method == 'GET':
        return redirect('/')
    return redirect('/')

@app.route('/delete_cart',methods=['POST'])
def delete_cart():
    if request.method == 'POST':
        soup_id = request.form['soup_id']
        next_cart_list = []
        for item in session['cart_list']:
            if int(item['soup_id']) == int(soup_id):
                continue
            next_cart_list.append(item)
        session['cart_list'] = next_cart_list
        return json.dumps({'message': 'delete success'})
###


### VIEW
@app.route('/')
def home():
    if not 'cart_list' in session:
        session['cart_list'] = []
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.HOME,
            }
    return render_template('home.html',ret=ret)

@app.route('/soup')
def soup():
    special_soups   = Soup.query.filter_by(is_special=1).order_by(Soup.id.desc()).all()
    soups           = Soup.query.filter_by(is_special=0).order_by(Soup.id.desc()).all()
    special_soups   = get_soup_information(special_soups)
    soups           = get_soup_information(soups)
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.SOUP,
            'special_soups': special_soups,
            'soups': soups,
            }
    return render_template('soup.html',ret=ret)

@app.route('/soup_detail/<int:soup_id>')
def soup_detail(soup_id):
    soup = Soup.query.filter_by(id=soup_id).first()
    soup = get_soup_information([soup])[0]
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.SOUP,
            'soup': soup,
            }
    return render_template('soup_detail.html',ret=ret)

@app.route('/soup_create')
@login_required
def soup_create():
    with app.app_context():
        soup_create_form = Soup_create_form()
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.SOUP,
            'soup_create_form': soup_create_form,
            }
    return render_template('soup_create.html',ret=ret)

@app.route('/soup_update/<int:soup_id>')
@login_required
def soup_update(soup_id):
    with app.app_context():
        soup_create_form = Soup_create_form()
    soup = Soup.query.filter_by(id=soup_id).first()
    soup_create_form.name.data = soup.name
    soup_create_form.price.data = soup.price
    soup_create_form.discounted_price.data = soup.discounted_price
    soup_create_form.description.data = soup.description
    soup_create_form.amount.data = soup.amount
    soup_create_form.is_special.data = soup.is_special
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.SOUP,
            'soup_create_form': soup_create_form,
            'soup': soup,
            }
    return render_template('soup_update.html',ret=ret)


@app.route('/about')
def about():
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.ABOUT,
            }
    return render_template('about.html',ret=ret)

@app.route('/board/<int:category_id>')
def board(category_id):
    search = False
    per_page = 10
    q = request.args.get('q')
    if q:
        search = True
    try:
        page = int(request.args.get('page',1))
    except ValueError:
        page = 1

    if category_id == 0:
        boards = Board.query.order_by(Board.created_at.desc()).limit(per_page).offset((page-1)*per_page)
        total_count = Board.query.count()
    else :
        boards = Board.query.filter_by(board_category_id=category_id).order_by(Board.created_at.desc()).limit(per_page).offset((page-1)*per_page)
        total_count = Board.query.filter_by(board_category_id=category_id).count()
    pagination = Pagination(page=page, total=total_count, search=search, record_name='board', per_page=per_page)
    boards = get_board_information(boards)

    if category_id != 1:
        notices = Board.query.filter_by(board_category_id=1).order_by(Board.created_at.desc()).all()
        notices = get_board_information(notices)
    else :
        notices = []

    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.BOARD,
            'boards': boards,
            'notices': notices,
            'pagination': pagination,
            'category_id': category_id,
            }
    return render_template('board.html',ret=ret)


@app.route('/board_detail/<int:board_id>')
def board_detail(board_id):
    with app.app_context():
        comment_create_form = Comment_create_form()
    board = get_board_by_board_id(board_id)
    comments = get_comments_by_board_id(board_id)
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.BOARD,
            'board': board,
            'comment_create_form': comment_create_form,
            'comments': comments,
            }
    return render_template('board_detail.html',ret=ret)

@app.route('/board_create')
@login_required
def board_create():
    with app.app_context():
        board_create_form = Board_create_form()
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.BOARD,
            'board_create_form': board_create_form,
            }
    return render_template('board_create.html',ret=ret)

@app.route('/board_update/<int:board_id>')
@login_required
def board_update(board_id):
    with app.app_context():
        board_create_form = Board_create_form()
    board = Board.query.filter_by(id=board_id).first()
    if not (session['user_id'] == board.user_id or session['level'] == 99):
        return redirect(url_for('home'))
    board_create_form.title.data = board.title
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.BOARD,
            'board_create_form': board_create_form,
            'board': board,
            }
    return render_template('board_update.html',ret=ret)



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
        session['level']    = user.level
        session['logged_in']= True
        if not 'cart_list' in session:
            session['cart_list'] = []

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
        session['level']    = newuser.level
        session['user_id']  = newuser.id
        session['logged_in']= True
        if not 'cart_list' in session:
            session['cart_list'] = []

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
    session.pop('level',None)

    return redirect(url_for('home'))

@app.route('/store')
def store():
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.STORE,
            }
    return render_template('store.html',ret=ret)


@app.route('/cart')
def cart():
    cur_cart_list = []
    for item in session['cart_list']:
        soup = Soup.query.filter_by(id=int(item['soup_id'])).first()
        d = {
                'soup_id': soup.id,
                'name': soup.name,
                'discounted_price': soup.discounted_price,
                'soup_cnt': item['soup_cnt'],
                }
        cur_cart_list.append(d)

    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.CART,
            'cur_cart_list': cur_cart_list,
            }
    return render_template('cart.html',ret=ret)

@app.route('/checkout')
def checkout():
    cart_list = session['cart_list']
    soups = []
    total_price = 0
    delivery_price = 0
    total_cnt   = 0
    for item in cart_list:
        soup = Soup.query.filter_by(id=int(item['soup_id'])).first()
        soup = get_soup_information([soup])[0]
        soup['soup_cnt'] = int(item['soup_cnt'])
        total_cnt += int(item['soup_cnt'])
        total_price += int(soup['discounted_price'])*int(soup['soup_cnt'])
        soups.append(soup)
    if total_price < 10000:
        delivery_price = 2000
    payment_price = total_price + delivery_price 
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.SOUP,
            'soups': soups,
            'total_price': total_price,
            'total_cnt': total_cnt,
            'delivery_price': delivery_price,
            'payment_price': payment_price 
            }
    return render_template('checkout.html',ret=ret)

@app.route('/mpayments/complete',methods=['GET'])
def mpayments_complete():
    if request.method == 'GET':
        imp_uid = request.args.get('imp_uid')
        response = iamport.find(imp_uid=imp_uid)

        cart_list = session['cart_list']
        soups = []
        total_price = 0
        delivery_price = 0
        total_cnt   = 0
        for item in cart_list:
            soup = Soup.query.filter_by(id=int(item['soup_id'])).first()
            soup = get_soup_information([soup])[0]
            soup['soup_cnt'] = int(item['soup_cnt'])
            total_cnt += int(item['soup_cnt'])
            total_price += int(soup['discounted_price'])*int(soup['soup_cnt'])
            soups.append(soup)
        if total_price < 10000:
            delivery_price = 2000
        payment_price = total_price + delivery_price 

        if iamport.is_paid(payment_price, response=response):
            apply_num       = response['apply_num']
            address         = response['buyer_addr']
            tel             = response['buyer_tel']
            imp_uid         = response['imp_uid']
            paid_amount     = response['amount']
            new_payment     = Payment(apply_num,address,tel,imp_uid,paid_amount)
            if 'logged_in' in session:
                new_payment.user_id = session['user_id']
            db.session.add(new_payment)
            db.session.commit()

            for soup in soups:
                payment_has_soup = Payment_has_soup(new_payment.id,soup['id'],soup['soup_cnt'])
                db.session.add(payment_has_soup)
                db.session.commit()

            session['cart_list'] = []
            return redirect(url_for('payment_result',imp_uid=imp_uid))
        else :
            return json.dumps({'success':False}), 402, {'ContentType':'application/json'} 



@app.route('/payments/complete',methods=['POST'])
def payments_complete():
    if request.method == 'POST':
        imp_uid = request.form.get('imp_uid')
        response = iamport.find(imp_uid=imp_uid)

        cart_list = session['cart_list']
        soups = []
        total_price = 0
        delivery_price = 0
        total_cnt   = 0
        for item in cart_list:
            soup = Soup.query.filter_by(id=int(item['soup_id'])).first()
            soup = get_soup_information([soup])[0]
            soup['soup_cnt'] = int(item['soup_cnt'])
            total_cnt += int(item['soup_cnt'])
            total_price += int(soup['discounted_price'])*int(soup['soup_cnt'])
            soups.append(soup)
        if total_price < 10000:
            delivery_price = 2000
        payment_price = total_price + delivery_price 

        if iamport.is_paid(payment_price , response=response):
            apply_num       = response['apply_num']
            address         = response['buyer_addr']
            tel             = response['buyer_tel']
            imp_uid         = response['imp_uid']
            paid_amount     = response['amount']
            new_payment     = Payment(apply_num,address,tel,imp_uid,paid_amount)
            if 'logged_in' in session:
                new_payment.user_id = session['user_id']
            db.session.add(new_payment)
            db.session.commit()

            for soup in soups:
                payment_has_soup = Payment_has_soup(new_payment.id,soup['id'],soup['soup_cnt'])
                db.session.add(payment_has_soup)
                db.session.commit()

            session['cart_list'] = []
            return json.dumps({'success':True,'imp_uid':imp_uid}), 200, {'ContentType':'application/json'} 
        else :
            return json.dumps({'success':False}), 402, {'ContentType':'application/json'} 

@app.route('/payment_result/<imp_uid>')
def payment_result(imp_uid):
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.CART,
            'imp_uid': imp_uid,
            }
    return render_template('payment_result.html',ret=ret)

@app.route('/payment_check',methods=['GET','POST'])
def payment_check():
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.CHECK,
            }
    if request.method == 'GET':
        if request.args.get('imp_uid'):
            ret['imp_uid'] = request.args.get('imp_uid')
        return render_template('payment_check.html',ret=ret)
    elif request.method == 'POST':
        imp_uid_search = request.form.get('imp_uid_search')
        payment = Payment.query.filter_by(imp_uid=imp_uid_search).first()
        if payment:
            ret['pay_check'] = True
            payment_has_soup = Payment_has_soup.query.filter_by(payment_id=payment.id).all()
            soups = []
            for phs in payment_has_soup:
                payment_id  = phs.payment_id
                soup_id     = phs.soup_id
                soup_cnt    = phs.soup_cnt
                soup = Soup.query.filter_by(id=soup_id).first()
                soup = get_soup_information([soup])[0]
                soup['soup_cnt'] = soup_cnt
                soups.append(soup)
            ret['payment'] = payment
            ret['soups'] = soups
            return render_template('payment_check.html',ret=ret)
        else:
            ret['pay_not_found'] = True
            return render_template('payment_check.html',ret=ret)
        return render_template('payment_check.html',ret=ret)

@app.route('/admin')
@login_required 
def admin():
    if not 'logged_in' in session:
        return redirect('/')
    if session['level'] < 99:
        return redirect('/')
    
    search = False
    per_page = 20
    q = request.args.get('q')
    if q:
        search = True
    try:
        page = int(request.args.get('page',1))
    except ValueError:
        page = 1
    gu = request.args.get('gu')
    if q:
        q = q.strip()
    if gu:
        gu = gu.strip()
    if gu and gu == u'전체':
        if q == '':
            payments = Payment.query.order_by(Payment.created_at.desc()).limit(per_page).offset((page-1)*per_page)
            total_count = Payment.query.count()
        else :
            payments = Payment.query.filter(Payment.tel.like('%'+q+'%')).order_by(Payment.created_at.desc()).limit(per_page).offset((page-1)*per_page)
            total_count = Payment.query.filter_by(tel=q).count()
    elif gu:
        if q == '':
            payments = Payment.query.filter(Payment.address.like('%'+gu+'%')).order_by(Payment.created_at.desc()).limit(per_page).offset((page-1)*per_page)
            total_count = Payment.query.filter(Payment.address.like('%'+gu+'%')).count()
        else:
            payments = Payment.query.filter(and_(Payment.tel.like('%'+q+'%'),Payment.address.like('%'+gu+'%'))).order_by(Payment.created_at.desc()).limit(per_page).offset((page-1)*per_page)
            total_count = Payment.query.filter(Payment.address.like('%'+gu+'%')).count()
    else:
        payments = Payment.query.order_by(Payment.created_at.desc()).limit(per_page).offset((page-1)*per_page)
        total_count = Payment.query.count()

    pagination = Pagination(page=page, total=total_count, search=search, record_name='payment', per_page=per_page)
    payments = get_payment_information(payments)
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.ADMIN,
            'payments': payments,
            'pagination': pagination,
            }

    return render_template('admin.html',ret=ret)

@app.route('/payment_state_edit',methods=['POST'])
@login_required
def payment_state_edit():
    if not 'logged_in' in session:
        return redirect('/')
    if session['level'] < 99 :
        return redirect('/')
    if request.method == 'POST':
        payment_id = request.form.get('payment_id')
        payment_state = request.form.get('payment_state')
        payment = Payment.query.filter_by(id=payment_id).first()
        payment.state = int(payment_state)
        db.session.commit()
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    return json.dumps({'success':False}), 402, {'ContentType':'application/json'}

@app.route('/mypage/<int:mypage_category>')
@login_required
def mypage(mypage_category):
    search = False
    per_page = 20
    q = request.args.get('q')
    if q:
        search = True
    try:
        page = int(request.args.get('page',1))
    except ValueError:
        page = 1
    user_id = session['user_id']
    user = User.query.filter_by(id=user_id).first()

    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.MYPAGE,
            'user': user
            }
    if mypage_category == 0:
        payments = Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).limit(per_page).offset((page-1)*per_page)
        total_count = Payment.query.filter_by(user_id=user_id).count()
        pagination = Pagination(page=page, total=total_count, search=search, record_name='payment', per_page=per_page)
        payments = get_payment_information(payments)
        ret['payments'] = payments
        ret['pagination'] = pagination
        return render_template('mypage.html',ret=ret)
    elif mypage_category == 1:
        with app.app_context():
            update_user_form = Update_user_form()
        update_user_form.username.data   = user.username
        update_user_form.address.data    = user.address
        update_user_form.tel.data        = user.tel
        ret['update_user_form']          = update_user_form 
        ret['si']                   = user.si
        ret['gu']                   = user.gu
        ret['dong']                 = user.dong
        return render_template('mypage_update_user.html',ret=ret)
    elif mypage_category == 2:
        with app.app_context():
            update_password_form = Update_password_form()
        ret['update_password_form'] = update_password_form
        return render_template('mypage_update_password.html',ret=ret)
    else :
        return redirect('/')

@app.route('/find_password')
def find_password():
    with app.app_context():
        find_password_form = Find_password_form()
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.LOGIN,
            'find_password_form': find_password_form,
            }
    return render_template('find_password.html',ret=ret)

@app.route('/send_new_password',methods=['POST'])
def send_new_password():
    with app.app_context():
        find_password_form = Find_password_form()
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.LOGIN,
            'find_password_form': find_password_form,
            }
    if not find_password_form.validate():
        return render_template('find_password.html',ret=ret)
    email = find_password_form.email.data.lower()
    ret['email'] = email
    user = User.query.filter_by(email=email).first()
    tmp_password = generate_temp_password()
    user.set_password(tmp_password)
    db.session.commit()
    send_email(u'[착한탕국] %s 임시 비밀번호 입니다.'%user.email,\
                u'ko.goodsoup@gmail.com',\
                [user.email],\
                u'임시 비밀번호 : %s'%tmp_password,\
                u'임시 비밀번호 : %s'%tmp_password)
    return render_template('send_email_result.html',ret=ret)



###

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    app.run(host='222.239.250.23',debug=True)
