#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/goodsoup/")
print sys.path

from goodsoup.routes import app as application
