import os
import requests
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import pytz
import pyimgur
from PIL import Image

class Thingspeak():
    def get_data_from_thingspeak(self, channel_id, field, api_read_key):
        url = f'https://thingspeak.com/channels/{channel_id}/feed.json?api_key={api_read_key}'
        data = requests.get(url).json()
        if data.get('error') == 'Not Found':
            return 'Not Found', 'Not Found'
        time_list = list()
        entry_id_list = list()
        bpm_list = list()
        溫度_list = list()
        濕度_list = list()
        體溫_list = list()
        ECG_list = list()
        field_list = list()
        for data_point in data['feeds']:
            time_list.append(data_point.get('created_at'))
            entry_id_list.append(data_point.get('entry_id'))
            bpm_list.append(data_point.get('field1'))
            溫度_list.append(data_point.get('field2'))
            濕度_list.append(data_point.get('field3'))
            體溫_list.append(data_point.get('field4'))
            ECG_list.append(data_point.get('field5'))
            field_list.append(data_point.get(field))

        # 換成台灣時間
        tw_time_list = self.format_time(time_list)
        return tw_time_list, field_list
    
    # 解析時間字符串並轉換為台灣時間
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
    def gen_chart(self, time_list, field_list):
        print(time_list, field_list)
        plt.figure(figsize=(12, 15))  # 設置圖片尺寸為 10x6
        field_list = [float(value) if value is not None else 0 for value in field_list]
        # 繪製圖表
        plt.plot(time_list, field_list, 'r-o')
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.title('Thingspeak')
        plt.xticks(rotation=45)
        plt.savefig('chart.jpg', format='jpg')
        return 
    
    def update_photo_size(self):
        img = Image.open('chart.jpg')   # 開啟圖片
        img2 = img.resize((240,240))       # 調整圖片尺寸為 200x200
        img2.save('pre_chart.jpg')   

    # 上傳圖片到 Imgur
    def upload_to_imgur(self):
        CLIENT_ID = os.environ.get('IMGUR_CLIENT_ID')
        PATH = "chart.jpg"  # A Filepath to an image on your computer
        title = "Uploaded with PyImgur"

        im = pyimgur.Imgur(CLIENT_ID)
        uploaded_image = im.upload_image(PATH, title=title)
        image_url = uploaded_image.link

        PATH = "pre_chart.jpg"  # A Filepath to an image on your computer
        title = "Uploaded with pre_PyImgur"

        pre_im = pyimgur.Imgur(CLIENT_ID)
        uploaded_pre_image = pre_im.upload_image(PATH, title=title)
        pre_image_url = uploaded_pre_image.link
        return image_url, pre_image_url

if __name__ == "__main__":
    ts = Thingspeak()
    tw_time_list, field_list = ts.get_data_from_thingspeak("2466473", "field1", "GROLYCVTU08JWN8Q")
    ts.gen_chart(tw_time_list, field_list)
    ts.update_photo_size()
    ts.upload_to_imgur()

