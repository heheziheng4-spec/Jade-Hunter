"""Walkable meadow relief and layered vegetation around the central settlement."""
import math
import random
from panda3d.core import Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter, Vec3, loadPrcFileData
from demo_v07 import IslandDemo

TAU=math.tau


class Batch:
    def __init__(self,name):
        self.data=GeomVertexData(name,GeomVertexFormat.getV3n3c4(),Geom.UHStatic)
        self.v,self.n,self.c=[GeomVertexWriter(self.data,k) for k in ('vertex','normal','color')]
        self.faces=GeomTriangles(Geom.UHStatic)

    def tri(self,a,b,c,color):
        normal=(Vec3(*b)-Vec3(*a)).cross(Vec3(*c)-Vec3(*a))
        normal.normalize()
        start=self.v.getWriteRow()
        for idx,p in enumerate((a,b,c)):
            self.v.addData3(*p);self.n.addData3(normal);self.c.addData4(*(color[idx] if isinstance(color[0],tuple) else color),1)
        self.faces.addVertices(start,start+1,start+2)

    def finish(self,parent):
        geom=Geom(self.data);geom.addPrimitive(self.faces)
        node=GeomNode(self.data.getName());node.addGeom(geom)
        obj=parent.attachNewNode(node);obj.setTwoSided(True)
        return obj


def tint(rgb,v):
    return tuple(min(1,c*v) for c in rgb)


