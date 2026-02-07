
import pandas as pd
import re
import yfinance as yf

from datetime import datetime, timedelta
from tqdm import tqdm

from stock_code_tse.stock_code_tse import Stock_Code_TSE

class StockAnalyzer:
    def __init__(self, args):
        self.args = args
        self.codeT = None
        self.ticker = None
        self.df = None
        self.name = None
        self.y_window = [3, 5, 7]
        self.trend_days = [5, 10, 15]
        self.summary_dict = []  #Summary Data Storage (stock.T base)
        self.single_dict = [] #for sigle
        self.total_summary = [] #for Total

        self.caller = ""
        self.fTODAY = False # when no "now" date exists
        self.bDprint = False

        self.X_history = "" #売買タイミング履歴
        self.X_singleL = ""  #今日の結果
        self.X_singleS = ""  #今日の結果
        self.X_summary = "" #銘柄個別の詳細
        self.X_total = ""   #総合計

        #Get stock code from TSE
        self.sctse = Stock_Code_TSE(self.args)
        #self.codeT = self.sctse.get_tse_prime_codes()
        self.codeT = self.sctse.get_volume_topX()

    def dPrint(self, bFlag, inText, eCode=None):
        if bFlag:
            if eCode is None:
                print(inText)
            else:
                print(inText, end=eCode)

    def PrintSummary(self):
        '''
            print self.summary_dict
        '''
        #---Print final results---
        self.dPrint(self.bDprint, f"\n\n\n---Single {self.code} {self.name} ---")
        df_single = pd.DataFrame(self.single_dict)
        self.dPrint(self.bDprint, df_single.to_string())

        self.dPrint(self.bDprint, f"\n---Period {self.code} {self.name}---")
        # DataFrame に変換
        df_period = pd.DataFrame(self.period_summary)
        self.dPrint(self.bDprint, df_period[df_period['match3'] | df_period['match5'] | df_period['match7']].to_string(index=False))
        
        return True

    def PrintSummaryTotalSum(self):
        '''
        retval = {}
        code, tret, win3, lose3, wrate3, tret3, win3, lose5, wrate5, tret5, win7, lose7, wrate7, tret7
        '''

        row = {}
        row['code'] = self.code

        df_period = pd.DataFrame(self.period_summary)
        df_period["diff"] = df_period["diff"].astype(float)

        for Y in self.y_window:
            #row[f'tret{Y}'] = df_period[df_period[f"match{Y}"]]["diff"].sum()
            tmp = df_period[f'treturn{Y}'].iloc[-1]
            row[f'tret{Y}'] = f"{float(tmp):.1f}"
            self.dPrint(False, f"tret{Y}: {row[f'tret{Y}']}")
            row[f'winCnt{Y}']  = (df_period[f"winlose{Y}"] == "WIN").sum()
            row[f'loseCnt{Y}']  = (df_period[f"winlose{Y}"] == "LOSE").sum()

            try:
                row[f'wlrate{Y}'] = float(f"{(float(row[f'winCnt{Y}']) / float(row[f'winCnt{Y}'] + row[f'loseCnt{Y}'])):.2f}")
            except:
                row[f'wlrate{Y}'] = float(0)

        # for matchA
        row[f'tretA'] = float(row['tret3']) + float(row['tret5']) + float(row['tret7'])
        row[f'winCntA']  = row['winCnt3'] + row['winCnt5'] + row['winCnt7']
        row[f'loseCntA'] = row['loseCnt3'] + row['loseCnt5'] + row['loseCnt7']
        try:
            row[f'wlrateA'] = float(f"{(float(row[f'winCntA']) / float(row[f'winCntA'] + row[f'loseCntA'])):.2f}")
        except:
            row[f'wlrateA'] = float(0)

        self.total_summary.append(row.copy())

        if self.bDprint:
            df = pd.DataFrame([row])
            print("--- TotalSum ---")
            print(df.to_string(index=False))

        return True

    def PrintSummaryFormat1(self):
        '''
        Merge all ticker data into "date" basis. Print date orders
        '''
        all_rows = []

        for row in self.summary_dict:
            ticker = row["ticker"]
            name = row["name"]
            df = row["rPeriod"]

            # ticker / name を period_summary 側にくっつける
            df2 = pd.DataFrame(df).copy()
            df2["ticker"] = ticker
            df2["name"] = name

            all_rows.append(df2)

        # でっかい DF にまとめる
        merged = pd.concat(all_rows, ignore_index=True)

        # 日付で sort（必要なら to_datetime して）
        merged["date"] = pd.to_datetime(merged["date"])
        merged = merged.sort_values("date")

        # ---- ここが重要 ----
        # 表示順を「ticker, name → period_summaryの列」にする
        cols = ["date", "ticker", "name"] + [c for c in merged.columns 
                                            if c not in ("date", "ticker", "name")]
        merged = merged[cols]
        cond = ((merged["match3"]) | (merged["match5"]) | (merged["match7"]) | 
                 merged["winlose3"].isin(["WIN", "LOSE"]) |
                 merged["winlose5"].isin(["WIN", "LOSE"]) |
                 merged["winlose7"].isin(["WIN", "LOSE"]))
               
        self.dPrint(self.bDprint, "\n--- Print Sum Format1")

        outText = merged[cond].to_string(index=False)
        self.dPrint(self.bDprint, outText)
        self.X_history = outText

        return True

    def PrintSummaryTotalReturnList(self):

        self.dPrint(self.bDprint, "\n\n---Total Returns---")
        df = pd.DataFrame(self.total_summary)
        # tretAの大きい順にソート
        df = df.sort_values(by="tretA", ascending=False)
        outText = df.to_string(index=False)
        self.X_summary = outText
        self.dPrint(self.bDprint, self.X_summary)

        # --- 合計の合計 ---
        tsum = {}
        tsum['Rule3'] = pd.to_numeric(df['tret3'], errors='coerce').sum()
        tsum['Rule5'] = pd.to_numeric(df['tret5'], errors='coerce').sum()
        tsum['Rule7'] = pd.to_numeric(df['tret7'], errors='coerce').sum()
        tsum['RuleA'] = pd.to_numeric(df['tretA'], errors='coerce').sum()

        self.dPrint(self.bDprint, "\n---Total Return Sum---")
        df = pd.DataFrame([tsum])
        outText = df.to_string(index=False)
        self.X_total = outText
        self.dPrint(self.bDprint, self.X_total)

        return True

    def PrintSummarySingleDayBasis(self, bShort=False):
        df = pd.DataFrame(self.single_dict)

        self.dPrint(self.bDprint, f"\n---Single Day {bShort} ---")
        if bShort:
            showCols = ['code', 'date', 'close', 'diff', 'match3', 'treturn3', 'winrate3', 'match5', 'treturn5', 'winrate5', 'match7', 'treturn7', 'winrate7']
            df = df[showCols]
            df = df[df["match3"] | df["match5"] | df["match7"]]
            if df.size > 0:
                self.X_singleS = df.to_string(index=False)
                self.X_singleS = re.sub(r'diff', '前日比', self.X_singleS)
                self.X_singleS = re.sub(r'match', '買い', self.X_singleS)
                self.X_singleS = re.sub(r'treturn', '儲け', self.X_singleS)
                self.X_singleS = re.sub(r'winrate', '勝率', self.X_singleS)
            else:
                self.X_singleS = "No Data"
            outText = self.X_singleS
        else:
            showCols = ['code', 'date', 'close', 'diff', "f1_3", "f2_3", 'match3', 'treturn3', 'winrate3', "f1_5", "f2_5", 'match5', 'treturn5', 'winrate5', "f1_7", "f2_7", 'match7', 'treturn7', 'winrate7']
            df = df[showCols]
            self.X_singleL = df.to_string(index=False)
            outText = self.X_singleL

        self.dPrint(self.bDprint, outText)

        return outText

    def load(self, end_date, period=None):
        if period is None:
            try:
                temp = int((pd.Timestamp(end_date)-pd.Timestamp('2024-01-01')).days * 1.25)
                period = f"{temp}d"
            except:
                temp = int((pd.Timestamp(end_date)-pd.Timestamp('2024-01-01', tz='Asia/Tokyo')).days * 1.25)
                period = f"{temp}d"
        
        self.ticker = yf.Ticker(self.code)

        df = self.ticker.history(period=period, interval="1d")
        df.index = pd.to_datetime(df.index).normalize()

        self.df = df
        df = None

        self.df = self.df.sort_index()
        self.df = self.df[~self.df.index.duplicated(keep="last")]

        self.df["diff"] = self.df["Close"] - self.df["Open"]
        info = self.ticker.get_info()
        self.name = info.get("longName", self.code)

    # --- フラグ1: 上り調子判定 ---
    def check_flag1(self, end_date, trend_days):
        '''
        移動平均を求めるコード
        旧コード
        for p in moving_window:   #移動平均間隔 (x日)
            df[f'MA{p}'] = df['Diff'].rolling(window=p).mean()
            df[f'Is_Uptrend{p}'] = df[f'MA{p}'].diff() > 0    #p日移動平均が上昇 = Is_Uptrend{p}
        '''

        self.dPrint(False, f"trend_days in F1: {trend_days}")

        idx = self.df.index.get_loc(end_date)

        # ma を計算するために最低 trend_days + 15 本必要
        need = trend_days + 15
        if idx < need: 
            return False

        # 必要な範囲を切り出す
        recent = self.df.iloc[idx-need:idx+1]["Close"]
        # ma を計算
        ma = recent.rolling(window=trend_days).mean().dropna()
        
        ## 直近 trend_days の ma を取り出す
        ma_recent = ma.tail(trend_days)
        diffs = ma_recent.diff().dropna()
        cUp = (diffs > 0).sum()
        cDw = (diffs <= 0).sum()
        if cUp > 0 and cDw > 0:
            ratio = cUp / (cDw + cUp)     #割合を出す
        else:
            ratio = 0
        
        retval = True if ratio > 1/2 else False
        retval = (diffs > 0).all()   #ma on each day must be higher than previous days

        self.dPrint(False, f"trend: {trend_days}, ma_r: {ma_recent}, retval: {retval}")

        return retval

    # --- フラグ2: 過去y_window日間のdiffチェック ---
    def check_flag2(self, end_date, Y):
        '''
            "-", "-", "+" 直近が"+"で、その前連続して"-"をチェック
        '''
        self.dPrint(False, f"\nThis turn's enddate(window {Y}): {end_date}")
        if self.df is None:
            raise ValueError("Call load() first")

        idx = self.df.index.get_loc(end_date)
        last_idx = len(self.df.index) - 1       #for debug.

        # 最新の情報を処理する(TRUE)、昨日以前(False)
        retval = False
        # End_date-1がプラス
        prev1 = self.df.iloc[idx:idx+1]
        if prev1["diff"].min() > 0:                     #一番最新(end_date)がプラスであり、
            # End_date-2 から Y 日間が全部マイナス
            start_idx = idx - Y + 1
            if start_idx >= 0:
                window = self.df.iloc[start_idx:idx]    #end_date-1 から Y 日間を確保
                retval = True if window["diff"].max() <= 0 else False

        return retval

    # --- 単日評価 ---
    def evaluate(self, check_date, y_window=None, trend_days=None):
        bDprint = False
        self.fTODAY = False

        if y_window is None:
            y_window = self.y_window[0]
        if trend_days is None:
            trend_days = self.trend_days[0]

        # check end_date is in self.df.
        # iは未使用。dfからcheck_dateを取得するのに使っているだけ
        try:
            self.yidx = self.df.index.get_loc(check_date)
        except:
            check_date = self.df.index.max() #最大日付のidxにあたる日付を取得
            self.yidx = self.df.index.get_loc(check_date)
            self.fTODAY = True #end_dateで引っ掛けられない = 最新の日付(=TODAYと命名)
        self.yidx = self.yidx - 1

        f1 = self.check_flag1(check_date, trend_days)
        f2 = self.check_flag2(check_date, y_window)

        result = None
        row = self.df.loc[check_date]

        if f1 and f2:
            strWinLose = "WIN" if row["diff"] > 0 else "LOSE"
        else:
            strWinLose = "NA"

        result = {
            "date": str(check_date.date()),
            "diff": f"{row['diff']:3.1f}",
            "close": f"{row['Close']:3.1f}",
            f"f1_{y_window}": bool(f1),
            f"f2_{y_window}": bool(f2),
            f"match{y_window}": bool(f1 and f2),
            f"winlose{y_window}":strWinLose
        }

        self.dPrint(bDprint, f'In Eva: {result}')
        return result

    def evaluate_single(self, end_date, trend_days=None):
        '''
        y_windowで回す必要があるため、evaluate()を直接呼ばず、evaluate_single経由で呼ぶ
        y_window引数は削除。回すため。
        '''
        self.caller = "single"

        row_dict = self.period_summary[-1]

        if False:
            row_dict = {}
            row_dict['date'] = row_last['date']
            row_dict['close'] = row_last['close']
            row_dict['diff'] = row_last['diff']
            for ydx in self.y_window:
                row_dict[f"f1_{ydx}"] = row_last[f"f1_{ydx}"]      
                row_dict[f"f2_{ydx}"] = row_last[f"f2_{ydx}"]
                row_dict[f"match{ydx}"] = row_last[f"match{ydx}"]
                row_dict[f"winlose{ydx}"] = row_last[f"winlose{ydx}"]
                row_dict[f'treturn{ydx}'] = row_last[f'treturn{ydx}']
                row_dict[f'win{ydx}'] = row_last[f'win{ydx}']
                row_dict[f'lose{ydx}'] = row_last[f'lose{ydx}']
                row_dict[f'winrate{ydx}'] = row_last[f'winrate{ydx}']

        single = {'code': self.code, **row_dict}
        self.single_dict.append(single.copy())

        return single

    def set_valid_date(self, start_date = None, end_date = None):
        tsDate = None

        if start_date is not None:
            tgtDate = start_date
            intDelta = int(1)
        elif end_date is not None:
            tgtDate = end_date
            intDelta = int(-1)
            intDelta = int(0)
        else:
            start_date = None
            end_date = None
            tsDate = None
            intDelta = int(0)

        try:
            tgtDate = tgtDate.tz_localize("Asia/Tokyo")
        except:
            tgtDate = pd.Timestamp(tgtDate).tz_convert("Asia/Tokyo")
        
        tgtDate = pd.Timestamp(tgtDate).normalize()

        #print(f"日付: {tgtDate}, 型: {type(tgtDate)}")
        #print("df tz       : ", self.df.index.tz, "    startdate tz: ", tgtDate.tzinfo, "    delta: ", intDelta)
        try:
            tsDate = self.df.index.get_loc(tgtDate)
        except KeyError:
            tgtDate = tgtDate + pd.Timedelta(days=intDelta)
            if intDelta > 0:
                tsDate = self.set_valid_date(start_date = tgtDate)
            elif intDelta < 0:
                tsDate = self.set_valid_date(end_date = tgtDate)
            else:
                tsDate = None
        
        return tsDate

    # --- 期間評価: 投資開始日からEnd_dateまでのTotal Return ---
    def evaluate_range(self, investment_start, end_date, y_window=None, trend_days=None):
        self.caller = "range"

        if y_window is None:
            y_window = self.y_window
        if trend_days is None:
            trend_days = self.trend_days[0]

        start = self.set_valid_date(start_date=investment_start)
        end = self.set_valid_date(end_date=end_date)
        df_slice = self.df.iloc[start:end]

        results = []
        row_dict = {}
        for ydx in y_window:
            row_dict['date'] = None
            row_dict['close'] = float(0)
            row_dict['diff'] = float(0)
            row_dict[f"f1_{ydx}"] = None     
            row_dict[f"f2_{ydx}"] = None
            row_dict[f"match{ydx}"] = None
            row_dict[f"winlose{ydx}"] = ""
            row_dict[f'treturn{ydx}'] = f"{float(0):.2f}"
            row_dict[f'win{ydx}'] = int(0)
            row_dict[f'lose{ydx}'] = int(0)
            row_dict[f'winrate{ydx}'] = float(0)

        for idx in df_slice.index:
            for ii, ydx in enumerate(y_window):
                pre_dict = row_dict.copy()

                trend_days = self.trend_days[ii]
                r = self.evaluate(idx, ydx, trend_days)

                if row_dict['date'] != r['date']:
                    row_dict['date'] = r['date']
                    row_dict['close'] = r['close']
                    row_dict['diff'] = r['diff']
                row_dict[f"f1_{ydx}"] = r[f"f1_{ydx}"]     
                row_dict[f"f2_{ydx}"] = r[f"f2_{ydx}"]
                row_dict[f"match{ydx}"] = r[f"match{ydx}"]
                row_dict[f"winlose{ydx}"] = "NA"

                # diff は常にその日の値
                diff = f"{float(row_dict['diff']):.2f}"

                if pre_dict[f"match{ydx}"]:
                    row_dict[f'treturn{ydx}'] = float(row_dict[f'treturn{ydx}']) + float(diff)  # match日だけ累積加算
                    bJudge = True if float(diff) > 0 else False
                    if bJudge:
                        row_dict[f'win{ydx}'] += 1
                        row_dict[f'winlose{ydx}'] = "WIN"
                    else:
                        row_dict[f'lose{ydx}'] += 1
                        row_dict[f'winlose{ydx}'] = "LOSE"

                try:
                    if (row_dict[f'win{ydx}'] is not None and row_dict[f'lose{ydx}'] is not None) and (row_dict[f'win{ydx}'] + row_dict[f'lose{ydx}']) > 0:
                        row_dict[f'winrate{ydx}'] = f"{row_dict[f'win{ydx}'] / (row_dict[f'win{ydx}'] + row_dict[f'lose{ydx}']):.2f}"
                    else:
                        row_dict[f'winrate{ydx}'] = 0
                except:
                    row_dict[f'win{ydx}'] = 0
                    row_dict[f'lose{ydx}'] = 0
                    row_dict[f'winrate{ydx}'] = 0

            results.append(row_dict.copy())

        return results

    # --- メイン分析 ---
    def analyze(self, investment_start, end_date, y_window=None, trend_days=None):
        bDprint = False

        if y_window is not None:
            self.y_window = [f'{y_window}']
        if trend_days is not None:
            self.trend_days = [f'{trend_days}']

        #print(self.codeT.columns)
        for self.code in tqdm(self.codeT['コード'], desc="codeT"):
            self.dPrint(bDprint, f"code: {self.code}")
            if not self.code.endswith('T'):
                self.code = f"{self.code}.T"
            self.dPrint(bDprint, f"\n--- Start loading ed: {end_date} ---")
            self.load(end_date)
            self.dPrint(bDprint, "\n\n--- Start range ---")
            self.period_summary = self.evaluate_range(investment_start, end_date, y_window, trend_days)
            self.dPrint(bDprint, "\n\n--- Start Single ---")
            self.single_day = self.evaluate_single(end_date, trend_days)
            self.caller = ""
            pass

            row_dict = {
                "ticker": self.code,
                "name": self.name,
                "rSingle": self.single_day,
                "rPeriod": self.period_summary
            }

            self.summary_dict.append(row_dict)
            self.PrintSummary()   # stock code/ticker単位で印刷
            self.PrintSummaryTotalSum()
    
        return self.summary_dict
