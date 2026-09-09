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
- Related commit:
- Remaining uncertainty: Not sure if NGINX is fully working or if there is remaining misconfigurations 







Do not fabricate a failed attempt just to fill the template. Record actual attempts.
