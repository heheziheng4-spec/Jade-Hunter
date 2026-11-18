"""Expanded ring islands, wind-driven rice and interactive pottery production."""
import json
import math
import random
import sys
import tempfile
import time
from pathlib import Path
from dataclasses import asdict
from collections import deque
from panda3d.core import Shader, TextNode, Filename, Vec3, TransparencyAttrib
from direct.gui.OnscreenText import OnscreenText
from direct.showbase import ShowBaseGlobal
import main
import demo_v02 as previous
from demo_v02 import RiverDemo
from world_v03 import Builder, floor_height
from geometry import mesh

SAVE = previous.SAVE.parent / 'SandlightDemo03'
SAVE.mkdir(exist_ok=True)
main.SAVE = SAVE
previous.SAVE = SAVE
main.loadPrcFileData('', 'window-title Sandlight 0.3 | Wind and Clay')

ISLANDS = [(-76, 0, '西南星纹祭岛'), (76, 0, '东南观星祭岛'),
           (-68, 87, '西北采石聚落'), (68, 87, '东北山地聚落')]

def on_extension(x, y):
    ring = math.sqrt((x / 83) ** 2 + ((y - 35) / 89) ** 2)
    if .95 < ring < 1.05:
        return True
    if abs(y) < 2.5 and 43 < abs(x) < 81:
        return True
    if abs(x) < 3 and -56 < y < -22:
        return True
    if abs(x) < 2.5 and 97 < y < 126:
        return True
    if -47 < y < -22 and 5 < abs(x) < 32:
        return True
    if -29 < y < -23 and abs(x) < 32:
        return True
    return any((x-a)**2+(y-b)**2 < 15**2 for a,b,_ in ISLANDS)

