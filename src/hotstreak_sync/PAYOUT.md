# 配当の同期（#40）

対象: `docs/design/hotstreak/features/payout/`、REQ-payout-001〜006。
前提: #26の共通状態・runtime、#44の確定レース結果。
合併順は公開カード準備 → レース進行 → 配当。

```python
from hotstreak_core.setup_cards import SetupCardsService
from hotstreak_core.race_service import RaceService
from hotstreak_core.payout_service import PayoutService
from hotstreak_sync.runtime import create_app
app = create_app([SetupCardsService(), RaceService(), PayoutService()])
```

runtimeはレース終了と同じ排他区間で `PayoutService.enter` を呼ぶ。
全員分の精算成功後にのみbalanceを変更する。失敗時は最後のめくりも復元し、
再送可能。一度精算したrace_indexは再精算しない。クライアント用settle APIはない。

GET `/api/sessions/{sid}/payout` とWSの `payout.state` に着順、残高、個人明細を返す。
個人明細はCookie `hs_{sid}` から本人を識別し、未認証にはnull。
Enterは既存advanceにphase/revision、Displayトークン、操作IDを送る。
`payout.advanced` で次のbettingまたはlobbyを通知する。

レース1/2後は既存18枚から各1枚補充し、札・仕込み・レース状態をリセット。
次のお題とドラフト先頭indexを進める。betting側は `draft_start` から
ストック・スネーク順を再作成する。初期お題一覧は前段サービスで用意する。
第3レースは指定札だけ損益2倍、負残高を0に丸め、同点最多を共同優勝にする。
結果をEnterまで保持し、その後に参加者を消して新規ロビーへ戻す。

## 検証

先行2PR合併後、`PYTHONPATH=src` で `python -m pytest tests/hotstreak_core -q`。
合併前は3ブランチのsrcをPYTHONPATHに追加する。
額表全組合せ、負額ダブル・下限、二重精算防止、部分精算/めくりのロールバック、
個人REST/WS、共同優勝、3〜8人×10乱数×3レースの個体保存・補充元を検証する。
betting/card-seedは別Issueなので、テスト内で受渡し状態を用意する。

## 設計書との差分

金額・リセット・共同優勝は設計どおり。個人明細のplayerIdをCookie認証から
決め、advanceには共通runtimeのrevision/操作ID/Displayトークンを指定する。
プロセス内メモリのみ（単一worker）。画面変更・参加受付・札選択は含まない。
