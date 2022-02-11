1. Create network if it not exists
```
docker network create revproxy
```

2. Build with
```
docker build -t alice_img .
```

3.1 Single run with
```
docker run -p 80:55401 alice_img
```

3.2 Run in traefik (https://doc.traefik.io/):
```
docker-compose -f alice-compose.yml up -d
```
Password for traefik can be genereted here: https://www.htaccessredirect.net/htpasswd-generator

