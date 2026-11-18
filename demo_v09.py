"""Quarry and stone-working route under low afternoon light."""
import math
import random
from panda3d.core import (CardMaker, ClockObject, ColorBlendAttrib, LineSegs,
                          PNMImage, Texture, TransparencyAttrib, loadPrcFileData)
from demo_v02 import PALETTES
from demo_v07 import IslandBuilder
from demo_v08 import MeadowDemo
from world_v03 import floor_height


class QuarryBuilder(IslandBuilder):
    def pillar(self,x,y,h=7,w=1.65,z=None,glow=False,parent=None):
        if y in (-21,70,90) or (x,y) in ((-37,29),(-9,40),(39,30)):
            base=floor_height(x,y) if z is None else z
            self.place('idol',x,y,base,h/2.312,-90)
            self.obstruction(x,y,h*.38,h*.34,base+h)
            return
        super().pillar(x,y,h,w,z,glow,parent)

    def canopy(self,x,y,*args,**kwargs):
        if (x,y)==(-20,37):
            self.building('mason',x,y,5.9,-90,4.8,4.8)
            return
        super().canopy(x,y,*args,**kwargs)

    def workshop_pots(self,x,y,z,parent):
        if (x,y)!=(-20,37):
            super().workshop_pots(x,y,z,parent)

    def house(self,x,y,*args,**kwargs):
        if (x,y)==(-74,90):
            self.place('mason',x,y,.1,6.4,-90)
            self.obstruction(x,y,5.5,5.4,6.2)
            return
        return super().house(x,y,*args,**kwargs)

    def taper(self,name,p,s,*args,**kwargs):
        if name=='jade boulder':
            return self.place('schist',*p,s[1],(p[0]*31)%360)
        return super().taper(name,p,s,*args,**kwargs)

    def build(self):
        super().build()
        rng=random.Random(911)
        for x,y,size in [(-66,92,5.4),(-61,85,3.1),(-40,46,3.3)]:
            z=.1 if x<-50 else floor_height(x,y)
            self.place('outcrop',x,y,z,size,rng.uniform(0,360))
            self.obstruction(x,y,size*.78,size*.78,z+size*.7)
        for cx,cy in [(-66,94),(-60,84),(-72,81),(-17,32),(36,51),(-38,-16)]:
            for i in range(5):
                x=cx+rng.uniform(-1.7,1.7);y=cy+rng.uniform(-1,1)
                z=.1 if x<-50 else floor_height(x,y)
                size=rng.uniform(.48,1.25)
                self.place('schist',x,y,z,size,rng.randrange(360))
                self.obstruction(x,y,size*.67,size*.66,z+size*.5)