class ExpandedDemo(RiverDemo):
    def __init__(self):
        self.pottery = 0
        self.kiln_remaining = -1.0
        self.visited_islands = []
        self.rice_count = 0
        super().__init__()
        self.title.setText('沙光 · 风过稻田')

    world_builder = Builder

    def world(self):
        builder = self.world_builder(self)
        builder.build()
        extra = builder.group('outer water and ring islands')
        # Ring-shaped geometry gives the expansion a legible shoreline.
        def annulus(name, rx, ry, inner, outer, z, color):
            verts = []
            for i in range(129):
                a = i * math.tau / 128
                for radius in (inner, outer):
                    verts.append((math.cos(a)*rx*radius, 35+math.sin(a)*ry*radius, z))
            obj = mesh(name, verts, [(i*2, i*2+1, i*2+3, i*2+2) for i in range(128)])
            obj.reparentTo(extra)
            obj.setColor(*color, 1)
            obj.setTwoSided(True)
            return obj
        annulus('outer river', 83, 89, .71, 1.30, -.28, (.26,.46,.47))
        annulus('ring embankment', 83, 89, .94, 1.06, .07, (.47,.43,.27))
        annulus('ring footpath', 83, 89, .965, 1.035, .1, (.72,.60,.37))
        for side in (-1,1):
            builder.box('southern rice island',(side*18.5,-34.5,-.35),(27,25,.9),(.54,.47,.29),extra)
            builder.box('south field access',(side*16,-26,.02),(32,6,.16),(.70,.57,.35),extra)
            builder.box('western eastern bridge',(side*62,0,-.05),(38,5,.3),(.43,.29,.15),extra)
            for x in range(45,82):
                builder.box('cross-river planks',(side*x,0,.11),(.8,5,.08),(.53,.38,.21),extra)
                if x%4==0:
                    for y in (-2.7,2.7):builder.box('bridge posts',(side*x,y,.6),(.18,.18,1.8),(.29,.20,.12),extra)
        builder.box('south causeway',(0,-39,-.05),(6,34,.3),(.70,.57,.35),extra)
        # A continuous descending northern causeway connects the upper terrace to the ring.
        for i in range(56):
            y = 98+i*.5
            z = max(.1, 6-(i+1)*5.9/56)
            builder.box('north descent',(0,y+.25,z-.15),(5,.5,.3),(.66,.51,.31),extra)
        for index,(x,y,label) in enumerate(ISLANDS):
            builder.taper('raised island',(x,y,-3),(32,32,3.1),(.59,.46,.29),1,extra)
            if index<2:
                for j in range(6):
                    a=j*math.tau/6
                    builder.pillar(x+8*math.cos(a),y+8*math.sin(a),4+j%2,1.3,.1,parent=extra)
                builder.taper('island altar',(x,y,.1),(5,5,.7),(.75,.61,.38),1,extra)
            else:
                builder.house(x-6,y+3,base=.1,parent=extra)
                builder.canopy(x+5,y+4,z=.1,parent=extra)
            self.add_target('island'+str(index),(x,y-3,.1),label,'调查遗迹 · 收集当地材料')
        for i in range(35):
            a=i*math.tau/35
            x=83*math.cos(a);y=35+89*math.sin(a)
            if abs(x)<7:continue
            builder.tree(x,y,z=.1,s=.65,parent=extra)
        # Remove ridges inside the new playable islands; the old horizon was too close.
        scenery = builder.groups['07 distant scenery']
        scenery.hide()
        for i in range(26):
            a=i*math.tau/26
            builder.taper('outer mesa',(145*math.cos(a),35+155*math.sin(a),-4),(26,26,25+i%6*5),(.61,.49,.38),.55,extra)
        self.add_target('kiln',(-26,36.5,2.4),'陶窑','添料 / 查看烧制 / 领取陶器')
        self.add_target('pottery_trade',(9,36.5,2.4),'粮仓交换','用 2 陶器换取 4 粮食')
        self.add_target('clay',(-34,33,2.4),'黏土料场','采集一份窑料 +3 材料')
        self.clay_cooldown = 0
        self.make_rice(builder, extra)
        extra.flattenStrong()

    def add_target(self,key,pos,label,verb):
        self.targets[key]=(pos,label,verb)
        text=TextNode(key)
        text.setFont(self.font)
        text.setText(label)
        text.setAlign(TextNode.ACenter)
        node=self.render.attachNewNode(text)
        node.setPos(pos[0],pos[1],pos[2]+2.6)
        node.setScale(.32)
        node.setBillboardPointEye()
        node.setLightOff()
        self.markers[key]=node

    def make_rice(self,builder,extra):
        self.crops.removeNode()
        self.crops=self.render.attachNewNode('curved wind-driven rice')
        rng=random.Random(77)
        vertices=[]
        faces=[]
        plots=[(x,y,3.3) for x in (18,26,34) for y in (-15,-6,3)]
        plots += [(x,y,5) for x in (-24,-12,12,24) for y in (-40,-28)]
        for x,y,radius in plots:
            if y<-22:
                builder.box('new paddy',(x,y,.12),(radius*2,radius*2,.10),(.32,.36,.22),extra)
                builder.box('new paddy water',(x,y,.18),(radius*2-.3,radius*2-.3,.025),(.35,.51,.39),self.water)
                for side in (-1,1):builder.box('new paddy bank',(x+side*radius,y,.21),(.22,radius*2,.25),(.61,.48,.28),extra)
            for i in range(int(radius*radius*12)):
                px=x+rng.uniform(-radius+.2,radius-.2)
                py=y+rng.uniform(-radius+.2,radius-.2)
                height=rng.uniform(.55,1.02)
                self.rice_count+=1
                for leaf in range(5):
                    angle=rng.uniform(0,math.tau)
                    length=height*rng.uniform(.65,1)
                    start=len(vertices)
                    for j in range(5):
                        t=j/4
                        bend=.35*t*t
                        width=.043*math.sin(math.pi*t)+.003
                        cx=px+math.cos(angle)*bend
                        cy=py+math.sin(angle)*bend
                        z=.18+length*(t-.20*t*t)
                        for side in (-1,1):vertices.append((cx-side*math.sin(angle)*width,cy+side*math.cos(angle)*width,z))
                    for j in range(4):faces.append((start+j*2,start+j*2+1,start+j*2+3,start+j*2+2))
        rice=mesh('tapered rice leaf ribbons',vertices,faces)
        rice.reparentTo(self.crops)
        rice.setTwoSided(True)
        shader=Shader.make(Shader.SL_GLSL, '''#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform float wind_time;
uniform float wind_strength;
in vec4 p3d_Vertex;
out vec3 color;
void main() {
 vec4 p=p3d_Vertex;
 float h=max(0.0,p.z-0.18);
 float wave=sin(p.x*.39+p.y*.24-wind_time*1.9);
 float flutter=sin(wind_time*3.1+p.x*2.7+p.y*1.6)*.24;
 p.x+=(wave+flutter)*h*h*wind_strength;
 p.y+=sin(p.x*.25+p.y*.31-wind_time*1.4)*h*h*wind_strength*.4;
 float variation=fract(sin(dot(p3d_Vertex.xy,vec2(12.9898,78.233)))*43758.5);
 color=mix(vec3(.25,.36,.10),vec3(.73,.72,.29),clamp(h*1.2,0.0,1.0))*(.9+variation*.14);
 gl_Position=p3d_ModelViewProjectionMatrix*p;
}''', '''#version 130
in vec3 color;
uniform vec3 rice_light;
out vec4 fragColor;
void main(){ fragColor=vec4(color*rice_light,1.0); }
''')
        self.crops.setShader(shader)
        self.crops.setShaderInput('wind_time',0.0)
        self.crops.setShaderInput('wind_strength',.27)
        self.crops.setShaderInput('rice_light',Vec3(1,1,1))

    def height(self,x,y):
        if abs(x)<2.5 and 98<=y<126:
            return max(.1,6-(int((y-98)*2)+1)*5.9/56)
        if -44.5<x<44.5 and -23<y<98:return floor_height(x,y)
        return .1

    def legal(self,x,y,z):
        central=(-44.5<x<44.5 and -23<y<98 and (y<=56 or abs(x)<37.4))
        if not central and not on_extension(x,y):return False
        if central and 12<y<24 and not any(abs(x-b)<3.5 for b in (-32,0,32)):return False
        for left,right,bottom,top,height in self.obstacles:
            if left-.26<x<right+.26 and bottom-.26<y<top+.26 and z<height:return False
        return self.height(x,y)-z<.4

    def ui(self):
        super().ui()
        self.kiln_label=OnscreenText(text='',font=self.font,pos=(1.48,.66),align=TextNode.ARight,scale=.027,fg=(1,.87,.62,1),mayChange=True)
        self.kiln_label.setText('陶窑等待添料 · 陶器 0')
        for node in self.routepanel.findAllMatches('**/+TextNode'):
            node.hide()
        OnscreenText(parent=self.routepanel,text='扩展路线  /  南门外稻田 → 环水步道 → 四座外围岛屿\n东西桥从聚落两侧通向祭岛。北侧下行步道连接山地聚落。\n西岸陶窑烧陶，氏族粮仓交换粮食。',font=self.font,pos=(0,.25),scale=.038,fg=(1,.87,.62,1))

    def interact(self):
        if self.dialog or self.preview or not self.near:
            return super().interact()
        key=self.near
        if key=='kiln':
            if self.kiln_remaining==0:
                self.pottery+=3
                self.kiln_remaining=-1
                self.toast='开窑取器，获得 3 陶器。前往氏族粮仓可交换粮食。'
            elif self.kiln_remaining>0:self.toast='正在烧制。晴天继续加热，雨天暂时封窑。'
            elif self.phase() in ('rain','flood'):self.toast='雨势太大，等待雨停再点火。'
            elif self.state.material<3:self.toast='需要 3 材料作为泥坯与燃料。附近黏土料场可以采集。'
            else:
                self.state.material-=3
                self.kiln_remaining=20
                self.toast='已装填泥坯和燃料。烧制需要 20 秒，可以继续在附近探索。'
        elif key=='pottery_trade':
            if self.pottery<2:self.toast='粮仓需要 2 陶器，可交换 4 粮食。'
            else:
                self.pottery-=2
                self.state.food+=4
                self.toast='送出 2 陶器，粮仓交付 4 粮食。'
        elif key=='clay':
            if self.clay_cooldown>0:self.toast='采集后需要等待片刻，让工匠整理下一批窑料。'
            else:
                self.state.material+=3
                self.clay_cooldown=30
                self.toast='采集黏土和枯枝，材料 +3。可送到旁边陶窑烧制。'
        elif key.startswith('island'):
            if key in self.visited_islands:self.toast='已记录此地神徽。沿环水步道继续探索其他岛屿。'
            else:
                self.visited_islands.append(key)
                self.state.material+=6
                self.toast='发现古老聚落留下的石料，材料 +6。'
        else:return super().interact()
        self.toasting=6
        self.sync_ui()
        self.save(quiet=True)

    def update(self,task):
        result=super().update(task)
        dt=min(ShowBaseGlobal.globalClock.getDt(),.045)
        rainy=self.phase() in ('rain','flood')
        if not self.dialog and not self.preview:
            self.clay_cooldown=max(0,self.clay_cooldown-dt)
            if self.kiln_remaining>0 and not rainy:
                self.kiln_remaining=max(0,self.kiln_remaining-dt)
                if self.kiln_remaining==0:
                    self.toast='陶窑烧成了。回到窑口按 E 领取陶器。'
                    self.toasting=8
                    self.save(quiet=True)
        burning=self.kiln_remaining>0 and not rainy
        for flame in self.kilnfires:flame.show() if burning else flame.hide()
        for puff,*_ in self.smokepuffs:puff.show() if burning else puff.hide()
        status='雨天封窑' if rainy and self.kiln_remaining>0 else (f'烧制剩余 {math.ceil(self.kiln_remaining)} 秒' if self.kiln_remaining>0 else ('烧成 · 可领取' if self.kiln_remaining==0 else '陶窑等待添料'))
        self.kiln_label.setText(f'{status}  ·  陶器 {self.pottery}')
        self.crops.setShaderInput('wind_time',self.t)
        self.crops.setShaderInput('wind_strength',.62 if rainy else .27)
        self.crops.setShaderInput('rice_light',Vec3(.56,.70,.72) if rainy else Vec3(1,1,1))
        pos=self.player.getPos()
        if on_extension(pos.x,pos.y) and not (-44<pos.x<44 and -23<pos.y<98):self.zone_text.setText('外环 · 稻田与群岛步道')
        return result

    def extra_save_data(self):
        return {}

    def restore_extra_data(self,data):
        pass

    def save_folder(self):
        return SAVE

    def load_paths(self):
        return [self.save_folder()/'save.json',SAVE.parent/'SandlightDemo02'/'save.json']

    def save(self,quiet=False):
        if self.preview:return
        data={'version':3,'village':asdict(self.state),'position':list(self.player.getPos()),'yaw':self.yaw,
              'pottery':self.pottery,'kiln_remaining':self.kiln_remaining,'visited_islands':self.visited_islands,'clay_cooldown':self.clay_cooldown}
        data.update(self.extra_save_data())
        path=self.save_folder()/'save.json'
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf8',dir=path.parent,delete=False) as f:
            temp=Path(f.name)
            json.dump(data,f,ensure_ascii=False,indent=2)
        try:
            for attempt in range(6):
                try:
                    temp.replace(path)
                    break
                except PermissionError:
                    if attempt==5:
                        self.toast='存档暂被占用。请稍后按 F5 保存。';self.toasting=5
                        return
                    time.sleep(.025*(1+attempt))
        finally:
            temp.unlink(missing_ok=True)
        if not quiet:self.toast='旅程与陶窑进度已保存。';self.toasting=4

    def load(self):
        try:
            paths=self.load_paths()
            path=next((p for p in paths if p.exists()),paths[0])
            data=json.loads(path.read_text(encoding='utf8'))
            self.state=main.Village(**data['village'])
            self.player.setPos(*data['position'])
            self.yaw=data['yaw']
            self.pottery=data.get('pottery',0)
            self.kiln_remaining=data.get('kiln_remaining',-1)
            self.visited_islands=data.get('visited_islands',[])
            self.clay_cooldown=data.get('clay_cooldown',0)
            self.restore_extra_data(data)
            self.preview=None;self.ceremony=0;self.dialog=False
            self.overlay.hide();self.routepanel.hide();self.map_open=False
            self.refresh();self.sync_ui()
            self.toast='已恢复旅程和陶窑进度。';self.toasting=4
            if self.state.won or self.state.population<=0:self.end_screen()
        except (OSError,ValueError,KeyError,TypeError):self.toast='尚无可用存档。';self.toasting=4

    def reset(self):
        self.pottery=0;self.kiln_remaining=-1;self.visited_islands=[];self.clay_cooldown=0
        super().reset()

    def reachable_starts(self):
        return [(0,-17)]

    def smoke(self,task):
        self.near='kiln';self.interact()
        assert self.kiln_remaining==20 and self.state.material==1
        self.kiln_remaining=0;self.interact()
        assert self.pottery==3
        self.near='pottery_trade';self.interact()
        assert self.pottery==1 and self.state.food==22
        self.save(True);self.load();assert self.pottery==1
        visited=set(self.reachable_starts());queue=deque(visited)
        while queue:
            x,y=queue.popleft()
            for dx,dy in [(.5,0),(-.5,0),(0,.5),(0,-.5)]:
                p=(x+dx,y+dy)
                if p not in visited and self.legal(*p,self.height(x,y)):
                    visited.add(p);queue.append(p)
        reachable={k:any((x-p[0])**2+(y-p[1])**2<2.6**2 for x,y in visited) for k,(p,_,_) in self.targets.items()}
        assert all(reachable.values()),reachable
        (SAVE/'verification.json').write_text(json.dumps({'reachable':reachable,'walkable_cells':len(visited),'rice_clumps':self.rice_count,'kiln_and_trade':'PASS','save_load':'PASS'},indent=2),encoding='utf8')
        self.reset();self.state.canal=True;self.refresh()
        self.player.setPos(14,-13,.1);self.yaw=-75;self.pitch=14
        self.taskMgr.doMethodLater(3,self.capture_check,'capture')
        return task.done

    def capture_check(self,task):
        self.win.saveScreenshot(Filename.fromOsSpecific(str(SAVE/'rice.png')))
        self.player.setPos(-23,31,2.4);self.yaw=15;self.pitch=10
        self.near='kiln';self.state.material=8;self.interact()
        self.taskMgr.doMethodLater(2,self.finish_check,'finish')
        return task.done

    def finish_check(self,task):
        self.win.saveScreenshot(Filename.fromOsSpecific(str(SAVE/'kiln.png')))
        if self.kiln_remaining > 0:
            self.taskMgr.doMethodLater(1,self.finish_check,'wait-for-real-firing')
            return task.done
        assert self.kiln_remaining == 0
        self.near='kiln'
        self.interact()
        assert self.pottery == 3
        self.near='pottery_trade'
        self.interact()
        assert self.pottery == 1
        self.save(True)
        self.load()
        assert self.pottery == 1 and self.kiln_remaining == -1
        (SAVE/'realtime_kiln_pass.txt').write_text('20 second real-time firing, collect, trade and persistence PASS',encoding='utf8')
        self.userExit()
        return task.done

if __name__=='__main__':
    ExpandedDemo().run()

