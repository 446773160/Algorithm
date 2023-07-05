# -*- coding: utf-8 -*-
"""
 @Time : 2023/6/10 16:12
 @Author : liao.sc
 @File : video
 @Contact : 446773160@qq.com
"""
import threading
import socket
import cv2
from ParkingGuide.custom.videotrans import recv
from django.utils import timezone
import re


encoding = 'utf-8'
BUFSIZE = 1024
from django.apps import apps


def get_park():
    config = apps.get_app_config('ParkingGuide')
    return config.park

def get_model():
    config = apps.get_app_config('ParkingGuide')
    return config.model


def get_parking_guide():
    ParkingLot = apps.get_model('ParkingGuide', 'ParkingLot')
    return ParkingLot



# 入口获取车牌信息并写入数据库
def entry_road(port):
    ParkingLot=get_parking_guide()
    model=get_model()
    park=get_park()
    park.parkreserve(model,port,ParkingLot)
# 出口获取车牌信息并写入数据库
def leave_road(port):
    ParkingLot=get_parking_guide()
    model=get_model()
    park=get_park()
    park.exitpark(ParkingLot,model,port)

#路口函数
def road_detect(port):
    model=get_model()
    park=get_park()
    park.conncamera(model,port)
