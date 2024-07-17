import os
import requests
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import pytz
import pyimgur
from PIL import Image
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Thingspeak:
    def get_data_from_thingspeak(self, channel_id, api_read_key):
        url = f'https://thingspeak.com/channels/{channel_id}/feed.json?api_key={api_read_key}'
        data = requests.get(url).json()
        if data.get('error') == 'Not Found':
            return 'Not Found', 'Not Found'
        
        time_list = list()
        field_data = {f'field{i}': [] for i in range(1, 6)}
        
        for entry in data['feeds']:
            time_list.append(entry.get('created_at'))
            for i in range(1, 6):
                field_data[f'field{i}'].append(entry.get(f'field{i}'))
                
        # Convert to Taiwan time
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
    
    def gen_chart(self, time_list, field_data, field_name):
        plt.figure(figsize=(12, 6))
        field_values = []
        valid_time_list = []
        for time, value in zip(time_list, field_data[field_name]):
            if value and value.strip():
                field_values.append(float(value))
                valid_time_list.append(time)
        
        plt.plot(valid_time_list, field_values, label=field_name)
        
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.title(f'Thingspeak - {field_name}')
        plt.legend()
        plt.xticks(rotation=45)
        chart_filename = f'{field_name}_chart.jpg'
        plt.savefig(chart_filename, format='jpg')
        plt.close()  # Close the plot to avoid overlapping of plots in successive calls
        return chart_filename
    
    def update_photo_size(self, chart_filename):
        img = Image.open(chart_filename)
        img2 = img.resize((240, 240))
        pre_chart_filename = f'pre_{chart_filename}'
        img2.save(pre_chart_filename)
        return pre_chart_filename
    
    def upload_to_imgur(self, chart_filename):
        CLIENT_ID = os.getenv('IMGUR_CLIENT_ID')
        if not CLIENT_ID:
            raise ValueError("IMGUR_CLIENT_ID environment variable not set")
        
        if not os.path.exists(chart_filename):
            raise FileNotFoundError(f"File {chart_filename} does not exist")
        
        title = "Uploaded with PyImgur"
        
        im = pyimgur.Imgur(CLIENT_ID)
        uploaded_image = im.upload_image(chart_filename, title=title)
        image_url = uploaded_image.link
        
        pre_chart_filename = self.update_photo_size(chart_filename)
        
        if not os.path.exists(pre_chart_filename):
            raise FileNotFoundError(f"File {pre_chart_filename} does not exist")
        
        pre_im = pyimgur.Imgur(CLIENT_ID)
        uploaded_pre_image = pre_im.upload_image(pre_chart_filename, title=title)
        pre_image_url = uploaded_pre_image.link
        
        return image_url, pre_image_url

if __name__ == "__main__":
    ts = Thingspeak()
    tw_time_list, field_data = ts.get_data_from_thingspeak("2466473", "GROLYCVTU08JWN8Q")
    for i in range(1, 6):
        field_name = f'field{i}'
        chart_filename = ts.gen_chart(tw_time_list, field_data, field_name)
        image_url, pre_image_url = ts.upload_to_imgur(chart_filename)
        print(f'{field_name} Image URL: {image_url}')
        print(f'{field_name} Pre Image URL: {pre_image_url}')
