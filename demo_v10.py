"""沙光 · 云上刻书。谷中的生活刻符唤醒后山日轮。"""
import math
import sys
from direct.gui.DirectGui import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Fog, TextNode, loadPrcFileData
from demo_v09 import QuarryDemo
from demo_v03 import SAVE as PREVIOUS_SAVE
from demo_v08 import Batch, tint
from sky_temple import SolarBuilder, CITY, image_card

# Visual readings invented for this game. Sheet order is preserved in the field journal.
SIGNS = [
    ('水鸟','动物',-6,7),('初芽','植物',3,58),('斑虎','动物',-30,54),
    ('游鱼','动物',-6,10),('垂穗','植物',16,-12),('伏兽','动物',-28,0),
    ('渔网','生活',-19,9),('新枝','植物',-3,62),('角鹿','动物',-30,-16),
    ('屋檐','生活',15,37),('织席','生活',-12,39),('三重浪','水文',6,10),
    ('鸟首','动物',-38,7),('鱼骨','动物',32,11),('蹲兽','动物',-65,83),
    ('泽龟','动物',36,7),('走兽','动物',-32,43),('长足鹿','动物',31,50),
    ('芦丛','植物',22,10),('量杆','生活',-20,31),('弯弓','生活',-13,52),
    ('长羽','动物',22,80),('雁阵','动物',27,150),('俯鸟','动物',73,3),
    ('曲水','水文',-32,18),('叶鞘','植物',10,-18),('陶铎','生活',-26,40),
    ('蜷鸟','动物',-76,-6),('分蘖','植物',-11,-29),('帆影','生活',-14,10),
    ('双涡','水文',32,24),('石耒','生活',-68,90),('弦月','天象',1,73),
    ('船桨','生活',-32,10),('合流','水文',18,149),('种仁','植物',-2,-16),
    ('谷仓','生活',9,43),('神木','植物',-33,39),('日眼','天象',3,68),
    ('展翼','动物',15,158),('抽梢','植物',20,162),('林鹿','动物',29,158)
]

def sign_key(i):
    return f'mark{i:02}'

