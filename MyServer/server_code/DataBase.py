# --*-- coding:utf-8 --*--

import hashlib
import os
import json


class MdFive(object):

    def __init__(self, un, pw):
        self.un = un
        self.pw = pw
        self.info_path = r"../Data/UserInfo/"  # 用户信息库的路径
        file = os.listdir(self.info_path)
        self.file_info = self.info_path + "/" + file[0]  # MyFTP/MyServer/Data/UserInfo/userinfo.txt

    def in_md5(self):
        # print("调用md5方法".center(30, '.'))
        md = hashlib.md5()
        pw_type = type(self.pw)
        if pw_type is bytes:
            print("是一个二进制")
            md.update(self.pw)
            self.pw = md.hexdigest()
            return self.pw
        elif pw_type is str:
            # print("是一个字符串")
            md.update(self.pw.encode())
            self.pw = md.hexdigest()
            return self.pw
        else:
            print("其他类型")
            pw = json.dumps(self.pw).encode()
            md.update(pw)
            self.pw = md.hexdigest()
            return self.pw

    def save_md5(self):
        pw = self.in_md5()
        if os.path.isdir(self.info_path):
            if os.path.isfile(self.file_info):
                try:
                    with open(self.file_info, 'ab') as f:
                        user_info = {"username": self.un,
                                     "password": pw
                                     }
                        f.write(json.dumps(user_info).encode())  # 以bytes写入
                        f.write(b"\n")
                    return True
                except:
                    return False
        else:
            os.makedirs(self.info_path)
            return False

    def get_md5(self):
        with open(self.file_info, 'rb') as f:
            data = f.readlines()
            a = []
            for line in data:
                a.append(json.loads(line.decode()))
            # print(type(a), len(a), a)


if __name__ == '__main__':
    username = input("username>>")
    password = input("password>>")
    md5 = MdFive(username, password)
    md5.get_md5()
    if md5.save_md5():  # 如果写入成功
        md5.get_md5()
    else:
        print('0')


