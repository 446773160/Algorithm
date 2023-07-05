import sys
import select
import threading
# 添加绝对路径
sys.path.append("/home/liaosc/project/pythonProject/Park/ParkingGuide/custom")
from datetime import datetime
from ParkingGuide.custom.log.log import *
from ParkingGuide.custom.structure.graph import *
from ParkingGuide.custom.A_Star_Search import *
from collections import OrderedDict
from django.utils import timezone
import redis
import socket
import cv2
import json
import ast
from decimal import Decimal
import re
import pickle

def calculate_fee(parking_time):
    '''
    根据我查到的信息，中国大陆停车场收费标准大致如下：
    停车时间不超过15分钟，免费；
    停车时间超过15分钟，不足1小时，按1小时计算；
    停车时间超过1小时，不足24小时，按每小时收费；
    停车时间超过24小时，按每天收费。
    假设每小时收费5元，每天收费50元，那么一个可能的函数如下：
    :param parking_time: 停车时间，单位为秒
    :return: 停车费用，单位为元
    '''
    # parking_time is the parking time in seconds
    # return the fee in yuan
    if parking_time <= 15 * 60:  # less than 15 minutes
        return 0
    elif parking_time <= 60 * 60:  # less than 1 hour
        return 5
    else:  # more than 1 hour
        hours = parking_time // (60 * 60)  # integer division
        if parking_time % (60 * 60) > 0:  # remainder
            hours += 1  # round up to the next hour
        if hours <= 24:  # less than 24 hours
            return hours * 5
        else:  # more than 24 hours
            days = hours // 24  # integer division
            if hours % 24 > 0:  # remainder
                days += 1  # round up to the next day
            return days * 50

def minDistance(word1: str, word2: str) -> int:
    if word1 is None or word2 is None:
        return -1
    n1 = len(word1)
    n2 = len(word2)
    dp = [[0] * (n2 + 1) for _ in range(n1 + 1)]
    # 第一行
    for j in range(1, n2 + 1):
        dp[0][j] = dp[0][j-1] + 1
    # 第一列
    for i in range(1, n1 + 1):
        dp[i][0] = dp[i-1][0] + 1
    for i in range(1, n1 + 1):
        for j in range(1, n2 + 1):
            if word1[i-1] == word2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = min(dp[i][j-1], dp[i-1][j], dp[i-1][j-1] ) + 1
    #print(dp)      
    return dp[-1][-1]
    
