# -*- coding: utf-8 -*-
"""
 @Time : 2023/6/5 19:15
 @Author : liao.sc
 @File : detect_plate_onnx
 @Contact : 446773160@qq.com
"""
import onnxruntime
import numpy as np
import cv2
import copy
import os
import argparse
from PIL import Image, ImageDraw, ImageFont
import time

plate_color_list = ['黑色', '蓝色', '绿色', '白色', '黄色']
plateName = r"#京沪津渝冀晋蒙辽吉黑苏浙皖闽赣鲁豫鄂湘粤桂琼川贵云藏陕甘青宁新学警港澳挂使领民航危0123456789ABCDEFGHJKLMNPQRSTUVWXYZ险品"
mean_value, std_value = ((0.588, 0.193))  # 识别模型均值标准差

def decodePlate(preds):  # 识别后处理
    pre = 0
    newPreds = []
    for i in range(len(preds)):
        if preds[i] != 0 and preds[i] != pre:
            newPreds.append(preds[i])
        pre = preds[i]
    plate = ""
    for i in newPreds:
        plate += plateName[int(i)]
    return plate
    # return newPreds


def rec_pre_precessing(img, size=(48, 168)):  # 识别前处理
    img = cv2.resize(img, (168, 48))
    img = img.astype(np.float32)
    img = (img / 255 - mean_value) / std_value  # 归一化 减均值 除标准差
    img = img.transpose(2, 0, 1)  # h,w,c 转为 c,h,w
    img = img.reshape(1, *img.shape)  # channel,height,width转为batc-h,channel,height,channel
    return img


def get_plate_result(img, session_rec):  # 识别后处理
    img = rec_pre_precessing(img)
    y_onnx_plate, y_onnx_color = session_rec.run([session_rec.get_outputs()[0].name, session_rec.get_outputs()[1].name],
                                                 {session_rec.get_inputs()[0].name: img})
    index = np.argmax(y_onnx_plate, axis=-1)
    # confidences = np.max(y_onnx_plate, axis=-1)
    # for i in range(len(confidences[0])):
    #     print("车牌号下标", index[0][i], "置信度：", confidences[0][i])
    index_color = np.argmax(y_onnx_color)
    plate_color = plate_color_list[index_color]
    # print(y_onnx[0])
    plate_no = decodePlate(index[0])
    return plate_no, plate_color


def allFilePath(rootPath, allFIleList):  # 遍历文件
    fileList = os.listdir(rootPath)
    for temp in fileList:
        if os.path.isfile(os.path.join(rootPath, temp)):
            allFIleList.append(os.path.join(rootPath, temp))
        else:
            allFilePath(os.path.join(rootPath, temp), allFIleList)


def get_split_merge(img):  # 双层车牌进行分割后识别
    h, w, c = img.shape
    img_upper = img[0:int(5 / 12 * h), :]
    img_lower = img[int(1 / 3 * h):, :]
    img_upper = cv2.resize(img_upper, (img_lower.shape[1], img_lower.shape[0]))
    new_img = np.hstack((img_upper, img_lower))
    return new_img


def order_points(pts):  # 关键点排列 按照（左上，右上，右下，左下）的顺序排列
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image, pts):  # 透视变换得到矫正后的图像，方便识别
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    # return the warped image
    return warped


def my_letter_box(img, size=(640, 640)):  #
    h, w, c = img.shape
    r = min(size[0] / h, size[1] / w)
    new_h, new_w = int(h * r), int(w * r)
    top = int((size[0] - new_h) / 2)
    left = int((size[1] - new_w) / 2)

    bottom = size[0] - new_h - top
    right = size[1] - new_w - left
    img_resize = cv2.resize(img, (new_w, new_h))
    img = cv2.copyMakeBorder(img_resize, top, bottom, left, right, borderType=cv2.BORDER_CONSTANT,
                             value=(114, 114, 114))
    return img, r, left, top


