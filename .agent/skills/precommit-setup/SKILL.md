---
name: precommit-setup
description: Installs and configures a pre-commit hook using husky and lint-staged that runs prettier (format), TypeScript type-checking, and tests before every commit. Use when setting up a new frontend/fullstack repo, when asked to add pre-commit hooks, or when asked to configure prettier or lint-staged.
---

# Setup Pre-Commit

Install husky + lint-staged + prettier with a pre-commit hook that enforces:
1. Auto-format staged files (prettier via lint-staged)
2. TypeScript type-check (whole project)
3. Tests (fast only — skip slow/integration)

## Steps

### 1. Detect package manager

```bash
[[ -f pnpm-lock.yaml ]] && PM=pnpm
[[ -f yarn.lock ]] && PM=yarn
[[ -f package-lock.json ]] && PM=npm
```

Use `$PM` for all subsequent install commands.

### 2. Install dependencies

```bash
$PM add -D husky lint-staged prettier
```

### 3. Initialise husky

```bash
npx husky init
```

This creates `.husky/` and adds a `prepare` script to `package.json`.

### 4. Create the pre-commit hook

Write `.husky/pre-commit`:

```bash
#!/usr/bin/env sh
npx lint-staged
npm run typecheck
npm run test
```

Make it executable: `chmod +x .husky/pre-commit`

### 5. Create `.lintstagedrc`

```json
{
  "*.{ts,tsx,js,jsx,json,css,md}": ["prettier --write"]
}
```

### 6. Create `.prettierrc` (if it doesn't exist)

```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2
}
```

If `.prettierrc` already exists, skip this step.

### 7. Verify

Stage a file and run `git commit --dry-run` (or `git stash && git stash pop` trick) to confirm the hook fires without errors.

### 8. Commit

```bash
git add .husky .lintstagedrc .prettierrc package.json
git commit -m "chore: add husky pre-commit hooks with lint-staged and prettier"
```
