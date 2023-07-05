from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.core.paginator import Paginator, EmptyPage
from .models import ParkingLot
from django.db.models import Q
import json


def process_time_string(time_list):
    result = []
    if time_list is None:
        return None
    for time_string in time_list:
        # 将时间字符串转换为 datetime 对象)
        # 将 datetime 对象格式化为想要的时间字符串格式
        if time_string['entry_time'] is not None:
            time_string['entry_time'] =  time_string['entry_time'].strftime('%Y-%m-%d %H:%M:%S')
        if time_string['exit_time'] is not None:
            time_string['exit_time'] = time_string['exit_time'].strftime('%Y-%m-%d %H:%M:%S')
        else:
            time_string['exit_time'] = '未离开'
        result.append(time_string)
    return result

class Result:
    def __init__(self, code, msg, data):
        self.code = code
        self.msg = msg
        self.data = data

    def success(self):
        return JsonResponse({
            'code': self.code,
            'msg': self.msg,
            'data': self.data
        })

    def fail(self):
        return JsonResponse({
            'code': self.code,
            'msg': self.msg,
            'data': self.data
        })


@require_http_methods(['GET', 'POST'])
def login(request):
    if request.method == 'POST':
        received_json_data = json.loads(request.body)
        username = received_json_data['username']
        password = received_json_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            return Result(200, '登录成功', None).success()
        else:
            return Result(400, '用户名或密码错误', None).fail()
    else:
        return Result(400, '请求方式错误', None).fail()


@require_http_methods(['GET', 'POST'])
def page(request):
    if request.method == 'GET':
        items_per_page = 10  # 每页显示的项数
        queryset = ParkingLot.objects.all()  # 查询所有的 ParkingLot 记录
        paginator = Paginator(queryset, items_per_page)  # 创建 Paginator 对象
        page_number = request.GET.get('page')  # 获取当前页数，默认为第一页
        if page_number is None:
            page_number = 1
        try:
            page_obj = paginator.page(page_number)  # 获取当前页的记录
        except EmptyPage:
            # 处理页码小于1的情况
            page_data = {
                'error': 'Invalid page number',
            }
            return Result(400, '页码错误', page_data).fail()
        page_data = {
            "page_number": page_obj.number,  # 当前页码
            'has_previous': page_obj.has_previous(),  # 是否有上一页
            'has_next': page_obj.has_next(),  # 是否有下一页
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,  # 上一页页码
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,  # 下一页页码
            'object_list': process_time_string(list(page_obj.object_list.values())),  # 转换为列表形式
            'total': queryset.count()
        }
        return Result(200, '查询成功', page_data).success()
    else:
        return Result(400, '请求方式错误', None).fail()


@require_http_methods(['GET', 'POST'])
def search_items(request):
    plate = request.GET.get('plate')  # 获取客户端传递的车牌号
    if plate is None:
        return Result(400, '车牌号不能为空', None).fail()
    # 构建查询条件
    query = Q(license_plate__icontains=plate) 

    # 执行查询
    parking_lots = list(ParkingLot.objects.filter(query).values())
    parking_lots = process_time_string(parking_lots)

    return Result(200, '查询成功', parking_lots).success()


@require_http_methods(['GET', 'POST'])
def delete_plate(request):
    id = request.GET.get('id')
    try:
        park = ParkingLot.objects.get(id=id)
    except ParkingLot.DoesNotExist:
        return Result(400, '搜索不存在', None).fail()
    park.delete()
    return Result(200, '删除成功', None).success()


@require_http_methods(['GET', 'POST'])
def add_plate(request):
    license_plate = request.GET.get('license_plate')  # 获取车牌号
    entry_time = request.GET.get('entry_time')  # 获取进入时间
    parking_spot = request.GET.get('parking_spot')  # 获取停车位信息
    # 使用 create() 方法添加记录
    try:
        parking_lot = ParkingLot.objects.create(
        license_plate=license_plate,
        entry_time=entry_time,
        parking_spot=parking_spot
        )
        parking_lot.save()
    except Exception as e :
        return Result(400,'添加失败',None).fail()
    
    return Result(200, '添加成功', None).success()
