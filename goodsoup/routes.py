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
        Soup_image,
        )
from forms import (
        Signup_form,
        Signin_form,
        Board_create_form,
        Comment_create_form,
        Soup_create_form,
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

navbar_menus = utils.enum('HOME','SOUP','ABOUT','BOARD','STORE','LOGIN','CART')


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
        soup_images = Soup_image.query.filter_by(soup_id=soup.id).order_by(Soup_image.created_at.desc())
        soup_images = get_soup_image_information(soup_images)
        d = {
                'id': soup.id,
                'name': soup.name,
                'price': soup.price,
                'discounted_price': soup.discounted_price,
                'description': soup.description,
                'amount': soup.amount,
                'is_special': soup.is_special,
                'soup_images': soup_images,
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
    for item in cart_list:
        soup = Soup.query.filter_by(id=int(item['soup_id'])).first()
        soup = get_soup_information([soup])[0]
        soup['soup_cnt'] = int(item['soup_cnt'])
        total_price += int(soup['discounted_price'])*int(soup['soup_cnt'])
        soups.append(soup)
    ret = {
            'navbar_menus': navbar_menus,
            'selected_navbar_index': navbar_menus.SOUP,
            'soups': soups,
            'total_price': total_price,
            }
    return render_template('checkout.html',ret=ret)
###

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    app.run(host='222.239.250.23',debug=True)
