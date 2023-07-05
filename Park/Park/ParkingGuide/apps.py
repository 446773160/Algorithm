from django.apps import AppConfig

from ParkingGuide.custom.platedetect.detect_plate_onnx import Onnx_Model
import cv2
import threading

from ParkingGuide.custom.videotrans.recvData import entry_road,leave_road,road_detect
from ParkingGuide.custom.structure import parking
import redis
import numpy as np
from ParkingGuide.custom.structure.graph import Graph
from ParkingGuide.custom.structure import layout
from ParkingGuide.custom.structure.parking import Park




class ParkingguideConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ParkingGuide"

    def ready(self):
        self.model = Onnx_Model()  # 预加载模型
        img = cv2.imread(r'/home/liaosc/project/pythonProject/Park/ParkingGuide/custom/platedetect/imgs/7.jpg')
        self.model.get_img_plate_color(img)  # GPU预热
        print("预热完成")
        ip = "localhost"
        port = 6379
        # 初始化redis连接池
        pool = redis.ConnectionPool(host=ip, port=port, decode_responses=True)
        # 初始化停车场
        graph = Graph(np.array(layout.parking_lot))

        # 创建park对象
        start = (17, 0)
        self.park = Park(graph, layout.parking_mapping, start, pool)
        for i in range(7):
             coord, path=self.park.getpark(f'皖A1234{i}')
             print(coord)
        print("停车场创建完成")
        # 创建线程  入口线程
        t1 = threading.Thread(target=entry_road, args=(9999,))
        t1.setDaemon(True)
        t1.start()
        print("入口线程创建完成") 
        t2 = threading.Thread(target=leave_road, args=(5555,))
        t2.setDaemon(True)
        t2.start()
        print("出口线程创建完成")
        t3 = threading.Thread(target=road_detect, args=(7777,))
        t3.setDaemon(True)
        t3.start()
        print("路口线程创建完成")
        
            


