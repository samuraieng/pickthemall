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
from analyze_wgraph.analyze_wgraph import AnalyzeWGraph


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='pickthemall, calculate some stock information')
    parser = Post2BlogSpot.add_arguments(parser)
    parser = Post2X.add_arguments(parser)
    parser = Stock_Code_TSE.add_arguments(parser)
    parser = AnalyzeWGraph.add_arguments(parser)
    args = parser.parse_args()

    bSend2Blogger = args.s2b
    bSend2X = args.s2x

    #codeT = ['XXXX.T']
    codeT = None

    strCode = args.code
    if strCode is not None:
        if not strCode.endswith(".T"):
            strCode = strCode + ".T"
        codeT = [strCode]

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

    # Plotting
    awg = AnalyzeWGraph(args)
    awg.end_date = end_date
    if strCode is not None:
        awg.AnalyzeWGraph(sa.summary_dict[0]["Period"])
    elif len(sa.codes) > 0:
        for code in sa.codes:
            bFound = False
            awg.code = None
            if not code.endswith(".T"):
                code = code + ".T"
            for i in range(len(sa.codes)):
                if code == sa.summary_dict[i]["ticker"]:
                    bFound = True
                    awg.code = code[:-2]
                    break
            if bFound:
                awg.AnalyzeWGraph(sa.summary_dict[i]["Period"])
    # Upload images to Google Drive
    awg.fUploaded = []
    for file_path in tqdm(awg.fProceeded):
        code, result, url = awg.upload2googledrive(file_path)
        awg.fUploaded.append((code, result, url))

    pb = None
    if bSend2Blogger:    #Post to blogspot
        pb = Post2BlogSpot()
        print("\n\n -- Posting to blogspot --")
        strLabel = ['Pick them all', 'Trading logs']
        # Process single day (short)
        strTitle = f"{datetime.today().strftime('%Y-%m-%d')}の記録"
        strSubtitle = f"シミュレーション予想 (ハイライト)"
        strBody = sa.X_singleS
        postId = pb.post_to_blogger(strLabel, strTitle, strSubtitle, strBody)
        # Proceed single day (graph)
        if len(awg.fUploaded) > 0:
            sorted_data = sorted(awg.fUploaded, key=lambda x: 0 if "MATCH" in x[1] else 1 if "LOSE" in x[1] else 2 if "WIN" in x[1] else 3)
            for strCode, strResult, strURL in sorted_data:
                strSubtitle = f"シミュレーション予想 グラフ : {strCode} ({strResult})"
                img_tag = f'<img src="{strURL}" border="0" style="max-width:100%;" />'
                strBody = f"<div>{img_tag}</div>"
                pb.append_log_to_post(postId, strSubtitle, strBody)

        # Process single day (long)
        strSubtitle = f"シミュレーション予想 (詳細)"
        strBody = sa.X_singleL
        lines = sa.X_singleL.split('\n')
        strBody = '\n'.join(lines[-100:])
        pb.append_log_to_post_pre(postId, strSubtitle, strBody)

        # Process single day
        strSubtitle = f"シミュレーション結果(概要)"
        strBody = sa.X_summary
        pb.append_log_to_post_pre(postId, strSubtitle, strBody)

        # Process history day
        strSubtitle = f"シミュレーション結果(履歴)"
        strBody = sa.X_history
        lines = sa.X_history.split('\n')
        strBody = '\n'.join(lines[-100:])
        pb.append_log_to_post_pre(postId, strSubtitle, strBody)

        # Process single day
        strSubtitle = f"シミュレーション結果(結果)"
        strBody = sa.X_total
        pb.append_log_to_post_pre(postId, strSubtitle, strBody)

        # Process single day
        strSubtitle = "注意事項/免責事項"
        strBody = """<p>当ブログで提供する情報は、投資助言を目的としたものではありません。投資の最終決定はご自身の判断と責任において行ってください。<br>当ブログの情報に基づいて生じたいかなる損害についても、当ブログおよび筆者は一切の責任を負いません。</p>"""
        pb.append_log_to_post(postId, strSubtitle, strBody)

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
