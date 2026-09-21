"""固定データのディスプレイモック。通信・ゲーム処理は行わない。"""
import argparse
from pathlib import Path
import pygame
if __package__:
    from .card_seed import DisplaySeedRoot
    from .race_sprites import sprite
else:
    from card_seed import DisplaySeedRoot
    from race_sprites import sprite

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

    def draw(self,surface,model):
        footer = "ENTER  →  参加受付へ" if model.race == 3 else f"ENTER  →  レース {model.race+1} のマ券選びへ"
        if model.confirmed:
            footer = "進行確認の表示例  /  次画面への接続は未実装"
        self.chrome(surface,f"RACE {model.race} RESULT","着順が確定しました。払戻の詳細はスマホで確認してください",footer)
        self.centered(surface,"ダングル  WINNER",640,138,44)
        # 視線が中央の1位へ向かう表彰台。素材の色・名前は共通カタログに合わせる。
        for rank, index, x, top in ((2,1,224,375),(1,0,512,322),(3,2,800,418)):
            size=(124,126) if rank==1 else (108,110)
            icon=pygame.transform.smoothscale(sprite(COLORS[index]),size)
            surface.blit(icon,icon.get_rect(midbottom=(x+128,top-8)))
            self.panel(surface,pygame.Rect(x,top,256,584-top))
            self.centered(surface,str(rank),x+128,top+17,44)
            self.centered(surface,NAMES[index],x+128,top+80,32)
        self.panel(surface,pygame.Rect(44,596,1192,39))
        fourth = "失格  ハーレー" if model.state == "dq" else "4位  ハーレー"
        fourth_icon=pygame.transform.smoothscale(sprite(COLORS[3]),(34,35))
        surface.blit(fourth_icon,(60,597))
        self.text(surface,fourth,(104,601),20,MUTED)
        if model.race == 3:
            message = "総合優勝  くま・さかな（共同優勝）" if model.state == "tie" else "総合優勝  くま"
            self.text(surface,message,(478,601),20,GOLD)

DESCRIPTION = "着順・結果モック / Issue #42"
STATES = ("normal", "dq", "tie")
DEFAULT_STATE = "normal"
def add_arguments(parser):
    parser.add_argument("--race",type=int,choices=(1,2,3),default=1)

class Model:
    def __init__(self,args):
        self.state = args.state
        self.race = 3 if self.state == "tie" else args.race
        self.confirmed = False
    @property
    def next_phase(self):
        return "lobby" if self.race == 3 else "betting"
    def handle_event(self,event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN,pygame.K_KP_ENTER):
            self.confirmed = True

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--windowed", action="store_true")
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
        if args.screenshot:
            view.draw(canvas, model)
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(canvas, str(args.screenshot))
            return
        display = pygame.display.set_mode((1280, 720), pygame.RESIZABLE if args.windowed else pygame.FULLSCREEN)
        pygame.display.set_caption(DESCRIPTION + " [MOCK]")
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    model.handle_event(event)
            view.draw(canvas, model)
            width, height = display.get_size()
            scale = min(width / 1280, height / 720)
            size = max(1, int(1280 * scale)), max(1, int(720 * scale))
            display.fill((9, 12, 17))
            display.blit(pygame.transform.scale(canvas, size), ((width-size[0])//2, (height-size[1])//2))
            pygame.display.flip()
            clock.tick(30)
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()
