# /bin/python3/bin/python3.6
# --*-- coding:utf-8 --*--
# Server

import json
import socket
import os
import sys
import time
from MyFTP.MyServer.server_code.DataBase import MdFive

Base_path = os.path.dirname(os.getcwd())
sys.path.append(Base_path)


class MyTCPHandler(object):

    def __int__(self):
        pass

    def handle(self):
        self.buff = 2048
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('192.168.43.232', 8001))
        self.sock.listen(5)
        print("Server is Running".center(30, "*"))
        while True:
            try:
                self.conn, self.addr = self.sock.accept()
                print('Client {} is connected'.format(self.addr).center(30, '='))
                login_msg = self.__login()  # 登录的返回信息True or False
                if login_msg:
                    self.__status_log("'{}' have connected with FTP successfully".format(self.username))  # 增加记录
                    self.page_main()  # 进入主页
                else:
                    # 返回False,登录失败
                    try:
                        request = self.receive()
                        print(request, type(request))
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
            print("\n", "home_page".center(30, '*'))
            try:
                print("waiting information from client..")
                msg = self.receive()  # 主请求,判断接下来做什么
                # print("收到请求: ", msg)
                if not msg:
                    print('客户端已断开连接')
                    self.__status_log("退出FTP")  # 用户退出记录
                    break  # 说明收到空请求（客户端要先自行检测不能发出空请求），断开连接
                else:
                    # print('收到信息：', msg)
                    if msg.get('Type') == 'put':
                        if self.__put(msg):  # 如果上传成功
                            # self.__show_dir()  # 上传之后，主动调用该函数，将用户文件夹下的文件列表发给用户
                            self.__logger(msg)  # 记录操作
                            continue
                        else:
                            print('这儿也不知道要写什么')
                            continue
                    elif msg.get('Type') == 'get':
                        self.__get(msg)
                        continue
                    elif msg.get("Type") == "del":
                        self.delete(msg)
                        self.__status_log("删除了文件->{}".format(msg.get("filename")))
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
        # print("获取用户文件目录".center(30, '-'))
        path = r"../Data/Users/" + self.username+r"/UserFiles"
        # print("path: ", path)
        if os.path.isdir(path):
            file_list = os.listdir(path)  # 获得文件夹下所有的文件名
            msg = {"status": 1,  # 1表示该文件夹存在
                   "file_list": file_list
                   }
            # print(path)
            self.conn.send(json.dumps(msg).encode())
            print("给用户返回： ", msg)
            return True
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
        print("\n", "注册主页".center(30, '-'))
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
            user_file = r"/root/PycharmProjects/net_programming/MyFTP/MyServer/Data/Users/" + self.username + r"/UserFiles"
            user_log = r"/root/PycharmProjects/net_programming/MyFTP/MyServer/Data/Users/" + self.username + r"/log"
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
        print("Verify filename")  # 验证帐号
        db_path = r"../Data/UserInfo/userinfo.txt"  # 存储用户的帐号和密码
        if os.path.isfile(db_path):
            with open(db_path, 'rb') as f:  # Md5写入时使用二进制的，所以这儿也用二进制读取
                try:
                    info = []
                    data = f.readlines()
                    for line in data:
                        info.append(json.loads(line))
                    # print(type(info), len(info), info)
                    return info
                except Exception as e:
                    print("读取MD5文件出错：", e)
                    return None
        else:
            print("信息库不存在")
            return None

    def receive(self):
        """
        Preliminary handing request from client in json and decode
        :return:  request from user
        """
        rec_msg = self.conn.recv(self.buff)
        # print(rec_msg)
        try:
            msg = json.loads(rec_msg.decode())
            return msg
        except Exception as e:
            print("receive None: ", e)
            return None

    def __login(self):
        """
        User login to their account
        :return:  Return "True" if login is successful, or return "False"
        """
        self.username = self.conn.recv(self.buff).decode()  # 用户账号
        print("received username:", self.username)
        user_info = self.__readmd5()  # ###读取MD5文件，返回文件中所有用户的信息，返回格式为[{},{},{}](是str的)
        msg = {"status": 1}
        user_list = [user.get("username") for user in user_info]  # 得到信息库中所有用户的用户名列表(str的)
        # print("user_list: ", user_list)
        if self.username in user_list:
            print('用户帐号：', self.username)
            self.conn.send(json.dumps(msg).encode())
            count = 1
            while True:
                self.password = self.conn.recv(self.buff).decode()  # 用户密码
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
                if md5_pw == real_pw[0].get("password"):
                    print('用户密码：', self.password)
                    print('用户{}已登录!'.format(self.username))
                    print("*"*30)
                    # 登录成功之后，将用户的云端文件目录传入字典, 并将登录信息写入log.txt
                    file_list = os.listdir(r"../Data/Users/{}/UserFiles".format(self.username))
                    msg = {"status": 1,
                           "file_list": file_list
                           }
                    # print("msg:  ", msg)
                    self.conn.send(json.dumps(msg).encode())
                    return True
                else:
                    msg['status'] = 0
                    print("错误密码->", self.password)
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
        path = r'/root/PycharmProjects/net_programming/MyFTP/MyServer/' + r"Data/Users/" + self.username + r"/log"
        if not os.path.isdir(path):  # 若文件夹不存在，则新建一个
            os.makedirs(path)
        if os.path.isdir(path):
            tm = time.strftime('%Y-%m-%d')
            with open(path + "/" + tm + '.txt', 'a', encoding='utf-8') as f:  # 每天的记录作为一个文件
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
        print("\n", "put center".center(30, '*'))
        fsize = msg_info.get("file_size")
        fname = msg_info.get("filename")
        print(fname, fsize)
        count_1 = fsize / self.buff
        count_2 = fsize % self.buff
        count = 1
        base_path = '../Data/Users/'+self.username+'/UserFiles/' + fname
        path = os.path.abspath(base_path)
        msg = {"status": 1}
        # print("要上传的文件：", path)
        if os.path.isfile(path):
            # 如果要上传的文件已经存在，返回提示
            msg["status"] = 0
            self.conn.send(json.dumps(msg).encode())
        else:
            self.conn.send(json.dumps(msg).encode())
            with open(path, 'wb') as f:
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
                    self.conn.send(json.dumps(msg).encode())
                    print("文件{}上传成功!".format(fname))
                    return True
                except Exception as e:
                    msg["status"] = 0
                    self.conn.send(json.dumps(msg).encode())
                    print("上传失败！", e)
                    return False

    def __get(self, msg):   # 客户端要下载文件
        """
        Request to upload file
        :param msg:  msg = {"Type": "get",
                            "filename": filename  # download filename
                            }
        :return:  Return "True" if user upload is successful, or return "False"
        """
        print("\n", 'get center'.center(30, '*'))
        filename = msg.get("filename")
        file_path = r"../Data/Users/" + self.username + r'/UserFiles/' + filename  # 注意这儿的filename的值应该为一个字符串才行
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)  # 得到该文件的大小
            # print('文件名：', filename)
            print('file_path', file_path)  # ######################################################del
            with open(file_path, 'rb') as f:
                data = f.read()
            send_msg = {"status": 1,
                        "file_size": size
                        }
            try:
                self.conn.send(json.dumps(send_msg).encode())  # give size client
                response = self.receive()  # {"status": 1 or 0}
                # print('服务器返回了信息：', response)
                if response["status"] == 1:  # 正常返回的是一个字典，值为1
                    self.conn.sendall(data)  # client准备好之后，就可以将文件上传
                    msg = self.receive()  # 打印client返回来的download情况
                    if msg["status"] == 1:
                        print("File {} have downloaded successfully".format(filename))
                        return True
                    else:
                        print("File {} download was error".format(filename))
                        return False
            except Exception as e:
                print("UPLOADING ERROR!: ", e)
                return False
        else:
            send_msg = {"status": 0}
            self.conn.send(json.dumps(send_msg).encode())
            return False

    def delete(self, msg):
        """
        Delete file
        :param msg: msg is request from client
                    send_msg = {"Type": "del",
                                "filename": filename
                                }
        :return: None
        """
        print("\n", "文件删除".format(msg.get("filename")).center(30, '-'))
        response = {"status": 1,
                    "file_list": []
                    }
        filename = msg.get("filename")
        path = r"/root/PycharmProjects/net_programming/MyFTP/MyServer/Data/Users/" + self.username + r"/UserFiles"
        if os.path.isdir(path):
            file_list = os.listdir(path)
            response["file_list"] = file_list
            if filename in file_list:
                try:
                    file_path = path + r"/" + filename
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        self.conn.send(json.dumps(response).encode())
                        print("成功删除文件->{}".format(filename))
                        # return 1
                    else:
                        print("找不到文件->{}".format(filename))
                        response["status"] = 0
                        self.conn.send(json.dumps(response).encode())
                        # return 0
                except Exception as e:
                    print("del出错：", e)
                    response["status"] = 0
                    self.conn.send(json.dumps(response).encode())
                    # return 0
            else:
                print("文件不在云端文件夹")
                response["status"] = 0
                self.conn.send(json.dumps(response).encode())
                # return 0
        else:
            print("找不到这个路径")
            response["status"] = 0
            self.conn.send(json.dumps(response).encode())
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
        base_path = r"../Data/Users/" + self.username + "/log"
        path = os.path.abspath(base_path)
        if not os.path.isdir(path):  # 若文件夹不存在，则新建一个
            os.makedirs(path)
        if os.path.isdir(path):
            tm = time.strftime('%Y-%m-%d')
            with open(path + "//" + tm + '.txt', 'a', encoding='utf-8') as f:  # 每天的记录作为一个文件
                data = time.strftime("%Y-%m-%d-%H-%M-%S:  ")+request_msg.get("Type")+' >> '+request_msg.get("filename")
                f.write(data)
                f.write('\n')
            print("增加一条记录")


if __name__ == '__main__':
    s = MyTCPHandler()
    s.handle()
