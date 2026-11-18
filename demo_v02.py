"""Sandlight 0.2: third-person settlement, rising water and ritual architecture."""
import os, sys, math, json, time
from pathlib import Path
from dataclasses import asdict
from collections import deque
import main as legacy
from main import Demo
from rules import Village
from world_v02 import Builder, floor_height, zone_name
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame

SAVE=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'SandlightDemo02'
SAVE.mkdir(parents=True,exist_ok=True)
legacy.SAVE=SAVE
loadPrcFileData('', 'window-title Sandlight 0.2 | River and Ritual\nwin-size 1440 900\nmultisamples 2')

# Sky, direct sun, ambient sky, fog density. Regional color is a small offset;
# the major event always controls weather, water and residents everywhere.
PALETTES={
 'calm':((.77,.73,.54),(1.03,.91,.65),(.45,.45,.35),.006),
 'warning':((.60,.63,.53),(.83,.76,.57),(.40,.44,.39),.009),
 'rain':((.35,.45,.47),(.44,.58,.61),(.36,.43,.44),.014),
 'flood':((.27,.39,.43),(.33,.48,.55),(.32,.40,.42),.017),
 'recovery':((.66,.72,.63),(.85,.93,.72),(.43,.49,.41),.008),
 'ritual':((.89,.65,.33),(1.23,.91,.50),(.52,.43,.29),.007),
 'empty':((.46,.47,.41),(.56,.51,.37),(.32,.34,.30),.014)}
EVENTS={
 'calm':('水泽初居','低地种稻，沿河筑屋。先疏渠，再为雨季留出材料。'),
 'warning':('河水渐涨','第 4 日洪水到来。东水门需要 10 材料加固。'),
 'rain':('长雨将至','窑火暂熄，居民转往高地。检查水门和粮仓。'),
 'flood':('洪水来临','水位上升。高地安全，低地的收成取决于堤坝。'),
 'recovery':('雨歇 · 水退','积水逐渐退去。河滩露玉，恢复生产后登台。'),
 'ritual':('玉礼 · 日光归来','玉光沿神徽柱亮起，聚落的生活重新汇合。'),
 'empty':('聚落沉寂','储粮耗尽，先民离去。重新规划水利与人口。')}

