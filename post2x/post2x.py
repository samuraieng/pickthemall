import os
import pandas as pd
from dotenv import load_dotenv

class Post2X:
    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--s2x', '--send2X', action='store_true', help='Enable to send to X')
        return parser

    def __init__(self):
        load_dotenv()
        self.BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN")
        self.API_KEY = os.environ.get("X_API_KEY")
        self.API_KEY_SECRET = os.environ.get("X_API_SECRET")
        self.ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
        self.ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_SECRET")
        self.CLIENT_ID = os.environ.get("X_CLIENT_ID")
        self.CLIENT_SECRET = os.environ.get("X_CLIENT_SECRET")

        self.send2X = False
        self.intVal = 300

        # 認証情報の確認
        if not self.API_KEY or not self.API_KEY_SECRET:
            print("Warning: X_API_KEY or X_API_SECRET is missing!")
        if not self.ACCESS_TOKEN or not self.ACCESS_TOKEN_SECRET:
            print("Warning: X_ACCESS_TOKEN or X_ACCESS_SECRET is missing!")


        self.REDIRECT_URI = "http://localhost:8181/callback"    #You need to prepare your own callback URL
        # 必要スコープ
        self.SCOPES = ["tweet.write", "users.read", "offline.access"]
        
        import tweepy
        self.client = tweepy.Client(
                consumer_key=self.API_KEY, consumer_secret=self.API_KEY_SECRET,
                access_token=self.ACCESS_TOKEN, access_token_secret=self.ACCESS_TOKEN_SECRET
            )

    def count_tweet_length(self, text):
        length = 0
        for char in text:
            if char.isascii():  # ASCII characters count as 1
                length += 1
            else:               # CJK and others count as 2
                length += 2
        return length

    def split_text_by_length(self, text, limit=200):
        chunks = []
        
        start_index = 0
        while start_index < len(text):
            current_weight = 0
            split_idx = -1
            
            # Start scanning from current position
            for i in range(start_index, len(text)):
                char = text[i]
                w = 2 if not char.isascii() else 1
                current_weight += w
                
                # If we exceed limit, we look for the *next* newline to split
                if current_weight >= limit:
                    if char == '\n':
                        split_idx = i + 1
                        break
            
            if split_idx != -1:
                # Found a newline after limit
                chunks.append(text[start_index:split_idx])
                start_index = split_idx
            else:
                # No newline found after limit, or reached end of text without exceeding limit
                # Append the rest
                remaining = text[start_index:]
                if remaining:
                    chunks.append(remaining)
                break
                
        return chunks

    def tweet(self, inText):
        '''
        curl --request GET 'https://api.x.com/2/users/USER_ID/tweets' --header 'Authorization: Bearer XXXXXX'
        '''

        # Add timestamp to the tweet text
        now_str = pd.Timestamp.now(tz="Asia/Tokyo").strftime('%Y-%m-%d %H:%M')
        inText = f"{now_str}\n{inText}"

        # Check length
        count = self.count_tweet_length(inText)
        # print(f"Tweet Length: {count} / 280 (approx.)")

        chunks = []
        if count > 280:
             print(f"Warning: Tweet length ({count}) exceeds 280 chars! Splitting...")
             chunks = self.split_text_by_length(inText, limit=250)
        else:
             chunks = [inText]

        print(f"\n\n-----Tweeting Sequence. intval: {self.intVal}s, send2X: {self.send2X}")
        retval = ""

        for i, chunk in enumerate(chunks):
            try:
                if self.send2X:
                    resp = self.client.create_tweet(text=chunk)
                    retval = resp
                #print(f"Posted chunk {i+1}/{len(chunks)}")
                print(chunk, end="")
                if self.send2X and i < len(chunks) - 1:
                    print(f"Sleeping for {self.intVal}s...")
                    time.sleep(self.intVal)
                else:
                    print("")
            except Exception as e:
                print(f"Error posting chunk {i+1}: {e}")
        
        return retval
