{
  "model": "GitHub Copilot (Auto mode)",
  "findings": [
    {
      "file": "lab5-canary/app/attachment_export.py",
      "start_line": 11,
      "end_line": 11,
      "class": "injection",
      "cwe": "CWE-78",
      "rule": "shell-command-injection",
      "message": "The ticket identifier is interpolated into a shell command executed with shell=True; pass an argument vector to subprocess.run instead."
    },
    {
      "file": "lab5-canary/app/attachment_read.py",
      "start_line": 9,
      "end_line": 10,
      "class": "path-traversal",
      "cwe": "CWE-22",
      "rule": "attachment-path-traversal",
      "message": "The request-derived filename is joined without a containment check, so traversal components can read files outside the attachment directory."
    },
    {
      "file": "lab5-canary/app/ticket_search.py",
      "start_line": 8,
      "end_line": 10,
      "class": "injection",
      "cwe": "CWE-89",
      "rule": "sql-like-injection",
      "message": "The search string is interpolated into SQL; use a bound parameter for the LIKE value."
    },
    {
      "file": "lab5-canary/config/github.py",
      "start_line": 3,
      "end_line": 3,
      "class": "secret",
      "cwe": "CWE-798",
      "rule": "hardcoded-github-token",
      "message": "A GitHub API token is hard-coded in application configuration; load credentials from a secret manager or environment."
    },
    {
      "file": "lab5-canary/config/mailer.py",
      "start_line": 4,
      "end_line": 4,
      "class": "secret",
      "cwe": "CWE-798",
      "rule": "hardcoded-smtp-password",
      "message": "An SMTP password is hard-coded in application configuration; load credentials from a secret manager or environment."
    },
    {
      "file": "lab5-canary/config/search.py",
      "start_line": 3,
      "end_line": 3,
      "class": "secret",
      "cwe": "CWE-798",
      "rule": "hardcoded-search-api-key",
      "message": "A search-service API key is hard-coded in application configuration; load credentials from a secret manager or environment."
    },
    {
      "file": "lab5-canary/requirements.txt",
      "start_line": 1,
      "end_line": 1,
      "class": "vulnerable-dependency",
      "cwe": "CWE-1395",
      "rule": "vulnerable-pyyaml-pin",
      "message": "PyYAML 5.3.1 is an outdated vulnerable dependency; upgrade to a maintained patched release."
    },
    {
      "file": "lab5-canary/requirements.txt",
      "start_line": 2,
      "end_line": 2,
      "class": "vulnerable-dependency",
      "cwe": "CWE-1395",
      "rule": "vulnerable-urllib3-pin",
      "message": "urllib3 1.24.1 is an outdated vulnerable dependency; upgrade to a maintained patched release."
    }
  ]
}
