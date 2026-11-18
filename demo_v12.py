"""Location-specific replacements from the eight reference views."""
from panda3d.core import loadPrcFileData
from demo_v11 import FrontierBuilder, FrontierDemo
from world_v03 import floor_height


class ReferenceBuilder(FrontierBuilder):
    def pillar(self,x,y,h=7,w=1.65,z=None,glow=False,parent=None):
        base=floor_height(x,y) if z is None else z
        if abs(x)==8 and y==70:
            size=h/1.645
            node=self.place('rune',x,y,base,size,0)
        elif (x,y) in ((-37,29),(-9,40),(39,30)):
            size=h/1.456
            node=self.asset('jadepost',x,y,base-.025,(size,)*3,-90)
        elif (x,y) in ((38,11),(38,23)):
            size=h/2.251
            node=self.asset('facet',x,y,base-.025,(size,)*3,180)
        else:
            return super().pillar(x,y,h,w,z,glow,parent)
        low,high=node.getTightBounds(self.g.render)
        self.obstruction((low.x+high.x)/2,(low.y+high.y)/2,
                         high.x-low.x,high.y-low.y,high.z)
        return node

    def house(self,x,y,w=5,d=4,base=None,grand=False,parent=None):
        if (x,y)!=(24,51):
            return super().house(x,y,w,d,base,grand,parent)
        node=self.asset('newarbor',x,y,2.375,(7.8,)*3,0)
        low,high=node.getTightBounds(self.g.render)
        self.obstruction(x,y,7.1,6.2,high.z)
        return node

    def court_gate(self,sacred):
        node=self.asset('arch',0,90,6.47,(12.4,)*3,-90)
        # Separate pier collisions leave the central portal accessible.
        for x in (-4.7,4.7):
            self.obstruction(x,90,2.6,3.7,18.5)
        return node


class ReferenceDemo(FrontierDemo):
    world_builder=ReferenceBuilder


if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.12 | Stone and Jade')
    ReferenceDemo().run()
