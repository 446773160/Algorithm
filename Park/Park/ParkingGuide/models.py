from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone

class ParkingLot(models.Model):
    id = models.AutoField(primary_key=True)  # 自增主键
    license_plate = models.CharField(max_length=10)  # 车牌号
    entry_time = models.DateTimeField(default=timezone.now,editable=False)  # 进入时间
    exit_time = models.DateTimeField(null=True, blank=True)  # 离开时间
    fee = models.DecimalField(max_digits=8, decimal_places=2, null=True)  # 费用
    parking_spot = models.CharField(max_length=20)  # 停车位信息

    class Meta:
        db_table = 'parking_lot'
        verbose_name = '停车场'
        verbose_name_plural = verbose_name
