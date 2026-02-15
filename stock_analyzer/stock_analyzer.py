
import pandas as pd
import re
import yfinance as yf

from datetime import datetime, timedelta
from tqdm import tqdm

from stock_code_tse.stock_code_tse import Stock_Code_TSE
from tse_logics.tse_logics import TSE_logics

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

        self.codes = []

        #Get stock code from TSE
        self.sctse = Stock_Code_TSE(self.args)
        self.codeT = self.sctse.get_volume_topX()

        self.flags = TSE_logics(self)

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
        self.dPrint(self.bDprint, df_period[df_period['Match3'] | df_period['Match5'] | df_period['Match7']].to_string(index=False))
        
        return True

    def PrintSummaryTotalSum(self):
        '''
        retval = {}
        code, tret, win3, lose3, wrate3, tret3, win3, lose5, wrate5, tret5, win7, lose7, wrate7, tret7
        '''

        row = {}
        row['code'] = self.code

        df_period = pd.DataFrame(self.period_summary)
        df_period["Diff"] = df_period["Diff"].astype(float)

        for Y in self.y_window:
            tmp = df_period[f'TReturn{Y}'].iloc[-1]
            row[f'TRet{Y}'] = f"{float(tmp):.1f}"
            self.dPrint(False, f"TRet{Y}: {row[f'TRet{Y}']}")
            row[f'WinCnt{Y}']  = (df_period[f"WinLose{Y}"] == "WIN").sum()
            row[f'LoseCnt{Y}']  = (df_period[f"WinLose{Y}"] == "LOSE").sum()

            try:
                row[f'Wlrate{Y}'] = float(f"{(float(row[f'WinCnt{Y}']) / float(row[f'WinCnt{Y}'] + row[f'LoseCnt{Y}'])):.2f}")
            except:
                row[f'Wlrate{Y}'] = float(0)

        # for matchA
        row[f'TRetA'] = float(row['TRet3']) + float(row['TRet5']) + float(row['TRet7'])
        row[f'WinCntA']  = row['WinCnt3'] + row['WinCnt5'] + row['WinCnt7']
        row[f'LoseCntA'] = row['LoseCnt3'] + row['LoseCnt5'] + row['LoseCnt7']
        try:
            row[f'WLRateA'] = float(f"{(float(row[f'WinCntA']) / float(row[f'WinCntA'] + row[f'LoseCntA'])):.2f}")
        except:
            row[f'WLRateA'] = float(0)

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
            df = row["Period"]

            # ticker / name を period_summary 側にくっつける
            df2 = pd.DataFrame(df).copy()
            df2["ticker"] = ticker
            df2["name"] = name

            all_rows.append(df2)

        # でっかい DF にまとめる
        merged = pd.concat(all_rows, ignore_index=True)

        # 日付で sort（必要なら to_datetime して）
        merged["Date"] = pd.to_datetime(merged["Date"])
        merged = merged.sort_values("Date")

        # ---- ここが重要 ----
        # 表示順を「ticker, name → period_summaryの列」にする
        cols = ["Date", "ticker", "name"] + [c for c in merged.columns 
                                            if c not in ("Date", "ticker", "name")]
        merged = merged[cols]
        cond = ((merged["Match3"]) | (merged["Match5"]) | (merged["Match7"]) | 
                 merged["WinLose3"].isin(["WIN", "LOSE"]) |
                 merged["WinLose5"].isin(["WIN", "LOSE"]) |
                 merged["WinLose7"].isin(["WIN", "LOSE"]))
               
        self.dPrint(self.bDprint, "\n--- Print Sum Format1")

        df_out = merged[cond]                     #nani日付順に履歴を保存
        outText = df_out.to_string(index=False)
        self.dPrint(self.bDprint, outText)
        self.X_history = outText

        df_out = df_out.sort_values(by=['WinRate3', 'Date'], ascending=[False, True]).reset_index(drop=True)
        self.codes = [c.split(".")[0] for c in df_out["ticker"].unique().tolist()]

        bOriginal = self.bDprint
        self.bDprint = True
        self.dPrint(self.bDprint, "\n codes")
        self.dPrint(self.bDprint, self.codes)
        self.bDprint = bOriginal

        return True

    def PrintSummaryTotalReturnList(self):

        self.dPrint(self.bDprint, "\n\n---Total Returns---")
        df = pd.DataFrame(self.total_summary)
        #TRetAの大きい順にソート
        df = df.sort_values(by="TRetA", ascending=False)
        outText = df.to_string(index=False)
        self.X_summary = outText
        self.dPrint(self.bDprint, self.X_summary)

        # --- 合計の合計 ---
        tsum = {}
        tsum['Rule3'] = pd.to_numeric(df['TRet3'], errors='coerce').sum()
        tsum['Rule5'] = pd.to_numeric(df['TRet5'], errors='coerce').sum()
        tsum['Rule7'] = pd.to_numeric(df['TRet7'], errors='coerce').sum()
        tsum['RuleA'] = pd.to_numeric(df['TRetA'], errors='coerce').sum()

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
            showCols = ['code', 'Date', 'Close', 'Diff', 'Match3', 'TReturn3', 'WinRate3', 'Match5', 'TReturn5', 'WinRate5', 'Match7', 'TReturn7', 'WinRate7']
            df = df[showCols]
            df = df[df["Match3"] | df["Match5"] | df["Match7"]]
            if df.size > 0:
                self.X_singleS = df.to_string(index=False)
                self.X_singleS = re.sub(r'Diff', '前日比', self.X_singleS)
                self.X_singleS = re.sub(r'Match', '買い', self.X_singleS)
                self.X_singleS = re.sub(r'TReturn', '儲け', self.X_singleS)
                self.X_singleS = re.sub(r'WinRate', '勝率', self.X_singleS)
            else:
                self.X_singleS = "No Data"
            outText = self.X_singleS
        else:
            showCols = ['code', 'Date', 'Close', 'Diff', "F1_3", "F2_3", 'Match3', 'TReturn3', 'WinRate3', "F1_5", "F2_5", 'Match5', 'TReturn5', 'WinRate5', "F1_7", "F2_7", 'Match7', 'TReturn7', 'WinRate7']
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

        # ★ ここが重要：index を tz-naive のまま日付正規化
        df.index = pd.to_datetime(df.index).normalize()

        self.df = df
        df = None

        self.df = self.df.sort_index()
        self.df = self.df[~self.df.index.duplicated(keep="last")]

        self.df["Diff"] = self.df["Close"] - self.df["Open"]
        info = self.ticker.get_info()
        self.name = info.get("longName", self.code)


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

        _, f1, f2 = self.flags.get_flag_TrendMA_TrendMMP(check_date, trend_days, y_window)

        result = None
        row = self.df.loc[check_date]

        if f1 and f2:
            strWinLose = "WIN" if row["Diff"] > 0 else "LOSE"
        else:
            strWinLose = "NA"

        result = {
            "Date": str(check_date.date()),
            "Diff": f"{row['Diff']:3.1f}",
            "Open": f"{row['Open']:3.1f}",
            "High": f"{row['High']:3.1f}",
            "Low": f"{row['Low']:3.1f}",
            "Close": f"{row['Close']:3.1f}",
            "Volume": f"{row['Volume']:3.1f}",
            f"F1_{y_window}": bool(f1),
            f"F2_{y_window}": bool(f2),
            f"Match{y_window}": bool(f1 and f2),
            f"WinLose{y_window}":strWinLose
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
            row_dict['Date'] = row_last['Date']
            row_dict['Close'] = row_last['Close']
            row_dict['Diff'] = row_last['Diff']
            for ydx in self.y_window:
                row_dict[f"F1_{ydx}"] = row_last[f"F1_{ydx}"]      
                row_dict[f"F2_{ydx}"] = row_last[f"F2_{ydx}"]
                row_dict[f"Match{ydx}"] = row_last[f"Match{ydx}"]
                row_dict[f"WinLose{ydx}"] = row_last[f"WinLose{ydx}"]
                row_dict[f'TReturn{ydx}'] = row_last[f'TReturn{ydx}']
                row_dict[f'Win{ydx}'] = row_last[f'Win{ydx}']
                row_dict[f'Lose{ydx}'] = row_last[f'Lose{ydx}']
                row_dict[f'WinRate{ydx}'] = row_last[f'WinRate{ydx}']

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
            row_dict['Date'] = None
            row_dict['Open'] = float(0)
            row_dict['High'] = float(0)
            row_dict['Low'] = float(0)
            row_dict['Close'] = float(0)
            row_dict['Diff'] = float(0)
            row_dict['Volume'] = float(0)
            row_dict[f"F1_{ydx}"] = None     
            row_dict[f"F2_{ydx}"] = None
            row_dict[f"Match{ydx}"] = None
            row_dict[f"WinLose{ydx}"] = ""
            row_dict[f'TReturn{ydx}'] = f"{float(0):.2f}"
            row_dict[f'Win{ydx}'] = int(0)
            row_dict[f'Lose{ydx}'] = int(0)
            row_dict[f'WinRate{ydx}'] = float(0)

        for idx in df_slice.index:
            for ii, ydx in enumerate(y_window):
                pre_dict = row_dict.copy()

                trend_days = self.trend_days[ii]
                r = self.evaluate(idx, ydx, trend_days)

                if row_dict['Date'] != r['Date']:
                    row_dict['Date'] = r['Date']
                    row_dict['Open'] = r['Open']
                    row_dict['High'] = r['High']
                    row_dict['Low'] = r['Low']
                    row_dict['Close'] = r['Close']
                    row_dict['Diff'] = r['Diff']
                    row_dict['Volume'] = r['Volume']
                row_dict[f"F1_{ydx}"] = r[f"F1_{ydx}"]     
                row_dict[f"F2_{ydx}"] = r[f"F2_{ydx}"]
                row_dict[f"Match{ydx}"] = r[f"Match{ydx}"]
                row_dict[f"WinLose{ydx}"] = "NA"

                # diff は常にその日の値
                diff = f"{float(row_dict['Diff']):.2f}"

                # winloseの判定は、昨日(pre_dict)のmatchに基づき、今日(row_dict)のdiffを評価する
                if pre_dict[f"Match{ydx}"]:
                    row_dict[f'TReturn{ydx}'] = float(row_dict[f'TReturn{ydx}']) + float(diff)  # match日だけ累積加算
                    bJudge = True if float(diff) > 0 else False
                    if bJudge:
                        row_dict[f'Win{ydx}'] += 1
                        row_dict[f'WinLose{ydx}'] = "WIN"
                    else:
                        row_dict[f'Lose{ydx}'] += 1
                        row_dict[f'WinLose{ydx}'] = "LOSE"

                try:
                    if (row_dict[f'Win{ydx}'] is not None and row_dict[f'Lose{ydx}'] is not None) and (row_dict[f'Win{ydx}'] + row_dict[f'Lose{ydx}']) > 0:
                        row_dict[f'WinRate{ydx}'] = f"{row_dict[f'Win{ydx}'] / (row_dict[f'Win{ydx}'] + row_dict[f'Lose{ydx}']):.2f}"
                    else:
                        row_dict[f'WinRate{ydx}'] = 0
                except:
                    row_dict[f'Win{ydx}'] = 0
                    row_dict[f'Lose{ydx}'] = 0
                    row_dict[f'WinRate{ydx}'] = 0

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
                "Single": self.single_day,
                "Period": self.period_summary
            }

            self.summary_dict.append(row_dict)
            self.PrintSummary()   # stock code/ticker単位で印刷
            self.PrintSummaryTotalSum()
    
        return self.summary_dict
