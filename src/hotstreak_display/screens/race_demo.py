"""追加効果を自動で順に再生する確認用デモ。"""
from argparse import Namespace

SCENES=(('★まで移動','blue_star',0),('移動してレーン変更','blue_swerve_2',1),
        ('衝突で転倒','blue_move_3',1),('倒れた相手に衝突 → 失格','blue_move_3',2),
        ('転倒中は1マス移動','blue_move_3',3),('全員同時に移動','green_move_2',0),
        ('全員が復帰して移動','green_recover_2',4),('方向転換','blue_turn',0))

class EffectsDemo:
    def __init__(self,model_type):
        self.model_type=model_type; self.index=-1; self.time=0; self.fired=False
        self.next()

    def next(self):
        self.index=(self.index+1)%len(SCENES)
        title,self.card,setup=SCENES[self.index]
        self.model=self.model_type(Namespace(state='running'))
        m=self.model
        m.positions=(4,6,7,4);m.previous=m.positions;m.visual_positions=list(m.positions)
        if setup in (1,2): m.lanes=[1,1,2,3]
        if setup==2: m.fallen[1]=True
        if setup==3: m.fallen[0]=True
        if setup==4: m.fallen=[True]*4;m.facing=[-1]*4
        m.previous_lanes=m.lanes[:];m.visual_lanes=m.lanes[:]
        m.preview_title=title;m.preview=True
        self.time=0;self.fired=False

    def update(self,dt):
        self.time+=dt
        if self.time>=3.2: self.next()
        if self.time>=.55 and not self.fired:
            self.model.apply_card(self.card);self.fired=True
        self.model.update(dt)
        return self.model
