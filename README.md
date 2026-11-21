# CW Keyer Trainer

[English](README.en.md) | 日本語

モールス符号（CW）を「打つ」「聞く」の両方で練習するための、エレキー（電子キーヤー）と練習アプリのセットです。

- **エレキー**：Seeed XIAO RP2040 に市販のパドルをつなぐ iambic キーヤー。ブザーで遅延なく鳴り、OLED とボタンだけでも練習できます
- **練習アプリ**：ブラウザで動く PWA（ホーム画面に追加でき、オフラインでも動く Web アプリ）。iPhone と PC で使えます

## できること

| 練習 | 内容 | 機器 |
|---|---|---|
| 受信 | Koch 法・コールサイン・定型 QSO を聞いて答える | 不要 |
| 筆記 | 符号 ↔ 文字（試験対策） | 不要 |
| 送信 | 出題文を打つ → 解読結果と、短点:長点比・字間のずれを表示 | 必要 |
| エコー | 聞いた符号を打ち返す | 必要（本体だけでも可） |
| 設定 | 機器の WPM・モード・トーンを読み書き | 必要（PC のみ） |

機器との接続：PC は USB シリアル（Web Serial。Chrome / Edge）、iPhone は USB キーボード（キーヤーの出力を F13 キーとして送る）。

## アプリを開く

- **iPhone・PC**：https://kajiyajp.github.io/cw-keyer-trainer/
- **PC でローカルに起動**（[Node.js](https://nodejs.org/) が必要）：

```powershell
./tools/serve.ps1
```

→ http://localhost:8000/ を Chrome / Edge で開きます（ポートを変えるときは `-Port 8001`）。

## 部品

| 部品 | 内容 |
|---|---|
| マイコン | Seeed XIAO RP2040 |
| 表示 | 0.96 インチ OLED SSD1306（I2C、4 ピン） |
| ブザー | パッシブ型の圧電ブザー |
| ボタン | タクトスイッチ 2 個（MENU / OK） |
| パドル接続 | 3.5mm ステレオジャック（先端＝短点、リング＝長点、根元＝GND） |
| パドル | 市販のパドル（3.5mm ステレオプラグ） |

## 配線

![配線図](docs/wiring.png)

| ピン | 用途 |
|---|---|
| D0 / D1 | 短点 / 長点（内部プルアップ、押すと GND） |
| D2 | ブザー（PWM） |
| D3 / D6 | MENU / OK ボタン |
| D4 / D5 | OLED SDA / SCL |

## ファームウェアを書き込む

[PlatformIO](https://platformio.org/) を使います。

```powershell
cd firmware
pio run -t upload
```

書き込めないときは、XIAO の BOOT ボタンを押しながら USB をつなぎ直してから実行します。

テスト：

```powershell
cd firmware
pio test -e native
```

```powershell
cd app
npm test
```

## ケース

準備中です（3D プリント用の STEP / STL を公開する予定）。

## ドキュメント

- [設計書](docs/cw-trainer-design.md)
- [HID キーの確認ページ](tools/hid_test.html)（ダウンロードしてブラウザで開き、iPhone で F13 が届くか確かめる）

## ライセンス

[MIT](LICENSE)
