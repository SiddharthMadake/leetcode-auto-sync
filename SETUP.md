# Setup, Security, and Maintenance

## What this project does

Every run queries LeetCode's internal GraphQL endpoint for your recent accepted submissions, fetches the source code and metadata for each submission, checks the repository path for an existing solution in that language, writes only missing solutions, regenerates the root README, then creates one focused git commit per newly detected solution and pushes each commit to `main`.

The repository intentionally stores the same problem once at the problem level, while languages live below it. For example:

```text
easy/0001-two-sum/
├── README.md
├── python/solution.py
└── cpp/solution.cpp
```

This scales better than a language-first tree because a problem has one stable identity and can accumulate solutions in multiple languages without duplicate problem folders.

## Important LeetCode API note

LeetCode does not publish a stable, documented developer API for this workflow. The implementation therefore uses LeetCode's web GraphQL endpoint at `https://leetcode.com/graphql/` and queries that current LeetCode web clients expose. Community-maintained tools and current third-party integrations document the same `recentAcSubmissionList` and `submissionDetails` operations. Treat this integration as unofficial and subject to breaking changes.

The client authenticates using your own LeetCode browser session cookies (`LEETCODE_SESSION` and `csrftoken`). It never stores a password. Because these values can authorize access to your account, store them only as GitHub Actions secrets or in a local `.env` that is excluded from git.

## Configuration

Required:

```env
LEETCODE_USERNAME=your_LeetCode_username
LEETCODE_SESSION=your_LEETCODE_SESSION_cookie
LEETCODE_CSRF_TOKEN=your_csrftoken_cookie
```

Optional locally:

```env
GITHUB_REPOSITORY=your-github-username/leetcode-solutions
DEFAULT_BRANCH=main
SYNC_LOOKBACK_LIMIT=100
HTTP_TIMEOUT_SECONDS=30
HTTP_MAX_RETRIES=4
REPO_ROOT=.
```

In GitHub Actions, `GITHUB_TOKEN` is supplied by GitHub automatically; do not create a PAT just to push this repository unless your repository policy requires it.

## Getting the LeetCode cookies

Sign in to LeetCode in your normal browser. Use the browser developer tools' Application/Storage area to inspect cookies for `leetcode.com`. Copy the values of `LEETCODE_SESSION` and `csrftoken` into your local `.env`, or into GitHub repository secrets. Do not paste them into source files, workflow YAML, issues, logs, or commits.

Cookie names and authentication behavior can change. When LeetCode invalidates the session, refresh the cookie values.

## GitHub repository setup

Create a repository named:

```text
leetcode-solutions
```

Initialize it with this project on the `main` branch and push the `.github/workflows/leetcode-sync.yml` file to that branch. GitHub scheduled workflows run from the default branch.

Add these repository secrets under **Settings → Secrets and variables → Actions**:

```text
LEETCODE_USERNAME
LEETCODE_SESSION
LEETCODE_CSRF_TOKEN
```

The workflow requests only `contents: write`, which lets its `GITHUB_TOKEN` push repository content. GitHub recommends using the least privileges necessary for Actions credentials.

## Local development

```bash
git clone <repo>
cd leetcode-solutions
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# macOS/Linux
source .venv/bin/activate

python -m pip install -r requirements-dev.txt
copy .env.example .env        # Windows
# or: cp .env.example .env    # macOS/Linux
python -m pytest
python sync.py
```

For local pushes, the repository's normal git credential manager should authenticate `git push`. The sync code does not require a GitHub API token; GitHub Actions uses its built-in `GITHUB_TOKEN` through the checkout action's persisted credentials.

## How the daily automation works

```text
GitHub Actions schedule / manual dispatch
                ↓
         checkout main branch
                ↓
          install Python deps
                ↓
               tests
                ↓
   recentAcSubmissionList(username)
                ↓
     for each recent accepted ID
                ↓
       submissionDetails(id)
                ↓
      accepted + source + language?
          ↙             ↘
        no                yes
        ↓                  ↓
      skip        build canonical path
                           ↓
              path already exists?
                    ↙           ↘
                  yes            no
                   ↓              ↓
                 skip       write source + README
                                  ↓
                             rebuild root README
                                  ↓
                         stage exact changed paths
                                  ↓
                               commit
                                  ↓
                                push
```

A single run can pick up several problems. They are committed atomically so one day's batch stays easy to audit.

## Duplicate handling

The canonical key for repository storage is effectively `(problem ID, language)`. The directory is problem-first and the file is language-specific. Solving the same problem again in the same language therefore produces no second file and no second commit. Solving it in a new supported language creates a new language folder under the same problem.

The repository itself is the persistent duplicate index; no secret database or local state file is needed.

## Supported languages

The built-in mapping supports:

