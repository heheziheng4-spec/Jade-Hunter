"""Connected field boundaries, quarry boulders and northern/southern wilderness."""
import math,random
from panda3d.core import loadPrcFileData,PointLight
from demo_v14 import IslandDetailDemo
from demo_v08 import Batch
from geometry import mesh

class WildernessDemo(IslandDetailDemo):
    @staticmethod
    def wild(x,y):
        return (-116<y<-54 or 124<y<213) and abs(x)<min(34,3+abs(y-(-54 if y<0 else 124))*.85)

    def height(self,x,y):
        if self.wild(x,y):
            distance=abs(y-(-54 if y<0 else 124))
            blend=min(1,max(0,(distance-5)/18))
            return .1+blend*(.65+.55*math.sin(x*.12+y*.065)*math.cos(y*.08))*(min(1,abs(x)/7))
        return super().height(x,y)

    def legal(self,x,y,z):
        if self.wild(x,y) and z<10:
            return self.height(x,y)-z<.4 and not any(l-.26<x<r+.26 and b-.26<y<t+.26 and z<h for l,r,b,t,h in self.obstacles)
        return super().legal(x,y,z)

    def world(self):
        super().world()
        rng=random.Random(161114)
        self.sunorb.setPos(-125,112,75)
        self.sunorb.setScale(.62)
        self.sunpath.setPos(-125,112,75);self.sunpath.lookAt(0,35,0)
        self.layout_stats={'fence':0,'rocks':0}
        # Long axes have been aligned in the imported models; adjacent ends overlap.
        def fence_run(kind,a,b):
            length=math.dist(a,b);count=max(1,round(length/3.4));step=length/count
            heading=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
            for i in range(count):
                t=(i+.5)/count;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
                z=self.height(x,y)
                if any(math.hypot(x-p[0],y-p[1])<2 for p,_,_ in self.targets.values()):continue
                self.builder.asset(kind,x,y,z-.035,(step*1.27,1.4,3.4 if kind=='fence16' else 2.2),heading)
                self.builder.obstruction(x,y,step if abs(b[0]-a[0])>abs(b[1]-a[1]) else .45,
                                         .45 if abs(b[0]-a[0])>abs(b[1]-a[1]) else step,z+1.1)
                self.layout_stats['fence']+=1
        for side in (-1,1):
            lo,hi=sorted((side*5,side*32))
            for y in (-47.6,-23.7):fence_run('hedge16',(lo,y),(hi,y))
            # An entrance in each side connects the field lanes to the outer walk.
            for x in (lo,hi):
                for ya,yb in [(-47.6,-38),(-34,-29.5)]:fence_run('hedge16',(x,ya),(x,yb))
        # Riverbank runs follow the water, leaving bridges and landing stages open.
        for y in (11.2,24.3):
            for lo,hi in [(-44,-37),(-27,-6),(6,27),(37,44)]:
                fence_run('fence16',(lo,y),(hi,y))
        for a,b in [((-28,51),(-17,51)),((17,58),(34,58)),((34,45),(34,54))]:
            fence_run('hedge16',a,b)

        def rock(kind,x,y,s,collision=True):
            z=self.height(x,y)
            n=self.builder.asset(kind,x,y,z-s*.035,(s,s*rng.uniform(.85,1.1),s*rng.uniform(.95,1.35)),rng.uniform(0,360))
            n.setP(rng.uniform(-4,4));n.setR(rng.uniform(-5,5))
            if collision:
                lo,hi=n.getTightBounds(self.render)
                self.obstacles.append((lo.x,hi.x,lo.y,hi.y,hi.z))
            self.layout_stats['rocks']+=1
        def available(x,y,s):
            z=self.height(x,y);r=s*.7
            return abs(x)>5 and all(self.legal(x+dx,y+dy,z) for dx,dy in [(0,0),(-r,-r),(r,r),(-r,r),(r,-r)]) and not any(math.hypot(x-p[0],y-p[1])<r+2.8 for p,_,_ in self.targets.values())
        # Anchor boulders are several metres wide, framed by much smaller chips.
        for x,y,s,k in [(-81,92,7,'rock2'),(-66,97,6,'rock3'),(-79,81,5,'rock1'),
                         (-62,82,4.5,'mossrock'),(-34,50,5,'mossrock'),(30,64,5,'rock2'),
                         (-29,-12,4.5,'rock3'),(39,4,4,'mossrock')]:
            if available(x,y,s):rock(k,x,y,s)
        for cx,cy,rx,ry in [(-72,88,12,11),(-34,-10,8,9),(34,-8,7,9),(-29,46,10,9),(30,48,10,10),(-24,83,9,10),(26,85,9,10)]:
            for j in range(25):
                x=cx+rng.uniform(-rx,rx);y=cy+rng.uniform(-ry,ry);s=rng.choice([.45,.7,1.2,1.8,3.2])
                if available(x,y,s):rock(rng.choice(['rock1','rock2','rock3','mossrock']),x,y,s)
        for kind,x,y,size in [('rock2',-79,77,6.5),('rock3',-71,99,7),('rock1',-59,91,5.5)]:
            rock(kind,x,y,size)
        # Separate connected wilderness areas extend beyond both ends of the old loop.
        ground=Batch('rolling wilderness soil')
        for bottom,top in [(-116,-54),(124,214)]:
            for x in range(-34,34,2):
                for y in range(bottom,top,2):
                    if not self.wild(x+1,y+1):continue
                    pts=[(xx,yy,self.height(xx,yy)-.015) for xx,yy in [(x,y),(x+2,y),(x+2,y+2),(x,y+2)]]
                    c=(.39,.40,.22) if abs(x)>4 else (.55,.42,.27)
                    ground.tri(*pts[:3],c);ground.tri(pts[0],pts[2],pts[3],c)
            for j in range(65):
                x=rng.uniform(-31,31);y=rng.uniform(bottom+6,top-6);s=rng.choice([.6,1.1,2.5,5,7.5])
                if self.wild(x,y) and available(x,y,s):rock(rng.choice(['rock1','rock2','rock3','mossrock']),x,y,s)
            grass=Batch('wild grasses')
            for j in range(1900):
                x=rng.uniform(-33,33);y=rng.uniform(bottom,top)
                if not self.wild(x,y) or abs(x)<4.8:continue
                z=self.height(x,y);h=rng.uniform(.15,.55)
                for dx,dy in [(.07,0),(0,.07)]:
                    grass.tri((x-dx,y-dy,z),(x+dx,y+dy,z),(x+.09,y+.03,z+h),(.32,.42,.17))
            grass.finish(self.render).setTwoSided(True)
        ground.finish(self.render)
        # Jagged earthen skirts cover the straight terrace fascias between stairs.
        for y,top,base,spans in [(56,6,2.4,[(-37,-8),(8,37)]),(24,2.4,.02,[(-44,-37),(-27,-5),(5,27),(37,44)])]:
            for left,right in spans:
                vertices=[];faces=[];count=math.ceil((right-left)/1.7)
                for i in range(count+1):
                    x=left+(right-left)*i/count
                    vertices.extend([(x,y+.12,top+.025),(x,y-1-rng.random()*.7,base+(top-base)*rng.uniform(.35,.65)),(x,y-2.4-rng.random()*.9,base-.04)])
                for i in range(count):
                    for row in range(2):
                        a=i*3+row;faces.extend([(a,a+3,a+1),(a+1,a+3,a+4)])
                n=mesh('eroded earthen terrace',vertices,faces);n.reparentTo(self.render);n.setColor(.54,.39,.24,1);n.setTwoSided(True)
                # Keep walking above the visual skirt on the original platforms.
        for n in self.render.findAllMatches('**/hearth ring'):n.hide()
        self.flame.hide()
        self.builder.asset('logs',0,0,.08,(2.15,2.15,2.15),20)
        self.living_flames=[]
        for i in range(9):
            n=self.builder.taper('wood fire tongue',(0,0,.45),(.3,.3,1),(1,.35,.04),0,self.effects);n.setLightOff()
            self.living_flames.append(n)
        light=PointLight('warm wood fire');light.setColor((1,.42,.09,1));light.setAttenuation((1,0,.25))
        self.firelight=self.render.attachNewNode(light);self.firelight.setPos(0,0,1.2)
        print('LAYOUT16',self.layout_stats,flush=True)

    def update(self,task):
        result=super().update(task)
        self.flame.hide()
        for i,n in enumerate(self.living_flames):
            flicker=.7+.3*math.sin(self.t*9+i*2.4)
            n.setPos(.45*math.cos(i*2.4),.4*math.sin(i*2.4),.35)
            n.setScale(.20+flicker*.15,.20+flicker*.15,.45+flicker*(.7 if i else 1.2))
        return result

if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.16 | Wilderness and Riverbanks')
    WildernessDemo().run()
