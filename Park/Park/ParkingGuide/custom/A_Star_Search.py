from queue import PriorityQueue
import sys
sys.path.append("/home/liaosc/project/pythonProject/Park/ParkingGuide/custom")
from structure.graph import *

def heuristic(start, end):

    return abs(end[0] - start[0]) + abs(end[1] - start[1])

def resolvePath(came_from:dict, goal):
    """根据父节点字典，解析出路径

    Args:
        came_from (dict): 父节点字典
        goal (_type_): 终点

    Returns:
        list: 路径
    """
    path = []
    current = goal
    while current:
        path.append(current)
        current = came_from[current]
    return path[::-1]

def a_start_search(graph:Graph, start, goal):
    """A*算法搜索最短路径

    Args:
        graph (_type_): 图，二维矩阵
        start (_type_): 起点
        goal (_type_): 终点
    """
    # 优先级队列 每次取出代价最低的节点
    frontier = PriorityQueue()
    frontier.put((0, start))
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0

    while not frontier.empty():
        # 取出优先级最高的节点
        current = frontier.get()[1]
        

        # 如果当前节点是目标节点，结束循环
        if current == goal:
            break
        
        l = graph.neighbors(current)
        # 遍历当前节点的所有邻居
        for next in l:
            # 计算从起点到邻居的花费，即当前节点的花费加上当前节点到邻居的花费（如果是网格则当前节点到邻居的花费就是1）
            new_cost = cost_so_far[current] + 1
            # 如果当前的节点没有被探测过且花费比之前的小，则将其加入到优先级队列中
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                # 更新花费字典
                cost_so_far[next] = new_cost
                # 计算优先级
                priority = new_cost + heuristic(goal, next)
                # 更新优先级队列
                frontier.put((priority, next))
                # 更新父节点字典
                came_from[next] = current
    
    if goal not in came_from:
        print(f"can not find path to {goal}")
        return None
    else:
        # print(f"find path to {goal}")
        return resolvePath(came_from, goal)