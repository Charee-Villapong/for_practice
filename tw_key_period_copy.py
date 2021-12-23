# 必要なモジュールのimport
from janome.tokenizer import Tokenizer
from os import name
import pandas as pd
import tweepy
import datetime

# 各種ツイッターのキーをセット　consumer_key, consumer_secret, access_key, access_secret
consumer_key = "N2kETsTqSiRccfJr8nx0027pa"  # API Key
consumer_secret = "J4AdSrjKjMoCbKvnD3mrnAzRrnGbd6A96mNeFLzUCFJmkIFqwD"  # API Key Secret
access_key = "1289362986210009089-n4jzw0lsL2qe6x0mhI3g7PY4LUXb1u"  # Access Token
access_secret = "QlCsTixYIY07OS0wjWupca2GiW0YLHhbKQNNN93VYWDhu"  # Access Token Secret

# 認証のためのAPIキーをセット
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)

'''
public_tweets = api.home_timeline()
for tweet in public_tweets:
    print('-------------------------')
    print(tweet.text)
'''

# API利用制限にかかった場合、解除まで待機する


'''
メインの実行部分
ツイートデータの取得からデータの出力まで
'''


def main():
    # ツイートデータの取得 日付の指定は 2020-7-30のみでもOK,
    # 日本時間で取得したい場合は2020-7-30_00:00:00_JSTのように指定
    # JSTをつけないと時間がUTCになる UTCは協定世界時間-> JST＋9:00(日本時間よりも9時間進んでいる)
    tweet_data = get_search_tweet("車　ステッカー", 100, 1)
    # ツイートデータを番号順に出力
    output_tweets(tweet_data)
    # ツイートデータをDataframeにする
    df = make_df(tweet_data)
    nega_pogi(df)
    # ツイートデータのCSVへの出力
    df.to_csv("sticker.csv")
    # ツイートを収集する関数


'''
ツイート情報を特定のキーワードで、期間を指定して収集
取得できるデータは1週間以内のデータだけ
リツイート数＋いいね数の合計でツイートを絞り込める
'''


def get_search_tweet(s, count, rlcount):
    # 検索キーワードの設定、 リツイートは除く
    searchkey = s + "-filter:retweets"
    # ツイートデータ取得部分

    # tweepy.CursorのAPIのキーワードサーチを使用(api.search)
    # qがキーワード, sinceがいつから, untilがいつまで, tweet_modeでつぶやきの省略ありなし, langで言語, .items(数)と書いてツイート数を指定
    tweets = tweepy.Cursor(api.search, q=searchkey,exclude_replies=True,
                           tweet_mode="extended", lang="ja").items(count)

    # ツイートのデータを取り出して、リストにまとめていく部分

    # ツイートデータを入れる空のリストを用意
    tweet_data = []
    for tweet in tweets:
        if tweet.favorite_count + tweet.retweet_count >= rlcount:  # いいねとリツイートの合計がrlcuont以上の条件
            # 空のリストにユーザーネーム、スクリーンネーム、RT数、いいね数、日付などを入れる
            tweet_data.append([tweet.user.name, tweet.user.screen_name, tweet.retweet_count, tweet.favorite_count,
                               tweet.created_at.strftime("%Y-%m-%d-%H:%M:%S_JST"), tweet.full_text.replace("\n", "")])
    return tweet_data


'''
ツイートのリストを順番をつけて出力する関数の作成
'''


def output_tweets(tweet_data):
    for i,tweet in enumerate(tweet_data,start=1):
        print(f"{i}番目のつぶやき{tweet}")



'''
ツイートデータからDataFrameを作成する
'''


def make_df(tweet_data):
    # データを入れる空のリストを用意(ユーザー名、ユーザーid、RT数、いいね数、日付け、ツイート本文)
    list_username = []
    list_userid = []
    list_rtcount = []
    list_fav = []
    list_date = []
    list_content = []
    # ツイートデータからユーザー名、ユーザーid、RT数、いいね数、日付け、ツイート本文のそれぞれをデータごとにまとめたリストを作る
    for i in range(len(tweet_data)):
        list_username.append(tweet_data[i][0])
        list_userid.append(tweet_data[i][1])
        list_rtcount.append(tweet_data[i][2])
        list_fav.append(tweet_data[i][3])
        list_date.append(tweet_data[i][4])
        list_content.append(tweet_data[i][5])
    # 先ほど作ったデータごとにまとめたリストからDataframeの作成
    tweet_df = pd.DataFrame({"ユーザー名": list_username, "ユーザーID": list_userid, "リツイート数": list_rtcount,
                             "いいね数": list_fav, "ツイート日付": list_date, "本文": list_content})
    print(tweet_df)
    return tweet_df


# 形態素解析をするためのjanomeをimport


'''
データフレームを引数に受け取り、
ネガポジ分析をする関数
'''


def nega_pogi(tweet_df):
    # 極性辞書をPythonの辞書にしていく
    np_dic = {}

    # 日本語評価極性辞書のファイルの読み込み
    with open("/Users/yoshitakanishikawa/Downloads/get_tweetdata/pn.csv.m3.120408.trim", "r", encoding="UTF-8") as f:
        # 1行1行を読み込み、文字列からリスト化。リストの内包表記の形に
        lines = [line.replace("\n", "").split("\t")for line in f.readlines()]

    # リストからデータフレームの作成
    pg_df = pd.DataFrame(lines, columns=["word", "score", "explain"])
    # データフレームの2つの列から辞書の作成　zip関数を使う
    np_dic = dict(zip(pg_df["word"], pg_df["score"]))
    # 形態素解析をするために必要な記述を書いていく
    tokenizer = Tokenizer()
    # ツイート一つ一つを入れてあるデータフレームの列（本文の列）をsentensesと置く
    sentences = tweet_df["本文"]
    #sentences = ["憧れの先輩に悪く言われた","明日は彼女の誕生日","俺は君だけを愛してるって言っただろ"]
    # p,n,e,?p?nを数えるための辞書を作成
    result = {"p": 0, "e": 0, "n": 0, "?n?p": 0}
    # ツイートを一つ一つ取り出す
    for sentence in sentences:
        for token in tokenizer.tokenize(sentence):  # 形態素解析をする部分
            word = token.surface  # ツイートに含まれる単語を抜き出す
            if word in np_dic:
                value = np_dic[word]
                if value in result:
                    result[value] += 1  # p,n,e,?p?nの個数を数える

    summary = result["p"] + result["n"] + result["e"] + result["?n?p"]  # 総和を求める

    # ネガポジ度の平均（pの総数 / summary, nの総数 / summary）を数値でそれぞれ出力
    try:
        print(result["p"]/summary)  # ポジティブ度の平均
        print(result["n"]/summary)  # ネガティブ度の平均
    except ZeroDivisionError:
        print("summaryが０です")  # summaryが0の場合


if __name__ == "__main__":
    main()
