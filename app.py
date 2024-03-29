import json
import openai
from flask import Flask, request, abort
import os
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *

from thingspeak import Thingspeak
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)
line_bot_api_key = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
line_bot_secret_key = os.environ.get('LINE_CHANNEL_SECRET_KEY')
# Channel Access Token
line_bot_api = LineBotApi(line_bot_api_key)
# Channel Secret
handler = WebhookHandler(line_bot_secret_key)

# Open AI key
openai.api_key = os.environ.get('OPEN_AI_KEY')


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


# input:  "圖表:2374700,2KNDBSF9FN4M5EY1"
# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    user_msg = event.message.text
    check = user_msg[:3].lower()
    user_msg = user_msg[3:]  # 2374700,2KNDBSF9FN4M5EY1
    print('check', check)
    print('user_msg', user_msg)
    if check in "圖表:":
        channel_id = user_msg.split(',')[0]
        key = user_msg.split(',')[1]
        print("User channel_id: ", channel_id, "key: ", key)
        ts = Thingspeak()
        tw_time_list, bpm_list = ts.get_data_from_thingspeak(channel_id, key)
        if tw_time_list == 'Not Found' or bpm_list == 'Not Found':
            message = TextSendMessage(text="User not found")
            line_bot_api.reply_message(event.reply_token, message)
        else:
            ts.gen_chart(tw_time_list, bpm_list)
            ts.update_photo_size()
            chart_link, pre_chart_link = ts.upload_to_imgur()
            print("圖片網址", chart_link)
            print("縮圖網址", pre_chart_link)
            image_message = ImageSendMessage(original_content_url=chart_link,
                                             preview_image_url=pre_chart_link)
            line_bot_api.reply_message(event.reply_token, image_message)
    elif check == 'ai:':
        # 將第六個字元之後的訊息發送給 OpenAI
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                max_tokens=128,
                                                temperature=0.5,
                                                messages=user_msg)
        # 接收到回覆訊息後，移除換行符號
        reply_msg = response["choices"][0]["text"].replace('\n', '')
        line_bot_api.reply_message(event.reply_token, reply_msg)

    else:  # 學使用者說話

        message = TextSendMessage(text=event.message.text)
        line_bot_api.reply_message(event.reply_token, message)


if __name__ == "__main__":
    # port = int(os.environ.get('PORT', 5001))
    # local
    # app.run(host='0.0.0.0', port=5001)
    # Render
    app.run()