def xywh2xyxy(boxes):  # xywh坐标变为 左上 ，右下坐标 x1,y1  x2,y2
    xywh = copy.deepcopy(boxes)
    xywh[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
    xywh[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
    xywh[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
    xywh[:, 3] = boxes[:, 1] + boxes[:, 3] / 2
    return xywh


def my_nms(boxes, iou_thresh):  # nms
    index = np.argsort(boxes[:, 4])[::-1]
    keep = []
    while index.size > 0:
        i = index[0]
        keep.append(i)
        x1 = np.maximum(boxes[i, 0], boxes[index[1:], 0])
        y1 = np.maximum(boxes[i, 1], boxes[index[1:], 1])
        x2 = np.minimum(boxes[i, 2], boxes[index[1:], 2])
        y2 = np.minimum(boxes[i, 3], boxes[index[1:], 3])

        w = np.maximum(0, x2 - x1)
        h = np.maximum(0, y2 - y1)

        inter_area = w * h
        union_area = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1]) + (
                boxes[index[1:], 2] - boxes[index[1:], 0]) * (boxes[index[1:], 3] - boxes[index[1:], 1])
        iou = inter_area / (union_area - inter_area)
        idx = np.where(iou <= iou_thresh)[0]
        index = index[idx + 1]
    return keep


def restore_box(boxes, r, left, top):  # 返回原图上面的坐标
    boxes[:, [0, 2, 5, 7, 9, 11]] -= left
    boxes[:, [1, 3, 6, 8, 10, 12]] -= top

    boxes[:, [0, 2, 5, 7, 9, 11]] /= r
    boxes[:, [1, 3, 6, 8, 10, 12]] /= r
    return boxes


def detect_pre_precessing(img, img_size):  # 检测前处理
    img, r, left, top = my_letter_box(img, img_size)
    # cv2.imwrite("1.jpg",img)
    img = img[:, :, ::-1].transpose(2, 0, 1).copy().astype(np.float32)
    img = img / 255
    img = img.reshape(1, *img.shape)
    return img, r, left, top


def post_precessing(dets, r, left, top, conf_thresh=0.7, iou_thresh=0.5):  # 检测后处理
    choice = dets[:, :, 4] > conf_thresh
    dets = dets[choice]
    dets[:, 13:15] *= dets[:, 4:5]
    box = dets[:, :4]
    boxes = xywh2xyxy(box)
    score = np.max(dets[:, 13:15], axis=-1, keepdims=True)
    index = np.argmax(dets[:, 13:15], axis=-1).reshape(-1, 1)
    output = np.concatenate((boxes, score, dets[:, 5:13], index), axis=1)
    reserve_ = my_nms(output, iou_thresh)
    output = output[reserve_]
    output = restore_box(output, r, left, top)
    return output
def rec_plate_score(outputs, img0, session_rec):  # 识别车牌
    for output in outputs:
        result_dict = {}
        rect = output[:4].tolist()
        land_marks = output[5:13].reshape(4, 2)
        score = output[4]
        return score


def rec_plate(outputs, img0, session_rec):  # 识别车牌
    dict_list = []
    for output in outputs:
        result_dict = {}
        rect = output[:4].tolist()
        land_marks = output[5:13].reshape(4, 2)
        roi_img = four_point_transform(img0, land_marks)
        label = int(output[-1])
        score = output[4]
        if label == 1:  # 代表是双层车牌
            roi_img = get_split_merge(roi_img)
        plate_no, plate_color = get_plate_result(roi_img, session_rec)
        result_dict['rect'] = rect
        result_dict['landmarks'] = land_marks.tolist()
        result_dict['plate_no'] = plate_no
        result_dict['roi_height'] = roi_img.shape[0]
        result_dict['plate_color'] = plate_color
        dict_list.append(result_dict)
    return dict_list


def cv2ImgAddText(img, text, left, top, textColor=(0, 255, 0), textSize=20):  # 将识别结果画在图上
    if (isinstance(img, np.ndarray)):  # 判断是否OpenCV图片类型
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    fontText = ImageFont.truetype(
        r"/home/liaosc/project/pythonProject/Park/ParkingGuide/custom/platedetect/fonts/platech.ttf", textSize, encoding="utf-8")
    draw.text((left, top), text, textColor, font=fontText)
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def draw_result(orgimg, dict_list, clors):
    result_str = ""
    for result in dict_list:
        rect_area = result['rect']

        x, y, w, h = rect_area[0], rect_area[1], rect_area[2] - rect_area[0], rect_area[3] - rect_area[1]
        padding_w = 0.05 * w
        padding_h = 0.11 * h
        rect_area[0] = max(0, int(x - padding_w))
        rect_area[1] = min(orgimg.shape[1], int(y - padding_h))
        rect_area[2] = max(0, int(rect_area[2] + padding_w))
        rect_area[3] = min(orgimg.shape[0], int(rect_area[3] + padding_h))

        height_area = result['roi_height']
        landmarks = result['landmarks']
        plate_color = result['plate_color']
        result = result['plate_no']
        result_str += result + " "
        for i in range(4):  # 关键点
            cv2.circle(orgimg, (int(landmarks[i][0]), int(landmarks[i][1])), 5, clors[i], -1)
        cv2.rectangle(orgimg, (rect_area[0], rect_area[1]), (rect_area[2], rect_area[3]), (255, 0, 0), 2)  # 画框
        if len(result) >= 1:
            orgimg = cv2ImgAddText(orgimg, result, rect_area[0] - height_area, rect_area[1] - height_area - 10,
                                   (0, 255, 0), height_area)
        if len(plate_color) >= 1:
            orgimg = cv2ImgAddText(orgimg, plate_color, rect_area[0] + height_area * 4.5,
                                   rect_area[1] - height_area - 10,
                                   (0, 255, 0), height_area)

    return orgimg, result, plate_color


def reload_model(detect_path, rec_path):
    '''
    预加载模型  以CPU加载模型
    Args:
        detect_path: detect模型路径
        rec_path: rec模型路径

    Returns:

    '''
    providers = ['CPUExecutionProvider']
    session_detect = onnxruntime.InferenceSession(detect_path, providers=providers)
    session_rec = onnxruntime.InferenceSession(rec_path, providers=providers)
    return session_detect, session_rec


def get_img_plate_color(img, session_detect, session_rec, img_size=640):
    '''
    获取图片车牌号和车牌颜色
    Args:
        img: 图片，以cv2读取
        session_detect: detect模型
        session_rec: rec模型
        img_size: 图片大小

    Returns:以元组形式返回图片，车牌号，车牌颜色

    '''
    img0 = copy.deepcopy(img)
    img_size = (img_size, img_size)
    clors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]
    img, r, left, top = detect_pre_precessing(img, img_size)  # 检测前处理
    y_onnx = session_detect.run([session_detect.get_outputs()[0].name], {session_detect.get_inputs()[0].name: img})[
        0]
    outputs = post_precessing(y_onnx, r, left, top)  # 检测后处理
    result_list = rec_plate(outputs, img0, session_rec)  # 识别车牌
    result = draw_result(img0, result_list, clors)  # 画图并且返回图片,车牌号和车牌颜色
    return result


