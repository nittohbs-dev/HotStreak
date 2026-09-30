"""Issue #23 / SCR-display-001: QR・参加者一覧の実表示。"""
import pygame
import qrcode
from .setup_cards import DisplaySetupRoot


class LobbyView(DisplaySetupRoot):
    def __init__(self, font=None):
        super().__init__(font)
        self.qr_url = None
        self.qr = None

    def qr_surface(self, url):
        if url != self.qr_url:
            code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
            code.add_data(url)
            code.make(fit=True)
            matrix = code.get_matrix()
            scale = max(1, 384 // len(matrix))
            self.qr = pygame.Surface((len(matrix)*scale, len(matrix)*scale))
            self.qr.fill('white')
            for row, line in enumerate(matrix):
                for col, dark in enumerate(line):
                    if dark:
                        pygame.draw.rect(self.qr, 'black', (col*scale, row*scale, scale, scale))
            self.qr_url = url
        return self.qr

    def draw_live(self, surface, snapshot, context):
        surface.blit(self.background, (0, 0))
        pygame.draw.rect(surface, (12, 15, 20), (20, 16, 1240, 65))
        self.text(surface, '参加受付', (44, 28), 32)
        self.text(surface, 'HOT STREAK', (1020, 39), 20, (223, 191, 134))
        self.text(surface, '同じWi-FiにつないでQRから参加', (65, 112), 24)
        url = context.get('joinUrl')
        if url:
            qr = self.qr_surface(url)
            surface.blit(qr, qr.get_rect(center=(275, 355)))
        self.text(surface, '参加者全員が入ってから名前を確定してください', (65, 579), 20)
        self.text(surface, url or 'セッションを作成しています…', (65, 620), 16, (223, 191, 134), 1140)
        players = snapshot.get('players', [])
        self.text(surface, f'参加者 {len(players)} / 8 人', (540, 112), 32, (223, 191, 134))
        for i in range(8):
            x, y = 550, 173+i*47
            pygame.draw.rect(surface, (12, 15, 20), (535, y-4, 675, 42))
            if i < len(players):
                player = players[i]
                self.mascot_icon(surface, ('blue', 'orange', 'yellow', 'salmon')[i % 4], (563, y+15), 2)
                self.text(surface, player.get('displayName') or '名前入力中…', (603, y), 24, max_width=410)
                self.text(surface, '入力済' if player.get('nameReady') else '入力中', (1080, y+3), 20)
            else:
                self.text(surface, '— 空き枠 —', (603, y), 24, (115, 116, 120))
        self.text(surface, '3〜8人で遊べます  /  参加受付後、会場のENTERで開始', (285, 678), 20, (223, 191, 134))
