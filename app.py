import json
from flask import Flask, request, abort
import os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from thingspeak import Thingspeak

app = Flask(__name__)

# 确保环境变量正确设置
line_bot_api_key = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
line_bot_secret_key = os.environ.get('LINE_CHANNEL_SECRET_KEY')

# 打印环境变量以进行调试
print(f"LINE_CHANNEL_ACCESS_TOKEN: {line_bot_api_key}")
print(f"LINE_CHANNEL_SECRET_KEY: {line_bot_secret_key}")

# 检查环境变量是否正确设置
if not line_bot_api_key or not line_bot_secret_key:
    raise EnvironmentError("LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_SECRET_KEY not set")

# Channel Access Token
line_bot_api = LineBotApi(line_bot_api_key)
# Channel Secret
handler = WebhookHandler(line_bot_secret_key)

# Auth User list
auth_user_list = os.environ.get('AUTH_USER_LIST', '').split(',')
print('auth_user_list', auth_user_list)

# 监听所有来自 /callback 的 Post Request
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

# 处理消息
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
            print("User channel_id: ", channel_id, "Read_key: ", key)
            ts = Thingspeak()
            tw_time_list, bpm_list, temperature_list, humidity_list, body_temperature_list, ECG_list = ts.get_data_from_thingspeak(channel_id, key)
            if tw_time_list == 'Not Found' or bpm_list == 'Not Found':
                message = TextSendMessage(text="User not found")
                line_bot_api.reply_message(event.reply_token, message)
            else:
                ts.gen_chart(tw_time_list, bpm_list, temperature_list, humidity_list, body_temperature_list, ECG_list)
                ts.update_photo_size()
                chart_link, pre_chart_link = ts.upload_to_imgur()
                print("圖片網址", chart_link)
                print("縮圖網址", pre_chart_link)
                image_message = ImageSendMessage(
                    original_content_url=chart_link,
                    preview_image_url=pre_chart_link)
                line_bot_api.reply_message(event.reply_token, image_message)
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=input_msg))
    else:
        message = TextSendMessage(text="你無權限使用該功能")
        line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    app.run()




