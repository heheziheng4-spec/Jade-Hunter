"""Natural rock clusters and open-ended boundaries for the existing settlement."""
import math
import random
from panda3d.core import loadPrcFileData
from demo_v14 import IslandDetailDemo


class LandscapeDemo(IslandDetailDemo):
    def world(self):
        super().world()
        rng=random.Random(151114)
        self.landscape_counts={k:0 for k in ('rock1','rock2','rock3','mossrock','fence','hedge')}
        existing=list(self.obstacles)

        def clear(x,y,r):
            z=self.height(x,y)
            if abs(x)<4.5 or (8<y<35 and any(abs(x-b)<4.5 for b in (-32,32))):return False
            if any(math.hypot(x-p[0],y-p[1])<r+2.8 for p,_,_ in self.targets.values()):return False
            if any(l-r<x<rr+r and b-r<y<t+r and z<h for l,rr,b,t,h in existing):return False
            return all(self.legal(x+dx,y+dy,z) and abs(self.height(x+dx,y+dy)-z)<.35
                       for dx,dy in ((0,0),(-r,-r),(-r,r),(r,-r),(r,r)))

        # Interrupted runs delimit yards and rice plots; openings face the paths.
        runs=[('hedge',[(x,-25.5) for x in (-27,-23,-19,19,23,27)],0),
              ('hedge',[(x,-43) for x in (-27,-23,-19,19,23,27)],0),
              ('fence',[(x,31) for x in (-23,-19,-15,15,19,23)],0),
              ('fence',[(35,y) for y in (40,44,48)],90),
              ('hedge',[(-30,y) for y in (35,39,43,47)],90),
              ('fence',[(x,80) for x in (19,23,27)],0)]
        for kind,points,heading in runs:
            for x,y in points:
                if not clear(x,y,1.7):continue
                z=self.height(x,y)
                n=self.builder.asset(kind,x,y,z-.04,(3.2,3.2,3.2),heading)
                low,high=n.getTightBounds(self.render)
                self.obstacles.append((low.x,high.x,low.y,high.y,high.z))
                existing.append(self.obstacles[-1])
                self.landscape_counts[kind]+=1

        # Clusters hug grassy margins and quarry edges, never the central axis.
        patches=[(-36,-12,8,8,True),(35,-12,8,8,True),(-20,6,9,5,True),
                 (19,6,9,5,True),(-37,28,6,4,True),(38,29,5,5,True),
                 (-32,52,6,5,True),(31,55,6,5,True),(-22,64,7,4,True),
                 (23,65,7,4,True),(-31,89,4,5,False),(32,90,4,5,False),
                 (-72,88,7,7,False),(72,88,7,7,True),(-76,5,6,5,False),
                 (76,5,6,5,False),(12,157,4,7,True),(33,158,3,6,True)]
        for cx,cy,rx,ry,moss in patches:
            for cluster in range(6):
                x=cx+rng.uniform(-rx,rx);y=cy+rng.uniform(-ry,ry)
                size=rng.uniform(1.05,2.6)
                if not clear(x,y,size*.85):continue
                # One main boulder and two or three smaller, partially overlapping stones.
                for j in range(rng.randint(2,4)):
                    s=size if j==0 else size*rng.uniform(.28,.65)
                    angle=rng.uniform(0,math.tau)
                    distance=0 if j==0 else size*rng.uniform(.22,.55)
                    xx=x+math.cos(angle)*distance;yy=y+math.sin(angle)*distance
                    kind='mossrock' if moss and (j==0 or rng.random()<.55) else rng.choice(('rock1','rock2','rock3'))
                    z=self.height(xx,yy)-s*.045
                    n=self.builder.asset(kind,xx,yy,z,(s*rng.uniform(.85,1.2),s*rng.uniform(.8,1.15),s*rng.uniform(.8,1.25)),rng.uniform(0,360))
                    n.setP(rng.uniform(-5,5));n.setR(rng.uniform(-6,6))
                    self.landscape_counts[kind]+=1
                # A compact obstacle covers the cluster while preserving passage around it.
                self.builder.obstruction(x,y,size*1.2,size*1.2,self.height(x,y)+size*.48)
        print('LANDSCAPE',self.landscape_counts,flush=True)


if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.15 | Rocks and Village Boundaries')
    LandscapeDemo().run()