class Park:
    def __init__(self, g, parking_mapping, enter, pool) -> None:
        log.logger.info("park init start!")
        self.g = g
        # 记录每个车位的路径，字典类型，坐标-路径
        self.path = {}
        # redis连接池
        self.pool = pool
        conn = self.pool.get_connection('PING')
        if conn is not None:
            log.logger.info("redis connect success!")
        else:
            log.logger.info("redis connect failed!")
        # 入口坐标
        self.enter = enter
        # coord_num 坐标-车位号字典
        self.coord_num = parking_mapping
        # coord_dist车位坐标-距离字典，坐标-距离，
        self.coord_dist = self.setdist()
        # 车位坐标列表
        self.coord = list(self.coord_dist.keys())
        # 当前空闲的最近的车位下标
        self.nearst = 0
        # 当前停车场的车位数
        self.count = len(self.coord)
        self.builddatabase()
        # self.startlisten()
        log.logger.info("park init end!")
        

    def setdist(self):
        """输入停车场的矩阵图，获取车位坐标、与入口的距离字典并按与入口的距离排序

        Args:
            g (Graph): _description_
            enter：入口坐标
        """
        i = 0
        j = 0
        dic = {}
        # 获取车位坐标
        for i in range(len(self.g.g)):
            for j in range(len(self.g.g[i])):
                if self.g.g[i][j] >= 2:
                    path = a_start_search(self.g, self.enter, (i, j))
                    dist = len(path)
                    self.path[str((i, j))] = path
                    dic[str((i, j))] = dist
        # 按距离排序
        coord_dist = OrderedDict(sorted(dic.items(), key=lambda x: x[1]))
        return coord_dist

    def builddatabase(self):
        """初始化数据表

        Args:
            coord (_type_): 车位位置坐标
            pool (_type_): redis连接池
        """
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        r = redis.Redis(connection_pool=self.pool)
        for item in self.coord:
            r.hset(item, "occupy", "0")
            r.hset(item, "reserved time", current_time)
            r.hset(item, "parking time", current_time)
            r.hset(item, "leaving time", current_time)
            r.hset(item, "car plate", "")
            r.hset(item, "distance", self.coord_dist[item])

    def leavepark(self, plate):
        """离开车位，更新数据库

        Args:
            coord (元组): 车位坐标

        Returns:
            _type_: 停车费用
        """
        r = redis.Redis(connection_pool=self.pool)
        coord = r.get(plate)
        if coord is None:
            return -1

        if r.hget(coord, "occupy") == "0":
            # 防止误报。如果车位为空闲，则不进行任何操作
            log.logger.error(f"No car in this parking {self.coord_num[coord]}!")
            return 0

        log.logger.info("car plate: %s leave park", plate)
        # 删除车牌号-车位坐标的键值对

        r.delete(plate)

        # 设置车位状态为空闲
        r.hset(coord, "occupy", 0)

        # 查看当前车位的距离是否比最近的车位距离近，如果是则更新最近的车位
        dist = self.coord_dist[coord]
        # 将dist转换为int类型，并于当前最近的车位进行比较
        if int(dist) < self.coord_dist[self.coord[self.nearst]]:
            self.nearst = self.coord.index(coord)

        self.count += 1
        return self.count

    def parkreserve(self,model,prot,ParkingLot):
        """
        与入口的摄像头建立TCP连接，感应到车后实时抓拍车辆图片
        """
        # 创建一个TCP套接字
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定本地IP和端口
        s.bind(('0.0.0.0', prot))
        # 监听连接请求
        s.listen(1)

        # 接受一个客户端连接

        print("wait connection")
        conn, addr = s.accept()
        log.logger.info("connect to enter success")
        lastplate = ''
        out = self.videosave("enter.avi", fps=10, width=1280, height=720)
        while True:
            size = int.from_bytes(conn.recv(4), 'big')
            if size > 0:
                # 接收图像数据
                data = b''
                while len(data) < size:
                    data += conn.recv(1024)
                # 将字节流转换为图像数组
                print(f"msg recv len {len(data)}")
                img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
                frame = cv2.resize(img, (1280, 720))
                out.write(frame)
                # 保存图像到本地
                plate = self.imgprocess(model,img)
                if self.platecheck(plate) is False:
                    continue

                if minDistance(plate, lastplate) > 2:
                    log.logger.info(f"car plate: {plate} enter park")
                    lastplate = plate
                    num ,_= self.getpark(plate)
                    if plate is None:
                        print(" plate is None")
                        continue 
                    s = plate + " " + num
                    conn.sendall(s.encode())
                    try:
                        parking_lot = ParkingLot.objects.create(
                        license_plate=plate,
                        entry_time=timezone.now(),
                        parking_spot=num)
                        parking_lot.save()
                        print(f"{plate}  save success ")
                    except Exception as e:
                        print(f"{e}")
                    log.logger.info(f"msg send to enter success")
                else:
                    log.logger.info(f"car plate: {plate} repeat!")
            else:
                break
        conn.close()

    def platecheck(self, plate):
        """
        车牌号正则表达式检验
        """
        if plate is None:
            return False
        pattern = "^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼A-Z]{1}[A-Z]{1}[A-Z0-9]{5}"
        return bool(re.findall(pattern, plate))
    
    def getpark(self, plate):
        """寻找当前最近的空车位，self.nearst下标后移1位，所以self.nearst指向的车位不一定时空闲的，
            比如：0 1 1 1 0，当前有车占了第一个空车位，然后调用getpark()，self.nearst指向第二个车位，但是第二个车位不一定是空闲的

            return：车位号，车位路径
        """
        r = redis.Redis(connection_pool=self.pool)
        i = self.nearst
        if i >= len(self.coord):
            # log.logger.info("No Parking left!")
            return None, None

        current_time = datetime.now()
        current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        for i in range(len(self.coord)):
            # redis 可以存数值型数据，但是取出来的都是字符串，所以这里用字符串"0"表示空闲，"1"表示占用。注意
            if r.hget(self.coord[i], "occupy") == "0":
                # 设置车位状态为占用
                r.hset(self.coord[i], "occupy", "1")
                r.hset(self.coord[i], "reserved time", current_time)
                r.hset(self.coord[i], "car plate", plate)
                r.set(plate, self.coord[i])
                path = self.path[self.coord[i]]
                self.nearst = (i + 1)
                self.count -= 1
                log.logger.info(f"car plate: {plate} park in {self.coord_num[ast.literal_eval(self.coord[i])]}")
                return self.coord_num[ast.literal_eval(self.coord[i])], path
        # log.logger.info("No Parking left!")
        log.logger.info("No Parking left!")
        return None, None

    def getparknum(self):
        """获取剩余车位的数量
        """
        return self.count
    def videosave(self, filename, fps, width, height):
        """
        图片保存成视频
        """
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
        if out.isOpened():
            log.logger.info("video saver open success")
        else:
            log.logger.info("video saver fail")
        return out
    def exitpark(self, ParkingLot,model,port):
        """
        出口车辆识别工作函数
        """
        # 创建一个TCP套接字
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定本地IP和端口
        s.bind(('0.0.0.0', port))
        # 监听连接请求
        s.listen(1)

        # 接受一个客户端连接
        conn, addr = s.accept()
        log.logger.info(f'Exit Connected by{addr}')
        lastplate = ''
        out = self.videosave("exit.avi", fps=15, width=1280, height=720)
        while True:
            size = int.from_bytes(conn.recv(4), 'big')
            if size > 0:
                # 接收图像数据
                data = b''
                while len(data) < size:
                    data += conn.recv(1024)
                # 将字节流转换为图像数组
                img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
                frame = cv2.resize(img, (1280, 720))
                out.write(frame)
                # 识别车牌号
                plate = self.imgprocess(model,img)
                print(f"{plate}  exit")
                if self.platecheck(plate) is False:
                    continue
                # 检查是否与上一辆车重复
                if minDistance(plate, lastplate) > 2:
                    log.logger.info(f"car plate: {plate} enter park")
                    lastplate = plate
                    if self.leavepark(plate)==-1:
                        continue
                    # try:
                    log.logger.info("delete start")
                    parking_lots = ParkingLot.objects.filter(license_plate=plate)
                    if parking_lots.exists():
                        parking_lot = parking_lots.first()
                        log.logger.info("create ParkingLot")
                        parking_lot.exit_time=timezone.now()
                        log.logger.info("datetime get success")
                        parking_lot.entry_time=parking_lot.entry_time.replace(tzinfo=parking_lot.exit_time.tzinfo)
                        parking_duration = (parking_lot.exit_time - parking_lot.entry_time).total_seconds()
                        log.logger.info("get seconds success")
                        fee = Decimal(str(calculate_fee(int(parking_duration))))
                        log.logger.info("calculate success ")
                        parking_lot.fee = fee
                        log.logger.info(f"fee is {fee}")
                        parking_lot.fee=Decimal('3.14159')
                        parking_lot.delete()
                        log.logger.info(f"{plate} delete success exit")
                        message=plate+' '+str(parking_lot.fee)
                        log.logger.info("send start")
                        conn.sendall(message.encode())
                        log.logger.info(f"{plate} delete success,fee is {parking_lot.fee}")
                    else :
                        message='None'+' '+'0'
                        conn.sendall(message.encode())
                    # except Exception as e:
                    #     log.logger.error(f"{e}")
                else:
                    log.logger.info(f"car plate: {plate} repeat!")                
            else:
                break
        conn.close()
                



    def imgprocess(self, model,img):
        if model.get_conf_thresh(img):
            _, plate, _ = model.get_img_plate_color(img)
            return plate
        return None



    def conncamera(self,model, PORT):
        """
        监听摄像头连接请求
        """
        # 创建一个监听套接字，绑定地址和端口，设置为非阻塞模式
        HOST = "0.0.0.0"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        s.setblocking(False)

        # 创建一个epoll对象
        epoll = select.epoll()

        # 将监听套接字的文件描述符注册到epoll对象中，设置为可读事件
        EPOLLIN = select.EPOLLIN
        EPOLLOUT = select.EPOLLOUT
        EPOLLERR = select.EPOLLERR
        EPOLLHUP = select.EPOLLHUP
        epoll.register(s.fileno(), EPOLLIN)
        log.logger.info(s.fileno())

        # 创建一个字典，存储文件描述符和套接字的映射关系
        fd_to_socket = {s.fileno(): s}
        log.logger.info("creat epoll success!")
        fd_videosave = {}
        r = redis.Redis(connection_pool=self.pool)
        
        # 使用一个无限循环，调用epoll对象的poll方法，获取活动的文件描述符列表
        while True:
            events = epoll.poll()
            # 遍历文件描述符列表，判断是监听套接字还是连接套接字
            for fd, event in events:
                # 如果是监听套接字，接受新的连接请求，将新的套接字设置为非阻塞模式，注册到epoll对象中，添加到字典中
                if fd == s.fileno():
                    conn, addr = s.accept()
                    log.logger.info(f"Connected by {addr}")
                    conn.setblocking(True)

                    out = self.videosave(f"intersection-{conn.fileno()}.avi", fps=15, width=1280, height=720)
                    fd_videosave[conn.fileno()] = out 
                    epoll.register(conn.fileno(), EPOLLIN | select.EPOLLET)
                    fd_to_socket[conn.fileno()] = conn

                    msg = pickle.dumps(self.g.g)
                    conn.sendall(msg)
                # 如果是连接套接字，接收数据，如果数据为空，关闭套接字，注销epoll对象中的文件描述符，删除字典中的映射关系
                elif event & EPOLLIN:
                    sock = fd_to_socket[fd]
                    data = sock.recv(4)
                    size = int.from_bytes(data, 'big')
                    total_data = b""
                    if not data:
                        log.logger.info(f"Disconnected by {sock.getpeername()}")
                        sock.close()
                        epoll.unregister(fd)
                        del fd_to_socket[fd]
                    # 如果数据不为空，将数据原样发送回客户端
                    else:
                        
                        while len(total_data) < size:
                            total_data += sock.recv(1024)
                        
                        img = cv2.imdecode(np.frombuffer(total_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                        frame = cv2.resize(img, (1280, 720))
                        fd_videosave[fd].write(frame)
                        # 识别图片置信度大于0.8返回发送车牌号
                        plate = self.imgprocess(model,img)
                        print(plate)
                        if self.platecheck(plate) == True:
                            r=redis.Redis(connection_pool=self.pool)
                            location=r.get(plate)
                            if location is not None:
                                message=plate+" "+location
                                sock.send(message.encode())
                                log.logger.info(f"recv img from {sock.getpeername()}")
                            else:
                                log.logger.error(f"no location of Redis")
                        else:
                            log.logger.error(f"no plate in img")
                # 如果发生错误或挂起事件，关闭套接字，注销epoll对象中的文件描述符，删除字典中的映射关系
                elif event & (EPOLLERR | EPOLLHUP):
                    sock = fd_to_socket[fd]
                    log.logger.info(f"Error or hang up by {sock.getpeername()}")
                    sock.close()
                    epoll.unregister(fd)
                    del fd_to_socket[fd]

        # 关闭监听套接字和epoll对象
        s.close()
        epoll.close()
