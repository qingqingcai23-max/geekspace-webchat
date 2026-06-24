# Public Server Quickstart

For a real public website, the fastest path is:

1. Buy a Tencent Cloud Lighthouse server in Hong Kong
2. Open ports `22`, `80`, `443`
3. SSH into the server
4. Run:

```bash
git clone https://github.com/qingqingcai23-max/geekspace-webchat.git /opt/geekspace-webchat
cd /opt/geekspace-webchat
bash deploy/bootstrap_ubuntu.sh
```

If the script stops and asks for `.env`, do this:

```bash
cd /opt/geekspace-webchat
nano .env
```

Set:

```bash
GEEKSPACE_API_KEY=your-real-key
```

Then start:

```bash
docker compose up -d --build
```

Verify:

```bash
curl http://127.0.0.1/api/health
```

Open in browser:

```text
http://your-server-ip/
```
