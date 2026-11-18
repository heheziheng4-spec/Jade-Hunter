import math
from panda3d.core import loadPrcFileData
from demo_v19 import AlignedDemo,AlignedBuilder
from world_v03 import floor_height
class GroundedBuilder(AlignedBuilder):
    def asset(self,kind,x,y,z,scale,heading=0):
        if kind=='wall19':
            return super().asset('wall20',x,y,z,(scale[0],scale[1],scale[2]*.3635/.276),heading)
        if kind=='ring18':return super().asset('ring19',76,0,.06,(9,9,9),-90)
        if kind in ('entry18','entry19') and x<0 and 24<y<60:
            return super().asset('border19',x,y,z,(5.5,3.5,18),0)
        return super().asset(kind,x,y,z,scale,heading)
    def place(self,kind,x,y,z,size,heading=0):
        if kind in ('idol','column') and x<0 and 24<y<60:
            return self.asset('border19',x,y,z,(5.5,3.5,18),0)
        node=super().place(kind,x,y,z,size,heading)
        if kind in ('oak','tree'):
            ground=self.g.height(x,y) if hasattr(self.g,'surface') else floor_height(x,y)
            if abs(x)>44 and y<98:ground=.1
            lo,hi=node.getTightBounds(self.g.render)
            node.setZ(node.getZ()+ground-lo.z-.06)
        return node
    def box(self,name,p,s,c=(.28,.18,.10),parent=None):
        if name=='bridge posts':return self.root.attachNewNode('replaced timber posts')
        return super().box(name,p,s,c,parent)
class GroundedDemo(AlignedDemo):
    world_builder=GroundedBuilder
    def world(self):
        super().world()
        self.markers['island1'].node().setText('')
        self.markers['star_ring'].setPos(76,0,8)
        for side in (-1,1):
            for i in range(9):self.builder.asset('hedge16',-78+i*3.6,side*2.65,.08,(3.9,1.1,1.9),0)
        self.builder.asset('camp20',-73,96,.08,(9,9,9),0)
        self.builder.obstruction(-73,96,7,5,3)
        for x,y,s in [(-80,93,1.1),(-62,94,.85),(-79,79,.6)]:
            self.builder.asset('raw20',x,y,.08,(s,s,s),30)
if __name__=='__main__':
    loadPrcFileData('','window-title Sandlight 0.20 | Grounded Walls')
    GroundedDemo().run()
