#!/usr/bin/python
#-*- coding:utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
from config import (
        MAIL_SERVER,
        MAIL_PORT,
        MAIL_USE_TLS,
        MAIL_USE_SSL,
        MAIL_USERNAME,
        MAIL_PASSWORD
        )

app = Flask(__name__)
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ko.goodsoup@gmail.com'
app.config['MAIL_PASSWORD'] = 'tkdrmsld123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

#app.config["MAIL_SERVER"] = MAIL_SERVER
#app.config["MAIL_PORT"] = MAIL_PORT
#app.config["MAIL_USE_TLS"] = False
#app.config["MAIL_USE_SSL"] = True
#app.config["MAIL_USERNAME"] = MAIL_USERNAME 
#app.config["MAIL_PASSWORD"] = MAIL_PASSWORD

mail = Mail(app)
from decorators import async

@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(app,msg)

if __name__ == '__main__':
    send_email('test','ko.goodsoup@gmail.com',['sisobus1@gmail.com'],'tst','test')
