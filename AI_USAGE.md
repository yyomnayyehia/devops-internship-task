# AI usage disclosure

Write None if no AI was used. Otherwise record each use:

- Tool/model: Claude(Anthropic , chat)
- Purpose: Used as a debugging guide and mentor throughout the assessment — explaining concepts I did not know going in and suggesting what to check next when debugging, and pushing back when something had not actually been verified. 
- Files or decisions affected: docker-compose.yml, nginx/nginx.conf, Dockerfile
- What you changed or rejected:  All fixes were applied manually after understanding the root cause. Every bug in troubleshooting.md was found by running commands myself and reading the actual output.
- How you independently verified it:Ran docker compose logs, curl, nc, and docker exec after every change to confirm each fix resolved exactly one symptom.
- Related commit: fde1f35a5c37a2e352cfa95955df017d35b50ca2, 8b2cfcbd56b4a875b178fb7f663292dfe132aeee

- Tool/model: Claude (Anthropic, chat)
- Purpose: Used AI as a guide and for help with structuring and formatting the Markdown files
- Files or decisions affected: security_review.md, decisions.md, log_analysis.md, troubleshooting.md
- What you changed or rejected: Rewrote all documentation in my own words and rejected generated ready to use documentataion
- How you independently verified it: Compared each item against TASK.md to ensure coverage
- Related commit:eacba5824443a642bf64335f0d5f1279f91a2715, f9a4afc74cd3d7ce08f50c9493578e2c7762bc5f

- Tool/model:  Claude (Anthropic, chat)
- Purpose: Used AI as a guide and for help creating initial boilerplate for validate.py, failure_test.py, backup.sh, and restore.sh
- Files or decisions affected: validate.py, failure_test.py, backup.sh, restore.sh
- What you changed or rejected: Reviewed and adapted the generated boilerplate to match the Compose project name, service behavior, backup requirements, failure-recovery flow, and task constraints.
- How you independently verified it: Compared each script with TASK.md and the project configuration. 
- Related commit: dc1866b2f3463328eb35e48143a0262277240339, 6d2ad82a7eda252d1ec2e5022d81248ac2b58b6b




You may use AI and external resources. You must understand and demonstrate the work.
