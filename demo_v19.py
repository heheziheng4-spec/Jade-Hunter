import math
from panda3d.core import loadPrcFileData
from demo_v18 import RuinsDemo,RuinsBuilder
class AlignedBuilder(RuinsBuilder):
    def asset(self,kind,x,y,z,scale,heading=0):
        if kind=='entry18':kind='entry19';heading=0
        elif kind=='ring18':kind='ring19';scale=(9,9,9);heading=0;z=.09
        elif kind=='ancient_tree':kind='tree18';scale=(15,15,20)
        return super().asset(kind,x,y,z,scale,heading)
    def taper(self,name,p,*args,**kwargs):
        if name=='island altar' and p[0]>0:return self.root.attachNewNode('removed ring plinth')
        return super().taper(name,p,*args,**kwargs)
    def box(self,name,p,s,c=(.28,.18,.10),parent=None):
        if name in ('south gate wall','outer earth wall'):
            horizontal=s[0]>s[1];length=max(s[0],s[1]);count=math.ceil(length/4)
            for i in range(count):
                offset=-length/2+(i+.5)*length/count
                self.asset('wall19',p[0]+(offset if horizontal else 0),p[1]+(0 if horizontal else offset),p[2]-s[2]/2,(length/count*1.04,2.8,s[2]/.3635),0 if horizontal else 90)
            return self.root.attachNewNode('continuous stone wall')
        if name=='bridge posts' and p[0]>43:return self.root.attachNewNode('replaced bridge post')
        return super().box(name,p,s,c,parent)
    def tree(self,x,y,z=None,s=1,parent=None):
        if math.hypot(x-76,y)<10:return
        return super().tree(x,y,z,s,parent)
    def place(self,kind,x,y,z,size,heading=0):
        if kind=='column' and y==55:
            node=self.asset('border19',x,y,z,(size*1.25,size*.8,size*3.4),0)
            return node
        return super().place(kind,x,y,z,size,heading)
class AlignedDemo(RuinsDemo):
    world_builder=AlignedBuilder
    def world(self):
        super().world()
        for side in (-1,1):
            for i in range(8):
                self.builder.asset('fence16',47+i*3.1,side*2.65,.1,(3.35,1.3,3.4),0)
if __name__=='__main__':
    loadPrcFileData('','window-title Sandlight 0.19 | Aligned Ruins')
    AlignedDemo().run()
