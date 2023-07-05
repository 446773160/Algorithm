import cv2
import socket
import numpy as np
import threading
import queue

data = bytearray()

# 采用队列存取单张图片数据
q = queue.Queue()

lock = threading.Lock()
# 定义一个函数，用于接收数据片并更新data
def receive(s, opt=0):
    """接收图片数据

    Args:
        s (_type_): socket句柄
    """
    global data # 声明全局变量
    with s:
        while True:
            # 接收数据包（最大65535字节）
            packet, addr = s.recvfrom(65535)
            if not packet:
                print("connection lost")
                break

            # 获取数据包的长度（字节）
            packet_size = len(packet)
            
            # 如果数据包长度小于4字节，说明是无效的数据包，直接丢弃
            if packet_size < 4:
                continue
            
            # 获取数据片的编号（4字节的整数）
            piece_index = int.from_bytes(packet[:4], "big")
            
            # 如果数据片编号为0，说明是新的一帧图片的开始，需要清空data
            if piece_index == 0:
                # 加锁
                data = bytearray() # 清空data
            
            # 如果数据包长度小于8字节，说明是无效的数据包，直接丢弃
            if packet_size < 8:
                continue
            
            # 获取数据片的大小（4字节的整数）
            piece_size = int.from_bytes(packet[4:8], "big")
            
            # 如果数据片大小不等于数据包长度减去8字节，说明是无效的数据包，直接丢弃
            if piece_size != packet_size - 8:
                continue
            piece_data = packet[8:]
            data[piece_index * piece_size : (piece_index + 1) * piece_size] = piece_data

            if piece_size < 60000:
                # 说明是最后一个数据片，释放锁
                q.put(data)
            with lock:
                if q.qsize() > 100:
                    q.queue.clear()
    
    print("recv thread end")

def checkqueue(maxsize=100):
    """检查队列中的元素数量，如果超过maxsize，则清空队列

    Args:
        maxsize (_type_): 队列最大长度
    """
    while True:
        if q.qsize() > maxsize:
            q.queue.clear()

def startrecv(port, opt=0):
    """启动接收端
    args:
        port (_type_): 端口号
        opt (_type_): 可选项，0表示安全队列，防止队列溢出，1表示不安全队列（即很长时间不取队列中元素）。0会增加计算量，1会可能会爆内存

    """

    # 创建一个UDP套接字
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # 绑定本地IP地址和端口号
    host = "0.0.0.0"
    port = port
    s.bind((host, port))
    # 将套接字设置为阻塞模式
    s.setblocking(True)

    # 创建一个线程，用于执行receive函数
    t = threading.Thread(target=receive, args=(s, opt))
    t.daemon = True # 设置线程为守护线程
    t.start()       # 启动线程
    print("recv thread start!")


def getimg():
    """获取单张图片数据（执行startrecv后才可以执行）
        return:返回图片
    """
    pic = q.get()
    img = cv2.imdecode(np.frombuffer(pic, dtype=np.uint8), cv2.IMREAD_COLOR)
    return img






if __name__ == "__main__":
    
    # 使用示例，启动接收端，然后获取图片，最好接收段先停止，然后停止发送端，否则可能会出现卡死的情况，采用TCP可以避免这个问题
    startrecv(8080, 0)
    while True:
        img = getimg()
        cv2.imshow("recv", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
