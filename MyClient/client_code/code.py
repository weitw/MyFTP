# --*-- coding:utf-8 --*--

import socket
import json
import os
import time


class Client(object):

    def __init__(self):
        pass

    def make_conn(self):
        """
        API
        :return:  None
        """
        # self.addr = input('输入服务器地址>>').strip()
        # self.port = int(input('输入端口号>>').strip())
        # addr = '127.0.0.1'
        # port = 9999
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect(('127.0.0.1', 8080))
            print('The server is running normally')
        except Exception as e:
            print('Server exception：', e)
            exit()
        try:
            hello = self.conn.recv(1024).decode()
            print(json.loads(hello))
        except:
            print("The welcome ceremony ended badly")
        msg = self.__login()  # msg是一个用户云端信息字典，{"status": ***, "file_list": ***}
        if msg["status"]:
            """Successful login interface"""
            self.__help()  # 显示使用指南
            self.page_main(msg)  # 登录成功，进入操作中心
        else:
            """Login was failed, then choose enroll or exit?"""
            while True:
                cmd = input("Choose register(y)or exit(q)?").strip()
                if cmd == "y":
                    request = {"Type": "enroll"}
                    self.conn.send(json.dumps(request).encode())
                    msg = self.__enroll()
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
                print("COMMAND CENTER".center(30, '-'))
                cmd = input('Enter command>>').strip().split()  # cmd是一个列表，例如：["get", "..\\file.txt"],
                # 文件名要是完整的，包含路径,文件路径输入时不要加""，输入示例：put D:\\python3\\清屏方法.txt
                if len(cmd) == 0:
                    # 请求为空值，重新输入请求
                    continue
                elif cmd[0] == "q":
                    print("EXIT FTP!")
                    exit()
                elif cmd[0] == "show":
                    print("PERSONAL HOME".center(30, '-'))
                    request = {"Type": "show"}
                    self.conn.send(json.dumps(request).encode())
                    self.show_file()   # 命令show会主动获得一次云端文件夹内容
                    continue
                elif cmd[0] == "put":
                    if os.path.isfile(cmd[1]):
                        top = self.__put(cmd[1])
                        if top == 0:
                            break  # 上传失败，则退出FTP
                        else:
                            continue
                    else:
                        print("File path must be complete")
                        continue
                elif cmd[0] == "get":
                    if cmd[1] in msg.get("file_list"):
                        self.__get(cmd[1])  # cmd[1]是要从云端下载的文件名
                        continue
                    else:
                        print("Bad filename!")
                        continue
                elif cmd[0] == "del":
                    if cmd[1] in msg.get("file_list"):
                        send_msg = {"Type": "del",
                                    "filename": cmd[1]
                                    }
                        self.conn.send(json.dumps(send_msg).encode())
                        self.delete(cmd[1])  # 删除云端文件
                        continue
                    else:
                        print("Bad filename！")
                        continue
                elif cmd[0] == "help":
                    self.__help()
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
        while True:
            try:
                file_info = self.receive()  # 返回的是 msg = {"status": 1( or 0), "file_list": file_list} # 1表示该文件夹存在,0表示不存在
                # print("file_info:  ", file_info)
                # count = 0  # 用来限制请求获取文件夹出错的次数，防止无限循环
                # file_info  # msg是一个用户云端信息字典，{"status": ***, "file_list": ***}
                if file_info["status"]:
                    for file in file_info["file_list"]:
                        print(file)   # 打印云端文件列表
                    break
                    # return file_info
                else:
                    print("You don't get files directory")
                    break
                    # if count >= 3:
                    # return file_info  # 表示没有获得信息，可能是服务端出错，所以退出，以免造成一个无限循环
                    # count += 1
                    # continue  # 表示这一次请求没有得到文件夹信息
                    # elif file_info.get("status") == 2:
                    #     exit()
            except ConnectionError as e:
                print("404! ", e)  # 服务器已经停止服务
                exit()
                # return False

    def __get(self, filename):
        """
        Request to download file
        :param filename: This is file user want to download from server
        :return: Return "True" if user download is successful, or return "False"
        """
        print("FILE DOWNLOAD".center(30, '-'))
        path = r'D:\\Projects\\net_programming\\MyFTP\\MyClient\\' + r"download_file"
        path_list = os.listdir(path)
        if filename in path_list:  # 判断该文件是否已经存在，若存在，则退出下载，
            print("File {} already exists, not re-downloadable".format(filename))
        else:
            first_send = {"Type": "get",
                          "filename": filename  # 要下载的文件
                          }
            self.conn.send(json.dumps(first_send).encode())
            response = self.receive()  # {"status": 1, "file_size": size},size为要下载的文件大小
            if response["status"]:  # 得到文件大小
                size = response.get("file_size")
            else:
                print("file{}not download".format(filename))
                return False
            count = int(size / 5215)
            digit = size % 5215
            data = []  # data是文件内容（二进制读取的）的一个容器
            num = 0
            confirm_send = {"cmd": 1}
            self.conn.send(json.dumps(confirm_send).encode())  # 返回信息，提示服务器已经准备好可以下载了
            # print("get......")
            while num < count:
                try:
                    data.append(self.conn.recv(5215))
                    # time.sleep(0.025)
                    # print(data[0:20])
                    num += 1
                except Exception as e:
                    print('Download error 1：', e)
                    return False
            if digit != 0:
                try:
                    data.append(self.conn.recv(digit))  # 文件使用二进制操作的，所以不用解码
                except Exception as er:
                    print('Download error 2：', er)
                    return False
            # 下载完，接下来存入文件
            # 递归的创建多级目录
            try:
                if not os.path.isdir(path):  # 判断这个用户是否已经建立过文件夹了（已经存在数据库中了）
                    os.makedirs(path)
            except Exception as e:
                print('该文件存储库已经存在：', e)
            if not os.path.isfile(path+"\\"+filename):  # 如果该文件不存在
                with open(path + "\\" + filename, 'wb') as f:
                    try:
                        print("DOWNLOADING".center(30, '#'))
                        for d in data:
                            f.write(d)
                    except Exception as e:
                        print('File write error 3：', e)
                print('Download successfully!')
                self.conn.send(json.dumps(confirm_send).encode())  # 回复服务器，确认已经下载完
                return True
            else:
                print("File {} is exists, not re-downloadable".format(filename))
                return False

    def __put(self, file_path):
        """
        Request to upload file
        :param file_path:  This is file user want to upload from server
        :return:  Return "True" if user upload is successful, or return "False"
        """
        print('FILE UPLOAD'.center(30, '-'))
        size = os.path.getsize(file_path)  # 得到该文件的大小
        filename = os.path.basename(file_path)  # 得到文件名
        # print('文件名：', filename)
        print('file_path', file_path)  # ######################################################del
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
                elif msg["status"] == 2:
                    print("File {} is exists, you can delete file in file's directory firstly".format(filename))
                    return True
                else:
                    print("File {} upload was error".format(filename))
                    return False
        except Exception as e:
            print("UPLOADING ERROR!: ", e)
            return False

    def receive(self):
        """
        Receive a response and preliminary handing it in json and decode from server
        :return:  Return the response from server
        """
        try:
            msg = self.conn.recv(1024)
            print("This is response from server：", msg)
            rec_msg = json.loads(msg.decode())
            # print("This is response from server：", rec_msg)
            return rec_msg
        except Exception as e:
            print('RESPONSE WRONG!', e)
            return None

    def delete(self, filename):
        """
        Request to delete file of user's person from server
        :param filename:  This is file user want to delete file from server
        :return: None
        """
        # send_msg = {"Type": "del",
        #             "filename": filename
        #             }
        # self.conn.send(json.dumps(send_msg).encode())
        msg = self.receive()
        if msg.get("status"):
            print("SUCCESSFUL'{}'".format(filename))
            # return 1
        else:
            print("FAILED")
            # return 0

    def __login(self):
        """
        This is the page when user login FTP
        :return: Return response that it include user's files directory from server
        """
        print('login'.center(30, '-'))
        username = input('USERNAME>>')
        try:
            self.conn.send(username.encode())
            msg = self.receive()
            count = 0
            while msg["status"]:
                password = input('PASSWORD>>')
                self.conn.send(password.encode())
                msg1 = self.receive()
                if msg1.get("status"):
                    print('{},I finally waited for you!'.format(username))
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
                print('This user has not registered yet, please register first')
                msg["status"] = 0
                return msg  # 返回0表示登录失败
        except Exception as e:
            print("WRONG!：", e)

    def __enroll(self):
        """
        This is the page when user registering FTP
        :return:  Return a response that it include user's file directory from server
        """
        msg = self.receive()   # {"status": 1 or 0, "file_list": file_list}
        if msg.get("status"):  # 允许注册
            print("enroll".center(30, "-"))
            username = input('USERNAME>>').strip()
            password = input('PASSWORD>>').strip()
            cmd = {"username": username,
                   "password": password
                   }
            try:
                self.conn.send(json.dumps(cmd).encode())
                response = self.receive()  # {"status": 1, "file_list": file_list} # 注册成功才会返回这条消息
                print(response)
                if response.get("status"):
                    print('SUCCESSFUL')
                    return response
                else:
                    print('FAILED')
                    return response
            except Exception as e:
                print('FAILED：', e)
                msg["status"] = 0
                return msg
        else:
            print("Registration is not allowed")
            exit()

    def __help(self):
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
