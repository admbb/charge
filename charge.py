"""
===========================
@author: csn
@time: 2022/4/6  23:58
@email: csnadmbb@gmail.com
===========================
"""
import requests
import time
import csv
import configparser
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('charge.log'),
        logging.StreamHandler()
    ]
)

class ConfigError(Exception):
    """配置文件错误异常"""
    pass

def load_config():
    """读取配置文件并进行验证"""
    config_path = Path('config.ini')
    if not config_path.exists():
        raise ConfigError("配置文件不存在")
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # 验证必要的配置项
    required_params = ['url', 'token', 'feeitemid', 'type', 'level', 'campus', 'building', 'room']
    if 'API' not in config:
        raise ConfigError("配置文件缺少 API 部分")
    
    for param in required_params:
        if param not in config['API']:
            raise ConfigError(f"配置文件缺少参数: {param}")
    
    # 验证 interval 配置项
    interval = config['API'].get('interval', '300')
    if not interval.isdigit() or int(interval) <= 0:
        raise ConfigError("interval 配置项必须为正整数")
    
    return config

def get_data(api_params):
    """获取电量数据"""
    headers = {
        'Host': 'wxxyshall.usts.edu.cn',
        'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Basic Y2hhcmdlOmNoYXJnZV9zZWNyZXQ=',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15',
        'synjones-auth': api_params['token'],
    }
    
    data = {
        'feeitemid': api_params['feeitemid'],
        'type': api_params['type'],
        'level': api_params['level'],
        'campus': api_params['campus'],
        'building': api_params['building'],
        'room': api_params['room']
    }
    
    try:
        response = requests.post(api_params['url'], data=data, headers=headers, timeout=10)
        response.raise_for_status()
        json_data = response.json()
        
        if 'map' not in json_data or 'showData' not in json_data['map']:
            raise ValueError("API 返回数据格式错误")
            
        new_data = float(json_data['map']['showData']['当前剩余电量'])
        return new_data
        
    except requests.exceptions.Timeout:
        logging.error("请求超时")
        raise
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response content: {response.content}")
        raise
    except Exception as err:
        logging.error(f"获取数据时发生错误: {err}")
        raise

def save_to_csv(timestamp, value):
    """保存数据到CSV文件，并限制数据行数"""
    csv_file_path = "charge.csv"
    max_rows = 10000
    delete_rows = 6000
    
    try:
        # 读取现有数据
        existing_data = []
        try:
            with open(csv_file_path, "r", encoding='utf-8') as f:
                reader = csv.reader(f)
                existing_data = list(reader)
        except FileNotFoundError:
            pass

        # 检查行数并在需要时删除旧数据
        if len(existing_data) >= max_rows:
            logging.info(f"CSV文件超过{max_rows}行，删除最早的{delete_rows}行数据")
            existing_data = existing_data[delete_rows:]

        # 添加新数据
        existing_data.append([timestamp, value])

        # 写入所有数据
        with open(csv_file_path, "w", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(existing_data)

    except Exception as e:
        logging.error(f"保存CSV文件时发生错误: {e}")
        raise

def main():
    """主函数"""
    retry_count = 0
    max_retries = 3
    
    try:
        config = load_config()
        api_params = config['API']
        interval = int(config['API'].get('interval', 300))  # 默认5分钟
        
        while True:
            try:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_data = get_data(api_params)
                save_to_csv(current_time, new_data)
                
                retry_count = 0  # 重置重试计数
                time.sleep(interval)
                
            except (requests.exceptions.RequestException, ConfigError) as e:
                retry_count += 1
                logging.error(f"第 {retry_count} 次重试: {str(e)}")
                
                if retry_count >= max_retries:
                    logging.critical("达到最大重试次数，程序退出")
                    break
                    
                time.sleep(60)  # 错误后等待1分钟再重试
                
            except Exception as e:
                logging.critical(f"发生未预期的错误: {e}")
                break
    except ConfigError as e:
        logging.critical(f"配置文件错误: {e}")
    except Exception as e:
        logging.critical(f"程序启动时发生错误: {e}")

if __name__ == "__main__":
    main()