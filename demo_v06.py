"""Sacred tree passage, river freight and artisan markets."""
import math
from panda3d.core import ClockObject, LineSegs, TransparencyAttrib, loadPrcFileData
from demo_v05 import SettlementBuilder, SettlementDemo
from world_v03 import floor_height

POINTS = {
    'gateway':((-32.7,36,2.4),'神树之门','前往祭祀侧院'),
    'return_gate':((-18,69.7,6),'浮碑之门','返回神树'),
    'shipping':((-25,10.2,.1),'木船货运','装运 2 材料至东侧收货点'),
    'delivery':((-8,10.2,.1),'河岸收货点','接收船运的 4 粮食'),
    'wares':((-33,45,2.4),'陶器货架','用 1 陶器换取 2 材料'),
    'jadeshop':((-13,45,2.4),'玉石货铺','用 2 材料换取 1 件玉饰'),
}


class RiverBuilder(SettlementBuilder):
    def house(self,x,y,*args,**kwargs):
        if (x,y)==(-39,36):
            self.building('arbor',x,y,12.6,0,9.7,10)
            return
        return super().house(x,y,*args,**kwargs)

    def pillar(self,x,y,h=7,w=1.65,z=None,glow=False,parent=None):
        kind = 'rune' if glow and y in (61,79) else 'column' if y==55 else None
        if not kind:
            return super().pillar(x,y,h,w,z,glow,parent)
        base = floor_height(x,y) if z is None else z
        size=h/(1.645 if kind=='rune' else 1.456)
        self.place(kind,x,y,base,size,0)
        self.obstruction(x,y,size*.7,size*.52,base+h)

    def banner(self,x,y,z=None,parent=None):
        self.place('flag',x,y,floor_height(x,y) if z is None else z,3.6,0)

    def boat(self,x,y,s=1,heading=0):
        if x==-22:
            x,y=-25,14.8
        boat=self.place('ship',x,y,-.12,6*s,heading)
        self.g.boats.append((boat,x,y,-.12))
        return boat

    def canopy(self,x,y,*args,**kwargs):
        if (x,y) in ((-33,48),(-12,48)):
            self.building('shelf' if x==-33 else 'jade',x,y,4.9,0,4.1,3.9)
            return
        return super().canopy(x,y,*args,**kwargs)

    def workshop_pots(self,x,y,z,parent):
        if x not in (-33,-12):
            super().workshop_pots(x,y,z,parent)

    def build(self):
        super().build()
        for x in (-25,-8):
            self.place('bridge',x,10.6,-.3,4.8,90)
        for x,y in ((-41,51),(-36,53),(29,54),(33,-18)):
            self.building('grove',x,y,2.8,35,.55,.55)


class RiverPassDemo(SettlementDemo):
    world_builder=RiverBuilder
    points=POINTS

    def world(self):
        super().world()
        self.freight=-1.
        self.ornaments=0
        self.rings={}
        self.flash={}
        for key,(pos,label,verb) in self.points.items():
            self.add_target(key,pos,label,verb)
            portal=key in ('gateway','return_gate')
            lines=LineSegs()
            lines.setThickness(4 if portal else 2)
            lines.setColor(.43,1,.88,1) if portal else lines.setColor(1,.82,.39,1)
            for i in range(65):
                a=math.tau*i/64
                u,v=math.cos(a),math.sin(a)
                pt=(0,1.05*u,1.55*v) if key=='gateway' else (1.05*u,0,1.55*v) if portal else (.68*u,.68*v,0)
                (lines.moveTo if i==0 else lines.drawTo)(*pt)
            ring=self.effects.attachNewNode(lines.create())
            ring.setPos(pos[0]-(.7 if key=='gateway' else 0),pos[1],pos[2]+(1.62 if portal else .1))
            ring.setLightOff();ring.setShaderOff();ring.setTransparency(TransparencyAttrib.MAlpha)
            self.rings[key]=ring
            self.flash[key]=0

    def interact(self):
        k=self.near
        if k not in self.points or self.dialog or self.preview:
            return super().interact()
        s=self.state
        if k in ('gateway','return_gate'):
            destination='return_gate' if k=='gateway' else 'gateway'
            x,y,z=self.points[destination][0]
            self.player.setPos(x+(.8 if destination=='gateway' else 0),y-.7,z)
            self.vertical=0;self.ground=True;self.near=None
            self.flash[destination]=1
            self.toast='穿过玉光，抵达'+self.points[destination][1]
        elif k=='shipping':
            if self.freight>=0:self.toast='船货已发出。沿南岸向东到收货点领取。'
            elif s.material<2:self.toast='装船需要 2 材料。'
            else:
                s.material-=2;self.freight=0
                self.toast='已装船。木船沿南岸向东航行，抵达后可领取 4 粮食。'
        elif k=='delivery':
            if self.freight<8:self.toast='等待到港。请先到西侧木船装货。' if self.freight<0 else '木船正在驶来。'
            else:
                self.freight=-1;s.food+=4;self.toast='船货已卸下，粮食 +4。'
        elif k=='wares':
            if self.pottery<1:self.toast='先到窑场烧制并领取陶器。'
            else:
                self.pottery-=1;s.material+=2;self.toast='已售出 1 陶器，材料 +2。'
        elif s.material<2:self.toast='交换玉饰需要 2 材料。'
        else:
            s.material-=2;self.ornaments+=1;self.toast=f'已收到玉饰，现有 {self.ornaments} 件。'
        self.flash[k]=1
        self.toasting=5;self.sync_ui();self.save(True)

    def update(self,task):
        result=super().update(task)
        dt=min(ClockObject.getGlobalClock().getDt(),.045)
        if 0<=self.freight<8 and not self.dialog and not self.preview:
            self.freight=min(8,self.freight+dt)
            if self.freight==8:self.save(True)
        self.boats[0][0].setX(-25+17*max(0,self.freight)/8)
        for key,ring in self.rings.items():
            self.flash[key]=max(0,self.flash[key]-dt)
            ring.setScale(1+.055*math.sin(self.t*2.6)+.38*self.flash[key])
            ring.setAlphaScale(.72+.18*math.sin(self.t*3)+.1*self.flash[key])
        return result

    def extra_save_data(self):
        return {'freight':self.freight,'ornaments':self.ornaments}

    def restore_extra_data(self,data):
        self.freight=data.get('freight',-1)
        self.ornaments=data.get('ornaments',0)

    def reset(self):
        self.restore_extra_data({})
        super().reset()


if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.6 | Sacred Tree Passage')
    RiverPassDemo().run()

