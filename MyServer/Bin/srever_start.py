# /bin/python3/bin/python3.6
# --*-- coding:utf-8 --*--
# the start of server

import sys
import os
from ..server_code.code import MyTCPHandler

Base_dir = os.path.dirname(os.getcwd())  # 目录为MyFTP\MyServer
sys.path.append(Base_dir)  # 将目录添加到环境变量，这样就可以不用来回切换路径了
# print("The current directory is : ", Base_dir)


if __name__ == "__main__":
    try:
        s = MyTCPHandler()
        s.handle()
    except Exception as e:
        print("运行程序出错：", e)

