# -*- coding: utf-8 -*-
"""
 @Time : 2023/6/13 14:01
 @Author : liao.sc
 @File : test
 @Contact : 446773160@qq.com
"""

import re
def is_china_license_plate(value):
    pattern_str = "^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼A-Z]{1}[A-Z]{1}[A-Z0-9]{4}[A-Z0-9挂学警港澳]{1}"
    return bool(re.findall(pattern_str, value))

if __name__ == '__main__':
    str = '沪A8888'
    print(is_china_license_plate(str))
