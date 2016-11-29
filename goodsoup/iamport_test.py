#!/usr/bin/python
#-*- coding:utf-8 -*-
from iamport import Iamport
import json
from config import (
        GS_IMP_TEST_KEY,
        GS_IMP_TEST_API_KEY,
        GS_IMP_TEST_SECRET_KEY
        )
iamport = Iamport(imp_key=GS_IMP_TEST_API_KEY,imp_secret=GS_IMP_TEST_SECRET_KEY)

if __name__ == '__main__':
    response = iamport.find(imp_uid='imp_115066558401')
    for key in response:
        print key,response[key]
    print json.loads(response['custom_data'])['delivery_time']
