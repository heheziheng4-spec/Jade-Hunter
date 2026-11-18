import math,random
from panda3d.core import loadPrcFileData,Shader
from demo_v16 import WildernessDemo
from demo_v08 import Batch
from demo_v14 import IslandDetailBuilder
class ForestBuilder(IslandDetailBuilder):
    def taper(self,name,*args,**kwargs):
        if name=='outer mesa':return self.root.attachNewNode('removed backdrop')
        return super().taper(name,*args,**kwargs)

class ForestDemo(WildernessDemo):
    world_builder=ForestBuilder
    @staticmethod
    def radius(x,y):return math.hypot(x/83,(y-35)/89)
    @staticmethod
    def wild(x,y):return 1.0<ForestDemo.radius(x,y)<1.75
    def height(self,x,y):
        r=self.radius(x,y)
        if self.wild(x,y):return .1+min(1,max(0,(r-1.05)*5))*(.7+.65*math.sin(x*.06)*math.cos(y*.07))
        return super().height(x,y)
    def world(self):
        super().world()
        for name in ['07 distant scenery','rolling wilderness soil','wild grasses','sandstone ridge','far mountain','distant broken lintel']:
            for n in self.render.findAllMatches('**/'+name):n.hide()
        rng=random.Random(1711);terrain=Batch('continuous forest ring');grass=Batch('pale wind grass');flowers=Batch('forest flowers')
        for i in range(240):
            a=i*math.tau/240;b=(i+1)*math.tau/240
            for j in range(16):
                r=1+j*.75/16;s=1+(j+1)*.75/16
                p=[(83*t*math.cos(v),35+89*t*math.sin(v)) for t,v in [(r,a),(s,a),(s,b),(r,b)]]
                q=[(x,y,self.height(x,y)-.025) for x,y in p];c=(.32,.41,.20) if j>2 else (.49,.46,.29)
                terrain.tri(*q[:3],c);terrain.tri(q[0],q[2],q[3],c)
        terrain.finish(self.render)
        for i in range(150):
            a=rng.uniform(0,math.tau);r=rng.uniform(1.17,1.68);x=83*r*math.cos(a);y=35+89*r*math.sin(a);z=self.height(x,y)
            if i%9==0:
                self.builder.asset('ancient_tree',x,y,z,(1,1,rng.uniform(.8,1.3)),rng.uniform(0,360))
            else:self.builder.tree(x,y,z,s=rng.uniform(1.3,2.6))
            self.builder.obstruction(x,y,2,2,z+12)
            for j in range(rng.randint(3,7)):
                xx=x+rng.uniform(-4,4);yy=y+rng.uniform(-4,4);s=rng.uniform(.4,4.8)
                self.builder.asset(rng.choice(['rock1','rock2','rock3','mossrock']),xx,yy,self.height(xx,yy)-.08,(s,s,s),rng.uniform(0,360))
        for i in range(18000):
            a=rng.uniform(0,math.tau);r=rng.uniform(1.09,1.73);x=83*r*math.cos(a);y=35+89*r*math.sin(a);z=self.height(x,y);h=rng.uniform(.2,.65)
            if 1.10<r<1.14:continue
            grass.tri((x-.08,y,z),(x+.08,y,z),(x+.12,y,z+h),(.48,.65,.28))
            if i%10==0:
                flowers.tri((x-.13,y,z+.28),(x+.13,y,z+.28),(x,y+.15,z+.4),(.8,.8,.62) if i%20 else (.51,.55,.86))
        self.forestgrass=grass.finish(self.render);self.forestgrass.setTwoSided(True);flowers.finish(self.render).setTwoSided(True)
        shader=Shader.make(Shader.SL_GLSL,'''#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;uniform float clock;in vec4 p3d_Vertex;in vec4 p3d_Color;out vec4 color;
void main(){vec4 p=p3d_Vertex;p.x+=.10*sin(clock*1.6+p.y*.5+p.x*.3);gl_Position=p3d_ModelViewProjectionMatrix*p;color=p3d_Color;}''','''#version 130
in vec4 color;out vec4 fragColor;void main(){fragColor=color;}''')
        self.forestgrass.setShader(shader);self.forestgrass.setShaderInput('clock',0)
        for x,y in [(-110,30),(105,90),(-45,167),(35,-90)]:
            z=self.height(x,y);self.builder.asset('arch',x,y,z,(6,6,6),0) if False else self.builder.asset('monument',x,y,z,(3,3,3),10)
            for j in range(7):self.builder.asset('rock1',x+j*.9,y-4,self.height(x+j*.9,y-4),(1.4,1.4,.5),j*17)
            person=self.person((.32,.40,.22))[0];person.reparentTo(self.render);person.setPos(x+4,y-3,self.height(x+4,y-3))
            # Stylized deer families share the scene's simple geometric vocabulary.
            for j in range(2):
                xx=x-5+j*2;yy=y-6;zz=self.height(xx,yy)
                self.builder.taper('forest deer',(xx,yy,zz+.7),(.6,1.1,.55),(.43,.31,.18))
                self.builder.taper('deer head',(xx,yy+.5,zz+1.1),(.32,.4,.6),(.48,.36,.22))
                for dx in (-.2,.2):
                    for dy in (-.35,.35):self.builder.beam((xx+dx,yy+dy,zz),(xx+dx,yy+dy,zz+.8),.09)
    def update(self,task):
        result=super().update(task)
        self.forestgrass.setShaderInput('clock',self.t)
        return result
if __name__=='__main__':
    loadPrcFileData('','window-title Sandlight 0.17 | Ring Forest')
    ForestDemo().run()


