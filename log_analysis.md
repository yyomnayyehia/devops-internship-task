# Log analysis

Use all three supplied logs. Answer every question with commands/scripts and actual output.

1. What UTC interval is covered? How many valid, malformed and duplicate lines are in each file?
2. How many distinct client requests occurred? How did you deduplicate and avoid counting retries twice?
3. What are the final client status counts and error rate? State your denominator.
4. Which paths, time windows and backends account for the failures?
5. What are the median and p95 client latencies? State the percentile method and units.
6. Which requests retried upstream? How many succeeded after retrying?
7. Build an incident timeline using evidence from access, error AND application logs.
8. Show one correlated failed request and one successful request. Include IDs and timestamps.
9. Which errors appear to be proxy/connectivity issues versus dependency/application issues? What proves it?
10. What do the logs not prove? What would you check next in a running environment?

## Commands / scripts
### QUESTION 1
1.To check the first ever access time stamp and last time stamp :
head -1 logs/access.log | grep -o '"timestamp":"[^"]*"'
tail -1 logs/access.log | grep -o '"timestamp":"[^"]*"' 
2. line counts wc -l logs/*.log
3. Malformed lines for json logs
grep -cv '^{' logs/access.log
grep -cv '^{' logs/application.log
grep '"request_id"' logs/access.log | grep -v '"request_id":"[^"]*"'
4. Duplicated lines 
sort logs/access.log | uniq -cd
sort logs/application.log | uniq -cd
5. line counts for error.log cat logs/error.log


### QUESTION 2:
1. Unique access logs with no duplication
grep -o '"request_id":"[^"]*"' logs/access.log | sort -u | wc -l 
### QUESTION 3
1. Command to get the status codes and how many times each status occured 
grep -o '"status":[0-9]*' logs/access.log | sort | uniq -c | sort -rn


### QUESTION 4
grep -E '"status":(404|502|503|504)' logs/access.log | grep -o '"path":"[^"]*"' | sort | uniq -c | sort -rn
grep -E '"status":(404|502|503|504)' logs/access.log | grep -oE '"timestamp":"[0-9-]+T[0-9]+:[0-9]+' | sort | uniq -c | sort -rn
grep -E '"status":(404|502|503|504)' logs/access.log | grep -o '"upstream":"[^"]*"' | sort | uniq -c | sort -rn
grep -E '"timestamp":"2026-08-20T11:(0[5-9]|1[0-9]|2[01]):' logs/access.log | grep -o '"status":[0-9]*' | sort | uniq -c

### QUESTION 5
grep -o '"request_id":"[^"]*"\|"request_time":[0-9.]*' logs/access.log | paste -d' ' - - | sort -u -k1,1 | awk '{print $2}' | sed 's/"request_time"://' | sort -n > /tmp/latencies_dedup.txt
awk '{a[NR]=$1} END {
  n=NR
  median = (n%2==1) ? a[(n+1)/2] : (a[n/2]+a[n/2+1])/2
  p95_idx = int(0.95*n)
  printf "n=%d median=%.3f p95=%.3f\n", n, median, a[p95_idx]
}' /tmp/latencies_dedup.txt


### QUESTION 6
grep "proxy_next_upstream" nginx/nginx.conf
awk -F'"' '{for(i=1;i<=NF;i++){if($i=="request_id")id=$(i+2); if($i=="upstream")up=$(i+2)} print id, up}' logs/access.log | sort | uniq | awk '{print $1}' | uniq -c | sort -rn | head -5

### QUESTION 7
grep "11:0[5-9]:\|11:1[0-9]:\|11:2[01]:" logs/application.log | grep -v '"status": 200'
grep "dependency_error" logs/application.log | grep -o '"timestamp": "[^"]*"' | sort | head -1
grep "dependency_error" logs/application.log | grep -o '"timestamp": "[^"]*"' | sort | tail -1
grep -c "dependency_error" logs/application.log
grep "dependency_error" logs/application.log | grep -o '"dependency": "[^"]*"' | sort | uniq -c
grep '"status":502' logs/access.log | grep -o '"timestamp":"[^"]*"' | sort | head -3
grep '"status":502' logs/access.log | grep -o '"timestamp":"[^"]*"' | sort | tail -3

### QUESTION 8
grep "lab-000606" logs/access.log logs/application.log


### QUESTION 9
grep "111: Connection refused" logs/error.log | wc -l
grep "dependency_error" logs/application.log | grep -o '"dependency": "[^"]*"' | sort | uniq -c

## Results

### QUESTION 1
1. The incident logs cover roughly 30 minutes, from `2026-08-20T11:00:00.015Z`
to `2026-08-20T11:29:57.578Z`
2. access.log: 726 total lines, 1 malformed line (ends abruptly right after
`"request_id":` with no value or closing brace), 5 duplicated lines (10 total lines involved)
3. application.log: 730 total lines, 0 malformed, 2 lines duplicated (4 total lines involved)
4. Manual inspection of error.log since it's plain text, not JSON: 68 total lines, no
malformed lines observed, no duplicates (every nginx line has a unique connection ID)
### QUESTION 2
720 distinct client requests, based on unique request_id in access.log (726 total lines,
minus 1 malformed line with no usable request_id, minus 5 request_ids that were logged as
duplicate lines and collapsed to 1 each).
 
### QUESTION 3
    620 "status":200
     47 "status":503
     40 "status":502
     10 "status":404
      8 "status":504
 
Removed 5 duplicate 200 lines to match the 720 distinct-request denominator (620-5=615).
Denominator: 720 (distinct requests, from Question 2).
Errors (non-2xx): 47+40+10+8 = 105.
Error rate = 105/720 = 14.58%.
 
### QUESTION 4
- Paths: /records (26) and /counter (26) worst, /ready (23), /health (10), / (10)
- /missing's 10 hits are expected 404s (nonexistent path), not incident failures
- Time window: failures concentrated 11:05-11:21, ~8-9/min throughout
- 40 502s + 47 503s = 100% of all 502/503 errors occur within that 11:05-11:21 window
- 504s (8 total) are separate, occurring only in the later 11:25-11:26 window
- Backends: 172.23.0.12 = 73 failures (~70%), 172.23.0.11 = 32 failures (~30%)
### QUESTION 5
n = 720
Median latency = 0.054 seconds (54ms)
p95 latency = 2.001 seconds (2001ms)
 
Method: sorted all latency values from smallest to largest, then picked the middle value
for median, and the value 95% of the way through the sorted list for p95.
Units: seconds (from access.log's request_time field).
 
### QUESTION 6
Zero requests retried upstream.
nginx.conf has proxy_next_upstream off, which disables automatic retries to a different
backend.
Confirmed in the logs too: every request_id only ever maps to one upstream IP, never two.
So the "succeeded after retrying" part doesn't apply — 0 retried, 0 succeeded after retry.
 
### QUESTION 7
**11:05:02 – 11:09:57**
Connections failed with error 111 according to error.log, and access.log had 40 502 Bad
Gateway responses — all because nginx could not establish a connection to 172.23.0.12.
 
**11:12:09 – 11:21:45**
application.log shows 47 dependency_error events (31 Redis TimeoutError, 16 Postgres
errors), each followed immediately by a 503 response. access.log shows 47 503 errors in
the same window, affecting /ready and /counter on both apps.
 
**11:25:14 – 11:26:47**
access.log has 8 504 errors, only on /records, roughly every 30s — however the same
request_ids were logged as 200 in application.log. The client received a timeout while
the backend actually received/completed the request successfully.
 
### QUESTION 8
request_id 606, path /records. access.log shows it as a 504 at 11:25:14.501, took 2.001s,
nginx gave up waiting. application.log shows the same request_id as a 200 at 11:25:15.200,
duration_ms 2700 — the app actually finished it fine, just after nginx already timed out
and told the client it failed.
 
For a normal request with no mismatch: request_id 600, path /, status 200 in both logs,
request_time 0.038s.
 
### QUESTION 9
Proxy/connectivity issues: the 40 502s in the 11:05-11:09 window. Proven by error.log
showing repeated "111: Connection refused" while nginx tried to reach 172.23.0.12 — nginx
never even reached the application layer, so there's no corresponding entry at all in
application.log for these requests (the app was never contacted, so it couldn't log
anything).
 
Dependency/application issues: the 47 503s in the 11:12-11:21 window. Proven by
application.log explicitly logging structured dependency_error events (31 Redis
TimeoutError, 16 Postgres errors) immediately before each 503 — the app WAS reached and
running, but one of its own dependencies failed to respond in time.
 
The 8 504s on /records (11:25-11:26) are a third, separate category — not really a
connectivity or dependency issue at all, but a timeout budget mismatch: application.log
shows these same requests completing successfully (200), just after nginx's
proxy_read_timeout had already run out.
 
40 + 47 + 8 = 95 errors total, matches the error count from Q3/Q4 exactly. Every error is
accounted for by one of these three phases.
 
### QUESTION 10
These logs don't prove why 172.23.0.12 was unreachable for those 5 minutes — crash,
restart, network issue, no way to tell from just this. Same for the Redis/Postgres
timeouts — no resource stats (CPU, memory, connection pool usage) in any of the three
logs, so I can't actually confirm what caused them to be slow. Also can't confirm if this
historical incident is even related to the bugs I found in my own environment —
APPLICATION.md says this is a separate training incident, so no real link between the two.
 
In a running environment I'd check: docker stats during a similar failure, Postgres/Redis's
own logs for connection pool exhaustion or slow queries, docker events or container logs
around 11:05 to see if 172.23.0.12 actually restarted, and whether bumping
proxy_read_timeout would just hide the /records slowness instead of fixing it.
 
## Timeline and correlated examples
- 11:05:02–11:09:57: connectivity failure on 172.23.0.12 (40× 502), nginx couldn't connect
  to that backend at all (error.log: connection refused)
- 11:12:09–11:21:45: Redis/Postgres dependency timeouts (47× 503), app reached fine but
  its dependencies weren't responding in time
- 11:25:14–11:26:47: /records client-side timeout vs backend-side success (8× 504) — nginx
  gave up before the app actually finished the request
- One correlated pair (request_id 606): access.log logged it as a 504, application.log
  logged the same request_id as a 200 ~700ms later
- 40+47+8 = 95 errors total, fully accounted for across these three phases
## Conclusions and limits
 -Three separate root causes: connectivity (172.23.0.12 unreachable), dependency
  timeouts (Redis/Postgres), and a timeout budget mismatch on /records
- Every error status (502/503/504) is accounted for by one of these three phases
- These are historical training logs, not my own environment — no direct link to my
  Docker setup, didn't try to fix anything based on them
- Logs don't prove why 172.23.0.12 went down or why Redis/Postgres were slow — no
  CPU/memory/pool metrics in any log
- Next steps in a live environment: docker stats during a similar failure, Postgres/Redis
  logs for pool exhaustion, docker events around 11:05 to check for a restart
 