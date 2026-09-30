"""ローカル会場用HTTP/WSとPhoneの配信。"""
import argparse
from pathlib import Path
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from hotstreak_core.lobby import LobbyService
from hotstreak_core.setup_cards import SetupCardsService
from .runtime import create_app

ROOT = Path(__file__).resolve().parents[2]


def build_app(public_base=None):
    app = create_app([LobbyService(), SetupCardsService()], public_base=public_base)

    @app.get('/join/{sid}')
    async def join_page(sid: str):
        app.state.runtime.get(sid)
        from urllib.parse import urlencode
        return RedirectResponse('/phone/lobby.html?' + urlencode({'session': sid}))

    app.mount('/phone', StaticFiles(directory=ROOT / 'src/hotstreak_phone'), name='phone')
    app.mount('/assets', StaticFiles(directory=ROOT / 'assets'), name='assets')
    app.mount('/data', StaticFiles(directory=ROOT / 'data'), name='data')
    return app


def main():
    parser = argparse.ArgumentParser(description='HotStreak 同期サーバ')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--public-base', help='スマホがアクセスするURL（例 http://192.168.1.10:8000）')
    args = parser.parse_args()
    import uvicorn
    uvicorn.run(build_app(args.public_base), host=args.host, port=args.port)


if __name__ == '__main__':
    main()
