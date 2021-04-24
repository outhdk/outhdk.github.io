import os
from dotenv import load_dotenv
import tweepy
import mysql.connector as mycon
import re
import datetime

load_dotenv()

CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

#対象ユーザー（@以下）を登録
Account = os.getenv("tw_name1")

#前回からの差分件数によりcountを変更（１日20~50件程度）
tweets = api.user_timeline(Account, count=200, page=1)

config = {
  'host' : os.getenv("host"),
  'user' : os.getenv("user"),
  'password' : os.getenv("password"),
  'database' : os.getenv("database"),
}

conn = mycon.connect(**config)
cursor = conn.cursor()

num = 1
for tweet in tweets:
  twid = tweet.id
  twuser = tweet.user.screen_name
  utc_date = tweet.created_at
  text = tweet.text

  #textからdefangされたurlを抽出する
  #正規表現「.」任意の１文字「+?」１回以上繰り返し　()内のみ抽出なので\nは括弧外
  #row[1]は複数行テキストなのでflags=re.MULTILINEでフラグ指定が必要
  twurl = re.findall('(^hxxps?://.+?)\n', text, flags=re.MULTILINE)
  
  #utc_dateをutcからjstに変換
  date = utc_date + datetime.timedelta(hours=10)
  
  try:
    #データベースに追加
    cursor.execute('INSERT IGNORE INTO twphish_tb(twid, twuser, date, text, url) VALUES(%s, %s, %s, %s, %s)', (twid, twuser, date, text, twurl[0]))
  except Exception as e:
    print(twid, ':', e)
    cursor.execute('INSERT IGNORE INTO twphish_tb(twid, twuser, date, text) VALUES(%s, %s, %s, %s)', (twid, twuser, date, text))

conn.commit()
conn.close()