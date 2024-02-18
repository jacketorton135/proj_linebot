import requests
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import pytz
	
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
            if data.get('field1') == '0':
                bpm_list.append('0.01')
            else:
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
        # 上傳圖片到 Imgur
        client_id = '1057e1ccf4ca17c'  # 替換成你的 Imgur Client ID

        headers = {'Authorization': 'Client-ID {}'.format(client_id)}
        data = {'image': open('chart.png', 'rb').read()}
        response = requests.post('https://api.imgur.com/3/image', headers=headers, data=data)
        if response.status_code == 200:
            return response.json()['data']['link']
        else:
            print('Error uploading image to Imgur')
            return None
        
if __name__ == "__main__":
    ts = Thingspeak()
    ts.get_data_from_thingspeak()