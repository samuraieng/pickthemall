import argparse
import os
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from tqdm import tqdm

from post2blogspot.post2blogspot import Post2BlogSpot
from post2x.post2x import Post2X
from stock_analyzer.stock_analyzer import StockAnalyzer
from stock_code_tse.stock_code_tse import Stock_Code_TSE


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='pickthemall, calculate some stock information')
    parser = Post2BlogSpot.add_arguments(parser)
    parser = Post2X.add_arguments(parser)
    parser = Stock_Code_TSE.add_arguments(parser)
    args = parser.parse_args()

    bSend2Blogger = args.s2b
    bSend2X = args.s2x

    #codeT = ['XXXX.T']
    codeT = None
    start_date = pd.Timestamp("2025-01-01", tz="Asia/Tokyo")
    end_date = pd.Timestamp.today()

    sa = StockAnalyzer(args)
    if codeT is not None:
        sa.codeT = pd.DataFrame(codeT, columns=['コード'])
    r = sa.analyze(start_date, end_date)

    sa.bDprint = True
    print(f"\n\n -- Final Results (print:{sa.bDprint})--")
    sa.PrintSummaryFormat1()
    strTextL = sa.PrintSummarySingleDayBasis(bShort=False)
    sa.PrintSummaryTotalReturnList()
    strTextS = sa.PrintSummarySingleDayBasis(bShort=True)

    pb = None
    if bSend2Blogger:    #Post to blogspot
        pb = Post2BlogSpot()
        print("\n\n -- Posting to blogspot --")
        strLabel = ['Pick them all', 'Trading logs']
        # Process single day (short)
        strTitle = f"{datetime.today().strftime('%Y-%m-%d')}の記録"
        strSubtitle = f"シミュレーション予想 (ハイライト)"
        stbBody = sa.X_singleS
        postId = pb.post_to_blogger(strLabel, strTitle, strSubtitle, stbBody)
        # Process single day (long)
        strSubtitle = f"シミュレーション予想 (詳細)"
        stbBody = sa.X_singleL
        pb.append_log_to_post(postId, strSubtitle, stbBody)
        # Process single day
        strSubtitle = f"シミュレーション結果(概要)"
        stbBody = sa.X_summary
        pb.append_log_to_post(postId, strSubtitle, stbBody)
        # Process history day
        strSubtitle = f"シミュレーション結果(履歴)"
        stbBody = sa.X_history
        pb.append_log_to_post(postId, strSubtitle, stbBody)
        # Process single day
        strSubtitle = f"シミュレーション結果(結果)"
        stbBody = sa.X_total
        pb.append_log_to_post(postId, strSubtitle, stbBody)

    if bSend2X:   #Tweeting to X
        tx = Post2X()
        print("\n\n -- Posting to X --")
        tx.send2X = True
        tx.intVal = 60
        if pb is not None:
            inText = f"Today’s update was completed: \n{pb.posted}"
        else:
            inText = "Today’s update was completed"
        tx.tweet(inText)

    pass
