from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

from thingspeak import Thingspeak
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('zesmpgsWsUy3JJtv+giJb/4cDV3L3g3JGrSodEArwQwpHJadCUTrhk6EEfQ5WzjImdeR4EWvMrzi+VQVvyY2oE9pOJUuTGYiXGdh06vPgn7tp3OSZ1asIvaSURETV+u6f8OheWISM9V32C6wxwj7YgdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('1b973f1211a9861d3a71bb6674dfc1bb')

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
    check = user_msg[:2].lower()
    data = user_msg[3:]  # 2374700,2KNDBSF9FN4M5EY1
    x = np.linspace(0.0, 2*np.pi)

    if check in "圖表:":
        channel_id = data.split(',')[0]
        key = data.split(',')[1]
        ts = Thingspeak()
        tw_time_list, bpm_list = ts.get_data_from_thingspeak(channel_id, key)
        ts.gen_chart(tw_time_list, bpm_list)
        chart_link = ts.upload_to_imgur()
        image_message = ImageSendMessage(
            original_content_url=chart_link,
            preview_image_url=chart_link
        )
        line_bot_api.reply_message(event.reply_token, image_message)
    else:

        message = TextSendMessage(text=event.message.text)
        line_bot_api.reply_message(event.reply_token, message)
        # chart = Thingspeak().get_data_from_thingspeak()

if __name__ == "__main__":
    # port = int(os.environ.get('PORT', 5001))
    # app.run(host='0.0.0.0', port=5001)
    app.run()
