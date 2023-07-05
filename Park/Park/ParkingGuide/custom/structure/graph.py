import numpy as np

class Graph:
    def __init__(self, g:np.ndarray) -> None:
        self.g = g
        # 记录图的边界值
        self.height, self.width = g.shape
        pass

    # 获取节点的邻居
    def neighbors(self, node):
        # x, y 表示第几行第几列
        # 0 0 0 0 0
        # 0 0 1 0 0 , (1, 2)表示图中的1
        x, y = node
        # 判断是否越界
        if not self.judge(node):
            return []
        
        neighbor = []
        # 右,self.g[y - 1][x] == 0表示该节点可以通行，0表示路，1表示墙壁，大于2表示是停车位，数值表示车位号
        if y - 1 >= 0 and (self.g[x][y - 1] == 0 or self.g[x][y - 1] >= 2):
            neighbor.append((x, y - 1))
        # 上
        if x - 1 >= 0 and (self.g[x - 1][y] == 0 or self.g[x - 1][y] >= 2):
            neighbor.append((x - 1, y))
        # 左
        if y + 1 < self.width and (self.g[x][y + 1] == 0 or self.g[x][y + 1] >= 2):
            neighbor.append((x, y + 1))

        # 下
        if x + 1 < self.height and (self.g[x + 1][y] == 0 or self.g[x + 1][y] >= 2):
            neighbor.append((x + 1, y))
        return neighbor
    
    def getvalue(self, node:tuple):
        x, y = node
        return self.g[x][y]
    
    def judge(self, node:tuple):
        x, y = node
        if x < 0 or x >= self.height or y < 0 or y >= self.width:
            # print(f" {node} out of boudary")
            return False

        return True

    