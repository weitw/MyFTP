# --*-- coding:utf-8 --*--

import json
import socket
import os
import sys
import time
import hashlib

Base_path = os.path.dirname(os.getcwd())
sys.path.append(Base_path)

from server_code.DataBase import MdFive


class MyTCPHandler(object):

    def __int__(self):
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sock.bind(('127.0.0.1', 9999))
        # self.sock.listen()
        pass

    def handle(self):
        """
        API
        """
        print("Server is Running".center(30, "="))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('127.0.0.1', 8080))
        self.sock.listen()
        print("Waiting connect...".center(30, '-'))
        while True:
            try:
                self.conn, self.addr = self.sock.accept()
                print('Client {} is connecting'.format(self.addr).center(30, '='))
                gg = {'hello': 'WELCOME USE FTP'}
                self.conn.send(json.dumps(gg).encode())
                login_msg = self.__login()  # 登录的返回信息1 or 0
                if login_msg:
                    self.__status_log("Client have connected with FTP successfully")  # 增加记录
                    self.page_main()  # 进入主页
                else:
                    # 返回False,登录失败
                    try:
                        request = self.receive()
                        print(request, type(request))
                        # enroll_msg = json.loads(self.receive().decode())
                        if request.get("Type") == "enroll":  # 如果客户端请求注册
                            # response = {"status": 1}
                            # self.conn.send(json.dumps(response).encode())
                            status = self.__enroll()  # 注册状态
                            if status:
                                self.__status_log("Enrolled FTP")
                                self.page_main()  # 进入主页
                            else:
                                print("User failed enroll")
                                print("Disconnect with client")
                                continue
                        else:
                            print("Client failed login FTP".center(30, '='))
                            print("已与用户断开连接")
                            self.__status_log("登录失败，退出FTP")
                            continue  # 重新接受新的连接
                    except Exception as e:
                        print("出错3：", e)
                        print("已与用户断开连接")
            except Exception as err:
                print('与客户端{}断开连接: '.format(self.addr).center(30, '='), err)
                self.__status_log("退出FTP")
                continue

    def page_main(self):
        """
        home page, handing requests
        :return: None
        """
        while True:
            print("main_page".center(30, '-'))
            try:
                msg = self.receive()  # 主请求,判断接下来做什么
                # print("收到请求: ", msg)
                if not msg:
                    print('客户端已断开连接')
                    self.__status_log("退出FTP")  # 用户退出记录
                    break  # 说明收到空请求（客户端要先自行检测不能发出空请求），断开连接
                else:
                    print('收到信息：', msg)
                    if msg.get('Type') == 'put':
                        # print('可以上传了')
                        if self.__put(msg):  # 如果上传成功
                            self.__show_dir()  # 上传之后，主动调用该函数，将用户文件夹下的文件列表发给用户
                            self.__logger(msg)  # 记录操作
                            # self.__update_dir()  # 上传完成，紧接着就将文件夹列表发给用户
                            print('已成功将文件夹返回给用户')
                            continue
                        else:
                            print('这儿也不知道要写什么')
                            continue
                    elif msg.get('Type') == 'get':
                        self.__get(msg)
                        continue
                    elif msg.get("Type") == "del":
                        self.delete(msg)
                        self.__status_log("删除了文件'{}'".format(msg.get("filename")))
                        continue
                    elif msg.get("Type") == "show":
                        self.__show_dir()
                        self.__status_log("查看了个人文件夹")
                        continue
                    else:
                        print('未识别出请求')
                        continue
            except Exception as er:
                print("Bad Request: ", er)
            break

    def __show_dir(self):
        """
        Show cloud folder directory
        :return:  return True if show is successful, or False
        """
        print("获取用户文件目录".center(30, '-'))
        path = r"D:\Projects\net_programming\MyFTP\MyServer"+r"\Data\Users\\" + self.username+r"\UserFiles"
        # print("path: ", path)
        if os.path.isdir(path):
            file_list = os.listdir(path)  # 获得文件夹下所有的文件名
            msg = {"status": 1,  # 1表示该文件夹存在
                   "file_list": file_list
                   }
            # print(path)
            self.conn.send(json.dumps(msg).encode())
            print("给用户返回： ", msg)
            return True   # ##############################################################################
        else:
            msg = {"status": 0,
                   "file_list": []}
            print("给用户返回： ", msg)
            self.conn.send(json.dumps(msg).encode())
            return False

    def __enroll(self):
        """
        enroll new user
        :return: Return "True" if the enroll is successful, or return "False"
        """
        print("注册主页".center(30, '-'))
        msg = {"status": 1,
               "file_list": []
               }  # 允许注册
        # print("注册")
        self.conn.send(json.dumps(msg).encode())
        enroll_info = self.receive()
        print(enroll_info)
        self.username = enroll_info.get("username")
        self.password = enroll_info.get("password")
        md5 = MdFive(self.username, self.password)
        status = md5.save_md5()  # 调用类MdFive的方法save_md5(),返回的，True,表示MD5成功，False表示失败
        if status:
            print("用户注册成功")
            user_file = r"D:\\Projects\\net_programming\\MyFTP\\MyServer\\Data\\Users/" + self.username + r"/UserFiles"
            user_log = r"D:\\Projects\\net_programming\\MyFTP\\MyServer\\Data\\Users/" + self.username + r"/log"
            if not os.path.isdir(user_file):
                os.makedirs(user_file)  # 为该注册用户建立一个自己的文件夹（文件内容）
                os.makedirs(user_log)  # （log）
            self.conn.send(json.dumps(msg).encode())
            return True
        else:
            """这应该增加一条语句，删除信息库找那个最后一条注册人的信息，因为再判断之前已经写入，所以注册失败应该删除"""
            msg["status"] = 0
            print("用户注册失败")
            self.conn.send(json.dumps(msg).encode())  # 注册失败则会发送条消息
            return False

    def __readmd5(self):
        """
        Read information, return username and password in directory of user's file, Mainly used when registering,
        or verifying that user information is consistent with the information in the repository at login
        :return:
        """
        print("调用MD5方法".center(30, '.'))
        path = r"D:\Projects\net_programming\MyFTP\MyServer\Data\UserInfo\userinfo.txt"
        if os.path.isfile(path):
            # print("文件存在")
            with open(path, 'rb') as f:  # Md5写入时使用二进制的，所以这儿也用二进制读取
                try:
                    info = []
                    data = f.readlines()
                    for line in data:
                        info.append(json.loads(line))
                    # print(type(info), len(info), info)
                    return info
                except Exception as e:
                    print("读取MD5文件出错：", e)
                    return []
        else:
            print("信息库不存在")
            return None

    def receive(self):
        """
        Preliminary handing request from client in json and decode
        :return:  request from user
        """
        rec_msg = self.conn.recv(1024)
        print(rec_msg)
        try:
            msg = json.loads(rec_msg.decode())
            return msg
        except Exception as e:
            print(e)
            msg = json.loads(rec_msg.decode("gbk"))  # 如果utf8不能decode，则尝试用gbk
            return msg

    def __login(self):
        """
        User login to their account
        :return:  Return "True" if login is successful, or return "False"
        """
        self.username = self.conn.recv(1024).decode()  # 用户账号
        # print(self.username)
        user_info = self.__readmd5()  # ###读取MD5文件，返回文件中所有用户的信息，返回格式为[{},{},{}](是str的)
        msg = {"status": 1,
               "file_list": []  # 用户的云端文件列表
               }
        user_list = [user.get("username") for user in user_info]  # 得到信息库中所有用户的用户名列表(str的)
        # print("user_list: ", user_list)
        if self.username in user_list:
            msg["file_list"] = os.listdir(r"D:\Projects\net_programming\MyFTP\MyServer\Data"
                                          r"\Users\{}\UserFiles".format(self.username))
            print('用户名为：', self.username)
            self.conn.send(json.dumps(msg).encode())
            count = 1
            while True:
                self.password = self.conn.recv(1024).decode()  # 用户密码
                real_pw = [user for user in user_info if user.get("username") == self.username]
                # print("real_pw: ", real_pw)
                # ***上面这段得到的结果类型类似：[{'username': 'Alex', 'password': '49573a1e417c0bca60d460d057e02a5b'}]
                """********下面将密码用哈希算法加密，与信息库中的匹配*******"""
                try:
                    md5 = MdFive(self.username, self.password)
                    md5_pw = md5.in_md5()  # 返回加密后的密码值,str
                    # print("md5_pw: {} type(md5_pw: {}".format(md5_pw, type(md5_pw)))
                except Exception as e:
                    print("哈希出错：", e)
                    continue
                # print(real_pw[0], type(real_pw))  # 该用户的信息,username, password
                # print(real_pw[0].get("password"))
                if md5_pw == real_pw[0].get("password"):
                    print('用户密码：', self.password)
                    print('合法用户已登录')
                    print("-"*30)
                    # 登录成功之后，将用户的云端文件目录传入字典, 并将登录信息写入log.txt
                    msg["status"] = 1
                    # print("msg:  ", msg)
                    self.conn.send(json.dumps(msg).encode())
                    return True
                else:
                    msg['status'] = 0
                    print("用户输入密码：", self.password)
                    # md5 = MdFive()
                    # md5.save_md5(self.username, self.password)
                    self.conn.send(json.dumps(msg).encode())
                    if count > 3:
                        # self.conn.send(json.dumps(msg).encode())  # 超过三次后，提示客户端登录失败
                        return False
                    count += 1
                    continue
        else:
            msg['status'] = 0
            self.conn.send(json.dumps(msg).encode())  # 账号输错，表示不是合法用户，退出提示用户重新输入
            return False

    def __status_log(self, msg):
        """
        这个日志记录的是注册、登录或者断开的记录的
        msg 是登录函数调用时写入的“登录FTP”，客户端请求show之后，写入的“用户查看了文件夹”
        或者退出连接时写入的“退出FTP”
        与self.logger()记录的不一样
        """
        path = r'D:\\Projects\\net_programming\\MyFTP\\MyServer\\' + r"Data\\Users\\" + self.username + r"\\log"
        if not os.path.isdir(path):  # 若文件夹不存在，则新建一个
            os.makedirs(path)
        if os.path.isdir(path):
            tm = time.strftime('%Y-%m-%d')
            with open(path + "\\" + tm + '.txt', 'a', encoding='utf-8') as f:  # 每天的记录作为一个文件
                data = time.strftime("%Y-%m-%d-%H-%M-%S:  ")+self.username + msg
                try:
                    if "退出FTP" in msg:
                        f.write(data)
                        f.write('\n\n')
                    else:
                        f.write(data)
                        f.write("\n")
                except Exception as e:
                    print("写入文件出错：", e)
                # elif "登录" in msg:
                #     f.write('\n')
                #     f.write(data)
                #     f.write('\n')
                # elif "个人文件夹" in msg:
                #     f.write(data)
                #     f.write('\n')
                # else:
                #     f.write(data)
                #     f.write('\n')

    def __put(self, msg_info):  # 这个put请求是针对客户端的，即这个put指的是客户端要上传文件
        """
         Handing file uploaded from client
        :param msg_info:   msg_info is a request from client
                msg_info = {"Type": "put",
                            'file_size': size,
                            "filename": filename  # upload filename
                            }
        :return:  Return "True" if upload is successful, or return "False"
        """
        # get_msg = self.conn.recv(1024)
        print("上载主页".center(30, '-'))
        msg = {"status": 1}  # 默认不能上传
        # print(msg_info, '可以了')
        path = r'D:\\Projects\\net_programming\\MyFTP\\MyServer\\' + r"Data\\Users\\" + self.username + r'\\UserFiles'
        try:
            if not os.path.isdir(path):
                os.makedirs(path)  # 能进入到这儿的，至少是注册过的，文件夹不存在，可能是操作失误删了，所以新建一个目录
        except Exception as e:
            print('该文件存储库已经存在，允许上传：', e)
        path_list = os.listdir(path)
        filename = msg_info.get("filename")
        size = msg_info.get("file_size")  # 得到文件大小
        print("客户端将上传文件：{}，大小：{}".format(filename, size))
        if filename in path_list:
            msg["status"] = 2      # 如果文件已经存在，则返回2，表示不能上传，提示用户可以先删除旧文件
            print("文件已经存在，不能上传")
            self.conn.send(json.dumps(msg).encode())
            return False
        else:
            self.conn.send(json.dumps(msg).encode())  # 收到文件大小之后，给客户端回话，可以上传文件了
            count = int(size/5215)
            digit = size % 5215
            data = []  # data是文件内容（二进制读取的）的一个容器
            num = 0
            print("put......")
            while num < count:  # #####################这个地方循环的次数一定要注意，
                try:
                    data.append(self.conn.recv(5215))  # 文件使用二进制操作的，所以不用解码
                    # time.sleep(0.025)
                    # print(data[0:100])
                    num += 1
                except Exception as e:
                    print('上传异常11：', e)
                    msg = {"status": 0}
                    self.conn.send(json.dumps(msg).encode())
                    return False  # 收不到信息的原因多半是文件传输过程遇到问题，反正都传不上了，索性断开连接
            if digit != 0:  # 要判断一下，因为可能文件大小刚好是1024的整数倍，如果这个digit==0，则不再接收
                try:
                    data.append(self.conn.recv(digit))  # 文件使用二进制操作的，所以不用解码
                except Exception as er:
                    print('上传异常2：', er)
                    msg = {"status": 0}
                    self.conn.send(json.dumps(msg).encode())
                    return False
            # try:
            #     if not os.path.isdir(path):  # 判断这个用户是否已经建立过文件夹了（已经存在数据库中了）
            #         os.makedirs(path)
            # except Exception as e:
            #     print('该目录已经存在：', e)
            if os.path.isdir(path):
                with open(path + "\\" + filename, 'wb') as f:
                    try:
                        print("size:{}, data:{}".format(size, count*1024+digit))
                        print("正在写入文件")
                        print("len(data): {},count:{},digit:{}".format(len(data), count, digit))
                        for i in range(len(data)):
                            f.write(data[i])
                        msg["status"] = 1
                        self.conn.send(json.dumps(msg).encode())  # 回馈用户，上传文件成功
                        print("文件上传成功")
                        return True
                    except Exception as e:
                        print('文件写入时出错3：', e)
                        msg = {"status": 0}
                        self.conn.send(json.dumps(msg).encode())
                        return False
            else:
                print("我也不知道错哪儿了")
                msg = {"status": 0}
                self.conn.send(json.dumps(msg).encode())
                return False

    def __get(self, msg):
        """
        Handing request downloaded from client
        :param msg:   msg is request from client
                send_msg = {"Type": "get",
                            "filename": filename  # download filename
                            }
        :return:
        """
        print("下载主页".center(30, '-'))
        cmd = {"status": 1}  # 默认不可下载
        path = r'D:\\Projects\\net_programming\\MyFTP\\MyServer\\'+r"Data\\Users\\"+\
               self.username+r'\\UserFiles\\'+msg.get("filename")  # 注意这儿的filename的值应该为一个字符串才行
        if os.path.isfile(path):
            print("文件存在，可以下载")
            size = os.path.getsize(path)
            with open(path, 'rb') as f:
                data = f.read()
            if len(data) == size:
                send_msg = {"status": 1,
                            "file_size": len(data)
                            }
                self.conn.send(json.dumps(send_msg).encode())  # 把文件大小给客户端，判断recv的次数
                response = self.receive()
                if response.get("cmd"):  # 客户端已经准备好了
                    self.conn.sendall(data)  # 把文件信息发出去
                    download_response = self.receive()
                    if download_response.get("cmd"):
                        print("下载成功")
                        self.__logger(msg)
                    else:
                        print("客户端未下载成功")
                        cmd = {"status": 0}
                        self.conn.send(json.dumps(cmd).encode())
                else:
                    print("客户端未准备好")
                    cmd = {"status": 0}
                    self.conn.send(json.dumps(cmd).encode())
            else:
                print("文件读取出错，不能下载")
                cmd = {"status": 0}
                self.conn.send(json.dumps(cmd).encode())
        else:
            print("未找到文件")
            cmd = {"status": 0}
            self.conn.send(json.dumps(cmd).encode())

    def delete(self, msg):
        """
        Delete file
        :param msg: msg is request from client
                    send_msg = {"Type": "del",
                                "filename": filename
                                }
        :return: None
        """
        print("文件删除".format(msg.get("filename")).center(30, '-'))
        response = {"status": 1,
                    "file_list": []
                    }
        filename = msg.get("filename")
        path = r"D:\Projects\net_programming\MyFTP\MyServer\Data\Users\\" + self.username + r"\UserFiles"
        if os.path.isdir(path):
            file_list = os.listdir(path)
            response["file_list"] = file_list
            if filename in file_list:
                try:
                    file_path = path + r"\\" + filename
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        self.conn.send(json.dumps(response).encode())
                        print("成功删除文件{}".format(filename))
                        # return 1
                    else:
                        print("找不到文件{}".format(filename))
                        response["status"] = 0
                        self.conn.send(response)
                        # return 0
                except Exception as e:
                    print("del出错：", e)
                    response["status"] = 0
                    self.conn.send(response)
                    # return 0
            else:
                print("文件不在云端文件夹")
                response["status"] = 0
                self.conn.send(response)
                # return 0
        else:
            print("找不到这个路径")
            response["status"] = 0
            self.conn.send(response)
            # return 0

    def __logger(self, request_msg):
        """
        Record user upload files and download files
        :param request_msg:  request_msg is request from client
                        {"Type": "get" or "put",
                        "filename": filename  # command filename
                        }
        :return:  None
        """
        path = r'D:\\Projects\\net_programming\\MyFTP\\MyServer\\' + r"Data\\Users\\" + self.username + "\\log"
        if not os.path.isdir(path):  # 若文件夹不存在，则新建一个
            os.makedirs(path)
        if os.path.isdir(path):
            tm = time.strftime('%Y-%m-%d')
            with open(path + "\\" + tm + '.txt', 'a', encoding='utf-8') as f:  # 每天的记录作为一个文件
                data = time.strftime("%Y-%m-%d-%H-%M-%S:  ")+request_msg.get("Type")+' >> '+request_msg.get("filename")
                f.write(data)
                f.write('\n')
            print("增加一条记录")


if __name__ == '__main__':
    s = MyTCPHandler()
    s.handle()
