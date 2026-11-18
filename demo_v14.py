"""Monumental court structures and furnished floating islands."""
import math
from panda3d.core import loadPrcFileData
from demo_v13 import CourtBuilder, CourtDemo
from sky_temple import image_card


class IslandDetailBuilder(CourtBuilder):
    def asset(self,kind,x,y,z,scale,heading=0):
        if kind=='rail':
            if y not in (76,88):
                return self.instances.attachNewNode('joined railing span')
            y+=4
            scale=(9,12,16)
            super().obstruction(x,y,1.4,12,z+7.5)
        return super().asset(kind,x,y,z,scale,heading)

    def obstruction(self,x,y,w,d,h):
        if abs(x)==12 and w==.55 and d==3.8:
            return
        return super().obstruction(x,y,w,d,h)

    def court_column(self,sacred,x,y,h,j,side):
        size=h/3.0599
        node=self.asset('stone',x,y,6.45,(size,)*3,-90)
        low,high=node.getTightBounds(self.g.render)
        self.obstruction(x,y,high.x-low.x,high.y-low.y,high.z)
        mark=36+(j+(side>0)*2)%6
        rune=image_card(self.g,sacred,f'mark{mark:02}',1.05,1.35,True)
        rune.setPos(x,low.y-.035,6.45+h*.72)

    def cloud_arch(self,root,x,y,z,j):
        size=11 if not j else 7.5
        self.asset('skyarch',x,y+4,z,(size,)*3,90)
        if not j:
            for dx in (-4,4):
                self.obstruction(x+dx,y+4,2.6,3,z+10)

    def cloud_tower(self,root,xx,yy,z,tall,j):
        kind='tower' if tall<9 else 'ancient'
        height=1.6431 if kind=='tower' else 1.7682
        size=(tall+1.7)/height
        # Tower models have a broader base than the previous whitebox.
        node=self.asset(kind,xx,yy,z,(min(4.5,size),min(4.5,size),size),0)
        if not j:self.obstruction(xx,yy,4.2,4.2,z+tall+2)

    def cloud_house(self,root,xx,yy,z):
        self.asset('hut',xx,yy,z,(3.8,)*3,0)
        if z==35:self.obstruction(xx,yy,3.4,3.15,z+2.6)

    def build(self):
        super().build()
        self.asset('hut',24,43.2,2.375,(4.6,)*3,0)
        self.obstruction(24,43.2,4.1,4,5.5)
        self.asset('cloth',19.7,45.2,2.40,(3.5,)*3,90)
        self.obstruction(19.7,45.2,2.8,1.2,3.6)

    def build_city(self):
        super().build_city()
        self.g.monument_glows=[]
        for index,(x,y,z,size) in enumerate([
                (15,145,35,2.8),(30,167,35,2.8),(-25,161,43,3.4),
                (59,173,47,3.4),(-50,193,55,3),(80,163,34,2.6),
                (-16,72,6,2.5),(35,52,2.4,2.1)]):
            self.asset('monument',x,y,z,(size,)*3,0)
            if z<40:self.obstruction(x,y,size*.8,size*.8,z+size*1.4077)
            glow=image_card(self.g,self.g.effects,f'mark{(index*5)%42:02}',.7,.9,True)
            glow.setPos(x,y-size*.52,z+size*.83)
            self.g.monument_glows.append(glow)


class IslandDetailDemo(CourtDemo):
    world_builder=IslandDetailBuilder

    def update(self,task):
        result=super().update(task)
        for i,node in enumerate(self.monument_glows):
            node.setAlphaScale(.75+.25*math.sin(self.t*1.1+i))
        return result


if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.14 | Cloud Monuments')
    IslandDetailDemo().run()
