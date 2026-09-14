# Technical decisions

Record at least 5 decisions. Include assumptions and limits.

## Decision 1
- Choice: Health checks of images are in docker-compose.yml not in the Dockerfile
- Why: Keeps the image simple and have the healthcheck configuration in the compose setup where it can be changed without having to rebuild the image
- Alternative: put healthcheck in the dockerfile so it comes with the image whenever its used
- Trade-off: If image is used somewhere else without the compose file the healthchecks wont be there and would have to redined again
- Evidence / commit: The healthcheck is defined in the x-app anchor in docker-compose.yml. docker compose ps -a showed all services as (healthy).
- Production improvement: Would use Kubernetes to use their healthcheck system

## Decision 2
- Choice: Redis uses --appendonly yes with volume redis-data:/data
- Why: The original configuration had --save"" --appendonly no which meant the counter was lost whenever Redis restarted so i enabled AOF so the writes remain 
- Alternative: Use Redis's defualt snapshooting instead
- Trade-off: AOF uses more dsk than snapshotting but this is only lab  so no issue when it comes to cost
- Evidence / commit: I incremented /counter and restarted Redis i then checked the value again and it continued from the previous value instead of going back to 0.
- Production improvement: Configure and moniotr AOF rewriting so file doesnt grow indefintely 




## Decision 3
- Choice: Enabled NGINX upstream retries max fails=2 fail_tiemout-3s and proxy_next_upstream for errors, timeouts and responses
- Why: The original configuration had proxy_next_upstream off so when one backend was down NGINX would return failure instead of trying the other backend
- Alternative: Use max_fails=1 and fail_timeout=30s, which was one of the suggested configurations.
- Trade-off: Instead of one temporary failure i used max fails=2 so 1 failure doesnt mark backend as failed and 5 seconds instead of 30s because 30s was long wait time to try a recovered backend again
- Evidence / commit: After changing the retry configuration I ran the same failure_test.py scenario again and got 0 errors out of 50 requests.
- Production improvement: Tune the configuration based on actual production traffic

## Decision 4
- Choice:set a 256M memory limit for all five services: app-01, app-02, nginx, postgres, and redis.
- Why: Resource limits werent used originally and a service could potentially use too much memory and affect others
- Alternative: Give each service a different limit based on what it actually needs 
- Trade-off: Unifying the resource limits for all services is not practical they should be set based on what each service needs
- Evidence / commit:docker stats --no-stream showed that all five containers have an actual memory limit and their normal usage was well below 50MiB.
- Production improvement: I would load-test the services and set the limits based on their actual memory usage instead of using the same number for everything.


## Decision 5
- Choice:I did not rewrite the Git history after finding that config/app.env had been committed from the first commit. I only stopped tracking it with git rm --cached.
- Why:The credentials in the file are lab credentials and because of that rewriting the entire history was not worth changing the assessment's commit timeline.
- Alternative:Use git filter-repo to remove file from all previous commits
- Trade-off: Rewriting the history would remove the file completely, but it would also change the existing commit history that shows how I investigated and fixed the problems.
- Evidence / commit: git ls-files | grep "app.env" no longer returns the file. git log --all --full-history -- config/app.env still shows it in the older commits
- Production improvement:If these were real credentials, I would rotate them immediately and remove the secret from the Git history as well.



Cover your base image, health checks, networks, timeouts/retries, restart/resource settings,
storage and any other meaningful choices.
