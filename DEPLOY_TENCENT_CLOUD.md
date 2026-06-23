# 腾讯云轻量应用服务器（香港）部署

适用目录：`C:\Users\Administrator\Desktop\新建文件夹\geekspace-webchat`

## 一、推荐购买

- 产品：腾讯云轻量应用服务器
- 地域：香港
- 系统：Ubuntu 22.04 LTS
- 套餐：先选最低可用配置即可

说明：
- 香港节点通常不需要中国大陆 ICP 备案即可先上线访问
- 这个项目当前采用 Docker 部署，后续升级会更省事

## 二、服务器放行端口

在腾讯云控制台放行：

- `22`：SSH
- `80`：HTTP
- `443`：HTTPS（后面绑域名时再用）

## 三、登录服务器后安装 Docker

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

## 四、拉取项目

```bash
git clone https://github.com/qingqingcai23-max/geekspace-webchat.git
cd geekspace-webchat
```

## 五、配置环境变量

先复制模板文件：

```bash
cp .env.example .env
```

再编辑 `.env`：

```bash
nano .env
```

## 六、启动项目

```bash
docker compose up -d --build
```

查看运行状态：

```bash
docker compose ps
docker compose logs -f
```

## 七、访问网站

直接用服务器公网 IP 打开：

```text
http://你的服务器公网IP
```

## 八、更新网站

以后更新代码只需要：

```bash
cd geekspace-webchat
git pull
docker compose up -d --build
```

## 九、排查命令

如果打不开：

```bash
docker compose ps
docker compose logs --tail=200
sudo ss -lntp | grep -E ':80|:8080'
```

如果容器正常但网页打不开，优先检查：

1. 腾讯云防火墙是否放行 `80`
2. 服务器系统防火墙是否拦截
3. `.env` 里的 `GEEKSPACE_API_KEY` 是否已正确填写
