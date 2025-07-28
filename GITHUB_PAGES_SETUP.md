# GitHub Pages Setup Instructions

## Repository Settings Configuration

To fix the GitHub Pages deployment permission issue, you need to configure the repository settings:

### Step 1: Enable GitHub Pages
1. Go to your repository: `https://github.com/Hassan-Naeem-code/RPA-Automation-Week-3`
2. Click on **Settings** tab
3. Scroll down to **Pages** section in the left sidebar
4. Under **Source**, select **GitHub Actions** (not Deploy from a branch)

### Step 2: Configure Actions Permissions
1. In the same **Settings** tab, click on **Actions** in the left sidebar
2. Click on **General**
3. Under **Workflow permissions**, select:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
4. Click **Save**

### Step 3: Alternative - Using Personal Access Token (if needed)
If the above doesn't work, you can create a Personal Access Token:

1. Go to GitHub Settings (your profile) → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with these scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
3. Copy the token
4. In your repository Settings → Secrets and variables → Actions
5. Create a new repository secret named `PERSONAL_TOKEN` with your token value

Then update the workflow to use:
```yaml
github_token: ${{ secrets.PERSONAL_TOKEN }}
```

### Step 4: Check Repository Visibility
- Ensure your repository is **public** for GitHub Pages to work with free accounts
- Or upgrade to GitHub Pro if you want private repository GitHub Pages

## Testing the Fix

After making these changes:

1. Commit and push the updated workflow files
2. The workflow should run automatically
3. Check the Actions tab to see if deployment succeeds
4. Your documentation will be available at: `https://hassan-naeem-code.github.io/RPA-Automation-Week-3/`

## Troubleshooting

If you still get permission errors:
- Check that GitHub Actions is enabled for your repository
- Verify the repository is public or you have GitHub Pro
- Ensure the workflow permissions are set correctly
- Try using the alternative workflow file provided
