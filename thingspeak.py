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
    def get_data_from_thingspeak(self, channel_id, api_read_key):
        url = f'https://thingspeak.com/channels/{channel_id}/feed.json?api_key={api_read_key}'
        data = requests.get(url).json()
        if data.get('error') == 'Not Found':
            return 'Not Found', 'Not Found'
        time_list = list()
        bpm_list = list()
        temperature_list = list()
        humidity_list = list()
        body_temperature_list = list()
        ECG_list = list()
        for data_point in data['feeds']:
            time_list.append(data_point.get('created_at'))
            bpm_list.append(data_point.get('field1'))
            temperature_list.append(data_point.get('field2'))
            humidity_list.append(data_point.get('field3'))
            body_temperature_list.append(data_point.get('field4'))
            ECG_list.append(data_point.get('field5'))

        # 換成台灣時間
        tw_time_list = self.format_time(time_list)
        return tw_time_list, bpm_list, temperature_list, humidity_list, body_temperature_list, ECG_list
    
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
    def gen_chart(self, time_list, *field_lists):
        print(time_list, field_lists)
        labels = ['BPM', 'temperature', 'humidity', 'body temperature', 'ECG']
        colors = ['r', 'g', 'b', 'y', 'm']
        
        for i, (field_list, label) in enumerate(zip(field_lists, labels)):
            field_list = [float(value) if value and value != '' else 0 for value in field_list]
            plt.figure(figsize=(12, 6))  # 設置圖片尺寸為 12x6
            plt.plot(time_list, field_list, f'{colors[i]}-o', label=label)
            plt.xlabel('Time')
            plt.ylabel('Value')
            plt.title(f'Thingspeak Data - {label}')
            plt.xticks(rotation=45)
            plt.legend()
            plt.savefig(f'{label}_chart.jpg', format='jpg')
            plt.close()

    def update_photo_size(self):
        for label in ['BPM', 'temperature', 'humidity', 'body temperature', 'ECG']:
            img = Image.open(f'{label}_chart.jpg')  # 開啟圖片
            img_resized = img.resize((240, 240))  # 調整圖片尺寸為 240x240
            img_resized.save(f'pre_{label}_chart.jpg')  # 保存調整後的圖片

    # 上傳圖片到 Imgur
    def upload_to_imgur(self):
        CLIENT_ID = os.environ.get('IMGUR_CLIENT_ID')
        urls = []
        pre_urls = []
        for label in ['BPM', 'temperature', 'humidity', 'body temperature', 'ECG']:
            PATH = f'{label}_chart.jpg'  # A Filepath to an image on your computer
            title = f"Uploaded with PyImgur - {label}"

            im = pyimgur.Imgur(CLIENT_ID)
            uploaded_image = im.upload_image(PATH, title=title)
            urls.append(uploaded_image.link)

            pre_PATH = f'pre_{label}_chart.jpg'  # A Filepath to a resized image on your computer
            pre_title = f"Uploaded with pre_PyImgur - {label}"

            pre_im = pyimgur.Imgur(CLIENT_ID)
            uploaded_pre_image = pre_im.upload_image(pre_PATH, title=pre_title)
            pre_urls.append(uploaded_pre_image.link)
        
        return urls, pre_urls

if __name__ == "__main__":
    ts = Thingspeak()
    tw_time_list, bpm_list, temperature_list, humidity_list, body_temperature_list, ECG_list = ts.get_data_from_thingspeak("2466473", "GROLYCVTU08JWN8Q")
    ts.gen_chart(tw_time_list, bpm_list, temperature_list, humidity_list, body_temperature_list, ECG_list)
    ts.update_photo_size()
    ts.upload_to_imgur()

