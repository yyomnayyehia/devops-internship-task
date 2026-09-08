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


## Entry 2 / date / time
- Symptom: 
- Hypothesis:
- Command or test:
- Actual output:
- Failed attempt and what changed your thinking:
- Root cause:
- Fix:
- Retest evidence:
- Related commit:
- Remaining uncertainty:












Do not fabricate a failed attempt just to fill the template. Record actual attempts.
