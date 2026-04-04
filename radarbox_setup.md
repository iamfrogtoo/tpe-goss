# RadarBox 账号注册与配置指南

## 1. 注册 RadarBox 账号

1. 访问 RadarBox 官方网站：https://www.radarbox.com/
2. 点击右上角的 "Sign Up" 或 "注册" 按钮
3. 填写注册信息，包括：
   - 电子邮件地址
   - 密码
   - 确认密码
   - 姓名（可选）
4. 点击 "Create Account" 或 "创建账号" 按钮
5. 检查您的电子邮件，点击验证链接完成注册

## 2. 获取 RadarBox API 密钥

1. 登录 RadarBox 账号
2. 访问以下链接：https://www.airnavradar.com/raspberry-pi/claim
3. 点击 "Add New Feeder" 或 "添加新 feeder"
4. 选择 "ADS-B" 作为 feeder 类型
5. 填写 feeder 信息：
   - Feeder Name: TPE-GOSS
   - Location: Taoyuan, Taiwan
   - Latitude: 25.07
   - Longitude: 121.23
   - Altitude: 0 (或实际海拔高度)
6. 点击 "Submit" 或 "提交" 按钮
7. 系统会生成一个唯一的 API 密钥，类似于：`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
8. 复制这个 API 密钥，稍后会用到

## 3. 配置 Docker Compose

1. 编辑树莓派上的 `docker-compose.yml` 文件：
   ```bash
   ssh xinzhi@192.168.31.221 nano adsb-stack/docker-compose.yml
   ```

2. 在 `ultrafeeder` 服务的 `environment` 部分添加 `RADARBOX_KEY` 环境变量：
   ```yaml
   services:
     ultrafeeder:
       image: ghcr.io/sdr-enthusiasts/docker-adsb-ultrafeeder:latest
       container_name: ultrafeeder
       restart: always
       privileged: true
       environment:
         - TZ=Asia/Taipei
         - READSB_DEVICE_TYPE=rtlsdr
         - READSB_RTLSDR_DEVICE=0
         - READSB_GAIN=49.6
         - READSB_LAT=25.07
         - READSB_LON=121.23
         - READSB_WRITE_JSON=/run/readsb
         - ENABLE_FR24=true
         - FR24KEY=de528ed33a3c9b26
         - ENABLE_PIAWARE=true
         - ENABLE_RADARBOX=true
         - RADARBOX_KEY=YOUR_RADARBOX_API_KEY  # 替换为实际的 API 密钥
         - ENABLE_ADSBEXCHANGE=true
         - ENABLE_PLANEFINDER=true
   ```

3. 保存文件并退出编辑器

## 4. 重启 Ultrafeeder 容器

1. 进入 adsb-stack 目录：
   ```bash
   ssh xinzhi@192.168.31.221 cd adsb-stack
   ```

2. 重启容器：
   ```bash
   ssh xinzhi@192.168.31.221 docker-compose up -d
   ```

3. 检查容器状态：
   ```bash
   ssh xinzhi@192.168.31.221 docker ps -a | grep ultrafeeder
   ```

4. 查看容器日志，确认 RadarBox 服务是否正常启动：
   ```bash
   ssh xinzhi@192.168.31.221 docker logs ultrafeeder 2>&1 | grep -i radarbox
   ```

## 5. 验证 RadarBox 连接

1. 登录 RadarBox 账号
2. 访问：https://www.radarbox.com/account/feeders
3. 查看您的 feeder 状态，应该显示为 "Online" 或 "在线"
4. 等待几分钟，您应该开始看到 feeder 数据在 RadarBox 网站上显示

## 6. 故障排除

如果 RadarBox 服务没有正常启动，请检查以下几点：

1. 确认 API 密钥是否正确
2. 检查容器日志，查找错误信息
3. 确保网络连接正常
4. 验证 RadarBox 网站是否可以访问

## 7. 相关资源

- RadarBox 官方文档：https://www.radarbox.com/support
- Docker ADS-B Ultrafeeder 文档：https://github.com/sdr-enthusiasts/docker-adsb-ultrafeeder
