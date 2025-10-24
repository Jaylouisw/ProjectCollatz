# GitHub Workflows

This directory contains automated GitHub Actions workflows for the Collatz Engine project.

## Workflows

### 1. Auto-Approve Benchmark PRs (`auto-approve-benchmarks.yml`)

**Purpose:** Automatically approve and merge pull requests that only contain benchmark JSON files.

**Triggers:**
- Pull request opened, synchronized, or reopened
- Only activates for changes in `benchmarks/benchmark_*.json`

**What it does:**
1. ✓ Validates that PR only contains benchmark files
2. ✓ Checks all files are in `benchmarks/` directory
3. ✓ Validates JSON format
4. ✓ Auto-approves the PR
5. ✓ Adds `benchmark` and `auto-approved` labels
6. ✓ Auto-merges the PR (squash merge)
7. ✓ Posts a success comment

**Requirements:**
- PR must ONLY contain files matching `benchmarks/benchmark_*.json`
- All JSON files must be valid
- No other files can be modified

**Permissions needed:**
- `contents: write` - For merging PRs
- `pull-requests: write` - For approving and labeling PRs

---

### 2. Benchmark PR Validator (`validate-benchmarks.yml`)

**Purpose:** Validate all PRs and provide feedback on benchmark submissions.

**Triggers:**
- All pull requests (opened, synchronized, or reopened)

**What it does:**
1. ✓ Detects benchmark files in PR
2. ✓ Validates JSON syntax
3. ✓ Checks for recommended fields (timestamp, hardware, performance)
4. ✓ Distinguishes between pure benchmark PRs and mixed PRs
5. ✓ Posts validation results as a comment

**Output:**
- **Pure benchmark PR:** Indicates eligibility for auto-approval
- **Mixed PR:** Notes that manual review is required
- **No benchmarks:** Silent (no comment)

**Permissions needed:**
- `contents: read` - For reading PR files
- `pull-requests: write` - For posting comments
- `checks: write` - For setting check status

---

## Setup Instructions

### Required GitHub Settings

1. **Enable auto-merge in repository settings:**
   - Go to Settings → General → Pull Requests
   - Check "Allow auto-merge"
   - Check "Allow squash merging"

2. **Configure branch protection (optional but recommended):**
   - Settings → Branches → Add rule for `master`
   - Enable "Require status checks to pass before merging"
   - Add `validate` check from `validate-benchmarks.yml`

3. **Workflow permissions:**
   - Go to Settings → Actions → General
   - Under "Workflow permissions", select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"

### Secrets (if needed)

The workflows use `GITHUB_TOKEN` which is automatically provided by GitHub Actions. No additional secrets are required unless you want to use a personal access token for enhanced permissions.

**Optional:** Create a PAT (Personal Access Token) with repo permissions:
- Settings → Developer settings → Personal access tokens → Fine-grained tokens
- Add token as repository secret named `GH_PAT`
- Replace `GITHUB_TOKEN` with `secrets.GH_PAT` in workflows

---

## Testing the Workflows

### Test with a benchmark PR:

1. Fork the repository
2. Add a benchmark file: `benchmarks/benchmark_test_20251024.json`
3. Create a pull request
4. Watch the workflows run:
   - ✓ `validate-benchmarks.yml` runs first (posts validation comment)
   - ✓ `auto-approve-benchmarks.yml` approves and merges (if pure benchmark PR)

### Expected behavior:

**Pure benchmark PR (only .json files in benchmarks/):**
- ✅ Validation passes
- ✅ Auto-approved
- ✅ Auto-merged
- ✅ Success comment posted

**Mixed PR (benchmark + other files):**
- ✅ Validation passes
- ⚠️ Warning comment posted
- ⏸️ Waits for manual review
- ❌ NOT auto-merged

**Invalid PR:**
- ❌ Validation fails
- ❌ NOT approved
- ❌ Error messages in workflow logs

---

## Customization

### Change merge method:
Edit `auto-approve-benchmarks.yml`, change `MERGE_METHOD`:
```yaml
MERGE_METHOD: "squash"  # Options: merge, squash, rebase
```

### Add more validations:
Edit the validation step in `auto-approve-benchmarks.yml`:
```bash
# Example: Check file size
if [ $(stat -f%z "$file") -gt 1048576 ]; then
  echo "::error::File too large: $file"
  exit 1
fi
```

### Change labels:
Edit the label step in `auto-approve-benchmarks.yml`:
```yaml
labels: ['benchmark', 'auto-approved', 'community']
```

---

## Troubleshooting

**Workflow not running:**
- Check that workflow permissions are enabled
- Verify the file path matches `benchmarks/benchmark_*.json`
- Check Actions tab for errors

**Auto-merge not working:**
- Ensure "Allow auto-merge" is enabled in repository settings
- Verify workflow has `contents: write` permission
- Check that branch protection isn't blocking

**Approval not working:**
- Ensure "Allow GitHub Actions to create and approve pull requests" is enabled
- Verify workflow has `pull-requests: write` permission
- Check that you're not trying to approve your own PR (GitHub limitation)

**JSON validation failing:**
- Ensure files are valid JSON (use `python -m json.tool file.json`)
- Check for trailing commas
- Verify UTF-8 encoding

---

## Security Considerations

✓ **Safe:** Workflows only auto-merge PRs with benchmark JSON files
✓ **Validated:** JSON syntax is checked before approval
✓ **Limited scope:** Only affects `benchmarks/` directory
✓ **Transparent:** All actions are logged and commented

⚠️ **Note:** The workflows have write access to approve and merge PRs. This is necessary for automation but means you should:
- Review workflow code before enabling
- Monitor the Actions tab for unexpected behavior
- Use branch protection for critical branches

---

## Contributing

To modify these workflows:
1. Test changes in a fork first
2. Ensure backward compatibility
3. Update this README with changes
4. Test with various PR scenarios

For questions or issues with the workflows, open an issue on GitHub.
