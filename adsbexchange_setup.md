# ADS-B Exchange 账号注册与配置指南

## 1. 关于 ADS-B Exchange

ADS-B Exchange 是一个开源的、社区驱动的飞行跟踪项目，允许用户免费贡献 ADS-B 数据并访问全球飞行数据。与其他服务不同，ADS-B Exchange 不需要 API 密钥来发送数据，它是完全免费和开放的。

## 2. 注册 ADS-B Exchange 账号

1. 访问 ADS-B Exchange 官方网站：https://adsbexchange.com/
2. 点击右上角的 "Sign Up" 或 "注册" 按钮
3. 填写注册信息，包括：
   - 电子邮件地址
   - 密码
   - 确认密码
4. 点击 "Create Account" 或 "创建账号" 按钮
5. 检查您的电子邮件，点击验证链接完成注册

## 3. 安装 Feed 客户端（如果需要）

如果您使用的是标准的 ADS-B 设备，您可能需要安装 ADS-B Exchange 的 feed 客户端：

1. 登录树莓派或其他设备
2. 运行以下命令：
   ```bash
   curl -L -o /tmp/axfeed.sh https://www.adsbexchange.com/feed.sh
   sudo bash /tmp/axfeed.sh
   ```
3. 按照提示完成安装

## 4. 关联 Feeder

1. 登录 ADS-B Exchange 账号
2. 访问以下链接：https://adsbexchange.com/my-feeders/
3. 您的 feeder 应该会自动显示在列表中，因为 ADS-B Exchange 会根据 IP 地址和其他标识符自动识别 feeder
4. 如果没有自动显示，您可以手动添加：
   - 点击 "Add New Feeder" 或 "添加新 feeder"
   - 输入 feeder 的详细信息，包括位置、硬件等
   - 点击 "Submit" 或 "提交" 按钮

## 5. 验证 Feeder 连接

1. 检查 feed 客户端是否连接：https://www.adsbexchange.com/myip/
2. 查看 MLAT 同步状态：https://map.adsbexchange.com/mlat-map/
3. 登录账号后，访问：https://adsbexchange.com/my-feeders/ 查看 feeder 状态

## 6. 安装统计包（可选）

如果您想查看只由您接收的飞机的在线地图，可以安装统计包：

```bash
curl -L -o /tmp/axstats.sh https://www.adsbexchange.com/stats.sh 
sudo bash /tmp/axstats.sh
```

## 4. 验证 Feeder 连接

1. 登录 ADS-B Exchange 账号
2. 访问：https://adsbexchange.com/my-feeders/
3. 查看您的 feeder 状态，应该显示为 "Online" 或 "在线"
4. 点击 feeder 名称，查看详细的统计信息，包括：
   - 接收的消息数量
   - 覆盖范围
   - 跟踪的航班数量
   - 历史数据

## 5. 配置 Docker Compose（可选）

虽然 ADS-B Exchange 不需要 API 密钥，但您可以在 Docker Compose 中添加一些可选的配置：

1. 编辑树莓派上的 `docker-compose.yml` 文件：
   ```bash
   ssh xinzhi@192.168.31.221 nano adsb-stack/docker-compose.yml
   ```

2. 可以添加以下可选的环境变量：
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
         - ENABLE_ADSBEXCHANGE=true
         - ADSBEXCHANGE_SITE_NAME=TPE-GOSS  # 可选：设置 feeder 站点名称
         - ENABLE_PLANEFINDER=true
   ```

3. 保存文件并退出编辑器

4. 重启容器：
   ```bash
   ssh xinzhi@192.168.31.221 cd adsb-stack && docker-compose up -d
   ```

## 8. 查看 Feeder 数据

1. 登录 ADS-B Exchange 账号
2. 访问：https://adsbexchange.com/my-feeders/
3. 点击您的 feeder 名称，查看详细的统计信息
4. 您还可以在地图上查看您的 feeder 覆盖范围：https://adsbexchange.com/map/

## 9. 故障排除

如果您的 feeder 没有显示在 ADS-B Exchange 网站上，请检查以下几点：

1. 确保 `ENABLE_ADSBEXCHANGE=true` 在 Docker Compose 中正确设置
2. 检查容器日志，查找错误信息：
   ```bash
   ssh xinzhi@192.168.31.221 docker logs ultrafeeder 2>&1 | grep -i adsbexchange
   ```
3. 确保网络连接正常，ADS-B Exchange 服务器可以访问
4. 等待一段时间，因为 feeder 可能需要一些时间才能被系统识别

## 10. 相关资源

- ADS-B Exchange 官方文档：https://adsbexchange.com/how-to-feed/
- Docker ADS-B Ultrafeeder 文档：https://github.com/sdr-enthusiasts/docker-adsb-ultrafeeder
- 现有设备加入指南：https://www.adsbexchange.com/ways-to-join-the-exchange/existing-equipment/