class QuarryDemo(MeadowDemo):
    world_builder=QuarryBuilder
    turf=(.225,.395,.345)
    blades=(.30,.47,.385)
    weather_palettes=dict(PALETTES,calm=((.99,.797,.51),(1.18,.91,.62),(.41,.41,.46),.009),
                          recovery=((.91,.78,.57),(1.08,.91,.69),(.42,.45,.46),.009))

    def meadow_relief(self,h):
        # Smooth shoulders between 18 cm grassy benches; the walkable mesh uses the same samples.
        level,frac=divmod(h*6.5,1)
        t=max(0,min(1,(frac-.24)/.52))
        return .18*(level+t*t*(3-2*t))

    def world(self):
        super().world()
        self.ore=0
        self.quarry_day=-1
        self.add_target('cutrock',(-66,88.6,.1),'西北青石矿脉','采青石 · 每日一批')
        self.add_target('dress',(-20,33.5,2.4),'石匠工坊','加工 1 青石换 3 材料')
        self.add_target('dress_north',(-74,86.2,.1),'矿场石匠工坊','加工 1 青石换 3 材料')
        self.sunpath.setHpr(153,-19,0)
        self.sunorb.setPos(-28,148,35)
        self.sky_now=list(self.weather_palettes['calm'][0])
        self.sparks=[]
        self.burst={}
        lines=LineSegs();lines.setThickness(1.7);lines.setColor(1,.93,.69,1)
        for x,z in [(-1,-1),(1,-1),(1,1),(-1,1),(-1,-1)]:
            if x==-1 and z==-1 and lines.getNumVertices()==0:lines.moveTo(x,0,z)
            else:lines.drawTo(x,0,z)
        lines.moveTo(-.42,0,-.28);lines.drawTo(.35,0,-.28);lines.drawTo(.35,0,.36)
        shape=lines.create()
        img=PNMImage(32,32,4)
        for y in range(32):
            for x in range(32):
                img.setXelA(x,y,1,.79,.38,max(0,1-((x-15.5)**2+(y-15.5)**2)/245)**3)
        tex=Texture('amber bloom');tex.load(img)
        card=CardMaker('soft penumbra');card.setFrame(-2.8,2.8,-2.8,2.8)
        halo=self.sunorb.attachNewNode(card.generate())
        halo.setPos(0,.5,0);halo.setScale(17);halo.setTexture(tex)
        halo.setLightOff();halo.setShaderOff();halo.setFogOff();halo.setDepthWrite(False)
        halo.setTransparency(TransparencyAttrib.MAlpha)
        halo.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd,ColorBlendAttrib.OIncomingAlpha,ColorBlendAttrib.OOne))
        halo.setColorScale(1,.86,.6,.85)
        rng=random.Random(909)
        for key,x,y,z in [('cutrock',-66,90,.1),('dress',-20,34.5,2.4),('dress_north',-74,87,.1),('gateL',-6,-21,.1),('gateR',6,-21,.1),('altar',0,84,6),('river',-23,12,.15)]:
            self.burst[key]=0.
            for i in range(12):
                node=self.effects.attachNewNode('drifting sigil')
                node.setBillboardPointEye();node.setLightOff();node.setShaderOff();node.setTransparency(TransparencyAttrib.MAlpha);node.setDepthWrite(False)
                node.attachNewNode(shape)
                glow=node.attachNewNode(card.generate());glow.setTexture(tex);glow.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd,ColorBlendAttrib.OIncomingAlpha,ColorBlendAttrib.OOne))
                self.sparks.append((node,key,x,y,z,rng.uniform(0,6.28),rng.uniform(.45,2.6),rng.uniform(.065,.15)))

    def update(self,task):
        result=super().update(task)
        dt=min(.045,ClockObject.getGlobalClock().getDt())
        for key in self.burst:self.burst[key]=max(0,self.burst[key]-dt)
        rain=.26 if self.phase() in ('rain','flood') else 1.
        for node,key,x,y,z,seed,radius,speed in self.sparks:
            u=(self.t*speed+seed)%1
            a=seed+self.t*.23+u*.9
            strength=self.burst[key]
            node.setPos(x+radius*math.cos(a),y+radius*math.sin(a),z+.25+u*(2.8+strength))
            node.setScale((.035+speed*.29)*(1+strength*.55))
            node.setAlphaScale(math.sin(math.pi*u)*rain*(.68+.32*min(1,strength)))
        return result

    def interact(self):
        key=self.near
        if self.dialog or self.preview or key not in ('cutrock','dress','dress_north'):
            return super().interact()
        success=False
        if key=='cutrock':
            if self.quarry_day==self.state.day:self.toast='今日矿料已收，营火休整后再来。'
            else:
                self.quarry_day=self.state.day;self.ore+=2;success=True
                self.toast=f'采得 2 青石，携带 {self.ore}。可前往岛上的石匠工坊切制。'
        elif self.ore:
            self.ore-=1;self.state.material+=3;success=True
            self.toast=f'石料切制完成，材料 +3，余下 {self.ore} 青石。'
        else:self.toast='缺少青石。西北采石聚落的怪石旁可以采集。'
        if success:self.burst[key]=1.8
        self.cue('work' if success else 'hint','石声回响' if success else '轻提示')
        self.sync_ui();self.save(True)

    def extra_save_data(self):
        return dict(super().extra_save_data(),ore=self.ore,quarry_day=self.quarry_day)

    def restore_extra_data(self,data):
        super().restore_extra_data(data)
        self.ore=data.get('ore',0);self.quarry_day=data.get('quarry_day',-1)


if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.9 | The Stonecutters')
    QuarryDemo().run()

