import sys
import configparser

# Azure Text Analytics
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient

from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)

# 配置解析器
config = configparser.ConfigParser()
config.read('config.ini')

# Azure Text Analytics 的驗證憑證
credential = AzureKeyCredential(config['AzureLanguage']['API_KEY'])

# 創建 Flask 應用
app = Flask(__name__)

# 從 config.ini 文件中讀取 Line 聊天機器人的 Channel Access Token 和 Channel Secret
channel_access_token = config['Line']['CHANNEL_ACCESS_TOKEN']
channel_secret = config['Line']['CHANNEL_SECRET']
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

# 設定 Line Webhook Handler
handler = WebhookHandler(channel_secret)

# Line API 的配置
configuration = Configuration(
    access_token=channel_access_token
)

# 設定 Flask 應用的 Webhook 路由
@app.route("/callback", methods=['POST'])
def callback():
    # 獲取 X-Line-Signature 首部的值
    signature = request.headers['X-Line-Signature']
    # 獲取請求主體的文本表示
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 解析 Webhook 主體
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理 Line 的 TextMessage 事件
@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    # 進行情感分析
    sentiment_result = azure_sentiment(event.message.text)
    # 透過 Line API 回復訊息
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=sentiment_result)]
            )
        )

# 執行 Flask 應用
if __name__ == "__main__":
    app.run()

# 函數：進行情感分析
def azure_sentiment(user_input):
    # 創建 Text Analytics 客戶端
    text_analytics_client = TextAnalyticsClient(
        endpoint=config['AzureLanguage']['END_POINT'], 
        credential=credential)
    documents = [user_input]

    # 進行情感分析
    response = text_analytics_client.analyze_sentiment(
        documents,
        language="zh-Hant",
        show_opinion_mining=True)

    # 獲取分析結果
    docs = [doc for doc in response if not doc.is_error]
    for idx, doc in enumerate(docs):
        print(f"Document text : {documents[idx]}")
        print(f"Overall sentiment : {doc.sentiment}")
    
        # 顯示意見探勘結果
        for sentence in doc.sentences:
            print(f"    Opinion mining: {sentence.text} (Sentiment: {sentence.sentiment}, Confidence: {sentence.confidence_scores[sentence.sentiment]:.2f})")

            # 提取關鍵詞
            extracted_keywords = []
            for mined_opinion in sentence.mined_opinions:
                target_sentiment = mined_opinion.target
                assessments = mined_opinion.assessments
                for assessment in assessments:
                    keyword = assessment.text
                    extracted_keywords.append(keyword)
                    print(f"    Extracted Keyword: {keyword}")

            # 如果無法提取關鍵詞，顯示提示訊息
            if not extracted_keywords:
                print("    Extracted Keyword:無法提取關鍵詞")

            # 將英文情感標籤轉換為中文
            sentiment_mapping = {
                'positive': '正面',
                'neutral': '中性',
                'negative': '負面'
            }
            chinese_sentiment = sentiment_mapping.get(sentence.sentiment, sentence.sentiment)

            # 如果提取到關鍵詞，顯示情感標籤和分數
            if extracted_keywords:
                # 將中文情感標籤和分數結合
                result_with_score = f"{chinese_sentiment}（{sentence.confidence_scores[sentence.sentiment]:.2f}）"
            else:
                # 如果未提取到關鍵詞，仍顯示中文情感標籤和分數
                result_with_score = f"{chinese_sentiment}（{sentence.confidence_scores[sentence.sentiment]:.2f}）"
            
            return result_with_score

    # 如果無法提取到任何意見探勘結果，返回一個預設值
    return "未知情感（0.0）"

if __name__ == "__main__":
    app.run()