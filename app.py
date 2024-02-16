from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('WrWuc3sqv+gIpcqpUD23unz6vy3Zq6tUg1z2vO8Mp4iWHkZCbIcJ/XnsbsXpgmfALS6VNNAGhTydI26i3dE20iHKhRxaJdSieC6V579F/onwkagqVGyp9BWwiJK3ua3vwefdmCwO95N4WXORXk6ebQdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('b341b992fd91941e3662f525178b01f9')

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
    message = TextSendMessage(text=event.message.text)
    line_bot_api.reply_message(event.reply_token, message)

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
