"""固定データのディスプレイモック。通信・ゲーム処理は行わない。"""
import argparse
from pathlib import Path
import pygame
if __package__:
    from .card_seed import DisplaySeedRoot
    from .race_sprites import sprite
    from .race_effects import EffectsMixin
    from .race_demo import EffectsDemo
else:
    from card_seed import DisplaySeedRoot
    from race_sprites import sprite
    from race_effects import EffectsMixin
    from race_demo import EffectsDemo

GOLD = (223, 191, 134)
MUTED = (200, 184, 144)
COLORS = ("blue", "orange", "yellow", "salmon")
NAMES = ("ダングル", "ゴブラー", "マム", "ハーレー")

class View(DisplaySeedRoot):
    def __init__(self, font_path=None):
        import os
        windows_font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/YuGothB.ttc"
        super().__init__(font_path or (str(windows_font) if windows_font.exists() else None))

    def centered(self, surface, text, x, y, size=24, color=GOLD):
        self.text(surface, text, (x - self.fonts[size].size(text)[0] // 2, y), size, color)

    def chrome(self, surface, title, subtitle, footer):
        surface.blit(self.background, (0, 0))
        self.panel(surface, pygame.Rect(20, 16, 1240, 65))
        self.text(surface, title, (44, 28), 32)
        self.text(surface, "HOT STREAK", (1070, 42), 16, MUTED)
        self.text(surface, subtitle, (44, 96), 20, MUTED)
        self.panel(surface, pygame.Rect(20, 649, 1240, 51))
        self.centered(surface, footer, 640, 659, 20)

    def sea(self, surface):
        # 参照の明るい海と小島。2倍ピクセルで細かい水面を描く。
        import random
        if hasattr(self,'sea_background'):
            surface.blit(self.sea_background,(0,0)); return
        rng=random.Random(7)
        sea=pygame.Surface((640,360))
        for y in range(360):
            if y<139:
                t=y/139
                c=(int(43+94*t),int(153+65*t),249)
            else:
                t=(y-139)/221
                c=(7,int(157-61*t),int(224-41*t))
            pygame.draw.line(sea,c,(0,y),(640,y))
        for x,y in ((20,42),(175,76),(316,29),(478,67)):
            for dx,dy,r in ((0,7,12),(16,0,18),(33,5,14),(47,11,10)):
                pygame.draw.circle(sea,(198,236,253),(x+dx,y+dy+4),r)
                pygame.draw.circle(sea,(249,254,255),(x+dx,y+dy),r)
        for _ in range(2300):
            x,y=rng.randrange(640),rng.randrange(141,360)
            c=rng.choice(((31,180,226),(94,215,243),(12,128,208),(154,237,249)))
            pygame.draw.line(sea,c,(x,y),(x+rng.randrange(1,7),y))
        for x,y in ((8,165),(355,148),(553,170)):
            pygame.draw.ellipse(sea,(77,206,224),(x-5,y-3,86,12))
            pygame.draw.polygon(sea,(251,222,143),[(x,y),(x+78,y),(x+56,y-15),(x+21,y-20)])
            pygame.draw.polygon(sea,(43,126,80),[(x+4,y-3),(x+23,y-37),(x+42,y-18),(x+57,y-32),(x+73,y-4)])
            for _ in range(65):
                dx=rng.randrange(14,66);dy=rng.randrange(4,21)
                pygame.draw.rect(sea,rng.choice(((39,152,81),(69,176,88),(22,109,74),(117,190,94))),(x+dx,y-dy,3,3))
        pygame.draw.rect(sea,(246,247,225),(596,124,7,32))
        pygame.draw.rect(sea,(228,55,64),(596,132,7,7))
        pygame.draw.rect(sea,(228,55,64),(596,146,7,6))
        pygame.draw.polygon(sea,(226,41,53),[(593,124),(599,116),(606,124)])
        pygame.draw.rect(sea,(23,66,90),(599,126,2,4))
        pygame.draw.line(sea,(55,64,95),(133,130),(133,174),2)
        pygame.draw.polygon(sea,(252,253,238),[(131,133),(131,167),(114,167)])
        pygame.draw.polygon(sea,(239,113,175),[(136,142),(153,167),(136,167)])
        pygame.draw.polygon(sea,(33,60,109),[(112,172),(155,172),(147,178),(122,178)])
        self.sea_background=pygame.transform.scale(sea,(1280,720))
        surface.blit(self.sea_background,(0,0))

    def ocean_panel(self,surface,rect):
        pygame.draw.rect(surface,(4,24,47),rect.move(4,5))
        pygame.draw.rect(surface,(225,248,255),rect)
        pygame.draw.rect(surface,(12,81,132),rect.inflate(-5,-5))
        pygame.draw.rect(surface,(3,32,60),rect.inflate(-12,-12))

    def point(self,col,row):
        # 台形の4レーン×12マス。手前ほど広くする。
        depth=row/4
        return (int(130-87*depth+col*(1010+164*depth)/12),int(344+depth*276))

    def sign(self,surface,label,x,y,color):
        pygame.draw.rect(surface,(100,63,24),(x+13,y+38,7,29))
        pygame.draw.rect(surface,(100,63,24),(x+101,y+38,7,29))
        pygame.draw.rect(surface,(6,28,43),(x-3,y-3,126,48))
        pygame.draw.rect(surface,(255,246,198),(x,y,120,42))
        pygame.draw.rect(surface,color,(x+4,y+4,112,34))
        self.centered(surface,label,x+60,y+5,24,(255,255,235) if label=='GOAL' else (10,25,35))

    def draw(self, surface, model):
        self.sea(surface)
        self.text(surface,"RACE 1 / 3",(32,28),32,(244,252,255))
        finishers=model.finished_entries
        if finishers:
            self.ocean_panel(surface,pygame.Rect(24,78,28+192*len(finishers),91))
            self.text(surface,"確定した着順",(40,87),16,(181,222,242))
            for slot,(place,who,status) in enumerate(finishers):
                x=40+slot*192
                self.text(surface,f"{place}位", (x,120),20,(255,231,115))
                icon=pygame.transform.smoothscale(sprite(COLORS[who]),(44,46))
                surface.blit(icon,(x+37,111))
                self.text(surface,NAMES[who],(x+85,124),20,(244,252,255))
        self.ocean_panel(surface,pygame.Rect(865,20,389,153))
        surface.blit(self.card_assets.card(model.card_id,(87,122)),(881,35))
        if model.card_id != 'card_back' and not model.card_id.startswith('green'):
            pygame.draw.rect(surface,(5,34,61),(890,91,68,49))
            avatar=pygame.transform.smoothscale(sprite(COLORS[model.active]),(40,44))
            surface.blit(avatar,(903,93))
        self.text(surface,"今回のカード",(986,38),24,(244,251,255))
        self.text(surface,model.effect,(986,83),20,(255,237,168),max_width=249)
        self.text(surface,f"残り {model.remaining} 枚",(986,124),20,(178,221,240))
        if getattr(model,"preview_title",None):
            self.ocean_panel(surface,pygame.Rect(270,190,710,65))
            self.centered(surface,model.preview_title,625,206,24,(255,240,185))
        removed=model.removed
        # 黄金の縁、緑の盤面、白い格子。
        corners=[self.point(removed,0),self.point(12,0),self.point(12,4),self.point(removed,4)]
        pygame.draw.polygon(surface,(7,42,46),[(x,y+15) for x,y in corners])
        pygame.draw.polygon(surface,(234,170,68),corners)
        for row in range(4):
            for col in range(removed,12):
                pts=[self.point(col,row),self.point(col+1,row),self.point(col+1,row+1),self.point(col,row+1)]
                pygame.draw.polygon(surface,(28,142,73) if (col+row)%2 else (22,125,65),pts)
                pygame.draw.polygon(surface,(139,222,156),pts,2)
                if col in (0,5,8):
                    x,y=self.point(col+.5,row+.5)
                    self.centered(surface,"★",x,y-17,32,(249,244,168))
        if removed<=2:
            pygame.draw.line(surface,(255,245,190),self.point(2,0),self.point(2,4),4)
        for row in range(8):
            for col in range(2):
                pts=[self.point(11.65+col*.17,row*.5),self.point(11.65+(col+1)*.17,row*.5),self.point(11.65+(col+1)*.17,(row+1)*.5),self.point(11.65+col*.17,(row+1)*.5)]
                pygame.draw.polygon(surface,(242,245,230) if (row+col)%2 else (12,23,33),pts)
        for edge in (0,4):
            for col in range(removed*2,24):
                x,y=self.point(col/2,edge)
                pygame.draw.rect(surface,(81,66,28),(x-3,y-4,43,15))
                pygame.draw.rect(surface,(249,204,103),(x,y-5,38,9),border_radius=3)
                pygame.draw.line(surface,(255,235,171),(x+2,y-4),(x+34,y-4),2)
        for i,pos in enumerate(model.visual_positions):
            if model.status[i] != 'racing':
                continue
            x,y=self.point(min(pos,12)+.3,model.visual_lanes[i]+.5)
            pose='run' if model.moving and i in model.targets else 'idle'
            tilt=0
            if model.action=='fall' and i in model.targets and model.moving:
                tilt=int(90*model.progress)
            elif model.action=='recover' and i in model.targets and model.old_fallen[i] and model.moving:
                tilt=int(90*(1-min(1,model.progress*2)))
            elif model.fallen[i] and not (model.moving and model.action=='recover' and i in model.targets):
                pose='fallen'
            image=sprite(COLORS[i],int(model.elapsed*10),pose,model.facing[i],tilt)
            pygame.draw.ellipse(surface,(12,82,50),(x-25,y+10,50,13))
            surface.blit(image,image.get_rect(midbottom=(x,y+20)))
        if model.action=='shorten' and model.moving:
            # 3列の床が順に沈む。短縮完了後にのみ失格を確定する。
            for col in range(model.removed,model.removed+3):
                t=max(0,min(1,model.progress*1.5-(col-model.removed)*.22))
                if t<=0: continue
                for row in range(4):
                    pts=[self.point(col,row),self.point(col+1,row),self.point(col+1,row+1),self.point(col,row+1)]
                    pygame.draw.polygon(surface,(12,112,184),pts)
                    x,y=self.point(col+.5,row+.5)
                    size=max(0,int(42*(1-t)))
                    if size:
                        pygame.draw.rect(surface,(222,174,75),(x-size//2,y+int(t*35),size,size//2))
                    pygame.draw.ellipse(surface,(118,220,248),(x-20,y+18,40,10),2)
        self.sign(surface,"START",max(20,self.point(max(2,removed),0)[0]-60),290,(247,207,42))
        self.sign(surface,"GOAL",1100,290,(225,39,46))
        if model.state=='start':
            self.ocean_panel(surface,pygame.Rect(368,195,538,103))
            self.centered(surface,"HOT STREAK",637,206,44,(255,231,115))
            self.centered(surface,"ENTERで最初のカードをめくる",637,260,20,(244,252,255))
        elif model.action=='shorten' and model.moving:
            self.ocean_panel(surface,pygame.Rect(381,211,514,73))
            self.centered(surface,"コース短縮  /  左から3マス",638,231,24,(255,234,164))
        if model.state=='finish':
            self.ocean_panel(surface,pygame.Rect(370,187,540,414))
            self.centered(surface,"RACE RESULT",640,203,32,(255,231,115))
            names=('ダングル','ゴブラー','マム','ハーレー')
            for rank,who in enumerate(model.standings):
                if who is None: continue
                y=267+rank*76
                self.text(surface,f"{model.tie_ranks.get(who,rank+1)}",(403,y+12),32,(255,231,115))
                avatar=pygame.transform.scale(sprite(COLORS[who],0,'idle',1,0),(50,55))
                surface.blit(avatar,(451,y))
                self.text(surface,names[who],(522,y+12),24,(248,252,240))
                result='失格' if model.status[who]=='dq' else 'ゴール' if model.status[who]=='goal' else 'レース終了'
                self.text(surface,result,(750,y+16),20,(181,222,242))

DESCRIPTION = "レース進行モック / Issue #37"
STATES = ("start", "running", "fall", "shorten", "finish")
DEFAULT_STATE = "start"
def add_arguments(parser):
    pass

class RaceState:
    SAMPLES = (
        ('blue_move_3','ダングル  +3',0,'move',3),
        ('orange_move_2','ゴブラー  +2',1,'move',2),
        ('yellow_move_3','マム  +3',2,'move',3),
        ('salmon_move_2','ハーレー  +2',3,'move',2),
        ('blue_fall','ダングル  転倒',0,'fall',0),
        ('blue_recover_2','ダングル  復帰して +2',0,'recover',2),
        ('salmon_turn','ハーレー  方向転換',3,'turn',0),
        ('salmon_move_3','ハーレー  後ろ向きに3マス',3,'move',3),
        ('salmon_recover_1','ハーレー  前を向いて +1',3,'recover',1),
        ('orange_fall','ゴブラー  転倒',1,'fall',0),
        ('orange_recover_2','ゴブラー  復帰して +2',1,'recover',2),
    )
    def __init__(self,args):
        self.enter_held=False
        self.set_state(args.state)

    def set_state(self,state):
        self.state=state
        self.removed=3 if state=='shorten' else 0
        self.status=['racing']*4
        self.standings=[None]*4
        self.deck_index=0
        self.index=0
        self.elapsed=0.0
        self.progress=1.0
        self.moving=False
        self.active=0
        self.action='idle'
        self.facing=[1]*4
        self.fallen=[state=='fall',False,False,False]
        self.positions=(2,2,2,2) if state=='start' else (8,5,7,3)
        if state=='finish': self.positions=(12,11,12,12)
        self.visual_positions=list(self.positions)
        self.previous=self.positions
        self.card_id='blue_fall' if state=='fall' else 'card_back'
        self.effect='3枚バーン済み' if state=='start' else '表示例'
        self.remaining=15
        self.label='Enterでカードをめくる'
        if state=='finish':
            self.status=['goal','racing','goal','goal']
            self.standings=[0,2,3,1]
        if state=='shorten':
            self.status[3]='dq'
            self.standings[3]=3

    @property
    def samples(self):
        return self.SAMPLES + (
            ('blue_move_3','ダングル +3',0,'move',3),
            ('blue_move_3','ダングル +3',0,'move',3),
            ('orange_move_3','ゴブラー +3',1,'move',3),
            ('yellow_move_3','マム +3',2,'move',3),
            ('blue_move_2','ダングル +2',0,'move',2),
            ('orange_move_3','ゴブラー +3',1,'move',3),
            ('yellow_move_3','マム +3',2,'move',3),
            ('orange_move_2','ゴブラー +2',1,'move',2),
        )

    def place(self,who,kind):
        if self.status[who]!='racing': return
        self.status[who]=kind
        slots=[i for i,v in enumerate(self.standings) if v is None]
        self.standings[slots[-1] if kind=='dq' else slots[0]]=who

    def finish_if_ready(self):
        if sum(x!='racing' for x in self.status)>=3:
            for who in range(4):
                if who not in self.standings:
                    self.standings[self.standings.index(None)]=who
            self.state='finish'
            self.label='3体がゴール・失格。着順確定'
            return True
        return False

class Model(EffectsMixin, RaceState):
    """既存の固定デモにも共通のカード効果を適用する。"""
    pass


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--windowed", action="store_true")
    parser.add_argument("--effects-demo", action="store_true")
    parser.add_argument("--font")
    parser.add_argument("--state", choices=STATES, default=DEFAULT_STATE)
    parser.add_argument("--screenshot", type=Path)
    add_arguments(parser)
    args = parser.parse_args()
    pygame.init()
    try:
        view = View(args.font)
        canvas = pygame.Surface((1280, 720))
        model = Model(args)
        demo=EffectsDemo(Model) if args.effects_demo else None
        if args.screenshot:
            view.draw(canvas, model)
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(canvas, str(args.screenshot))
            return
        display = pygame.display.set_mode((1280, 720), pygame.RESIZABLE if args.windowed else pygame.FULLSCREEN)
        pygame.display.set_caption("Hot Streak — 採用キャラクター版モック")
        clock = pygame.time.Clock()
        running = True
        while running:
            dt=clock.tick(60)/1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE):
                    running = False
                else:
                    model.handle_event(event)
            if demo: model=demo.update(dt)
            else: model.update(dt)
            view.draw(canvas, model)
            width, height = display.get_size()
            scale = min(width / 1280, height / 720)
            size = max(1, int(1280 * scale)), max(1, int(720 * scale))
            display.fill((9, 12, 17))
            display.blit(pygame.transform.scale(canvas, size), ((width-size[0])//2, (height-size[1])//2))
            pygame.display.flip()
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()

