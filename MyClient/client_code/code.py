# --*-- coding:utf-8 --*--
# Client

import socket
import json
import os
import time
from tkinter import *


class Client(object):

    def __init__(self):
        pass

    def make_conn(self):
        """
        API
        :return:  None
        """
        self.buff = 2048
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect(('192.168.43.232', 8001))
            print('The server is running normally')
        except Exception as e:
            print('Server exception：', e)
            exit()
        msg = self.login()  # msg是一个用户云端信息字典，{"status": ***, "file_list": ***}
        if msg["status"]:
            """Successful login interface"""
            self.help()  # 显示使用指南
            self.page_main(msg)  # 登录成功，进入操作中心
        else:
            """Login was failed, then choose enroll or exit?"""
            while True:
                cmd = input("Choose register(y)or exit(q)?").strip()
                if cmd == "y":
                    request = {"Type": "enroll"}
                    self.conn.send(json.dumps(request).encode())
                    msg = self.enroll()
                    if msg["status"]:
                        self.page_main(msg)   # 注册成功则进入操作中心
                        break
                    else:
                        break   # 注册失败，退出注册界面
                elif cmd == "q":
                    request = {"Type": "q"}  # q表示不注册，退出FTP
                    self.conn.send(json.dumps(request).encode())
                    print("Disconnect from server")
                    exit()
                else:
                    print("BAD COMMAND!")
            print("EXIT FTP!")

    def page_main(self, msg):
        """
        home page, send response to server
        :param msg:  The msg is a response from server after requesting, it include user's files directory
        :return: None
        """
        while True:
            try:
                print("\n")
                print("home page".center(30, '*'))
                cmd = input(self.username+' >>').strip().split()  # cmd是一个列表，例如：["get", "../file.txt"],
                # 文件名要是完整的，包含路径,文件路径输入时不要加""，输入示例：put D:/python3/清屏方法.txt
                if len(cmd) == 0:
                    # 请求为空值，重新输入请求
                    continue
                elif cmd[0] == "q":
                    print("EXIT FTP!")
                    exit()
                elif cmd[0] == "show":
                    self.show_file()   # 命令show会主动获得一次云端文件夹内容
                    continue
                elif cmd[0] == "put":
                    try:
                        if os.path.isfile(cmd[1]):
                            if self.put(cmd[1]):
                                continue
                            else:
                                break  # 上传失败，则退出FTP
                        else:
                            print("file is not found")
                    except:
                        print("File cant not empty\n")
                        continue
                elif cmd[0] == "get":
                    try:
                        if cmd[1] in msg.get("file_list"):
                            print(msg.get("file_list"))
                            self.get(cmd[1])  # cmd[1]是要从云端下载的文件名
                            continue
                        else:
                            print("file is not found")
                    except:
                        print("File cant not empty\n")
                        continue
                elif cmd[0] == "del":
                    try:
                        if cmd[1] in msg.get("file_list"):
                            self.delete(cmd[1])  # 删除云端文件
                            continue
                        else:
                            print("file is not found")
                    except:
                        print("File cant not empty")
                        continue
                elif cmd[0] == "help":
                    self.help()
                    continue
                else:
                    print("Bad Command!")
                    continue
            except Exception as e:
                print('BAD CMD!, ', e)
                break

    def show_file(self):
        """
        Request to get a list of user's files from the server
        :return: None
        """
        print("\n")
        print("personal home".center(30, '-'))
        request = {"Type": "show"}
        self.conn.send(json.dumps(request).encode())
        while True:
            try:
                file_info = self.receive()  # 返回的是 msg = {"status": 1( or 0), "file_list": file_list} # 1表示该文件夹存在,0表示不存在
                if file_info["status"]:
                    for file in file_info["file_list"]:
                        print(file)   # 打印云端文件列表
                    break
                    # return file_info
                else:
                    print("You don't get files directory")
                    break
            except ConnectionError as e:
                print("404! ", e)  # 服务器已经停止服务
                exit()
                # return False

    def get(self, filename):
        """
         Handing file uploaded from client
        :param filename:   msg_info is a request from server
        :return:  Return "True" if upload is successful, or return "False"
        """
        print("\n", "get center".center(30, '*'))
        base_path = '../download_file/'
        path = os.path.abspath(base_path)
        print(path)
        file_list = os.listdir(path)
        print("had file::  ", file_list)
        if filename in file_list:
            print("can`t redownload!")
            return False
        first_send = {"Type": "get",
                      "filename": filename  # 要下载的文件
                      }
        self.conn.send(json.dumps(first_send).encode())
        msg_info = self.receive()
        # msg_info = {"status": 1,
        #             "file_size": size
        #             }
        fsize = msg_info.get("file_size")
        msg = {"status": 1}
        self.conn.send(json.dumps(msg).encode())
        count_1 = fsize / self.buff
        count_2 = fsize % self.buff
        count = 1
        with open('../download_file/'+filename, 'wb') as f:
            try:
                while True:
                    try:
                        if count_2 == 0:
                            f.write(self.conn.recv(self.buff))
                            count += 1
                            if count > count_1:
                                break
                        else:
                            if count <= count_1:
                                f.write(self.conn.recv(self.buff))
                            else:
                                f.write(self.conn.recv(self.buff))
                            count += 1
                            if count > (count_1 + 1):
                                break
                    except Exception as e:
                        print(e)
                print("文件{}下载成功!".format(filename))
                self.conn.send(json.dumps(msg).encode())
                return True
            except Exception as e:
                msg["status"] = 0
                self.conn.send(json.dumps(msg).encode())
                print("下载失败！", e)
                return False

    def put(self, file_path):
        """
        Request to upload file
        :param file_path:  This is file user want to upload to server
        :return:  Return "True" if user upload is successful, or return "False"
        """
        print("\n", 'put center'.center(30, '*'))
        size = os.path.getsize(file_path)  # 得到该文件的大小
        filename = os.path.basename(file_path)  # 得到文件名
        # print('文件名：', filename)
        print('file_path', file_path)
        with open(file_path, 'rb') as f:
            data = f.read()
        send_msg = {"Type": "put",
                    "file_size": size,
                    "filename": filename
                    }
        try:
            self.conn.send(json.dumps(send_msg).encode())  # 将上传的文件大小、文件名和请求方式传出去
            response = self.receive()  # {"status": 1 or 0}
            # print('服务器返回了信息：', response)
            if response["status"] == 1:  # 正常返回的是一个字典，值为1
                print('Server allows uploading files')
                self.conn.sendall(data)  # 等服务器准备好之后，就可以将文件上传
                msg = self.receive()  # 打印服务器返回来的上传情况  "上传成功"
                if msg["status"] == 1:
                    print("File {} have uploaded successfully".format(filename))
                    return True
                else:
                    print("File {} upload was error".format(filename))
                    return False
            else:
                print("File {} is exists, you can delete file in file's directory firstly".format(filename))
                return True
        except Exception as e:
            print("UPLOADING ERROR!: ", e)
            return False

    def receive(self):
        """
        Receive a response and preliminary handing it in json and decode from server
        :return:  Return the response from server
        """
        try:
            msg = self.conn.recv(self.buff)
            # print("This is response from server：", msg)
            rec_msg = json.loads(msg.decode())
            return rec_msg
        except Exception as e:
            print('response warning!', e)
            return None

    def delete(self, filename):
        """
        Request to delete file of user's person from server
        :param filename:  This is file user want to delete file from server
        :return: None
        """
        print("\n")
        send_msg = {"Type": "del",
                    "filename": filename
                    }
        self.conn.send(json.dumps(send_msg).encode())
        msg = self.receive()
        if msg.get("status"):
            print("You have successfully deleted {}".format(filename))
            # return 1
        else:
            print("FAILED")
            # return 0

    def login(self):
        """
        This is the page when user login FTP
        :return: Return response that it include user's files directory from server
        """
        print("\n", 'login'.center(30, '-'))
        self.username = input('username>>')
        try:
            self.conn.send(self.username.encode())
            msg = self.receive()
            count = 0
            while msg["status"]:
                password = input('password>>')
                self.conn.send(password.encode())
                msg1 = self.receive()
                if msg1.get("status"):
                    print('{},I finally waited for you!'.format(self.username))
                    return msg1
                else:
                    print('WRONG!')
                    count += 1
                    if count > 3:  # 输密码有4次机会
                        print('You have entered the wrong 4 times!')
                        msg["status"] = 0
                        return msg  # 返回0表示登录失败
                    else:
                        continue
            else:
                print('用户名不存在')
                msg["status"] = 0
                return msg  # 返回0表示登录失败
        except Exception as e:
            print("WRONG!：", e)

    def enroll(self):
        """
        This is the page when user registering FTP
        :return:  Return a response that it include user's file directory from server
        """
        msg = self.receive()   # {"status": 1 or 0, "file_list": file_list}
        if msg.get("status"):  # 允许注册
            print("enroll".center(30, "-"))
            username = input('username>>').strip()
            password = input('password>>').strip()
            cmd = {"username": username,
                   "password": password
                   }
            try:
                self.conn.send(json.dumps(cmd).encode())
                response = self.receive()  # {"status": 1, "file_list": file_list} # 注册成功才会返回这条消息
                print(response)
                if response.get("status"):
                    print('successful')
                    return response
                else:
                    print('failed')
                    return response
            except Exception as e:
                print('failed：', e)
                msg["status"] = 0
                return msg
        else:
            print("Registration is not allowed")
            exit()

    def help(self):
        """
        There are some tips to help user better use FTP.
        :return:  None
        """
        info = {"get": "Download file Tip：get file",
                "put": "Upload file Tip：put file",
                "show": "Show user's files Tip：show",
                "help": "User's guidance Tip：help",
                "q": "Exit FTP Tip: q",
                "del": "Delete file Tip：del filename"
                }
        key_list = ["get", "put", "show", "help", "q", "del"]
        print("User's guidance".center(30, '-'))
        for key in key_list:
            print("{}:  {}".format(key, info[key]))


if __name__ == '__main__':
    c = Client()
    c.make_conn()