| LeetCode value | Repository folder | Extension |
|---|---|---|
| `python` / `python3` | `python` | `.py` |
| `javascript` | `javascript` | `.js` |
| `typescript` | `typescript` | `.ts` |
| `cpp` / `c++` | `cpp` | `.cpp` |
| `java` | `java` | `.java` |
| `golang` / `go` | `go` | `.go` |
| `rust` | `rust` | `.rs` |

Unsupported languages are logged and skipped rather than generating a misleading extension.

## Error handling

The client retries transient HTTP failures and rate limiting with exponential backoff. GraphQL errors, authentication failures, malformed responses, unavailable submission details, missing source code, and schema changes are surfaced in the job logs.

A single broken submission does not discard unrelated submissions from the same run: the runner logs the failure and continues processing other recent accepted submissions.

Git staging is deliberately strict. Before committing, the script verifies that the index contains exactly the generated files plus the root README update. This prevents unrelated working-tree changes from being swept into the automation's commit.

## GitHub Actions security

Secrets are referenced only through `${{ secrets.* }}` and are not written to disk by the workflow. The workflow uses GitHub's built-in `GITHUB_TOKEN` for pushes and requests `contents: write`. Because a push made by `GITHUB_TOKEN` does not recursively trigger another workflow run, this design does not need a push-trigger loop breaker.

If the repository is public, remember that GitHub can disable scheduled workflows after long periods without repository activity. A manual `workflow_dispatch` run or a normal commit can re-enable the workflow when appropriate.

## Testing strategy

Tests cover:

- accepted-submission filtering;
- duplicate detection through existing language-specific files;
- supported-language normalization;
- path generation;
- solution and per-problem README generation;
- root README statistics/table generation;
- commit message generation and exact staged-path enforcement;
- LeetCode GraphQL parsing and error handling.

The tests never contact LeetCode or GitHub.

## Fallback if the LeetCode GraphQL API changes

1. Check the failing GitHub Actions log for the exact schema/HTTP error.
2. In an interactive browser session, inspect a LeetCode GraphQL request made by the submissions page.
3. Compare the current `recentAcSubmissionList` and `submissionDetails` response shape with `leetcode_sync/leetcode_client.py`.
4. Update the two queries/parser mappings and extend the tests with a saved response fixture.
5. Rotate your LeetCode session secrets if the old session was invalidated.

A third-party proxy/scraper service can be used as a temporary fallback, but it adds another credential/vendor dependency and is less desirable than calling LeetCode directly.

## Terms / policy consideration

**Important: the current LeetCode Terms of Service create a material deployment risk for this design.** The current terms say that running processes that operate while you are not logged into the platform or that interfere with the service is not allowed, and they explicitly prohibit crawling, scraping, or spidering any part of the Service. That means an unattended GitHub Actions job calling LeetCode's internal GraphQL endpoint is **not something this project can represent as LeetCode-approved or ToS-compliant**. Review the current terms and obtain permission from LeetCode before using this unattended automation.

The technical implementation is intentionally limited to your own account, one scheduled run per day, a bounded recent-submission window, and conservative retries. There is no official per-endpoint rate-limit contract for these internal GraphQL operations that this project can rely on; the client treats HTTP 429 and common transient 5xx responses as retryable and otherwise fails loudly.

## Known limitations

- The GraphQL endpoint and field names are controlled by LeetCode's web application and can change without notice.
- The recent accepted-submission query is a bounded window. Increase `SYNC_LOOKBACK_LIMIT` for unusually high-volume accounts, but do not turn the job into an aggressive historical crawler.
- If more accepted submissions exist between runs than the returned window, a submission older than the window can be missed. A future enhancement could use a persistent cursor or a broader historical scan.
- LeetCode can invalidate browser session cookies. Replace the repository secrets when that happens.
- Runtime/memory display values depend on LeetCode returning those fields for the submission.
- The root README table grows linearly with the number of archived solutions. For very large archives, consider generating a separate index or splitting the index by difficulty/year.
- A push can conflict if someone edits the same branch at exactly the same time. The current concurrency group prevents overlapping copies of this workflow; manual human pushes should be followed by a rerun if a race still occurs.

## Example generated solution

Example path:

```text
easy/0001-two-sum/python/solution.py
easy/0001-two-sum/README.md
```

Example `solution.py`:

```python
class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, value in enumerate(nums):
            needed = target - value
            if needed in seen:
                return [seen[needed], i]
            seen[value] = i
        return []
```

## Example commit history

For one newly detected solution:

```text
Solve Two Sum [Easy]
```

For several newly detected solves in one daily run:

```text
Solve 3 LeetCode problems
```

Each newly detected accepted solution receives its own commit, so a day with three new solves produces three focused commits.
