import json
from openai import OpenAI
from flask import Flask, request, abort
import os
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *
from thingspeak import Thingspeak

app = Flask(__name__)
line_bot_api_key = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
line_bot_secret_key = os.environ.get('LINE_CHANNEL_SECRET_KEY')

# 確認環境變量是否正確設置
if not line_bot_api_key:
    raise ValueError("環境變量 LINE_CHANNEL_ACCESS_TOKEN 未設置")
if not line_bot_secret_key:
    raise ValueError("環境變量 LINE_CHANNEL_SECRET_KEY 未設置")

# Channel Access Token
line_bot_api = LineBotApi(line_bot_api_key)
# Channel Secret
handler = WebhookHandler(line_bot_secret_key)

# Open AI key
openai_api_key = os.environ.get('OPEN_AI_KEY')
if not openai_api_key:
    raise ValueError("環境變量 OPEN_AI_KEY 未設置")

# Auth User list
auth_user_list = os.environ.get('AUTH_USER_LIST')
if not auth_user_list:
    raise ValueError("環境變量 AUTH_USER_LIST 未設置")
auth_user_list = auth_user_list.split(',')

# Auth AI User list
auth_user_ai_list = os.environ.get('AUTH_USER_AI_LIST')
if not auth_user_ai_list:
    raise ValueError("環境變量 AUTH_USER_AI_LIST 未設置")
auth_user_ai_list = auth_user_ai_list.split(',')

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
    input_msg = event.message.text
    check = input_msg[:3].lower()
    user_msg = input_msg[3:]  # 2374700,2KNDBSF9FN4M5EY1

    if get_request_user_id in auth_user_list:
        if check == "圖表:":
            channel_id = user_msg.split(',')[0]
            key = user_msg.split(',')[1]
            ts = Thingspeak()
            tw_time_list, bpm_list, temperature_list, humidity_list, body_temperature_list, ECG_list = ts.get_data_from_thingspeak(
                channel_id, key)
            if tw_time_list == 'Not Found' or bpm_list == 'Not Found':
                message = TextSendMessage(text="User not found")
                line_bot_api.reply_message(event.reply_token, message)
            else:
                ts.gen_chart(tw_time_list, bpm_list, temperature_list, humidity_list, body_temperature_list, ECG_list)
                ts.update_photo_size()
                chart_links, pre_chart_links = ts.upload_to_imgur()
                image_messages = [ImageSendMessage(original_content_url=chart_link, preview_image_url=pre_chart_link)
                                  for chart_link, pre_chart_link in zip(chart_links, pre_chart_links)]
                line_bot_api.reply_message(event.reply_token, image_messages)
        elif check == 'ai:' and get_request_user_id in auth_user_ai_list:
            try:
                client = OpenAI(api_key=openai_api_key)

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
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


