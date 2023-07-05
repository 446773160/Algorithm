# -*- coding: utf-8 -*-
"""
 @Time : 2023/6/10 8:58
 @Author : liao.sc
 @File : urls
 @Contact : 446773160@qq.com
"""
from django.urls import path
from . import views

app_name = 'myapp'
urlpatterns = [
    path('login', views.login, name='login'),
    path('page', views.page, name='page'),
    path('search_items', views.search_items, name='search_items'),
    path('delete_plate', views.delete_plate, name='delete_plate'),
    path('add_plate', views.add_plate, name='add_plate'),
]