class MeadowDemo(IslandDemo):
    turf=(.245,.43,.17)
    blades=(.36,.51,.19)

    def meadow_relief(self,h):
        return h

    def world(self):
        super().world()
        rng=random.Random(812)
        self.surface={}
        grass=Batch('meadow and worn paths')
        leaves=Batch('river reeds, grass and flowers')
        woods=Batch('needled branches and granite')
        template=self.render.attachNewNode('spruce nursery')
        spruces=[]
        for variant in range(4):
            pine=Batch('spruce')
            for i in range(7):
                a=i*TAU/7;b=(i+1)*TAU/7
                pine.tri((.038*math.cos(a),.038*math.sin(a),0),(.038*math.cos(b),.038*math.sin(b),0),(0,0,.96),(.29,.18,.1))
            for tier in range(9):
                level=.15+tier*.088
                for j in range(11):
                    a=(j+rng.random()*.48+tier*.4)*TAU/11
                    length=(1-level)*rng.uniform(.24,.37)
                    for fan in (-1,0,1):
                        angle=a+fan*.15
                        tip=(length*math.cos(angle),length*math.sin(angle),level-.062+rng.uniform(-.022,.023))
                        for side in (-1,1):
                            mid=angle+side*.24
                            pine.tri((0,0,level+.105),(length*.72*math.cos(mid),length*.72*math.sin(mid),level+.024),tip,tint((.14,.33,.185),rng.uniform(.70,1.23)))
            spruces.append(pine.finish(template))
        strips=[(-42,42,-20,11),(-43,43,34,55),(-26,-9,25,34),(9,26,25,34)]
        obstacles=list(self.obstacles)
        targets=[p for p,_,_ in self.targets.values()]
        for left,right,bottom,top in strips:
            density={}
            for x in range(left,right+1):
                for y in range(bottom,top+1):
                    path=3+.85*math.sin(y*.19)
                    clearance=min(abs(x)-path,abs(y-(3 if bottom<0 else 42)-1.2*math.sin(x*.16))-1.2)
                    if bottom<0 and x>7 and y<8:clearance=-1
                    for lo,hi,by,ty,h in obstacles:
                        clearance=min(clearance,max(lo-x,x-hi,by-y,y-ty)-.45)
                    for px,py,_ in targets:
                        clearance=min(clearance,math.hypot(x-px,y-py)-2)
                    cover=max(0,min(1,clearance*.6))
                    edge=min(x-left,right-x,y-bottom,top-y,3)/3
                    relief=cover*edge*(.18+.16*math.sin(x*.44+y*.16)+.09*(1+math.cos(y*.63-x*.23)))
                    self.surface[x,y]=self.meadow_relief(relief)
                    density[x,y]=cover
            for x in range(left,right):
                for y in range(bottom,top):
                    q=[(x,y),(x+1,y),(x+1,y+1),(x,y+1)]
                    cover=sum(density[p] for p in q)/4
                    if cover<=.01:continue
                    base=super().height(x+.5,y+.5)
                    pts=[(i,j,base+.013+self.surface[i,j]) for i,j in q]
                    grain=.92+.06*math.sin(.48*x+.28*y)+rng.uniform(-.035,.035)
                    colors=[]
                    for i,j in q:
                        blend=density[i,j]*min(1,(i-left)*.48,(right-i)*.48,(j-bottom)*.48,(top-j)*.48)
                        noise=.5+.5*math.sin(i*.51+j*.36)*math.cos(j*.72-i*.19)
                        blend*=.83+.17*noise
                        colors.append(tint(tuple(a+(b-a)*blend for a,b in zip((.59,.46,.29),self.turf)),grain))
                    grass.tri(*pts[:3],colors[:3])
                    grass.tri(pts[0],pts[2],pts[3],[colors[0],colors[2],colors[3]])
                    if rng.random()>cover*.67:continue
                    xx=x+rng.random();yy=y+rng.random();zz=self.height(xx,yy)+.01
                    wet=8<yy<12 or 25<yy<28
                    if getattr(self,'fine_meadow',False):
                        self.flowering_grass(leaves,rng,xx,yy,zz,wet)
                    for j in range(0 if getattr(self,'fine_meadow',False) else 13):
                        a=rng.random()*TAU
                        bx=xx+rng.uniform(-.25,.25);by=yy+rng.uniform(-.25,.25)
                        h=rng.uniform(.16,.56)*(1.85 if wet else 1)
                        dx,dy=.21*math.cos(a),.21*math.sin(a)
                        col=tint(self.blades,rng.uniform(.67,1.25))
                        leaves.tri((bx-dy*.13,by+dx*.13,zz),(bx+dy*.13,by-dx*.13,zz),(bx+dx,by+dy,zz+h),col)
                        if j<3 and not wet and math.sin(x*.42+y*.56)>.74:
                            for k in range(5):
                                t=k*TAU/5
                                leaves.tri((bx+dx,by+dy,zz+h),(bx+dx+.055*math.cos(t),by+dy+.055*math.sin(t),zz+h+.035),(bx+dx+.043*math.cos(t+.9),by+dy+.043*math.sin(t+.9),zz+h+.028),(.99,.74,.29))
                    forest=abs(xx)>34 or (yy>49 and abs(xx)>12) or (yy<-14 and xx<-9)
                    if forest and cover>.93 and rng.random()<.105:
                        tree=self.render.attachNewNode('forest spruce')
                        rng.choice(spruces).instanceTo(tree)
                        tree.setPos(xx,yy,zz-.16);tree.setScale(rng.uniform(3.9,8.7));tree.setH(rng.uniform(0,360))
                        self.obstacles.append((xx-.2,xx+.2,yy-.2,yy+.2,zz+5))
                    elif cover>.8 and rng.random()<(.105 if wet else .024):
                        for k in range(rng.randint(2,5)):
                            sx,sy=xx+rng.uniform(-.5,.5),yy+rng.uniform(-.5,.5)
                            sz=self.height(sx,sy)-.03
                            r=rng.uniform(.16,.60);peak=(sx+r*.17,sy,sz+r*.8)
                            rim=[(sx+r*math.cos(i*TAU/7),sy+r*.78*math.sin(i*TAU/7),sz+r*rng.uniform(.14,.35)) for i in range(7)]
                            for i,b in enumerate(rim):
                                c=rim[(i+1)%7];col=tint((.48,.48,.385),rng.uniform(.82,1.1))
                                woods.tri(b,c,peak,col);woods.tri(b,(sx,sy,sz-r*.65),c,col)
        for batch in (grass,leaves,woods):batch.finish(self.render)
        template.detachNode()

    def height(self,x,y):
        base=super().height(x,y)
        surface=getattr(self,'surface',{})
        i,j=math.floor(x),math.floor(y);u,v=x-i,y-j
        a=surface.get((i,j),0);c=surface.get((i+1,j+1),0)
        if u>v:return base+a*(1-u)+surface.get((i+1,j),0)*(u-v)+c*v
        return base+a*(1-v)+surface.get((i,j+1),0)*(v-u)+c*u


if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.8 | Riverside Meadows')
    MeadowDemo().run()

