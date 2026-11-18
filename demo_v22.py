"""Grounded landscape and central jade resonance."""
import math,random
from panda3d.core import loadPrcFileData,Shader
from demo_v21 import JadeDemo,JadeBuilder
from demo_v08 import Batch
from sky_temple import image_card
class NaturalBuilder(JadeBuilder):
 def pillar(self,x,y,h=7,w=1.65,z=None,glow=False,parent=None):
  if abs(y)<.1 and 65<abs(x)<85:return self.instances.attachNewNode('clear island sightline')
  return super().pillar(x,y,h,w,z,glow,parent)
 def asset(self,kind,x,y,z,scale,heading=0):
  if kind=='border19' and abs(x)<45:
   return super().asset('jadepost',x,y,z,(5.4,)*3,-90)
  if kind=='ring18':z=-.18
  if kind in ('border18','border19'):
   scale=(9,)*3
  n=super().asset(kind,x,y,z,scale,heading)
  if kind in ('wall19','wall20'):
   n.setP(0);n.setR(0)
   lo,hi=n.getTightBounds(self.g.render);n.setZ(n.getZ()+z-lo.z-.13)
  return n
class NaturalDemo(JadeDemo):
 world_builder=NaturalBuilder
 def world(self):
  super().world();self.resonance_time=0;self.resonance=[]
  for key in list(self.targets):
   if key.startswith('jade_node'):
    del self.targets[key];self.markers.pop(key).removeNode()
  for q,j,g,h,f,z in self.jade_nodes:g.removeNode();h.removeNode();f.removeNode()
  self.jade_nodes=[]
  for n in self.builder.instances.getChildren():
   name=n.getName();p=n.getPos(self.render)
   if name in ('oak','tree','frontier_tall21','frontier_tree18','frontier_newarbor','frontier_ancient_tree'):
    if p.z<25:
     lo,hi=n.getTightBounds(self.render);n.setZ(n.getZ()+self.height(p.x,p.y)-lo.z-.12)
   if name in ('frontier_jade21','frontier_orbit21'):
    lo,hi=n.getTightBounds(self.render);n.setZ(n.getZ()+self.height(p.x,p.y)-lo.z-.08)
  self.builder.asset('camp20',-65,80,.05,(10,)*3,90)
  for q,(cx,cy) in enumerate([(-95,-43),(95,-43)]):
   for j in range(24):
    n=image_card(self,self.effects,'disc',.35,.35,True);n.setBillboardPointEye();n.setColorScale(.3,1,.7,.7);self.resonance.append((n,cx,cy,j))
  rng=random.Random(2216);flowers=Batch('dense wind flowers')
  for i in range(12000):
   a=rng.random()*math.tau;r=rng.uniform(1.08,1.72);x=83*r*math.cos(a);y=35+89*r*math.sin(a);z=self.height(x,y);h=rng.uniform(.25,.7)
   flowers.tri((x-.06,y,z),(x+.06,y,z),(x+.08,y,z+h),(.52,.7,.32))
   if i%3==0:
    c=rng.choice([(.92,.82,.53),(.72,.62,.9),(.92,.9,.8)])
    flowers.tri((x-.13,y,z+h),(x+.13,y,z+h),(x,y+.15,z+h+.08),c)
  n=flowers.finish(self.render);n.setTwoSided(True);self.windflowers=n
  shader=Shader.make(Shader.SL_GLSL,'''#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;uniform float clock;in vec4 p3d_Vertex;in vec4 p3d_Color;out vec4 color;
void main(){vec4 p=p3d_Vertex;p.x+=.16*sin(clock*2.1+p.y*.5+p.x*.3);gl_Position=p3d_ModelViewProjectionMatrix*p;color=p3d_Color;}''','''#version 130
in vec4 color;out vec4 fragColor;void main(){fragColor=color;}''');n.setShader(shader);n.setShaderInput('clock',0)
  self.arm_controls={s:self.king.controlJoint(None,'modelRoot','upper_arm.'+s) for s in ('L','R')}
  self.arm_rest={s:n.getHpr() for s,n in self.arm_controls.items()}
 def interact(self):
  if (self.near or '').startswith('jade_start') and not self.dialog:
   self.resonance_time=self.t+7;self.pick_until=self.t+1.4;self.king.play('pickup');self.king_anim='pickup';self.cue('portal','玉石共鸣');self.toast='玉光环绕中心升起，古玉回应了你的触碰。';self.toasting=5;return
  return super().interact()
 def update(self,task):
  result=super().update(task)
  self.windflowers.setShaderInput('clock',self.t)
  moving=not self.dialog and any(self.keys.get(k) for k in ('w','a','s','d'))
  for i,(s,n) in enumerate(self.arm_controls.items()):
   rest=self.arm_rest[s];wave=math.sin(self.t*(12 if self.keys.get('shift') else 8)+i*math.pi)
   n.setHpr(rest.x,rest.y+(wave*(45 if self.keys.get('shift') else 25) if moving else 2*math.sin(self.t*2)),rest.z)
  for n,x,y,j in self.resonance:
   a=self.t*.6+j*math.tau/24;r=3.7+.3*math.sin(self.t+j)
   n.setPos(x+r*math.cos(a),y+r*math.sin(a),self.height(x,y)+1+(j%8)*.6)
   n.setScale(1.8 if self.t<self.resonance_time else .6)
  return result
if __name__=='__main__':
 loadPrcFileData('','window-title Sandlight 0.22 | Natural Landscape')
 NaturalDemo().run()
