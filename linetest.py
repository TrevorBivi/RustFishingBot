class LineIter(object):
    def __init__(self, p1, p2):
        self.line = Line(p1,p2)
        
        if abs(p2[0] - p1[0]) > abs(p2[1] - p1[1]):
            self.dir = 'x'
            self.min = min(p1[0], p2[0])
            self.max = max(p1[0], p2[0])
        else:
            self.dir = 'y'
            self.min = min(p1[1], p2[1])
            self.max = max(p1[1], p2[1])
        self.cur = self.min-1

    def __iter__(self):
        return self

    def __next__(self):
        self.cur += 1
        if self.cur > self.max:
            raise StopIteration
        if self.dir == 'x':
            return self.cur,self.line.fox(self.cur)
        else:
            return self.line.foy(self.cur),self.cur
        
class Line(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        if (p2[1] - p1[1]) == 0:
            self.m = 9999
        else:
            self.m = (p2[0] - p1[0]) / (p2[1] - p1[1])
        self.b = p1[0] - self.m * p1[1]
        
    def fox(self,x):
        return int( (x - self.b)/self.m)

    def foy(self,y):
        return int(self.m * y + self.b)

    def getIter(self):
        return LineIter(self.p1, self.p2)

