# charge
宿舍电费监控，可以用来卡电费

一个学校宿舍电费的 爬虫+预测+（消息推送） 项目，用于爬取并展示本学校宿舍各个时间的用电情况和低电量预警，了解用电规律，并避免因欠费导致的突然断电，也可以用来卡电费。

## 运行

> 本项目仅适用于苏州科技大学江枫校区，个人稳定用了三年多了，学校前段时间更新了服务，改了接口，特地更新了一下，打包了docker，顺带上传一下。本项目一般不需要迭代。

### Docker 容器化启动

1. `clone`本项目到服务器
   ```shell
   git clone https://github.com/admbb/charge.git
   ```
2. 修改`charge`文件夹下`config.ini`
   ```ini
   # 本处只列出十分建议更改的选项，其他选项请根据自身需求更改
   [API]
    token = bearer eyJh # 自己抓包获取
    url = https://wxxyshall.usts.edu.cn/charge/feeitem/getThirdData # 接口地址，一般无需更改
    referer = https://wxxyshall.usts.edu.cn/charge-app/  # 接口地址，一般无需更改
    feeitemid = # 自己抓包获取
    type = IEC
    level = # 自己抓包获取
    campus = # 自己抓包获取
    building = # 自己抓包获取
    room = # 自己抓包获取
    interval = 1800 # 间隔时间
   ```
   
3. 使用`docker`启动本项目
   ```shell
   docker run -d \
     -p 13333:13333 \
     -v $(pwd)/config.ini:/app/config.ini \
     -v $(pwd)/charge.csv:/app/charge.csv \
       charge:latest
   ```
   docker镜像可以自己构建`docker build -t charge:latest .`，也可以用我构建的。

4. 访问网站(ip:13333)检查是否正常

## 用到的技术
`requests`: 用于发送HTTP请求，通常用于与Web服务进行交互。
`csv`: 用于读写CSV文件，处理表格数据。
`flask`: 一个轻量级的Web应用框架，用于构建Web应用和API。
`pandas`: 提供强大的数据结构和数据分析工具，特别适合处理结构化数据。
`numpy`: 提供高性能的多维数组对象和工具，用于科学计算。

## 项目性质

本项目为Python综合性练手项目，可在不违反法律和开源许可证的前提下进行任意的二次开发。
