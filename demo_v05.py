"""The ritual terrace, residential tents and workshop woodland."""
import math
import random
from panda3d.core import loadPrcFileData
from demo_v04 import WorkshopBuilder, WorkshopDemo
from world_v03 import floor_height, SAND


class SettlementBuilder(WorkshopBuilder):
    def building(self,kind,x,y,size,heading,width,depth):
        z = floor_height(x,y)
        node = self.place(kind,x,y,z,size,heading)
        self.obstruction(x,y,width,depth,z+size)
        return node

    def house(self,x,y,w=5,d=4,base=None,grand=False,parent=None):
        if grand and y==84:
            if x<0:
                self.building('ruin',x,y,12,85,11,9.7)
            else:
                # The east hall is assembled by ritual_hall and revealed on repair.
                self.box('east hall plinth',(x,y,6.16),(16,12,.32),SAND,parent)
            return
        if (x,y)==(-39,36):
            self.building('arbor',x,y,7.5,-70,6.2,6.5)
        elif (x,y) in {(19,39),(14,49)}:
            self.building('lodge',x,y,w+.4,180,w*.86,d*.87)
        else:
            super().house(x,y,w,d,base,grand,parent)

    def ritual_hall(self,sacred):
        g=self.g
        g.palace=g.render.attachNewNode('east ritual hall after restoration')
        for dx in (-6,-3,3,6):
            for dy in (-4,4):
                self.box('timber column',(23+dx,84+dy,9.4),(.42,.42,6.5),parent=g.palace)
        self.roof(23,84,12.5,17,12,4.6,g.palace)
        self.roof(23,84,10.4,17.6,12.8,1.35,g.palace)

    def offering_altar(self,sacred):
        g=self.g
        g.offer=self.building('ruin',0,89,12,-90,11.1,9.8)
        self.taper('jade offering rest',(0,84,6),(1.45,1.45,.7),SAND,.9,sacred)
        g.altarjade=self.taper('offered jade',(0,84,6.71),(.65,.65,.9),(.46,.94,.77),1,g.effects)
        g.altarjade.setLightOff()
        self.building('stele',-18,73,5.5,-70,4.2,4.7)

    def tree(self,x,y,z=None,s=1,parent=None):
        # Exclude the discarded old horizon and the water between playable terraces.
        if z is None and (abs(x)>42 or y>98 or (11<y<24)):
            return
        if z is not None and parent is not None and parent.getName().startswith('outer water'):
            x*=1.027
            y=35+(y-35)*1.027
        base=floor_height(x,y) if z is None else z
        heading=(x*37+y*13)%360
        self.place('oak',x,y,base,6.5*s,heading)
        self.obstruction(x,y,.58*s,.58*s,base+3*s)

    def build(self):
        super().build()
        for x,y,size,h in [(7,47,4.3,0),(16,54,4,180)]:
            self.building('lodge',x,y,size,h,size*.86,size*.64)
        for x,y,size,h in [(-13,28,5,165),(-9,54,4.5,0),(35,36,5,-65)]:
            self.building('camp',x,y,size,h,size*.8,size*.78)
        rng=random.Random(1107)
        for cx,cy in [(-40,30),(-42,49),(-18,53),(35,52),(-34,-17),(24,29)]:
            for dx in (-1.25,1.25):
                x=cx+dx+rng.uniform(-.45,.45)
                y=cy+rng.uniform(-1.2,1.2)
                size=rng.uniform(.65,1.12)
                self.building('stump',x,y,size,rng.uniform(0,360),size*.57,size*.57)


class SettlementDemo(WorkshopDemo):
    world_builder=SettlementBuilder


if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.5 | Liangzhu Settlement')
    SettlementDemo().run()
