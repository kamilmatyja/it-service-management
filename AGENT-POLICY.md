# Agent Policy

- Bash(rm *): the AI agent is not allowed to delete files automatically to prevent accidental data loss.
- Bash(docker *): the AI agent should not interact with the docker daemon directly, as containers are managed by testing scripts.
- WebFetch: the agent must not fetch external code during the generation process to maintain strictly reproducible builds.