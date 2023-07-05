from django.test import TestCase

# Create your tests here.
def calculate_fee(parking_time):
    '''
    根据我查到的信息，中国大陆停车场收费标准大致如下：

停车时间不超过15分钟，免费；
停车时间超过15分钟，不足1小时，按1小时计算；
停车时间超过1小时，不足24小时，按每小时收费；
停车时间超过24小时，按每天收费。
假设每小时收费5元，每天收费50元，那么一个可能的函数如下：
    :param parking_time:
    :return:
    '''
    # parking_time is the parking time in seconds
    # return the fee in yuan
    if parking_time <= 15 * 60: # less than 15 minutes
        return 0
    elif parking_time <= 60 * 60: # less than 1 hour
        return 5
    else: # more than 1 hour
        hours = parking_time // (60 * 60) # integer division
        if parking_time % (60 * 60) > 0: # remainder
            hours += 1 # round up to the next hour
        if hours <= 24: # less than 24 hours
            return hours * 5
        else: # more than 24 hours
            days = hours // 24 # integer division
            if hours % 24 > 0: # remainder
                days += 1 # round up to the next day
            return days * 50


if __name__ == '__main__':
    # test cases
    test_times = [10 * 60, 20 * 60, 30 * 60, 2 * 60 * 60,
                  10 * 60 * 60, 23 * 60 * 60,
                  24 * 60 * 60, 25 * 60 * 60,
                  48 * 60 * 60, 50 * 60 * 60]
    # expected results
    test_results = [0, 5, 5, 10,
                    50, 115,
                    50, 100,
                    100, 150]
    # loop through the test cases and compare the results
    for i in range(len(test_times)):
        fee = calculate_fee(test_times[i])
        print("Parking time: {} seconds, Fee: {} yuan".format(test_times[i], fee))
        if fee == test_results[i]:
            print("Correct!")
        else:
            print("Wrong! Expected: {} yuan".format(test_results[i]))