class RiverDemo(Demo):
    weather_palettes=PALETTES
    def __init__(self):
        self.event='';self.event_time=10.;self.preview=None;self.preview_index=-1
        self.sky_now=[.77,.73,.54];self.sun_now=[1.03,.91,.65];self.ambient_now=[.45,.45,.35];self.fog_now=.006
        self.water_level=-.15;self.overflow_level=.1;self.rest_lock=0;self.ui_zone='';self.last_day=0
        super().__init__()
        self.camLens.setNearFar(.12,420);self.distance=8.6;self.pitch=15
        self.toast='欢迎来到沙光。沿南北石径前往营火，与长者交谈。';self.toasting=10
        if '--tour' in sys.argv and not legacy.SMOKE:self.taskMgr.doMethodLater(2,self.start_tour,'tour')

    def light(self):
        self.ambient=AmbientLight('sky fill');self.ambient.setColor((.45,.45,.35,1))
        self.render.setLight(self.render.attachNewNode(self.ambient))
        self.sun=DirectionalLight('low golden sun');self.sun.setColor((1.03,.91,.65,1))
        self.sunpath=self.render.attachNewNode(self.sun);self.sunpath.setHpr(-27,-35,0);self.render.setLight(self.sunpath)
        self.render.setShaderAuto()
        self.fog=Fog('layered river haze');self.fog.setColor(.77,.73,.54);self.fog.setExpDensity(.006);self.render.setFog(self.fog)

    def world(self):Builder(self).build()
    def height(self,x,y):return floor_height(x,y)

    def legal(self,x,y,z):
        if not (-44.5<x<44.5 and -23<y<98):return False
        if y>56 and abs(x)>37.4:return False
        if 12<y<24 and not any(abs(x-b)<3.5 for b in (-32,0,32)):return False
        for lo,hi,b,t,h in self.obstacles:
            if lo-.26<x<hi+.26 and b-.26<y<t+.26 and z<h:return False
        return self.height(x,y)-z<.4

    def ui(self):
        super().ui()
        self.title.setText('沙光 · 水城与玉礼')
        self.zone_text=OnscreenText(text='',font=self.font,pos=(-1.49,.70),align=TextNode.ALeft,scale=.038,fg=(1,.91,.67,1),mayChange=True)
        self.event_text=OnscreenText(text='',font=self.font,pos=(-1.49,.635),align=TextNode.ALeft,scale=.027,fg=(.92,.89,.76,1),mayChange=True)
        self.wayfinder=OnscreenText(text='',font=self.font,pos=(0,-.53),scale=.029,fg=(.91,.94,.79,1),mayChange=True)
        self.controls_text.setText('WASD 移动   Shift 奔跑   空格 跳跃   右键拖动 / 方向键 环视   E 互动\nM 路线图   F6 氛围预览   F5 保存 / F9 读取   R 重开   Esc 暂停')
        self.routepanel=DirectFrame(frameColor=(.10,.15,.13,.96),frameSize=(-1.12,1.12,-.66,.62));self.routepanel.hide()
        OnscreenText(parent=self.routepanel,text='水城行旅图',font=self.font,pos=(0,.48),scale=.065,fg=(1,.86,.58,1))
        OnscreenText(parent=self.routepanel,text='北 ↑\n\n高地  /  莫角山祭坛 · 神徽柱廊 · 礼制殿堂\n                           ↑  仪式长阶  ↑\n中台  /  西侧：百工作坊、陶窑   |   东侧：氏族居所、粮仓\n                           ↑  三座木桥  ↑\n水系  /  西侧码头 ━ 东西向主河道 ━ 东水门\n\n低地  /  西侧：干栏聚落、集市   |   东侧：稻田、水渠、河滩\n                           ↑  南门营火  ↑',font=self.font,pos=(0,.34),scale=.037,fg=(.91,.88,.72,1),align=TextNode.ACenter)
        OnscreenText(parent=self.routepanel,text='大事记：第 2 日预警 → 第 3 日降雨 → 第 4 日洪水 → 第 5–6 日恢复 → 献玉礼成\n在营火按 E 推进一天；地图为路线示意。按 M 或 Esc 返回行走。',font=self.font,pos=(0,-.49),scale=.028,fg=(.77,.84,.73,1))
        self.map_open=False

    def controls(self):
        super().controls();self.accept('m',self.toggle_map);self.accept('f6',self.cycle_preview)

    def toggle_map(self):
        if self.state.won or self.state.population<=0:return
        self.map_open=not self.map_open;self.dialog=self.map_open;self.keys.clear();self.overlay.hide()
        self.routepanel.show() if self.map_open else self.routepanel.hide()

    def pause(self):
        if self.map_open:self.toggle_map();return
        super().pause()
        if self.dialog:self.overlaydetail.setText('低地耕作，西岸制器，北台献玉。\n在营火休整，第 4 日洪水来临。\nF6 可预览天气；再次切回“跟随旅程”继续。')

    def phase(self):
        if self.preview:return self.preview
        s=self.state
        if s.population<=0:return 'empty'
        if s.won:return 'ritual'
        return 'calm' if s.day<2 else 'warning' if s.day==2 else 'rain' if s.day==3 else 'flood' if s.day==4 else 'recovery'

    def cycle_preview(self):
        options=['calm','warning','rain','flood','recovery','ritual',None]
        self.preview_index=(self.preview_index+1)%len(options);self.preview=options[self.preview_index]
        self.refresh();self.toast='氛围预览：'+(EVENTS[self.preview][0]+'（不推进日期，不改变资源）' if self.preview else '跟随旅程');self.toasting=5

    def refresh(self):
        phase=self.phase()
        if phase!=self.event:self.event=phase;self.event_time=0
        s=self.state
        for node,show in [(self.water,s.canal),(self.canalwater,s.canal),(self.crops,s.canal),(self.blockage,not s.canal),(self.damroot,s.dam),(self.jadelight,s.day>=4 and not s.jade and not s.won),(self.palace,s.shrine),(self.altarjade,s.won or self.preview=='ritual')]:
            node.show() if show else node.hide()
        for key,node in self.cache_nodes.items():node.hide() if key in s.caches else node.show()
        for r in self.runes:r.setColorScale((1.35,1.2,.8,1) if phase=='ritual' else ((.85,.77,.52,1) if s.shrine else (.28,.30,.22,1)))
        rainy=phase in ('rain','flood');self.rain.show() if rainy else self.rain.hide()
        self.sunorb.hide() if rainy else self.sunorb.show()
        for p in self.kilnfires:p.hide() if rainy else p.show()
        for i,(npc,parts) in enumerate(self.npcs):
            home=self.resident_homes[i]
            if rainy and home[1]<24 and i!=0:npc.setPos(11+(i%3)*1.8,36+(i//3)*2,2.4)
            elif phase=='ritual' and i!=0:npc.setPos((-1 if i%2 else 1)*(3.8+(i%3)*.6),77+(i//2)*1.2,6)
            else:npc.setPos(*home)
        if hasattr(self,'event_text'):self.event_text.setText(('预览 · ' if self.preview else '')+EVENTS[phase][0]+'  /  '+EVENTS[phase][1])

    def interact(self):
        if self.dialog or not self.near:return
        if self.preview:
            self.toast='当前为氛围预览。按 F6 切回“跟随旅程”后可以继续互动。';self.toasting=5;return
        if self.near=='rest' and self.rest_lock>0:
            self.toast='正在休整，请稍候再推进下一日。';self.toasting=2;return
        key=self.near;super().interact()
        if key=='rest':self.rest_lock=2.5
        if key=='altar' and self.state.shrine:
            self.toast='高台修复，礼制殿堂与柱廊重新亮起。' if not self.state.won else '玉光苏醒。水城的先民在高台共同观礼。'
        self.sync_ui()

    def sync_ui(self):
        super().sync_ui()
        if hasattr(self,'event_text'):self.event_text.setText(('预览 · ' if self.preview else '')+EVENTS[self.phase()][0]+'  /  '+EVENTS[self.phase()][1])

    def reset(self):
        self.preview=None;self.preview_index=-1;self.rest_lock=0;self.map_open=False
        self.routepanel.hide();super().reset();self.player.setPos(0,-17,.1);self.pitch=15;self.distance=8.6

    def save(self,quiet=False):
        if self.preview:
            if not quiet:self.toast='预览期间不覆盖旅程存档。';self.toasting=3
            return
        super().save(quiet)

    def load(self):
        self.preview=None;self.preview_index=-1;self.ceremony=0;self.rest_lock=0
        self.map_open=False;self.routepanel.hide();super().load()
        p=self.player.getPos()
        if not self.legal(p.x,p.y,p.z):self.player.setPos(0,-17,.1)

    def objective_key(self):
        s=self.state
        if not s.greeted:return 'elder'
        if not s.canal:return 'canal'
        if s.day<4 and not s.dam:
            if s.material>=10:return 'dam'
            return next((k for k in self.cache_nodes if k not in s.caches),'rest')
        if s.day<4:return 'rest'
        if not s.jade and not s.won:return 'jade'
        if s.food<10:return 'rest'
        if not s.shrine and s.material<12:return next((k for k in self.cache_nodes if k not in s.caches),'rest')
        return 'altar'

    def update(self,task):
        result=super().update(task);dt=min(globalClock.getDt(),.045)
        self.rest_lock=max(0,self.rest_lock-dt);self.event_time+=dt
        phase=self.phase();sky,sun,amb,density=self.weather_palettes[phase]
        pos=self.player.getPos();zone=zone_name(pos.x,pos.y)
        if zone!=self.ui_zone:self.ui_zone=zone;self.zone_text.setText(zone)
        # Warmer high ground, cooler humid river/craft area, with a smooth transition.
        tint=(.045,-.012,-.035) if pos.y>56 else ((-.025,.025,.018) if pos.y>10 else (0,0,0))
        if phase in ('flood','rain'):tint=(0,0,0)
        alpha=min(1,dt*.9)
        for i in range(3):
            self.sky_now[i]+=(sky[i]+tint[i]-self.sky_now[i])*alpha
            self.sun_now[i]+=(sun[i]-self.sun_now[i])*alpha
            self.ambient_now[i]+=(amb[i]-self.ambient_now[i])*alpha
        self.fog_now+=(density-self.fog_now)*alpha
        self.fog.setColor(*self.sky_now);self.setBackgroundColor(*self.sky_now,1);self.fog.setExpDensity(self.fog_now)
        self.sun.setColor((*self.sun_now,1));self.ambient.setColor((*self.ambient_now,1))
        target=.58 if phase=='flood' else .23 if phase=='rain' else .10 if phase=='warning' else -.02 if phase=='recovery' and self.state.day<=5 else -.15
        self.water_level+=(target-self.water_level)*min(1,dt*.35)
        self.river.setZ(self.water_level);self.waterlines.setZ(self.water_level+.15)
        inundated=(phase=='flood' or (phase=='recovery' and self.state.day==5)) and not self.state.dam
        floodtarget=.70 if phase=='flood' and inundated else .29 if inundated else .08
        self.overflow_level+=(floodtarget-self.overflow_level)*min(1,dt*.45)
        self.flood.setZ(self.overflow_level);self.flood.show() if self.overflow_level>.18 else self.flood.hide()
        self.crops.setColorScale(.58,.67,.57,1) if inundated else self.crops.setColorScale(1,1,1,1)
        for j,(boat,x,y,z) in enumerate(self.boats):
            boat.setZ(self.water_level+.06+math.sin(self.t*1.3+j)*.06);boat.setR(math.sin(self.t+j)*1.5)
        for p,x,y,z,i in self.smokepuffs:
            if phase in ('rain','flood'):p.hide();continue
            p.show();age=(self.t*.35+i/6)%1
            p.setPos(x+age*.8,y+age*.4,z+age*4);p.setScale(.6+age*1.4,.6+age*1.4,.9+age)
            p.setColor(.72,.70,.60,(1-age)*.18)
        self.rain.setX(pos.x);self.rain.setY(pos.y);self.rain.setZ(pos.z-(self.t*8)%6)
        for p in self.dust:p.hide() if phase in ('rain','flood') else p.show()
        key=self.objective_key();targetpos=Vec3(*self.targets[key][0]);delta=targetpos-pos
        bearing=math.degrees(math.atan2(-delta.x,delta.y));diff=(bearing-self.yaw+180)%360-180
        direction='前方' if abs(diff)<25 else '左前方' if 25<diff<100 else '右前方' if -100<diff<-25 else '身后'
        self.wayfinder.setText(f'{direction} · {self.targets[key][1]}  {delta.length():.0f} 米' if not self.dialog else '')
        if hasattr(self,'tour_fixed') and self.tour_fixed:
            self.camera.setPos(*self.tour_fixed[0]);self.camera.lookAt(*self.tour_fixed[1])
        return result

    def smoke(self,task):
        results=[]
        for key in ['elder','canal','cache0','cache1','cache2','dam','rest','rest','rest','rest','jade','altar','altar']:
            self.rest_lock=0;self.player.setPos(*self.targets[key][0]);self.near=key;self.interact()
            results.append({'action':key,'state':asdict(self.state),'phase':self.phase()})
        assert self.state.won and self.state.population==6 and self.state.food==16 and self.state.material==10
        start=(0,-17);visited={start};q=deque([start])
        # Half-metre traversal validates every actual stair riser and all three bridges.
        while q:
            x,y=q.popleft();z=self.height(x,y)
            for dx,dy in [(.5,0),(-.5,0),(0,.5),(0,-.5)]:
                n=(x+dx,y+dy)
                if n not in visited and self.legal(n[0],n[1],z):visited.add(n);q.append(n)
        reachable={k:any((x-p[0])**2+(y-p[1])**2+(self.height(x,y)-p[2])**2<2.6**2 for x,y in visited) for k,(p,_,_) in self.targets.items()}
        assert all(reachable.values()),reachable
        # Verify that atmosphere preview cannot mutate production/save state.
        state_before=asdict(self.state);self.cycle_preview();self.near='rest';self.interact();assert asdict(self.state)==state_before
        self.preview=None;self.save(quiet=True);expected=asdict(self.state);self.load();assert asdict(self.state)==expected
        report={'result':'PASS','actions':results,'reachable':reachable,'walkable_halfmetre_cells':len(visited),'third_person':True,'preview_isolated':True,'save_load':True,'renderer':self.win.getGsg().getDriverRenderer()}
        (SAVE/'smoke_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        return self.start_tour(task)

    def start_tour(self,task):
        self.reset();self.state.greeted=True;self.state.canal=True
        self.tour_index=0;self.tour_specs=[
            ('01_arrival',0,False,False,(0,-14,.1),0,10),
            ('02_harbor',0,False,False,(-28,5,.4),-40,8),
            ('03_workshops',1,False,False,(-19,29,2.4),15,8),
            ('04_ritual_axis',1,True,False,(0,48,2.4),0,8),
            ('05_rain_warning',3,False,False,(4,5,.1),-28,10),
            ('06_flood_unprotected',4,False,False,(14,-9,.1),-46,17),
            ('07_flood_protected',4,False,True,(14,-9,.1),-46,17),
            ('08_recovery',6,True,True,(-23,29,2.4),8,9),
            ('09_ritual',6,True,True,(0,77,6),0,7)]
        self.next_tour();return task.done

    def next_tour(self):
        name,day,shrine,dam,pos,yaw,pitch=self.tour_specs[self.tour_index]
        self.state.day=day;self.state.shrine=shrine;self.state.dam=dam;self.state.won=name=='09_ritual'
        self.dialog=False;self.ceremony=0;self.overlay.hide();self.player.setPos(*pos);self.yaw=yaw;self.pitch=pitch;self.distance=8.6
        self.toast='';self.toasting=0;self.refresh();self.sync_ui()
        self.taskMgr.doMethodLater(7,self.capture_tour,'capture-tour')

    def capture_tour(self,task):
        name=self.tour_specs[self.tour_index][0]
        out=Path(__file__).parent/'captures_v02' if not getattr(sys,'frozen',False) else SAVE/'captures'
        out.mkdir(exist_ok=True);self.win.saveScreenshot(Filename.fromOsSpecific(str(out/(name+'.png'))))
        self.tour_index+=1
        if self.tour_index<len(self.tour_specs):self.next_tour()
        else:self.userExit()
        return task.done

if __name__=='__main__':
    try:RiverDemo().run()
    except Exception:
        import traceback
        (SAVE/'error.log').write_text(traceback.format_exc(),encoding='utf8');raise
