import os
from dotenv import load_dotenv

class Post2BlogSpot:
    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--s2b', '--send2Blogger', action='store_true', help='Enable to send to Blogger')
        return parser

    def __init__(self):
        load_dotenv()
        self.BLOG_ID = os.environ.get("BLOG_ID")    #You must set environment variable BLOG_ID
        self.BLOG_KEY = os.environ.get("BLOG_KEY")  #You must set environment variable BLOG_KEY, unused

        self.foauth = 'pickthemall_oauth.json'      #You need to prepare your own oauth file
        self.ftoken = 'pickthemall_token.json'      #You need to prepare your own token file

        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        self.InstalledAppFlow = InstalledAppFlow
        self.Request = Request
        self.Credentials = Credentials
        self.build = build

        # Bloggerのフルアクセス権限
        self.SCOPES = ['https://www.googleapis.com/auth/blogger']

        self.posted = "" #URL
        self.postID = 0  #ID

    def get_credentials(self):
        creds = None
        # token.jsonがあればそれを使う
        if os.path.exists(self.ftoken):
            creds = self.Credentials.from_authorized_user_file(self.ftoken, self.SCOPES)
        
        # 有効な認証情報がない場合はログイン
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(self.Request())
            else:
                flow = self.InstalledAppFlow.from_client_secrets_file(self.foauth, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 次回のために保存
            with open(self.ftoken, 'w') as token:
                token.write(creds.to_json())
        return creds

    def get_latest_post_id(self):
        creds = self.get_credentials()
        service = self.build('blogger', 'v3', credentials=creds)
        
        # 最新の投稿を1件だけ取得
        results = service.posts().list(blogId=self.BLOG_ID, maxResults=1).execute()
        posts = results.get('items', [])
        
        if not posts:
            print("投稿が見つかりませんでした。")
            self.latest_post_id = ""
            self.latest_post_title = ""
            return None
        
        # 一番新しい投稿のIDを返す
        self.latest_post_id = posts[0]['id']
        self.latest_post_title = posts[0]['title']
        
        print(f"最新記事を発見: {self.latest_post_title} (ID: {self.latest_post_id})")
        return self.latest_post_id

    def post_to_blogger(self, label, title, subtitle, content):
        creds = self.get_credentials()
        service = self.build('blogger', 'v3', credentials=creds)

        # ログを新規投稿として送信
        body = {
            'kind': 'blogger#post',
            'labels': label,
            'title': title,
            'content': f"""
            <h3>{subtitle}</h3>
            <pre style="overflow-x:auto; white-space:pre; max-width:100%;">
            {content}</pre><hr>
            """,
        }
        
        posts = service.posts()
        result = posts.insert(blogId=self.BLOG_ID, body=body).execute()
        self.posted = result.get('url')
        self.postID = result.get('id')
        print(f"Post completed: {self.posted}")

        return self.postID

    # 既存の記事の内容を取得して、末尾に追記するイメージ
    def append_log_to_post(self, post_id, subtitle, content):
        creds = self.get_credentials()
        service = self.build('blogger', 'v3', credentials=creds)
        
        # 1. 現在の記事内容を取得
        current_post = service.posts().get(blogId=self.BLOG_ID, postId=post_id).execute()
        prev_content = current_post.get('content', '')
        
        # 2. 新しい章（ログ）を作成（HTMLで整形）
        # <h3>などで章立てすると見やすくなります
        new_content = f"""
        <h3>{subtitle}</h3>
        <pre style="overflow-x:auto; white-space:pre; max-width:100%;">{content}</pre><hr>
        """
        updated_content = prev_content + new_content
        
        # 3. 記事を更新
        service.posts().patch(
            blogId=self.BLOG_ID, 
            postId=post_id, 
            body={'content': updated_content}
        ).execute()
