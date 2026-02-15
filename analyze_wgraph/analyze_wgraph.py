import mplfinance as mpf
import os
import pandas as pd
from tqdm import tqdm

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials

from datetime import timedelta

class AnalyzeWGraph:
    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--code', default=None, type=str, help='TSE Code without .T')
        return parser

    def __init__(self, args):
        self.code = args.code
        self.end_date = None
        self.fProceeded = []
        self.fpass = "charts"

        if self.code is not None and not self.code.endswith(".T"):
            self.code = self.code + ".T"

        #For google APIs
        self.foauth = 'pickthemall_oauth.json'      #You need to prepare your own oauth file
        self.ftoken = 'pickthemall_token.json'      #You need to prepare your own token file
        self.fsrvac = 'pickthemall_gdrive.json'     #You need to prepare your own service account file

        # GoogleDrive, Bloggerのフルアクセス権限
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/blogger'
            ]

        self.fgdf_id = '[YOUR_FILE_ID]' #Please set your file_id provided by Google Drive
        self.creds = self.get_credentials()
        self.service = build('drive', 'v3', credentials=self.creds)

        pass

    def AnalyzeWGraph(self, graphdat):
        df = pd.DataFrame(graphdat)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        bShifted = False
        if self.end_date is None:
            self.end_date = df.index.max()
        else:
            if self.end_date not in df.index:
                self.end_date = min(self.end_date, df.index.max())
                bShifted = True

        cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        colors = mpf.make_marketcolors(up='white', down='navy',
                                       edge='black',
                                       wick='black',
                                       volume='gray')

        # スタイルの作成
        my_style = mpf.make_mpf_style(
            marketcolors=colors,
            gridcolor='lightgray',
            gridstyle='--',
            gridaxis='horizontal'
            )

        # MATCHの行だけを抽出
        trgtcols_Buy = ['Match3', 'Match5', 'Match7']
        trgtDate_Buy = df[df[trgtcols_Buy].any(axis=1)].index
        strMsg_Buy = "Buy"

        # WIN/LOSEの行だけを抽出
        trgtcols_WL = ['WinLose3', 'WinLose5', 'WinLose7']
        trgtDate_WL = df[df[trgtcols_WL].isin(['WIN', 'LOSE']).any(axis=1)].index
        strMsg_WL = "WL"

        trgtcols = trgtcols_Buy + trgtcols_WL
        trgtDate = trgtDate_Buy.union(trgtDate_WL)

        for day in trgtDate:
            # 1. 前後5日と3日の範囲を計算 (DatetimeIndexなので計算可能)
            start_date = day - timedelta(days=30)
            end_date = day + timedelta(days=7)
            
            # 2. その期間だけを切り抜く
            df_slice = df.loc[start_date:end_date]

            # 3. VLINEの色を決める
            current_wl = df.loc[day, trgtcols].values # 値のリストを取得

            bDraw = False
            if 'LOSE' in current_wl:
                line_color = 'pink'
                summary_text = 'LOSE'
                strMsg = 'LOSE'
                bDraw = True
            elif 'WIN' in current_wl:
                line_color = 'lightblue'
                summary_text = 'WIN'
                strMsg = 'WIN'
                bDraw = True
            elif True in current_wl:
                line_color = 'lightgreen'
                summary_text = 'MATCH'
                strMsg = 'MATCH'
                bDraw = True
            else:
                continue # どちらもなければ（NAなど）次の日付へ            
    
            if bDraw:
                # 4. プロット実行 (savefigで保存するのがおすすめ)
                strTitle = f"{self.code}_{day.date()}_{strMsg}"
                output_dir = f"{self.fpass}/{self.code}"
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                fname = f"{output_dir}/{strTitle}.png" # ファイル名に日付を入れる
                if not os.path.exists(fname):
                    mpf.plot(df_slice, type='candle', style=my_style,
                            mav=(5, 10, 15),
                            vlines=dict(vlines=day, colors=line_color, linewidths=0.5, alpha=0.5, linestyle='--'),
                            title=strTitle,
                            savefig=fname,
                            volume=True)
                if self.end_date.strftime('%Y-%m-%d') in fname and fname not in self.fProceeded:
                    self.fProceeded.append(fname)

        pass

    def get_credentials(self):
        creds = None

        # 2回目以降は保存された token.json を使う
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        
        # 期限切れ、または初回の場合
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # client_secret_xxxx.json は Google Cloud Console からダウンロードしたもの
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.foauth, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 次回のために認証情報を保存
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        return creds

    def upload2googledrive(self, file_path):

        file_name = os.path.basename(file_path)
        query = f"name = '{file_name}' and '{self.fgdf_id}' in parents and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        if len(items) > 0:
            name = items[0]['name']
            file_id = items[0]['id']
        else:
            file_metadata = {
                'name': os.path.basename(file_path),
                'parents': [self.fgdf_id]
            }
            media = MediaFileUpload(file_path, mimetype='image/png')
        
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webContentLink'
            ).execute()
        
            file_id = file.get('id')

            print(f"Success! {file_path} file_id: {file_id}")

        # 共有設定（公開）
        new_permission = {
            'type': 'anyone',
            'role': 'reader',
        }
        self.service.permissions().create(fileId=file_id, body=new_permission).execute()

        code = file_name.split('_')[0]
        result = file_name.split('_')[2][:-4]
        public_url = f"https://lh3.google.com/u/0/d/{file_id}=s800?auditContext=thumbnail"

        return code, result, public_url

if __name__ == "__main__":
    pass
