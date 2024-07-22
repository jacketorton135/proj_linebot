from flask import Flask, request, abort
import os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from thingspeak import Thingspeak
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
line_bot_api_key = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
line_bot_secret_key = os.getenv('LINE_CHANNEL_SECRET_KEY')

# Channel Access Token
line_bot_api = LineBotApi(line_bot_api_key)
# Channel Secret
handler = WebhookHandler(line_bot_secret_key)

# Auth User list
auth_user_list = os.getenv('AUTH_USER_LIST').split(',')

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    get_request_user_id = event.source.user_id
    input_msg = event.message.text
    check = input_msg[:3].lower()
    user_msg = input_msg[3:]

    if get_request_user_id in auth_user_list:
        if check == "圖表:":
            try:
                channel_id, field_name, key = user_msg.split(',')
                ts = Thingspeak()
                tw_time_list, field_data = ts.get_data_from_thingspeak(channel_id, key)
                if tw_time_list == 'Not Found' or field_data == 'Not Found':
                    message = TextSendMessage(text="資料不存在")
                    line_bot_api.reply_message(event.reply_token, message)
                else:
                    chart_filename = ts.gen_chart(tw_time_list, field_data, field_name)
                    image_url, pre_image_url = ts.upload_to_imgur(chart_filename)
                    image_message = ImageSendMessage(
                        original_content_url=image_url,
                        preview_image_url=pre_image_url
                    )
                    line_bot_api.reply_message(event.reply_token, image_message)
            except ValueError:
                message = TextSendMessage(text="請輸入正確的格式：圖表:channel_id,field_name,key")
                line_bot_api.reply_message(event.reply_token, message)
        else:
            message = TextSendMessage(text="無效的請求")
            line_bot_api.reply_message(event.reply_token, message)
    else:
        message = TextSendMessage(text='使用者沒有權限')
        line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    app.run()