def get_conf_thresh(img, session_detect, img_size=640):
    img_size = (img_size, img_size)
    img, r, left, top = detect_pre_precessing(img, img_size)  # 检测前处理
    y_onnx = session_detect.run([session_detect.get_outputs()[0].name], {session_detect.get_inputs()[0].name: img})[0]
    # config = outputs[:, :, 4] > 0.6
    # box = outputs[config == True]
    # if box.size > 0:
    #     print('有车牌')
    # else:
    #     print('无车牌')
    outputs = post_precessing(y_onnx, r, left, top)  # 检测后处理
    for output in outputs:
        if output[4] > 0.6:
            return True
    return False


class Onnx_Model:
    '''
    onnx模型类
    detect_path: detect模型路径
    rec_path: rec模型路径
    providers: 加载模型的设备
    get_img_plate_color: 获取图片车牌号和车牌颜色   返回图片，车牌号和车牌颜色
    get_conf_thresh: 获取图片是否有车牌  有车牌返回True  无车牌返回False
    '''

    def __init__(self, detect_path=r'ParkingGuide/custom/platedetect/weights/plate_detect.onnx',
                 rec_path=r'ParkingGuide/custom/platedetect/weights/plate_rec_color.onnx',
                 providers=['CUDAExecutionProvider']):
        self.session_detect = onnxruntime.InferenceSession(detect_path, providers=providers)
        self.session_rec = onnxruntime.InferenceSession(rec_path, providers=providers)
        self.img_size = 640
    def get_img_plate_color(self, img):
        '''
    Args:
        img: 图片，以cv2读取
        session_detect: detect模型
        session_rec: rec模型
        img_size: 图片大小

    Returns:以元组形式返回图片，车牌号，车牌颜色
        '''
        img0 = copy.deepcopy(img)
        img_size = (self.img_size, self.img_size)
        clors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]
        img, r, left, top = detect_pre_precessing(img, img_size)  # 检测前处理
        y_onnx = self.session_detect.run([self.session_detect.get_outputs()[0].name],
                                         {self.session_detect.get_inputs()[0].name: img})[
            0]
        outputs = post_precessing(y_onnx, r, left, top)  # 检测后处理
        result_list = rec_plate(outputs, img0, self.session_rec)  # 识别车牌
        result = draw_result(img0, result_list, clors)  # 画图并且返回图片,车牌号和车牌颜色
        return result

    def get_conf_thresh(self, img):
        img_size = (self.img_size, self.img_size)
        img, r, left, top = detect_pre_precessing(img, img_size)  # 检测前处理
        y_onnx = self.session_detect.run([self.session_detect.get_outputs()[0].name],
                                          {self.session_detect.get_inputs()[0].name: img})[0]
        outputs = post_precessing(y_onnx, r, left, top)  # 检测后处理
        for output in outputs:
            if output[4] > 0.7:
                return True
        return False



if __name__ == '__main__':
    detect_path = './weights/plate_detect.onnx'
    rec_path = './weights/plate_rec_color.onnx'
    img = cv2.imread('./imgs/5.jpg')
    # session_detect, session_rec = reload_model(detect_path, rec_path)
    #
    # statr = time.time()
    # result = get_img_plate_color(img, session_detect, session_rec)
    # end = time.time()
    # print('cpu time:', end - statr)

    Onnx_Model = Onnx_Model(detect_path, rec_path)  # 加载模型
    statr = time.time()
    Onnx_Model.get_img_plate_color(img)
    end = time.time()
    print('Warm-up time:', end - statr)
    statr = time.time()
    Onnx_Model.get_img_plate_color(img)
    end = time.time()
    print('GPU1 time:', end - statr)
    statr = time.time()
    Onnx_Model.get_img_plate_color(img)
    end = time.time()
    print('GPU2 time:', end - statr)