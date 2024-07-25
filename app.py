import boto3
import json
from openai import OpenAI
from flask import Flask, request, abort
import os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from io import BytesIO
from thingspeak import Thingspeak
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

# 確保環境變數正確設置
line_bot_api_key = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
line_bot_secret_key = os.environ.get('LINE_CHANNEL_SECRET_KEY')
openai_api_key = os.environ.get('OPEN_AI_KEY')
imgur_client_id = os.environ.get('IMGUR_CLIENT_ID')

# 檢查環境變數是否正確設置
if not line_bot_api_key or not line_bot_secret_key:
    raise EnvironmentError("LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_SECRET_KEY not set")

if not openai_api_key:
    raise EnvironmentError("OPEN_AI_KEY not set")

if not imgur_client_id:
    raise EnvironmentError("IMGUR_CLIENT_ID not set")

# Channel Access Token
line_bot_api = LineBotApi(line_bot_api_key)
# Channel Secret
handler = WebhookHandler(line_bot_secret_key)

# Auth User list
auth_user_list = os.environ.get('AUTH_USER_LIST', '').split(',')
print('auth_user_list', auth_user_list)

# Auth AI User list
auth_user_ai_list = os.environ.get('AUTH_AI_USER_LIST', '').split(',')
print('auth_user_ai_list', auth_user_ai_list)

# Auth AWS User list
auth_user_aws_list = os.environ.get('AUTH_AWS_USER_LIST', '').split(',')
print('auth_user_aws_list', auth_user_aws_list)

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    get_request_user_id = event.source.user_id
    print('get_request_user_id', get_request_user_id)
    input_msg = event.message.text
    check = input_msg[:3].lower()
    user_msg = input_msg[3:]  # 2374700,2KNDBSF9FN4M5EY1
    print('check', check)
    print('user_msg', user_msg)
    if get_request_user_id in auth_user_list:
        if check == "圖表:":
            channel_id = user_msg.split(',')[0]
            key = user_msg.split(',')[1]
            field = user_msg.split(',')[2] if len(user_msg.split(',')) > 2 else 'field1'
            print("User channel_id: ", channel_id, "Read_key: ", key, "Field: ", field)
            ts = Thingspeak()
            tw_time_list, data_list = ts.get_data_from_thingspeak(channel_id, field, key)
            if tw_time_list == 'Not Found' or data_list == 'Not Found':
                message = TextSendMessage(text="User not found")
                line_bot_api.reply_message(event.reply_token, message)
            else:
                ts.gen_chart(tw_time_list, data_list)
                ts.update_photo_size()
                chart_link, pre_chart_link = ts.upload_to_imgur()
                print("圖片網址", chart_link)
                print("縮圖網址", pre_chart_link)
                image_message = ImageSendMessage(
                    original_content_url=chart_link,
                    preview_image_url=pre_chart_link)
                line_bot_api.reply_message(event.reply_token, image_message)
        elif check == 'ai:' and get_request_user_id in auth_user_ai_list:
            try:
                client = OpenAI(api_key=openai_api_key)

                response = client.chat_completions.create(
                    model="gpt-3.5-turbo-0125",
                    messages=[
                        {
                            "role": "system",
                            "content": "如果回答問題盡可能用簡潔的話回復"
                        },
                        {
                            "role": "user",
                            "content": user_msg,
                        },
                    ],
                )
                reply_msg = response.choices[0].message.content
                print('reply_msg', reply_msg)
                message = TextSendMessage(text=reply_msg)
                line_bot_api.reply_message(event.reply_token, message)
            except Exception as e:
                print(e)
        else:  # 學使用者說話
            message = TextSendMessage(text=event.message.text)
            line_bot_api.reply_message(event.reply_token, message)
    else:
        message = TextSendMessage(text='使用者沒有權限')
        line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    app.run()

