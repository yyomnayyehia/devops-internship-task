# Troubleshooting journal

Keep chronological entries. Copy this block for each meaningful investigation.

## Entry 1 / 08/09/2026 10:30
- Symptom: docker compose -p barq-assessment up --build -d works but app-01 and app-02 show "unhealthy"
- Hypothesis: health check api incorrectly configured inside the yml file
- Command or test: docker compose -p barq-assessment logs app-01 app-02 | grep healthz

- Actual output: 
app-01  | {"timestamp": "2026-09-08T17:43:43.168+00:00", "level": "WARN", "service": "barq-api", "event": "http_request", "instance_id": "app-01", "request_id": "fc5b64684d3e4e74bdb663f97b85cf35", "method": "GET", "path": "/healthz", "status": 404, "duration_ms": 0.18}


- Failed attempt and what changed your thinking: Thought the app was crashing but after further investigation saw that the server was up and running normally so immediately realized it has something to do with configuration inside the yml file

- Root cause: Inside the docker-compose.yml, Docker checks if the app is healthy through /healthz endpoint while the correct endpoint is /health based on server.py

- Fix: Change the incorrect endpoint(/healthz) to the correct one (/health)

- Retest evidence:  re ran docker compose -p barq-assessment ps -a

NAME       IMAGE                                                                                        COMMAND                  SERVICE    CREATED          STATUS                    PORTS
app-01     barq-assessment-app-01                                                                       "python -m app.server"   app-01     59 seconds ago   Up 54 seconds (healthy)   8080/tcp
app-02     barq-assessment-app-02                                                                       "python -m app.server"   app-02     59 seconds ago   Up 54 seconds (healthy)   8080/tcp

- Related commit: 88b4e87cae795397f9c1d898e4039d62f3adc7f3

- Remaining uncertainty: The apps are now healthy there might be still underlying issuses 


## Entry 2 / 08/09/2026 / 10:48
- Symptom: app-02 instance id is app-01 inside its logs report instead of its own identity 

- Hypothesis: wrongly configured in the docker-compose.yml

- Command or test: grep -n "INSTANCE_ID\|instance_id\|container_name" docker-compose.yml

- Actual output:
yomna@LAPTOP-KLHNR2J1:~/devops-internship-task$ grep -n "INSTANCE_ID\|instance_id\|container_name" docker-compose.yml
21:    container_name: postgres
39:    container_name: redis
50:    container_name: app-01
53:      INSTANCE_ID: "app-01"
56:    container_name: app-02
59:      INSTANCE_ID: "app-01"
62:    container_name: nginx

- Failed attempt and what changed your thinking:


- Root cause: Inside the docker-compose.yml file, app-02 is hardcoded to app-01 instead if app-02 

- Fix: Rename app-02's instance ID from app-01 to app-02

- Retest evidence:
yomna@LAPTOP-KLHNR2J1:~/devops-internship-task$ grep -n "INSTANCE_ID\|instance_id\|container_name" docker-compose.yml
21:    container_name: postgres
39:    container_name: redis
50:    container_name: app-01
53:      INSTANCE_ID: "app-01"
56:    container_name: app-02
59:      INSTANCE_ID: "app-02"
62:    container_name: nginx

- Related commit: a3b826e0d370c13dfb0bd2fc59a6e9345169c699

- Remaining uncertainty: unsure if assigning app-02 its correct instance id in the yml file is enough or if there might be remaining mismatch error

 

## Entry 3 /08/09/2026 / 11:37
- Symptom: App log reports REDIS_URL on port 6380, but redis's own log shows it running on 6379

- Hypothesis: The redis url is configured to the 
wrong port inside the app's config file 

- Command or test: grep -rn "REDIS"  docker-compose.yml config

- Actual output: 
config/app.env:2:REDIS_URL=redis://redis:6380/0

- Failed attempt and what changed your thinking:

- Root cause: config/app.env hardcodes redis_url to port 6380 

- Fix: change REDIS_URL in app.env from redis://redis:6380/0 to redis://redis:6379/0 