class SkyDemo(QuarryDemo):
    world_builder=SolarBuilder
    fine_meadow=True
    turf=(.26,.425,.36)
    blades=(.32,.54,.39)

    def __init__(self):
        self.found=set()
        self.awake=False
        self.seal_complete=False
        self.journal_open=False
        self.light_pulse=0.
        self.crossing=0.
        self.ink_time=0.
        super().__init__()
        self.title.setText('沙光良渚 · 云上刻书')
        if '--altar' in sys.argv and '--load' not in sys.argv:
            self.player.setPos(0,55,2.4)
            self.yaw=0;self.pitch=5
        self.toast='北台日轮沉睡。走近金色刻符按 E 拓印，集齐任意三枚即可登云。按 G 查阅纹谱。'
        self.toasting=14

    def height(self,x,y):
        if math.hypot(x-CITY[0],y-CITY[1])<20:
            return 35.225 if math.hypot(x-22,y-155)<3.7 else 35.
        h=super().height(x,y)
        r=math.hypot(x,y-90)
        if r<9.6:return 6.49 if r<8.55 else 6.32 if r<9.25 else 6.14
        return h

    def flowering_grass(self,batch,rng,x,y,z,wet):
        # Tapered, curved leaves share a prevailing wind direction. The colour runs
        # from a shaded teal base to sage at the tips, with blooms growing in drifts.
        bloom=not wet and math.sin(.34*x+.21*y)+math.cos(.47*y-.17*x)>.75
        petal=(.98,.95,.79) if math.sin(x*.39)>.05 else (.63,.77,.95) if y>0 else (.93,.59,.27)
        for i in range(21):
            bx=x+rng.uniform(-.43,.43);by=y+rng.uniform(-.43,.43)
            h=rng.uniform(.12,.42)*(1.5 if wet else 1)
            a=rng.random()*math.tau
            width=rng.uniform(.011,.026)
            wx=math.cos(a)*width;wy=math.sin(a)*width
            dx=.065+.095*math.sin(a);dy=.075*math.cos(a)
            left=(bx-wx,by-wy,z);right=(bx+wx,by+wy,z)
            mid=(bx+.29*dx,by+.29*dy,z+.59*h)
            ml=(mid[0]-.69*wx,mid[1]-.69*wy,mid[2])
            mr=(mid[0]+.69*wx,mid[1]+.69*wy,mid[2])
            tip=(bx+dx,by+dy,z+h)
            root=tint(self.blades,rng.uniform(.60,.90));end=tint(self.blades,rng.uniform(1.12,1.44))
            batch.tri(left,right,mr,[root,root,end]);batch.tri(left,mr,ml,[root,end,end]);batch.tri(ml,mr,tip,end)
            if bloom and i in (3,8,13):
                tx,ty,tz=tip
                for j in range(5):
                    b=a+j*math.tau/5
                    points=[(tx+r*math.cos(b+s),ty+r*math.sin(b+s),tz+lift) for r,s,lift in ((.052,-.45,.02),(.073,0,.029),(.052,.45,.022))]
                    batch.tri(tip,points[0],points[1],petal);batch.tri(tip,points[1],points[2],petal)
                batch.tri((tx-.018,ty-.012,tz+.015),(tx+.018,ty-.012,tz+.015),(tx,ty+.019,tz+.021),(.96,.63,.17))

    def legal(self,x,y,z):
        if z>28 or math.hypot(x-22,y-155)<20:
            return z>=34.7 and math.hypot(x-22,y-155)<17.6 and not any(
                l-.25<x<r+.25 and b-.25<y<t+.25 and z<h for l,r,b,t,h in self.obstacles)
        return super().legal(x,y,z)

    def world(self):
        super().world()
        self.builder.build_city()
        self.add_target('sun_gate',(0,88,6.49),'日轮之门','与日轮共鸣')
        self.add_target('cloud_return',(22,143,35),'云岸归门','返回莫角山')
        self.add_target('cloud_seal',(22,154.5,35.225),'云上刻书台','查阅云城刻书')
        n=image_card(self,self.effects,'disc',3.0,3.0,True)
        n.setPos(22,142.2,36.65)
        self.sign_nodes={}
        self.sign_targets={}
        self.ink=self.effects.attachNewNode('flecks of gold leaf')
        self.ink.hide()
        for j in range(18):
            fleck=self.unit.copyTo(self.ink);fleck.setLightOff();fleck.setShaderOff()
            fleck.setColor(1,.82+.14*(j%2),.44,1)
            fleck.setScale(.026,.019,.043)
        occupied=[p for p,_,_ in self.targets.values()]
        for i,(name,theme,cx,cy) in enumerate(SIGNS):
            for j in range(360):
                rad=.43*math.sqrt(j)
                x=round((cx+rad*math.cos(j*2.4))*2)/2
                y=round((cy+rad*math.sin(j*2.4))*2)/2
                z=self.height(x,y)
                if self.legal(x,y,z) and all(math.hypot(x-px,y-py)>2.8 for px,py,_ in occupied):break
            else:raise ValueError('No accessible space for '+name)
            key=sign_key(i)
            pos=(x,y,z)
            self.add_target(key,pos,name,'拓印「'+name+'」')
            self.sign_targets[i]=self.targets[key]
            occupied.append(pos)
            n=self.effects.attachNewNode(key+' carving')
            n.setPos(x,y,z+1.28)
            n.setBillboardPointEye()
            image_card(self,n,key,1.12,1.12,False)
            self.sign_nodes[i]=n
        for index,tree in enumerate(self.render.findAllMatches('**/forest spruce')):
            if tree.getY()<23:continue
            for child in tree.getChildren():child.detachNode()
            kind='grove' if index%4==0 else 'oak'
            holder=tree.attachNewNode('native woodland')
            holder.setScale(.44 if kind=='grove' else 1.08)
            self.builder.models[kind].instanceTo(holder)
        self.cloud_mix=0.
        # A gradient dome stays centred on the viewer. Distance haze still acts
        # on the architecture, so the nearest engravings retain their contrast.
        sky=Batch('graduated firmament')
        rows=[(-1.5,(.98,.81,.60)),(0,(.99,.82,.59)),(.09,(.97,.78,.56)),(.30,(.69,.76,.79)),(.72,(.38,.63,.82)),(1.571,(.23,.51,.73))]
        def vertex(a,e):
            return (295*math.cos(e)*math.sin(a),295*math.cos(e)*math.cos(a),295*math.sin(e))
        for (u,c),(v,d) in zip(rows,rows[1:]):
            for k in range(40):
                a=k*math.tau/40;b=(k+1)*math.tau/40
                p,q,r,s=vertex(a,u),vertex(b,u),vertex(b,v),vertex(a,v)
                sky.tri(p,q,r,[c,c,d]);sky.tri(p,r,s,[c,d,d])
        self.dome=sky.finish(self.render);self.dome.setLightOff();self.dome.setShaderOff();self.dome.setFogOff()
        self.dome.setDepthWrite(False);self.dome.setBin('background',0)

    def ui(self):
        super().ui()
        self.controls_text.setText(self.controls_text.getText()+'   G 刻符纹谱')
        self.journal=DirectFrame(frameColor=(.045,.085,.086,.98),frameSize=(-1.13,1.13,-.89,.91))
        self.journal.hide()
        self.veil=image_card(self,self.aspect2d,'disc',3.9,3.9,True)
        self.veil.hide()
        self.j_title=OnscreenText(parent=self.journal,text='',font=self.font,pos=(0,.79),scale=.057,fg=(1,.89,.60,1),mayChange=True)
        self.j_tiles=[]
        for i,(name,theme,*_) in enumerate(SIGNS):
            x=-.91+(i%6)*.362
            y=.61-(i//6)*.192
            n=image_card(self,self.journal,sign_key(i),.14,.14)
            n.setPos(x,0,y)
            label=OnscreenText(parent=self.journal,text=name+' · '+theme,font=self.font,pos=(x,y-.096),scale=.031,fg=(.89,.87,.73,1))
            self.j_tiles.append((n,label))
        OnscreenText(parent=self.journal,text='亮金为已拓印  ·  图名采用游戏意象联想  ·  G / Esc 合卷',font=self.font,pos=(0,-.82),scale=.031,fg=(.81,.87,.79,1))
        self.accept('g',self.toggle_journal)

    def toggle_journal(self):
        if self.dialog and not self.journal_open:return
        self.journal_open=not self.journal_open
        self.dialog=self.journal_open;self.keys.clear()
        if self.journal_open:
            self.j_title.setText(f'良渚刻符纹谱     {len(self.found)} / 42')
            for i,(n,label) in enumerate(self.j_tiles):
                n.setColorScale(*((1,1,1,1) if i in self.found else (.48,.52,.51,.73)))
            self.journal.show()
        else:self.journal.hide()

    def pause(self):
        if self.journal_open:self.toggle_journal()
        else:super().pause()

    def toggle_map(self):
        if self.journal_open:self.toggle_journal()
        super().toggle_map()

    def apply_collection(self):
        for i,n in self.sign_nodes.items():
            key=sign_key(i)
            if i in self.found:
                n.hide();self.markers[key].hide();self.targets.pop(key,None)
            else:
                n.show();self.targets[key]=self.sign_targets[i]

    def extra_save_data(self):
        return dict(super().extra_save_data(),inscriptions=sorted(self.found),solar_awake=self.awake,cloud_seal=self.seal_complete)

    def save_folder(self):
        folder=PREVIOUS_SAVE.parent/'SandlightDemo10'
        folder.mkdir(exist_ok=True)
        return folder

    def load_paths(self):
        return [self.save_folder()/'save.json',PREVIOUS_SAVE/'save.json',PREVIOUS_SAVE.parent/'SandlightDemo02'/'save.json']

    def reachable_starts(self):
        # The second connected component is entered via the tested solar gate.
        return super().reachable_starts()+[(22,144)]

    def smoke(self,task):
        for key in ['sun_gate','mark01','mark07','mark38','sun_gate','sun_gate']:
            self.player.setPos(*self.targets[key][0]);self.near=key;self.interact()
        assert self.awake and self.player.getZ()==CITY[2]
        self.near='cloud_return';self.interact()
        assert self.player.getY()==87
        self.save(True);self.load()
        assert self.awake and self.found=={1,7,38}
        self.reset()
        return super().smoke(task)

    def restore_extra_data(self,data):
        super().restore_extra_data(data)
        self.found={i for i in data.get('inscriptions',[]) if type(i) is int and 0<=i<len(SIGNS)}
        self.awake=bool(data.get('solar_awake')) and len(self.found)>=3
        self.seal_complete=bool(data.get('cloud_seal')) and len(self.found)==42
        if self.journal_open:self.toggle_journal()
        self.apply_collection()

    def interact(self):
        key=self.near
        if self.dialog or self.preview or not key:return super().interact()
        if key.startswith('mark'):
            i=int(key[4:])
            if i in self.found:return
            self.found.add(i);self.apply_collection()
            px,py,pz=self.sign_targets[i][0]
            self.ink.setPos(px,py,pz+1.2);self.ink.show();self.ink_time=1.
            name,theme,*_=SIGNS[i]
            self.toast=f'已拓印「{name}」 · {theme}   {len(self.found)} / 42'
            if len(self.found)==3:self.toast+='   三纹齐鸣，北台日轮可以唤醒。'
            self.cue('trade','刻纹入谱')
        elif key=='sun_gate' and len(self.found)<3:
            self.toast=f'日轮尚暗，还需拓印 {3-len(self.found)} 枚刻符。长阶两旁有金色刻痕。'
            self.cue('hint','石门低鸣');return
        elif key=='sun_gate' and not self.awake:
            self.awake=True;self.light_pulse=1
            self.toast='日轮苏醒，悬柱应声升起。再按 E 穿过日轮，抵达云城。'
            self.cue('portal','日轮共鸣')
        elif key in ('sun_gate','cloud_return'):
            outward=key=='sun_gate'
            self.player.setPos(*((22,144.2,35) if outward else (0,87,6.49)))
            self.yaw=0 if outward else 180;self.pitch=5;self.vertical=0;self.ground=True
            self.light_pulse=1;self.near=None
            self.crossing=1.
            self.toast='已抵达云城。前方为刻书台，身后为归门。' if outward else '已穿过云海，返回莫角山祭坛。'
            self.cue('portal','云门回声')
        elif key=='cloud_seal':
            if len(self.found)==42:
                self.seal_complete=True;self.light_pulse=1
                self.toast='四十二纹合卷。日轮将谷地的刻痕留在云上。'
                self.cue('portal','四十二纹齐鸣')
            else:
                self.toast=f'云上刻书台映出 {len(self.found)} 道纹。集齐 42 枚，可在此合卷。'
                self.cue('hint','石台回响')
        else:return super().interact()
        self.save(True)

    def update(self,task):
        result=super().update(task)
        dt=min(.045,globalClock.getDt())
        self.light_pulse=max(0,self.light_pulse-dt*.35)
        if self.crossing>0:
            self.crossing=max(0,self.crossing-dt*.9)
            self.veil.show();self.veil.setAlphaScale(self.crossing*.59);self.veil.setScale(2.9-1.8*self.crossing)
            if not self.crossing:self.veil.hide()
        if self.ink_time>0:
            self.ink_time=max(0,self.ink_time-dt*1.35)
            travel=1-self.ink_time
            for j,n in enumerate(self.ink.getChildren()):
                a=j*2.4+travel*2
                r=.19+math.sin(travel*math.pi)*(.26+.08*(j%4))
                n.setPos(r*math.cos(a),r*math.sin(a),travel*(.57+.12*(j%5))-.12)
                n.setScale(.026*self.ink_time,.021*self.ink_time,.052*self.ink_time)
            if not self.ink_time:self.ink.hide()
        x,y,z=self.player.getPos()
        sky=z>29 and y>132
        self.cloud_mix+=(float(sky)-self.cloud_mix)*min(1,dt*1.8)
        wet=self.phase() in ('rain','flood')
        tint=(.56,.67,.70) if wet else (.70,.83,.90)
        self.fog.setMode(Fog.MLinear)
        self.fog.setLinearRange(9 if wet else 24,96 if wet else 176)
        hz=tuple(a+(b-a)*self.cloud_mix for a,b in zip(self.sky_now,tint))
        self.fog.setColor(*hz);self.setBackgroundColor(*hz,1)
        self.dome.setPos(self.camera.getPos())
        weather=.65 if wet else 1.
        self.dome.setColorScale(weather*(1-.32*self.cloud_mix),weather*(1-.03*self.cloud_mix),weather*(1+.46*self.cloud_mix),1)
        if sky:
            self.zone_text.setText('云上 · 悬圃刻书台')
            self.wayfinder.setText('云岸南侧可返回莫角山' if not self.dialog else '')
        elif math.hypot(x,y-90)<11:
            self.zone_text.setText('莫角山 · 日轮神庭')
            if not self.dialog:self.wayfinder.setText('日轮之门 · 已苏醒' if self.awake else f'唤醒日轮 · 拓印 {min(3,len(self.found))} / 3')
        elif self.zone_text.getText() in ('云上 · 悬圃刻书台','莫角山 · 日轮神庭'):
            self.zone_text.setText(self.ui_zone)
        for i,n in self.sign_nodes.items():
            if i in self.found:continue
            px,py,pz=self.sign_targets[i][0]
            if (px-x)**2+(py-y)**2>46**2:n.hide();continue
            n.show();n.setZ(pz+1.35+.14*math.sin(1.7*self.t+i))
            if self.near!=sign_key(i):self.markers[sign_key(i)].hide()
        self.wheel.setR(self.t*(1.9 if self.awake else .6))
        pulse=self.light_pulse
        self.wheel.setScale((1.12 if self.awake else .91)+pulse*.16)
        self.wheel.setAlphaScale((.98 if self.awake else .62)+pulse*.4)
        for j,n in enumerate(self.shafts):
            n.setAlphaScale((.12 if self.awake else .077)+pulse*.12+.035*math.sin(self.t*.7+j))
        for n,z0,phase in self.suspended:
            n.setZ(z0+.24*math.sin(self.t*.55+phase)+(1 if self.awake else 0)+pulse*.3)
        self.skyseal.setR(-self.t*(4 if self.seal_complete else 1))
        self.skyseal.setScale(1.6 if self.seal_complete else 1)
        return result

if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.10 | The Solar Court')
    SkyDemo().run()

