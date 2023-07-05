import cv2
import socket
import numpy as np

def videotrans(device, clt_ip, port, width=640, height=480, MTU=60000):
    """视频实时传输函数

    Args:
        device (int): 摄像头设备号
        clt_ip (str): 客户端IP地址
        port (int): 客户端端口号
        width (int, optional): 视频的宽度. Defaults to 640.
        height (int, optional): 视频的高度. Defaults to 480.
        MTU (int, optional): 最大传输单元. Defaults to 60000.
    """
    # 创建UDP套接字
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 打开摄像头
    cap = cv2.VideoCapture(device)
    # 设置摄像头的分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    while True:
        # 读取摄像头的画面
        ret, frame = cap.read()
        if not ret:
            print("cap.read() failed")
            break
        
        # 将画面压缩成jpg格式
        _, data = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
        
        # 计算数据片的数量
        num_pieces = len(data) // MTU + 1
        
        # 将数据片发送给接收端
        for i in range(num_pieces):
            # 获取当前数据片的内容和大小
            piece_data = data[i * MTU : (i + 1) * MTU]
            piece_size = len(piece_data)
            
            # 将数据片的编号和大小转换成4字节的整数
            piece_index = i.to_bytes(4, "big")
            piece_size = piece_size.to_bytes(4, "big")
            
            # print(type(piece_index), type(piece_size), type(piece_data))
            # 将数据片的编号、大小和内容拼接成一个数据包
            packet = piece_index + piece_size + piece_data.tobytes()
            
            # 发送数据包
            s.sendto(packet, (clt_ip, port))
        
if __name__ == "__main__":
     # 使用示例
     videotrans(0, "127.0.0.1", 8080, width=640, height=480, MTU=60000)