- Retest evidence:  app-01  | {"timestamp": "2026-09-08T20:59:37.455+00:00", "level": "INFO", "service": "barq-api", "event": "configuration_loaded", "database_url": "postgresql://barq_app:BarqLabOnly_7qN2vK8d@postgres:5433/barq_tasks", "redis_url": "redis://redis:6379/0"}

- Related commit: 60295ad6f4bf4986f83fd36374a8ba205a6d4911

- Remaining uncertainty: Havent confirmed yet if redis's port number is hardcoded wrongly somewhere else or not.

## Entry 4 / 09/09/2026 / 12:00

- Symptom: App does not connect to database 

- Hypothesis: mismatch of database configurations in docker-compose.yml or the app.env

- Command or test: docker compose -p barq-assessment logs --no-color | grep -i postgres

- Actual output:
 app-01  | {"timestamp": "2026-09-08T20:59:37.455+00:00", "level": "INFO", "service": "barq-api", "event": "configuration_loaded", "database_url": "postgresql://barq_app:BarqLabOnly_7qN2vK8d@postgres:5433/barq_tasks", "redis_url": "redis://redis:6379/0"}

postgres  | 2026-09-07 17:07:20.496 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432

- Failed attempt and what changed your thinking:

- Root cause: app.env uses port 5433 but postgres listens on 5432

- Fix: Update the DATABASE_URL in app.env to use port 5432 

- Retest evidence:
app-01  | {"timestamp": "2026-09-08T21:29:48.849+00:00", "level": "INFO", "service": "barq-api", "event": "configuration_loaded", "database_url": "postgresql://barq_app:BarqLabOnly_7qN2vK8d@postgres:5432/barq_tasks", "redis_url": "redis://redis:6379/0"}

- Related commit: 10a54cb9be03b0fb3cbef834897fba55d278c19e

- Remaining uncertainty: port is correct but database still failing




## Entry 5 / 09/09/2026 / 12:32

- Symptom: App still fails to connect after port mismatch 

- Hypothesis: The database credentials is wrong

- Command or test: grep -E "POSTGRES_PASSWORD|DATABASE_URL" docker-compose.yml config/app.env

- Actual output:
docker-compose.yml:      POSTGRES_PASSWORD: BarqLabOnly_7qN2vK8c
config/app.env:DATABASE_URL=postgresql://barq_app:BarqLabOnly_7qN2vK8d@postgres:5432/barq_tasks 
- Failed attempt and what changed your thinking:
- Root cause: Password for postgres in app.env ends with d while the password in docker-compose.yml ends with c

- Fix: Update app.env to the correct password from the docker-compose.yml 

- Retest evidence: 
docker-compose.yml:      POSTGRES_PASSWORD: BarqLabOnly_7qN2vK8c
config/app.env:DATABASE_URL=postgresql://barq_app:BarqLabOnly_7qN2vK8c@postgres:5432/barq_tasks

- Related commit: e82e12a200050ce43917da2fd615788415a182bb

- Remaining uncertainty: None for database connection



## Entry 6  / 09/09/2026 / 3:00 
- Symptom: All requests to http://127.0.0.1:8080 fail with curl error 

- Hypothesis: nginx container not running or port mapping in the docker-compose.yml does not match NGINX configuration

- Command or test: docker compose -p barq-assessment ps -a
grep -A 10 "nginx:" docker-compose.yml

- Actual output:
nginx      nginx:1.28-alpine@sha256:a8b39bd9cf0f83869a2162827a0caf6137ddf759d50a171451b335cecc87d236    "/docker-entrypoint.…"   nginx      43 hours ago     Up 22 minutes             127.0.0.1:8080->81/tcp

nginx:
    image: nginx:1.28-alpine@sha256:a8b39bd9cf0f83869a2162827a0caf6137ddf759d50a171451b335cecc87d236
    container_name: nginx
    ports: ["127.0.0.1:${PUBLIC_PORT:-8080}:81"]
- Failed attempt and what changed your thinking:
- Root cause: Docker-compose.yml maps host port 8080 to container port 8081 but nginx.conf congfigures NGINX to listen on port 8080

