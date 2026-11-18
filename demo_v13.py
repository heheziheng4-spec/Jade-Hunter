"""Upper court residences, timber balustrades and inscribed floating stones."""
from panda3d.core import loadPrcFileData
from demo_v12 import ReferenceBuilder, ReferenceDemo
from sky_temple import image_card
from world_v03 import WOOD


class CourtBuilder(ReferenceBuilder):
    def house(self,x,y,w=5,d=4,base=None,grand=False,parent=None):
        if (x,y)==(24,51):
            node=self.asset('newarbor',x,y,2.375,(7.8,)*3,0)
            self.obstruction(x,y,7.1,6.2,10.7)
            return node
        return super().house(x,y,w,d,base,grand,parent)

    def ritual_hall(self,sacred):
        # The residence occupies the east court from the beginning. The existing
        # restoration milestone reveals its ceremonial forecourt stones.
        self.asset('noble',23,84,6.30,(12,)*3,90)
        self.obstruction(23,84,10.6,10.6,13.7)
        self.g.palace=self.g.render.attachNewNode('restored noble forecourt')
        for x in (18,28):
            node=self.asset('stone',x,76.8,6,(1.15,)*3,-90)
            node.wrtReparentTo(self.g.palace)
            self.obstruction(x,76.8,.9,.9,9.6)

    def box(self,name,p,s,c=WOOD,parent=None):
        if name in ('ritual corridor post','ritual corridor rail','ritual corridor lintel'):
            return (parent if parent is not None else self.root).attachNewNode('replaced court railing')
        return super().box(name,p,s,c,parent)

    def offering_altar(self,sacred):
        super().offering_altar(sacred)
        for side in (-1,1):
            for y in (76,80,84,88,92):
                self.asset('rail',side*12,y,5.98,(4.05,)*3,0 if side<0 else 180)
                self.obstruction(side*12,y,.55,3.8,7.8)
        replacements=[]
        for index,(old,z,phase) in enumerate(self.g.suspended):
            x,y,_=old.getPos(self.g.render)
            height=old.getSz()
            old.removeNode()
            holder=self.g.effects.attachNewNode('inscribed floating stele')
            holder.setPos(x,y,z)
            scale=height/3.1739
            stone=self.asset('floatstone',0,0,-height/2,(scale,)*3,0)
            stone.reparentTo(holder)
            # A separate decal keeps the previous carving legible while moving
            # with the same suspended assembly.
            mark=(index%4)*6+(3 if index>=4 else 0)
            for front in (-1,1):
                stamp=image_card(self.g,holder,f'mark{mark:02}',.85,1.2,True)
                stamp.setPos(0,front*scale*.51,-.6)
                if front>0:stamp.setH(180)
            replacements.append((holder,z,phase))
        self.g.suspended=replacements


class CourtDemo(ReferenceDemo):
    world_builder=CourtBuilder


if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.13 | Inscribed Court')
    CourtDemo().run()
