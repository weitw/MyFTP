# /bin/python3/bin/python3.6
# --*-- coding:utf-8 --*--
# the start of client

import os
import sys
from ..client_code.code import Client

BaseDir = os.path.dirname(os.getcwd())  # 目录为MyFTP/MyClient
sys.path.append(BaseDir)


if __name__ == '__main__':
    c = Client()
    c.make_conn()
