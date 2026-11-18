import math
from panda3d.core import loadPrcFileData
from demo_v17 import ForestDemo,ForestBuilder
from demo_v10 import SkyDemo
from world_v03 import floor_height
class RuinsBuilder(ForestBuilder):
    def place(self,kind,x,y,z,size,heading=0):
        if kind=='column':return self.asset('entry18',x,y,z,(size*.78,)*3,heading)
        return super().place(kind,x,y,z,size,heading)
    def pillar(self,x,y,h=7,w=1.65,z=None,glow=False,parent=None):
        if abs(x)>55 or y<0:
            base=floor_height(x,y) if z is None else z
            node=self.asset('entry18',x,y,base,(w,w,h/1.8582),0)
            self.obstruction(x,y,w,w,base+h);return node
        return super().pillar(x,y,h,w,z,glow,parent)
    def pot(self,x,y,z,s=.55,parent=None):
        return self.asset('vase18',x,y,z,(s*1.5,)*3,0)
    def box(self,name,p,s,c=(.28,.18,.10),parent=None):
        if name=='south gate wall':
            for i in range(10):self.asset('wall18',p[0]-s[0]/2+(i+.5)*s[0]/10,p[1],.1,(4,4,6),45)
            return self.root.attachNewNode('stone wall replacement')
        if name=='collectable wood':return self.root.attachNewNode('replaced supplies')
        return super().box(name,p,s,c,parent)
class RuinsDemo(ForestDemo):
    world_builder=RuinsBuilder
    def height(self,x,y):
        if getattr(self,"cloud_ready",False) and math.hypot(x-22,y-155)<20:return 35.225 if math.hypot(x-22,y-155)<3.7 else 35
        return super().height(x,y)
    def world(self):
        super().world()
        for key,node in self.cache_nodes.items():
            p=self.targets[key][0];n=self.builder.asset('wood18',*p,(1.8,)*3,0);n.wrtReparentTo(node)
        # Landmark treehouse in the northern forest, visible from the cloud terrace.
        self.builder.asset('tree18',-30,166,self.height(-30,166),(18,18,23),0)
        self.builder.obstruction(-30,166,10,10,25)
        for x,y in [(-118,55),(116,48),(-36,-91),(52,165)]:
            self.builder.asset('border18',x,y,self.height(x,y),(9,9,12),20)
        self.builder.asset('ring18',76,0,.8,(6,6,6),90)
        self.add_target('star_ring',(76,-3,.1),'观星石环','共鸣 · 短暂观星')
        for x,y in [(60,82),(74,81),(77,94)]:
            self.builder.asset('hut',x,y,.1,(4.3,)*3,0)
            self.builder.obstruction(x,y,3.8,3.8,4)
            n=self.person((.36,.43,.24))[0];n.reparentTo(self.render);n.setPos(x-2,y-3,.1)
        self.star_time=0;self.cloud_ready=True
    def interact(self):
        if self.near=='star_ring' and not self.dialog:
            self.star_time=5;self.light_pulse=1;self.toast='石环回应了星光。仰望天空，聆听遗址的回声。';self.toasting=5;self.cue('portal','观星石环');return
        return super().interact()
    def update(self,task):
        result=super().update(task)
        if self.star_time>0:
            self.star_time=max(0,self.star_time-.016);self.light_pulse=max(self.light_pulse,.15+.1*math.sin(self.t*3))
        return result
if __name__=='__main__':
    loadPrcFileData('','window-title Sandlight 0.18 | Stone Ring Ruins')
    RuinsDemo().run()
