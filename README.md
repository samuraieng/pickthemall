# pickthemall
Trading tool for Tokyo Stock Exchange
東証、プライムの値動きを見て、デイトレをしようとするチャレンジコードです。[目指せデイトレ](https://note.com/preview/n5e67416d0222?prev_access_key=fafba2e84d6760eb69fd690f4d91ecb1) で解説しているコード本体です。

## 関連リンク
- [目指せデイトレ (note記事)](https://note.com/preview/n5e67416d0222?prev_access_key=fafba2e84d6760eb69fd690f4d91ecb1)
- [blogspot 投稿](https://cdevguy.blogspot.com/)
- [x 投稿](https://x.com/pickthemall)

## 注意
ライセンスはAGPL v3です。Copy Leftにご協力ください。

## コマンド

```bash
$ python3 ./pickthemall.py --help
usage: pickthemall.py [-h] [--s2b] [--s2x] [--topx TOPX]

pickthemall, calculate some stock information

options:
  -h, --help            show this help message and exit
  --s2b, --send2Blogger
                        Enable to send to Blogger
  --s2x, --send2X       Enable to send to X
  --topx TOPX, --topX TOPX
                        Number of top stocks to get
```

## インストール

```bash
$ git clone https://github.com/samuraieng/pickthemall.git
$ cd pickthemall
$ pip install -r requirements.txt
```

### ファイル構成

cloneしたファイル以外にも、pickthemall_oauth.jsonが必要。
実行後に生成されるファイルは、次のファイル
- pickthemall_token.json
- tse_codes.txt
- tse_vol_topX.txt

```bash
├── LICENSE
├── pickthemall_oauth.json
├── pickthemall.py
├── pickthemall_token.json
├── post2blogspot
│   ├── __init__.py
│   └── post2blogspot.py
├── post2x
│   ├── __init__.py
│   ├── post2blogspot
│   │   ├── __init__.py
│   │   └── post2blogspot.py
│   └── post2x.py
├── README.md
├── requirements.txt
├── stock_analyzer
│   ├── __init__.py
│   └── stock_analyzer.py
├── stock_code_tse
│   ├── __init__.py
│   └── stock_code_tse.py
├── tse_codes.txt
└── tse_vol_topX.txt
```

**各種自動投稿について (oauth.jsonなど)**

blogspotに自動投稿するために必要なもので、今回のメインスコープではないため、説明は省略。取得したい場合は、Google Cloudから取得可能</br>
X.comへの投稿も同じ。自動投稿するための儀式があるので、その対応が必要。
これらに関係した設定は、環境変数で管理しています。

## 解説

|ファイル名|説明|
|---|---|
|pickthemall.py|メインファイル|
|post2blogspot.py|blogspot投稿用ファイル|
|post2x.py|X.com投稿用ファイル|
|stock_analyzer.py|株式分析用ファイル|
|stock_code_tse.py|東証コード取得用ファイル|
|tse_codes.txt|東証コード一覧 (自動生成)|
|tse_vol_topX.txt|東証取引量上位一覧 (自動生成)|

