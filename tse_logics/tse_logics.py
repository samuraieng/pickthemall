class TSE_logics:
    def __init__(self, sa):
        self.sa = sa
        pass

    def dPrint(self, bFlag, inText, eCode=None):
        if bFlag:
            if eCode is None:
                print(inText)
            else:
                print(inText, end=eCode)


    # --- フラグ1: 上り調子判定 ---
    def check_trendMA(self, end_date, trend_days):
        '''
        移動平均を求めるコード
        旧コード
        for p in moving_window:   #移動平均間隔 (x日)
            df[f'MA{p}'] = df['Diff'].rolling(window=p).mean()
            df[f'Is_Uptrend{p}'] = df[f'MA{p}'].diff() > 0    #p日移動平均が上昇 = Is_Uptrend{p}
        '''

        self.dPrint(False, f"trend_days in F1: {trend_days}")

        idx = self.sa.df.index.get_loc(end_date)

        # ma を計算するために最低 trend_days + 15 本必要
        need = trend_days + 15
        if idx < need: 
            return False

        # 必要な範囲を切り出す
        recent = self.sa.df.iloc[idx-need:idx+1]["Close"]
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
    def check_trendMMP(self, end_date, Y):
        '''
            "-(M)", "-(M)", "+(P)" 直近が"+"で、その前連続して"-"をチェック
        '''
        self.dPrint(False, f"\nThis turn's enddate(window {Y}): {end_date}")
        if self.sa.df is None:
            raise ValueError("Call load() first")

        idx = self.sa.df.index.get_loc(end_date)
        last_idx = len(self.sa.df.index) - 1       #for debug.

        # 最新の情報を処理する(TRUE)、昨日以前(False)
        retval = False
        # End_date-1がプラス
        prev1 = self.sa.df.iloc[idx:idx+1]
        if prev1["Diff"].min() > 0:                     #一番最新(end_date)がプラスであり、
            # End_date-2 から Y 日間が全部マイナス
            start_idx = idx - Y + 1
            if start_idx >= 0:
                window = self.sa.df.iloc[start_idx:idx]    #end_date-1 から Y 日間を確保
                retval = True if window["Diff"].max() <= 0 else False

        return retval

    def get_flag_TrendMA_TrendMMP(self, end_date, trend_days, y_window):
        self.f1 = self.check_trendMA(end_date, trend_days)
        self.f2 = self.check_trendMMP(end_date, y_window)
        return (self.f1 and self.f2), self.f1, self.f2

