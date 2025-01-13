from flask import Flask, request, flash, render_template_string, jsonify
from configparser import ConfigParser
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/', methods=['GET', 'POST'])
def index():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 读取配置
    config = ConfigParser()
    config.read('config.ini')
    token = config['API']['token']
    url = config['API']['url']
    referer = config['API']['referer']
    feeitemid = config['API']['feeitemid']
    level = config['API']['level']
    campus = config['API']['campus']
    building = config['API']['building']
    room = config['API']['room']
    interval = config['API']['interval']

    if request.method == 'POST':
        # 保存配置
        config['API']['token'] = request.form.get('token')
        config['API']['url'] = request.form.get('url')
        config['API']['referer'] = request.form.get('referer')
        config['API']['feeitemid'] = request.form.get('feeitemid')
        config['API']['level'] = request.form.get('level')
        config['API']['campus'] = request.form.get('campus')
        config['API']['building'] = request.form.get('building')
        config['API']['room'] = request.form.get('room')
        config['API']['interval'] = request.form.get('interval')

        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        flash('保存成功！', 'success')

    html_template = '''
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>电费监控</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/moment"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-moment"></script>
        <style>
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.4);
            }
            .modal-content {
                background-color: #fefefe;
                margin: 15% auto;
                padding: 20px;
                border: 1px solid #888;
                width: 80%;
                max-width: 500px;
                border-radius: 5px;
            }
            .chart-container {
                position: relative;
                height: 60vh;
                width: 100%;
                margin: 20px 0;
            }
            .time-btn {
                min-width: 100px;
                margin: 0 5px;
                transition: all 0.3s;
            }
            .time-btn.active {
                background-color: #0056b3;
                border-color: #0056b3;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
            }
            .card {
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .card-body {
                padding: 2rem;
            }
            .current-time {
                color: #6c757d;
                font-size: 1.2rem;
                margin-bottom: 2rem;
            }
            .config-btn {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 100;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            .config-btn i {
                font-size: 24px;
            }
        </style>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container-fluid py-4">
            <div class="row justify-content-center">
                <div class="col-lg-11">
                    <div class="card">
                        <div class="card-body">
                            <h2 class="card-title text-center text-primary mb-4">电费监控系统</h2>
                            
                            <!-- 当前时间显示 -->
                            <div class="text-center current-time">
                                <i class="bi bi-clock"></i> {{ current_time }}
                            </div>
                            
                            <!-- 图表按钮组 -->
                            <div class="d-flex justify-content-center mb-4">
                                <div class="btn-group">
                                    <button class="btn btn-primary time-btn active" data-hours="24" onclick="updateChartAndButton(this, 24)">
                                        <i class="bi bi-1-circle"></i> 一天
                                    </button>
                                    <button class="btn btn-primary time-btn" data-hours="72" onclick="updateChartAndButton(this, 72)">
                                        <i class="bi bi-3-circle"></i> 三天
                                    </button>
                                    <button class="btn btn-primary time-btn" data-hours="168" onclick="updateChartAndButton(this, 168)">
                                        <i class="bi bi-7-circle"></i> 七天
                                    </button>
                                    <button class="btn btn-primary time-btn" onclick="updateSimulation(this)">
                                        <i class="bi bi-graph-up"></i> 模拟
                                    </button>
                                </div>
                            </div>

                            <!-- 图表容器 -->
                            <div class="chart-container">
                                <canvas id="myChart"></canvas>
                            </div>
                            <div id="prediction-info" class="text-center mb-4" style="display: none;">
                                <p class="h5 text-primary"></p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 配置按钮 -->
        <button class="btn btn-primary config-btn" onclick="openConfigModal()">
            <i class="bi bi-gear-fill"></i>
        </button>

        <!-- 配置模态框 -->
        <div id="configModal" class="modal">
            <div class="modal-content">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h3 class="m-0">配置设置</h3>
                    <button type="button" class="btn-close" onclick="closeConfigModal()"></button>
                </div>
                <form method="post" action="/">
                    <div class="mb-3">
                        <label for="token" class="form-label">Token:</label>
                        <input type="text" class="form-control" id="token" name="token" value="{{ token }}">
                    </div>
                    <div class="mb-3">
                        <label for="url" class="form-label">URL:</label>
                        <input type="text" class="form-control" id="url" name="url" value="{{ url }}">
                    </div>
                    <div class="mb-3">
                        <label for="referer" class="form-label">Referer:</label>
                        <input type="text" class="form-control" id="referer" name="referer" value="{{ referer }}">
                    </div>
                    <div class="mb-3">
                        <label for="feeitemid" class="form-label">Feeitemid:</label>
                        <input type="text" class="form-control" id="feeitemid" name="feeitemid" value="{{ feeitemid }}">
                    </div>
                    <div class="mb-3">
                        <label for="level" class="form-label">Level:</label>
                        <input type="text" class="form-control" id="level" name="level" value="{{ level }}">
                    </div>
                    <div class="mb-3">
                        <label for="campus" class="form-label">Campus:</label>
                        <input type="text" class="form-control" id="campus" name="campus" value="{{ campus }}">
                    </div>
                    <div class="mb-3">
                        <label for="building" class="form-label">Building:</label>
                        <input type="text" class="form-control" id="building" name="building" value="{{ building }}">
                    </div>
                    <div class="mb-3">
                        <label for="room" class="form-label">Room:</label>
                        <input type="text" class="form-control" id="room" name="room" value="{{ room }}">
                    </div>
                    <div class="mb-3">
                        <label for="interval" class="form-label">刷新间隔(秒):</label>
                        <input type="number" class="form-control" id="interval" name="interval" value="{{ interval }}">
                    </div>
                    <div class="d-flex justify-content-end gap-2">
                        <button type="button" class="btn btn-secondary" onclick="closeConfigModal()">取消</button>
                        <button type="submit" class="btn btn-primary">保存</button>
                    </div>
                </form>
            </div>
        </div>

        <script>
        let myChart = null;
        let currentButton = document.querySelector('.time-btn.active');

        function updateChartAndButton(button, hours) {
            // 更新按钮状态
            document.querySelectorAll('.time-btn').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            currentButton = button;
            
            // 更新图表
            updateChart(hours);
        }

        async function updateChart(hours) {
            try {
                // 隐藏预测信息
                document.getElementById('prediction-info').style.display = 'none';
                
                const response = await fetch(`/get_data?hours=${hours}`);
                const data = await response.json();
                
                if (myChart) {
                    myChart.destroy();
                }

                const ctx = document.getElementById('myChart').getContext('2d');
                myChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.map(item => item.timestamp),
                        datasets: [{
                            label: '电费数据',
                            data: data.map(item => item.value),
                            borderColor: 'rgb(75, 192, 192)',
                            backgroundColor: 'rgba(75, 192, 192, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 0,  // 默认不显示数据点
                            pointHoverRadius: 5,  // 鼠标悬停时显示点
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                            }
                        },
                        scales: {
                            x: {
                                type: 'time',
                                time: {
                                    unit: 'hour',
                                    displayFormats: {
                                        hour: 'MM-DD HH:mm'
                                    }
                                },
                                grid: {
                                    display: false
                                },
                                title: {
                                    display: true,
                                    text: '时间',
                                    font: {
                                        size: 16,
                                        weight: 'bold'
                                    },
                                    padding: {
                                        top: 10
                                    }
                                },
                                ticks: {
                                    maxTicksLimit: hours > 72 ? 7 : (hours > 24 ? 12 : 24),  // 控制时间轴刻度数量
                                    source: 'auto',
                                }
                            },
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.1)'
                                },
                                title: {
                                    display: true,
                                    text: '剩余电费',
                                    font: {
                                        size: 16,
                                        weight: 'bold'
                                    },
                                    padding: {
                                        bottom: 10
                                    }
                                }
                            }
                        },
                        interaction: {
                            intersect: false,
                            mode: 'index'
                        },
                        elements: {
                            point: {
                                radius: 0,  // 默认不显示点
                                hoverRadius: 5,  // 鼠标悬停时显示点
                            },
                            line: {
                                borderWidth: 2
                            }
                        }
                    }
                });
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }

        // 模态框控制
        function openConfigModal() {
            document.getElementById('configModal').style.display = 'block';
        }

        function closeConfigModal() {
            document.getElementById('configModal').style.display = 'none';
        }

        window.onclick = function(event) {
            if (event.target == document.getElementById('configModal')) {
                closeConfigModal();
            }
        }

        // 页面加载时显示一天的数据
        document.addEventListener('DOMContentLoaded', () => {
            updateChart(24);
        });

        // 添加模拟数据更新函数
        async function updateSimulation(button) {
            // 更新按钮状态
            document.querySelectorAll('.time-btn').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            try {
                const response = await fetch('/get_simulation_data');
                const responseData = await response.json();
                const data = responseData.data;
                
                if (myChart) {
                    myChart.destroy();
                }

                const ctx = document.getElementById('myChart').getContext('2d');
                myChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.map(item => item.timestamp),
                        datasets: [{
                            label: '电费数据',
                            data: data.map(item => item.value),
                            borderColor: 'rgb(75, 192, 192)',
                            backgroundColor: 'rgba(75, 192, 192, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            pointRadius: function(context) {
                                const point = data[context.dataIndex];
                                return point.isCritical ? 6 : 0;
                            },
                            pointBackgroundColor: function(context) {
                                const point = data[context.dataIndex];
                                return point.isCritical ? 'red' : 'rgb(75, 192, 192)';
                            },
                            pointBorderColor: function(context) {
                                const point = data[context.dataIndex];
                                return point.isCritical ? 'red' : 'rgb(75, 192, 192)';
                            },
                            pointHoverRadius: 5,
                            segment: {
                                borderDash: function(ctx) {
                                    return data[ctx.p1DataIndex].isSimulated ? [6, 6] : undefined;
                                }
                            }
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                                callbacks: {
                                    label: function(context) {
                                        let label = '';
                                        if (data[context.dataIndex].isSimulated) {
                                            label = '模拟数据: ';
                                        } else {
                                            label = '实际数据: ';
                                        }
                                        label += context.parsed.y.toFixed(2);
                                        return label;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                type: 'time',
                                time: {
                                    unit: 'hour',
                                    displayFormats: {
                                        hour: 'HH:mm'
                                    },
                                    tooltipFormat: 'MM-DD HH:mm'
                                },
                                grid: {
                                    display: false
                                },
                                title: {
                                    display: true,
                                    text: '时间',
                                    font: {
                                        size: 16,
                                        weight: 'bold'
                                    },
                                    padding: {
                                        top: 10
                                    }
                                },
                                ticks: {
                                    maxTicksLimit: 24  // 显示24小时的刻度
                                }
                            },
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.1)'
                                },
                                title: {
                                    display: true,
                                    text: '剩余电费',
                                    font: {
                                        size: 16,
                                        weight: 'bold'
                                    },
                                    padding: {
                                        bottom: 10
                                    }
                                }
                            }
                        },
                        interaction: {
                            intersect: false,
                            mode: 'index'
                        }
                    }
                });

                // 显示预测信息
                const predictionInfo = document.getElementById('prediction-info');
                if (responseData.criticalPoint) {
                    predictionInfo.style.display = 'block';
                    predictionInfo.querySelector('p').textContent = 
                        `预测宿舍电费在${responseData.criticalPoint.time}时为${responseData.criticalPoint.value}度`;
                } else {
                    predictionInfo.style.display = 'none';
                }
            } catch (error) {
                console.error('Error fetching simulation data:', error);
            }
        }
        </script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

    return render_template_string(html_template, 
                                current_time=current_time,
                                token=token, url=url, referer=referer,
                                feeitemid=feeitemid, level=level,
                                campus=campus, building=building, room=room,
                                interval=interval)

@app.route('/get_data')
def get_data():
    try:
        hours = int(request.args.get('hours', 24))
        df = pd.read_csv('charge.csv')
        df.columns = ['timestamp', 'value']
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        filtered_df = df[(df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)]
        
        # 根据时间范围调整采样率
        if hours > 72:  # 7天数据
            filtered_df = filtered_df.set_index('timestamp').resample('2h').mean().reset_index()
        elif hours > 24:  # 3天数据
            filtered_df = filtered_df.set_index('timestamp').resample('1h').mean().reset_index()
        
        result = []
        for _, row in filtered_df.iterrows():
            result.append({
                'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'value': float(row['value'])
            })
        
        return jsonify(result)
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify([])

@app.route('/get_simulation_data')
def get_simulation_data():
    try:
        df = pd.read_csv('charge.csv')
        df.columns = ['timestamp', 'value']
        time_column = 'timestamp'
        value_column = 'value'
        
        print("Debug: Original data shape:", df.shape)
        
        df[time_column] = pd.to_datetime(df[time_column])
        
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        # 获取今天的实际数据
        today_data = df[(df[time_column] >= today) & (df[time_column] <= now)].copy()
        print(f"Debug: Today's data count: {len(today_data)}")
        
        # 计算当天数据的趋势
        if len(today_data) >= 2:
            # 计算当天数据的斜率
            today_times = (today_data[time_column] - today).dt.total_seconds()
            slope, intercept = np.polyfit(today_times, today_data[value_column], 1)
            print(f"Debug: Today's trend slope: {slope}")
        else:
            slope = 0
            
        # 获取历史数据
        three_days_ago = today - timedelta(days=3)
        historical_data = df[(df[time_column] >= three_days_ago) & (df[time_column] < today)].copy()
        print(f"Debug: Historical data count: {len(historical_data)}")
        
        # 创建完整的时间序列
        full_timeline = pd.date_range(start=today, end=tomorrow, freq='10min')[:-1]
        result_df = pd.DataFrame({time_column: full_timeline})
        print(f"Debug: Timeline points: {len(result_df)}")
        
        # 合并今天的实际数据
        result_df = result_df.merge(today_data[[time_column, value_column]], 
                                  on=time_column, 
                                  how='left')
        
        # 获取最后一个实际数据点
        last_real_data = today_data.iloc[-1] if not today_data.empty else None
        
        # 对未来时间点进行预测
        prediction_count = 0
        for idx, row in result_df.iterrows():
            if pd.isna(row[value_column]):
                current_time = row[time_column]
                
                # 获取历史数据中相同时间点的数据
                similar_times = historical_data[
                    (historical_data[time_column].dt.hour == current_time.hour) &
                    (historical_data[time_column].dt.minute == current_time.minute)
                ]
                
                if not similar_times.empty:
                    base_value = similar_times[value_column].mean()
                    
                    if last_real_data is not None:
                        # 根据当天趋势调整预测值
                        time_diff = (current_time - last_real_data[time_column]).total_seconds()
                        trend_adjustment = slope * time_diff
                        
                        # 将趋势调整应用到预测值
                        predicted_value = last_real_data[value_column] + trend_adjustment
                        
                        # 使用历史数据和趋势预测的加权平均
                        result_df.at[idx, value_column] = (predicted_value * 0.7 + base_value * 0.3)
                    else:
                        result_df.at[idx, value_column] = base_value
                    
                    prediction_count += 1
                elif last_real_data is not None:
                    # 如果没有历史数据，仅使用趋势预测
                    time_diff = (current_time - last_real_data[time_column]).total_seconds()
                    trend_adjustment = slope * time_diff
                    result_df.at[idx, value_column] = last_real_data[value_column] + trend_adjustment
                    prediction_count += 1
        
        print(f"Debug: Predicted points count: {prediction_count}")
        
        # 确定今天是周几（0-6，0是周一）
        current_weekday = datetime.now().weekday()
        
        # 确定关键时间点
        if current_weekday in [4, 5]:  # 周五、周六
            critical_hour = 23
            critical_minute = 30
        else:  # 周日到周四
            critical_hour = 23
            critical_minute = 0
            
        # 转换为前端需要的格式
        result = []
        current_time = datetime.now()
        critical_value = None
        
        for _, row in result_df.iterrows():
            if not pd.isna(row[value_column]):
                is_critical_time = (row[time_column].hour == critical_hour and 
                                  row[time_column].minute == critical_minute)
                                  
                data_point = {
                    'timestamp': row[time_column].strftime('%Y-%m-%d %H:%M:%S'),
                    'value': float(row[value_column]),
                    'isSimulated': row[time_column] > current_time,
                    'isCritical': is_critical_time
                }
                
                if is_critical_time and row[time_column] > current_time:
                    critical_value = {
                        'time': f"{critical_hour:02d}:{critical_minute:02d}",
                        'value': round(float(row[value_column]), 2)
                    }
                    
                result.append(data_point)
        
        return jsonify({
            'data': result,
            'criticalPoint': critical_value
        })
        
    except Exception as e:
        print(f"Error in simulation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'data': [], 'criticalPoint': None})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=13333)
