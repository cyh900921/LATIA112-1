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

#Config Parser
config = configparser.ConfigParser()
config.read('config.ini')

#Config Azure Analytics
credential = AzureKeyCredential(config['AzureLanguage']['API_KEY'])

app = Flask(__name__)

channel_access_token = config['Line']['CHANNEL_ACCESS_TOKEN']
channel_secret = config['Line']['CHANNEL_SECRET']
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

handler = WebhookHandler(channel_secret)

configuration = Configuration(
    access_token=channel_access_token
)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    sentiment_result = azure_sentiment(event.message.text)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=sentiment_result)]
            )
        )
# 取得分析結果
def azure_sentiment(user_input):
    text_analytics_client = TextAnalyticsClient(
        endpoint=config['AzureLanguage']['END_POINT'], 
        credential=credential)
    documents = [user_input]
    response = text_analytics_client.analyze_sentiment(
        documents,
        language="zh-Hant",
        show_opinion_mining=True)
    print(response)
    docs = [doc for doc in response if not doc.is_error]
    for idx, doc in enumerate(docs):
        print(f"Document text : {documents[idx]}")
        print(f"Overall sentiment : {doc.sentiment}")

        # 顯示意見探勘結果
        extracted_targets = []  # 新增這一行，用來儲存提取的主詞
        for sentence in doc.sentences:
            print(f"    Opinion mining: {sentence.text} (Sentiment: {sentence.sentiment}, Confidence: {sentence.confidence_scores[sentence.sentiment]:.2f})")

            # 提取關鍵詞
            for mined_opinion in sentence.mined_opinions:
                target_sentiment = mined_opinion.target
                assessments = mined_opinion.assessments
                for assessment in assessments:
                    keyword = assessment.text
                    extracted_targets.append(target_sentiment.text)
                    print(f"    主詞: {', '.join(extracted_targets)}")
                    print(f"    關鍵字: {keyword}")

        # 如果無法提取關鍵詞，顯示提示訊息
        if not extracted_targets:
            print("    主詞:無法提取主詞")
            print("    關鍵字:無法提取關鍵詞")

        # 將英文情感標籤轉換為中文
        sentiment_mapping = {
            'positive': '正面',
            'neutral': '中性',
            'negative': '負面'
        }
        
        chinese_sentiment = sentiment_mapping.get(sentence.sentiment, sentence.sentiment)

        # 如果提取到關鍵詞，顯示情感標籤和分數
        if extracted_targets:
            # 將中文情感標籤和分數結合
            result_with_score = f"{chinese_sentiment}（{sentence.confidence_scores[sentence.sentiment]:.2f}），主詞：{', '.join(extracted_targets)}"
        else:
            # 如果未提取到關鍵詞，仍顯示中文情感標籤和分數
            result_with_score = f"{chinese_sentiment}（{sentence.confidence_scores[sentence.sentiment]:.2f}），主詞：無法提取主詞"

        return result_with_score


if __name__ == "__main__":
    app.run()