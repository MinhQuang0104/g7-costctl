# Reflections — costctl W6 Side Challenge

## 1. Multi-account deployment

**Question:** To run `costctl` against 100 AWS accounts (not just yours), what changes?

**Answer:**

**AWS Organizations + cross-account roles:**
- Create a central "audit" account with an IAM role that can assume roles in each member account
- Modify `costctl.py` to accept `--profile` or `--role-arn` argument
- Loop through each account and call each command N times
- Aggregate results into a CSV report

**Alternative: AWS SSO (IAM Identity Center)**
- Configure SSO with multiple account profiles in `~/.aws/config`
- Add `--profile all` mode to iterate through all profiles
- Simpler operationally than manual cross-account roles

**Choice:** Cross-account roles for explicit audit trail; SSO for teams already using it.

---

## 2. `idle` vs Trusted Advisor — which to trust?

**Question:** `idle` uses a 24h CPU window. Trusted Advisor uses 14 days. When do you trust `idle` more?

**Answer:**

**Trust `idle` more when:**
- You want **short feedback loops** — daily check for quick cost wins
- **Recent spikes matter** — catch newly-idle instances before waste accumulates
- You're **testing/iterating** — spin up, idle for a day, clean up
- You have **unpredictable traffic** — a 2-week average is stale

**Trust Trusted Advisor more when:**
- You want **statistical stability** — 14-day average smooths blips
- You're finding **systemic waste** — resources genuinely unused long-term
- Your workload has **daily cyclicity** — weekends look idle but are normal

**Best practice:** Run both. `idle --hours 24` catches quick wins; TA finds structural problems.

---

## 3. `clean --apply` blast radius — how to limit damage

**Question:** If you accidentally ran `clean --tag Environment=dev --apply` in a shared account, what would you want in place?

**Answer:**

**Three-layer defense:**

1. **Dry-run by default** ✓ Already built into costctl
   - Require explicit `--apply` flag
   - Print count: "About to delete 12 instances. Proceed? [y/N]"

2. **Tag-based owner filtering**
   - Add `--owner alice_team` filter
   - Only delete if resource has both `Environment=dev` **AND** `Owner=alice_team`
   - Prevents cross-team deletions

3. **IAM policy enforcement**
   - Only allow `terminate_instances` if resource has both `Deletable=true` **AND** `Team=us` tags
   - Forces explicit opt-in per resource

**I would pick #2 + #3:** Combination of tag-based filtering + IAM policy = strong safety net.

---

## 4. AI assistance in this codebase

**Question:** What fraction of code came from AI tools unmodified? Which parts did you modify?

**Answer:**

- **AI-generated (≈70%):** Skeleton of `_list_ec2()`, `_list_rds()`, `_list_s3()` — boto3 API patterns are standard
- **Manually modified (≈30%):**
  - Tag filtering logic (`tags_to_dict` + `tags_match` calls)
  - S3 tagging edge case (handling `ClientError` when no tagging config)
  - Volume type formatting (`f"{type}-{size}GB"`)
  - Error messages to match test assertions exactly

**Key debugging (all manual):**
- terminate_cmd merge conflict — rewrote entire file
- clean_cmd "nothing to clean" edge case
- tag_cmd S3 merge logic (don't replace, merge with existing)

**Lesson:** AI excels at boilerplate AWS API calls. Human judgment needed for edge cases, error handling, business logic.

---

## 5. W7 carry-over — which commands scale to production?

**Question:** Which commands will you keep going into W7 (production-style multi-account)?

**Answer:**

**Keep (core):**
- ✅ `list` — foundational for governance tools
- ✅ `cost` — required for chargeback by tag
- ✅ `tag` — enforces tagging discipline

**Redesign (automate instead):**
- `terminate` → AWS Config remediation action (automatic)
- `clean` → EventBridge rule (auto-terminate after N days)
- `idle` → Lambda fed by CloudWatch Insights (auto-stop cheaper than terminate)

**Drop:**
- `migrate-gp3` — one-time migration; bake into Terraform instead

**Future add-ons:**
- `compliance` — scan for untagged resources
- `quota` — AWS Service Quotas per account (multi-account view)
