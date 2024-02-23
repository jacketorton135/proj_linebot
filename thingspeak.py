import requests
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import pytz
import pyimgur
from imgurpython import ImgurClient


class Thingspeak():
    def get_data_from_thingspeak(self, channel_id, api_read_key):
        url = 'https://thingspeak.com/channels/{channel_id}/feed.json?api_key={api_read_key}'.format(channel_id = channel_id,api_read_key = api_read_key)
        data = requests.get(url).json()
        if data.get('error') == 'Not Found':
            return 'Not Found', 'Not Found'
        time_list = list()
        entry_id_list = list()
        bpm_list = list()
        for data in data['feeds']:
            time_list.append(data.get('created_at'))
            entry_id_list.append(data.get('entry_id'))
            bpm_list.append(data.get('field1'))

        #換成台灣時間
        tw_time_list = self.format_time(time_list)
        return tw_time_list, bpm_list
    
    # 解析时间字符串并转换为台湾时间
    def format_time(self, time_list):
        taiwan_tz = pytz.timezone('Asia/Taipei')
        tw_time_list = []
        for timestamp in time_list:
            dt = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
            dt_utc = pytz.utc.localize(dt)
            dt_taiwan = dt_utc.astimezone(taiwan_tz)
            tw_time_list.append(dt_taiwan.strftime('%Y-%m-%d %H:%M:%S'))
        return tw_time_list
    
    # 從 JSON 數據中提取數字並繪製折線圖
    def gen_chart(self, time_list, bpm_list):
        print(time_list, bpm_list)
        plt.figure(figsize=(12, 15))  # 設置圖片尺寸為 10x6
        bpm_list = [float(value) for value in bpm_list]
        # 绘制图表
        plt.plot(time_list, bpm_list, 'r-o')
        plt.xlabel('Time')
        plt.ylabel('BPM')
        plt.title('Thingspeak')
        plt.xticks(rotation=45)
        plt.savefig('chart.png', format='png')
        return 
    

    # 上傳圖片到 Imgur
    def upload_to_imgur(self):
        client_id = '1057e1ccf4ca17c'
        client_secret = '4207a25500bd516266c39c3f831ab8da7d47d0a1'

        client = ImgurClient(client_id, client_secret)

        # Example request
        items = client.gallery()
        for item in items:
            print(item.link)
        # Authorization flow, pin example (see docs for other auth types)
        authorization_url = client.get_auth_url('pin')

        # ... redirect user to `authorization_url`, obtain pin (or code or token) ...

        credentials = client.authorize(authorization_url, 'pin')
        client.set_user_auth(credentials['access_token'], credentials['refresh_token'])

        return item.link
        # CLIENT_ID = "1057e1ccf4ca17c"
        # PATH = "chart.png" #A Filepath to an image on your computer"
        # title = "Uploaded with PyImgur"

        # im = pyimgur.Imgur(CLIENT_ID)
        # uploaded_image = im.upload_image(PATH, title=title)
        # # print(uploaded_image.title)
        # image_url = uploaded_image.link
        # return  image_url
        
if __name__ == "__main__":
    ts = Thingspeak()
    ts.get_data_from_thingspeak()