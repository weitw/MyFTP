# --*-- coding:utf-8 --*--

import os
import sys

BaseDir = os.path.dirname(os.getcwd())  # 目录为MyFTP/MyClient
sys.path.append(BaseDir)
from client_code.code import Client

if __name__ == '__main__':
    c = Client()
    c.make_conn()
