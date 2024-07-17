import os
import requests
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import pytz
import pyimgur
from imgurpython import ImgurClient
from PIL import Image

class Thingspeak():
    def get_data_from_thingspeak(self, channel_id, api_read_key):
        url = f'https://thingspeak.com/channels/{channel_id}/feed.json?api_key={api_read_key}'
        data = requests.get(url).json()
        if data.get('error') == 'Not Found':
            return 'Not Found', 'Not Found'
        
        time_list = list()
        field_data = {f'field{i}': [] for i in range(1, 6)}
        
        for data in data['feeds']:
            time_list.append(data.get('created_at'))
            for i in range(1, 6):
                field_data[f'field{i}'].append(data.get(f'field{i}'))
                
        # 換成台灣時間
        tw_time_list = self.format_time(time_list)
        return tw_time_list, field_data
    
    def format_time(self, time_list):
        taiwan_tz = pytz.timezone('Asia/Taipei')
        tw_time_list = []
        for timestamp in time_list:
            dt = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
            dt_utc = pytz.utc.localize(dt)
            dt_taiwan = dt_utc.astimezone(taiwan_tz)
            tw_time_list.append(dt_taiwan.strftime('%Y-%m-%d %H:%M:%S'))
        return tw_time_list
    
    def gen_chart(self, time_list, field_data):
        plt.figure(figsize=(12, 15))
        for i in range(1, 6):
            field_values = [float(value) for value in field_data[f'field{i}'] if value is not None]
            plt.plot(time_list, field_values, label=f'Field {i}')
        
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.title('Thingspeak')
        plt.legend()
        plt.xticks(rotation=45)
        plt.savefig('chart.jpg', format='jpg')
        return
    
    def update_photo_size(self):
        img = Image.open('chart.jpg')
        img2 = img.resize((240, 240))
        img2.save('pre_chart.jpg')
    
    def upload_to_imgur(self):
        CLIENT_ID = os.environ.get('IMGUR_CLIENT_ID')
        PATH = "chart.jpg"
        title = "Uploaded with PyImgur"
        
        im = pyimgur.Imgur(CLIENT_ID)
        uploaded_image = im.upload_image(PATH, title=title)
        image_url = uploaded_image.link
        
        PATH = "pre_chart.jpg"
        title = "Uploaded with pre_PyImgur"
        
        pre_im = pyimgur.Imgur(CLIENT_ID)
        uploaded_pre_image = pre_im.upload_image(PATH, title=title)
        pre_image_url = uploaded_pre_image.link
        
        return image_url, pre_image_url

if __name__ == "__main__":
    ts = Thingspeak()
    tw_time_list, field_data = ts.get_data_from_thingspeak("2466473", "GROLYCVTU08JWN8Q")
    ts.gen_chart(tw_time_list, field_data)
    ts.update_photo_size()
    image_url, pre_image_url = ts.upload_to_imgur()
    print(f'Image URL: {image_url}')
    print(f'Pre Image URL: {pre_image_url}')
