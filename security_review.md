# Security and production-readiness review

Record at least 8 concrete risks or improvements relevant to your final solution.
This is a review requirement, not the number of hidden faults.

For each finding:
### 1. Exposed database ports
- Risk and evidence: docker compose.yml had postgres mapped to internap port of 15432 and rredis to 16379 and they were both bounded to 127.0.0.1 violating requirment only ngnix be published to host.
ports: ["127.0.0.1:15432:5432"]   # postgres
ports: ["127.0.0.1:16379:6379"]   # redis
- Impact: Local proccesses could connect to postgres or redis and not go through the app and nginx
- Implemented fix / commit: Removed the port lines from postgres and redis inside the docker-compose.yml
- Production follow-up: Add  security rules to restrict database access
- How to verify: docker compose -p barq-assessment ps -a should show no port mapping for redis and postgres



### 2. NGINX had access to the backend network
- Risk and evidence: Nginx was attached to both frontend and backend networks in docker-compose.yml, giving it a path to postgres/redis if compromised.
$ docker exec app-01 whoami
root
- Impact: If nginx was compromised it would reach database directly instead of just apps
- Implemented fix / commit: Removed backend from nginx network list and kept frontend
- Production follow-up: Enforce network isolation using Kubernetes Network policies by adding explicit rules
- How to verify:
  docker exec -it nginx sh -c "wget -qO- --timeout=2 postgres:5432 || echo UNREACHABLE"
  docker exec -it nginx sh -c "wget -qO- --timeout=2 redis:6379 || echo UNREACHABLE"


### 3. App containers were running as root
- Risk and evidence: docker exec app-01 whoami returned root
- Impact: If app had vulnerability the attacker will gain root inside container
- Implemented fix / commit:User set to app not root then re built docker containers so app runs as user 
- Production follow-up: Make sure badly configured docker images wont run as root by using kubernetes to enforce runasnonroot set to true
- How to verify: n docker exec app-01 whoami and docker exec app-02 whoami 



### 4. Missing resource limits
- Risk and evidence: No resources were set for any service or app in docker-compose.yml
- Impact: Proccesses with no set resource could crash other services or starve them
- Implemented fix / commit: Added 256M to apps and for nginx, postgres and redis
- Production follow-up: Lab starting point not production grade
- How to verify: docker stats --no-stream



### 5. Missing restart policies
- Risk and evidence: All services needed a restart policy so they recover automatically from crashes rather than requiring manual intervention.
- Impact: A crashed container will go unnoticed until someone fixes it manually
- Implemented fix / commit: Added restart:unless stopped
- Production follow-up: Implement liveness probes to automatically detect and restart unhealthy containers.
- How to verify:grep -n "restart:" docker-compose.yml


### 6. Secrets exposed via Git tracking and Docker image layers
- Risk and evidence: app.env tracked in git and not in .gitignore when it contains sensitive credentials and the Docker file bakes the app.env into every image built making the credentials easy to extract from image layers

- Impact: A public repo would cause anyone to access them and anyone with access to build image can extract the credentials 

- Implemented fix / commit: Ran git rm --cached config/app.env to stop tracking it going forward. The docker file was not fixed as they are lab only data

- Production follow-up: Would have to change the credentials and scrub it from git history and for the docker file delete copy of app.env and use env vars 
- How to verify:git ls-files | grep "app.env" 



### 7. No TLS/SSL on NGINX

- Risk and evidence: Nginx configured to only listen on port 80 with no ssl or tls certificate configured
- Impact: All traffic between the client and application is not encrypted and vulnerable to attacks
- Implemented fix / commit: Not implemented
- Production follow-up:Generate SSL certificates
- How to verify: curl -I https://127.0.0.1 and verify a successful TLS handshake (when actually impelemented)


### 8. PostgreSQL data not actually persistent
- Risk and evidence: Postgres-data mounted to /var/lib/postgresql/backup which is not a path used by postgres for live data and the correct path was mounted as tmpfs 
- Impact: Total data loss on postgres container if restarted or recreated
- Implemented fix / commit: Removed tmpfs mount and corrected the path from /backup to /data
- Production follow-up: Automate volume snapshots and test restores
- How to verify:
 curl -X POST http://127.0.0.1:8080/records -H "Content-Type: application/json" -d '{"title":"postgre-test"}'
curl http://127.0.0.1:8080/records
docker compose -p barq-assessment restart postgres
sleep 10
curl http://127.0.0.1:8080/records



### 9. Redis persistence disabled
- Risk and evidence: redis ran with `--save "" --appendonly no` which disabled both of redis's
  persistence mechanisms and there was no volume mounted for its data directory.
- Impact:All counter/cache data lost on any redis restart or recreation.
- Implemented fix / commit: changed the command to `--appendonly yes` and added a named
  volume  so data survives container recreation
- Production follow-up: Back up the redis volume periodically
- How to verify: curl http://127.0.0.1:8080/counter
docker compose -p barq-assessment restart redis
sleep 10
curl http://127.0.0.1:8080/counter


### 10. Image selection (SHA-pinned digests)

- Risk and evidence: All images are pinned by SHA256 digest
- Impact: A different tag like postgre:16-alpine can silently repoint to a different image later which a rebuild could pull malicious code without any change to project files
- Implemented fix / commit: This was already done 
- Production follow-up: Set up automated image update scanning through dependabot or renovate
- How to verify: grep "image:" docker-compose.yml


### 11. No centralized logging or monitoring
- Risk and evidence: Services are just logging toits own container stdout but no centralized logging or metrics set up
- Impact: If something goes wrong have to manually pull container logs and search the incident and if something failed silently would not be able to tell
- Implemented fix / commit: Didnt implement
- Production follow-up: Send logs somewhere centralized and add basic dashboards annd set up alerts for errors or failed health checks
- How to verify:

Cover secrets, ports, container user, image selection, networks, persistence/backup,
logging/monitoring and availability. Separate completed work from planned improvements.