- Fix: Change the nginx port mapping in docker-compose.yml from ["127.0.0.1:${PUBLIC_PORT:-8080}:81"] to ["127.0.0.1:${PUBLIC_PORT:-8080}:80"]

- Retest evidence:

curl -i http://127.0.0.1:8080/
HTTP/1.1 502 Bad Gateway
Server: nginx/1.28.3
Date: Wed, 09 Sep 2026 12:32:28 GMT
Content-Type: text/html
Content-Length: 157
Connection: keep-alive

<!-- <html>
<head><title>502 Bad Gateway</title></head>
<body>
<center><h1>502 Bad Gateway</h1></center>
<hr><center>nginx/1.28.3</center>
</body>
</html> -->
- Related commit: fde1f35a5c37a2e352cfa95955df017d35b50ca2
- Remaining uncertainty: Nginx port fix allowed the request to reach NGINX but still an issue remains as NGINX failed to get a valid response "502 bad gateaway"


## Entry 7 / 09/09/2026 / 3:42
- Symptom: curl http://127.0.0.1:8080 returns a 502 Bad Gateway error from NGINX.

- Hypothesis: Nginx failing to forward traffic because of port mismatch
- Command or test: cat nginx/nginx.conf docker-compose.yml
- Actual output:
worker_processes auto;
error_log /dev/stderr warn;
pid /var/run/nginx.pid;
events { worker_connections 1024; }
http {
    include /etc/nginx/mime.types;
    log_format assessment escape=json '{"timestamp":"$time_iso8601","service":"edge","request_id":"$request_id","method":"$request_method","path":"$uri","status":$status,"upstream":"$upstream_addr","upstream_status":"$upstream_status","request_time":"$request_time"}';
    access_log /dev/stdout assessment;
    upstream application_pool {
        server app-01:8081 max_fails=0;
        server app-02:8080 max_fails=0;
    }
    server {
        listen 80;

- Failed attempt and what changed your thinking: Once the docker port mapping was fixed in the previous step I got a 502 error. This proved NGINX was reachable but the backend wasn't so I checked the upstream block inside nginx.conf 
- Root cause: nginx.conf incorrectly configures the upstream for app-01 to port 8081 when it is supposed to be 8080
- Fix: Correct the upstream for app-01 from port 8081 to port 8080
- Retest evidence:
yomna@LAPTOP-KLHNR2J1:~/devops-internship-task$ curl http://127.0.0.1:8080
<!-- <html>
<head><title>502 Bad Gateway</title></head>
<body>
<center><h1>502 Bad Gateway</h1></center>
<hr><center>nginx/1.28.3</center>
</body>
</html> -->
- Related commit: 79079b6e741e09bad0dc8c49267f127d68cfe3b2
- Remaining uncertainty: Nginx still fails even after fixing upstream



## Entry 8 / 09/09/2026 / 4:01
- Symptom: NGINX returns a 502 Bad Gateway error because it cannot connect to the upstream Flask apps.

- Hypothesis: docker-compose.yml is passing APP_HOST:127.0.0.1 while app-01 and app-02 have default setting of 0.0.0.0

- Command or test:  
grep -rn "run(" app/server.py
 grep -rn "run(" app/server.py

- Actual output:
144:    create_app().run(host=os.getenv("APP_HOST", "0.0.0.0"),
  APP_HOST: "127.0.0.1"

- Failed attempt and what changed your thinking:

- Root cause: APP_HOST is set to 127.0.0.1 which overrides the defualt settings of the flask app to 0.0.0.0 preventing them from accepting connections

- Fix: Correct APP_HOST in docker-compose.yml from 127.0.0.1 to 0.0.0.0

- Retest evidence:
<!-- HTTP/1.1 200 OK
Server: nginx/1.28.3
Date: Wed, 09 Sep 2026 13:19:18 GMT
Content-Type: application/json
Content-Length: 100
Connection: keep-alive
X-Instance-ID: app-02
X-Request-ID: dd29686c7a747a7d6f857bf166b5f75e
Cache-Control: no-store
{"instance_id":"app-02","message":"Welcome to BARQ Systems","service":"barq-api","version":"2.0.0"} -->

- Related commit: d269576d0ccb97d6002ca929b24a19ca48aebecf

- Remaining uncertainty:  none


## Entry 9 / 10/09/2026 / 12:00
- Symptom: A record created with POST/records disappears after the postgres container is restarted

- Hypothesis: The named vollume is not actaully storing PostgreSQL's  data
- Command or test:
  curl -X POST http://127.0.0.1:8080/records -H "Content-Type: application/json" -d '{"title":"postgre-test"}'
curl http://127.0.0.1:8080/records
docker compose -p barq-assessment restart postgres
sleep 10
curl http://127.0.0.1:8080/records
- Actual output:
{"instance_id":"app-01","record":{"id":4,"title":"postgre-test"},"service":"barq-api","version":"2.0.0"}
{"instance_id":"app-01","records":[{"id":1,"title":"Review service readiness"},{"id":2,"title":"Document the operating procedure"},{"id":3,"title":"postgre-test"},{"id":4,"title":"postgre-test"}],"service":"barq-api","version":"2.0.0"}
[+] restart 0/1
 ⠼ Container postgres Restarting                                        0.4s
{"instance_id":"app-01","records":[{"id":1,"title":"Review service readiness"},{"id":2,"title":"Document the operating procedure"}],"service":"barq-api","version":"2.0.0"}

- Failed attempt and what changed your thinking: At first got error for postgre being not available because of the immediate curl right after restarting, but after adding sleep 10 to allow time for postgre to fully boot up the error was gone.

- Root cause: The path postgre service uses for live data was set to /var/lib/postgresql/backup which is not what postgre uses and the actual directory /var/lib/postgresql/data is set as tmpfs which stores data in RAM causing the data to be wiped up on every container restart.

- Fix: Remove the tmpfs for /var/lib/postgresql/data and change /var/lib/postgresql/backup to /var/lib/postgresql/data

- Retest evidence:
curl http://127.0.0.1:8080/records
{"instance_id":"app-01","record":{"id":3,"title":"postgre-test"},"service":"barq-api","version":"2.0.0"}
{"instance_id":"app-01","records":[{"id":1,"title":"Review service readiness"},{"id":2,"title":"Document the operating procedure"},{"id":3,"title":"postgre-test"}],"service":"barq-api","version":"2.0.0"}
[+] restart 0/1
 ⠴ Container postgres Restarting                                                                                                                        0.5s
{"instance_id":"app-01","records":[{"id":1,"title":"Review service readiness"},{"id":2,"title":"Document the operating procedure"},{"id":3,"title":"postgre-test"}],"service":"barq-api","version":"2.0.0"}

- Related commit: b1927fb678d51014299942c61280e0b1c7ff0897
- Remaining uncertainty: 




## Entry 10 / 12/09/2026 / 11:30

- Symptom: Redis counter resets to 0 when Redis counter restarts 

- Hypothesis: Redis presistence disabled in configuration 
- Command or test:  grep -A 7 "redis:" docker-compose.yml
- Actual output:
is:
    image: redis:7.4-alpine@sha256:ff02b58f971e7d7d156a1267e283fcbbeee91773b6aa36c49dac28ecfe28eadf
    container_name: redis
    command: ["redis-server", "--save", "", "--appendonly", "no"]
    ports: ["127.0.0.1:16379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 3s
      timeout: 2s
- Failed attempt and what changed your thinking:
- Root cause: The command override disables Redis snapshotting and append-only log
- Fix: Change appendonly from no to yes and add  a named volume so data survives recreation of container
- Retest evidence:
  redis:
    image: redis:7.4-alpine@sha256:ff02b58f971e7d7d156a1267e283fcbbeee91773b6aa36c49dac28ecfe28eadf
    container_name: redis
    command: ["redis-server",  "--appendonly", "yes"]
    ports: ["127.0.0.1:16379:6379"]
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
- Related commit:708fc42e176bcd389df40cb15b04e09d039ecf36
- Remaining uncertainty:











Do not fabricate a failed attempt just to fill the template. Record actual attempts.
