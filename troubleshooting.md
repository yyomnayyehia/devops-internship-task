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

- Retest evidence: pending

- Related commit: pending

- Remaining uncertainty: Havent confirmed yet if redis's port number is hardcoded wrongly somewhere else or not.






Do not fabricate a failed attempt just to fill the template. Record actual attempts.
