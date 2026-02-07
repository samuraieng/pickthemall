import argparse
import pandas as pd
import yfinance as yf
from pathlib import Path
from tqdm import tqdm

class Stock_Code_TSE:
    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--topx', '--topX', type=int, default=50, help='Number of top stocks to get')
        return parser

    def __init__(self, args):
        self.codes = None
        self.topX = 50 if args is None else args.topx
        self.outFile = "tse_codes.txt"
        self.volFile = "tse_vol_topX.txt"

        self.bDprint = False

        # JPX公式の統計資料（銘柄一覧Excel）のURL
        self.URL = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"

    def dPrint(self, bFlag, inText, eCode=None):
        if bFlag:
            if eCode is None:
                print(inText)
            else:
                print(inText, end=eCode)

    def get_tse_prime_codes(self):
        if Path(self.outFile).exists():
            #FIle existed
            self.codes = pd.read_csv(self.outFile, header=None)
            self.codes.columns = ['コード', '銘柄名']
        else:
            #self.outfile is not existed
            #Read from URL
            # Excelを読み込み（直接URLを指定できます）
            df = pd.read_excel(self.URL)
            
            # 市場区分が「プライム（内国株式）」のものを抽出
            # ※JPXのファイル形式に合わせ、「市場・商品区分」列を使用します
            prime_df = df[df['市場・商品区分'] == 'プライム（内国株式）']
            
            # 証券コードと銘柄名だけをリスト化
            # 証券コードは通常「コード」列にあります
            self.codes = prime_df[['コード', '銘柄名']].copy()
            if len(self.codes) > 1500:
                self.codes.to_csv(self.outFile, index=False, header=False)

        self.dPrint(self.bDprint, self.codes.to_string(), "\n")
        return self.codes

    def get_volume_topX(self):
        """
        東証プライム市場の取引高トップXを取得
        """
            
        if Path(self.volFile).exists():
            #FIle existed
            self.codes = pd.read_csv(self.volFile, header=None)
            self.codes.columns = ['コード', '銘柄名', '出来高', '終値', '閉開差']
        else:
            if self.codes is None:
                self.get_tse_prime_codes()

            # 逐次処理
            results = []
            for code in tqdm(self.codes['コード'],desc="Generating rank"):
                results.append(self.fetch_stock_data(code))

            # 有効なデータのみフィルタ
            valid_results = [r for r in results if r is not None]
            
            self.codes = pd.DataFrame(valid_results)
            #print(self.codes)
            self.codes.to_csv(self.volFile, index=False, header=False)

        # 取引高でソートしてトップX
        self.codes = self.codes.nlargest(self.topX, '出来高')
        
        #self.dPrint(self.bDprint, self.codes)
        return self.codes

    def fetch_stock_data(self, code):
        """個別銘柄データを取得"""
        try:
            ticker = f"{code}.T"  # 東証銘柄は.Tを付ける
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 今日の取引データ取得
            #hist = stock.history(period="1d", interval="1d")
            hist = stock.history(period="1d")
            if not hist.empty:
                volume = hist['Volume'].iloc[-1]
                return {
                    'コード': code,
                    '銘柄名': info.get('shortName', info.get('longName', 'N/A')),
                    '出来高': int(volume),
                    '終値': hist['Close'].iloc[-1],
                    '閉開差': hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                }
        except:
            print(f"Error fetching data for {code}")
            pass

        return None
