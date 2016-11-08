#!/usr/bin/python
#-*- coding:utf-8 -*-
__author__ = 'sisobus'
import commands
import os
import json

ALLOWED_EXTENSIONS = set(['txt','pdf','png','jpg','JPG','jpeg','JPEG','gif','GIF','zip'])

def allowedFile(filename):
    return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

def createDirectory(directoryName):
    if not os.path.exists(directoryName):
        command = 'mkdir %s'%directoryName
        ret = commands.getoutput(command)
        command = 'chmod 777 %s'%directoryName
        ret = commands.getoutput(command)

def get_image_path(real_image_path):
    ret = ''
    for t in real_image_path.lstrip().rstrip().split('/')[6:]: ret=ret+t+'/'
    return ret[:-1]

def convert_email_to_directory_name(email):
    return email.replace('@','_at_')

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)

if __name__ == '__main__':
    print enum('HOME','ABOUT','BOARD','LOGIN','CART').HOME
