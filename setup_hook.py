import os
import sys
from pathlib import Path

def install_git_hook():
    git_dir = Path(".git")
    if not git_dir.exists():
        print("❌ Error: Not a Git repository!")
        sys.exit(1)

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    
    hook_path = hooks_dir / "pre-commit"

    hook_content = """#!/bin/sh
echo "🔍 Running pre-commit AI security check..."

python reviewer.py > precommit_review.json

if [ $? -ne 0 ]; then
    echo "❌ AI Scanner failed to run. Commit aborted."
    exit 1
fi

python -c "
import json, sys
try:
    data = json.load(open('precommit_review.json'))
    score = data.get('overall_score', 100)
    print(f'📊 Code Health Score: {score}/100')
    if score < 50:
        print('🚨 COMMIT REJECTED: Code health score is below threshold (50/100). Fix flaws before committing.')
        sys.exit(1)
except Exception as e:
    print(f'Warning: Could not parse pre-commit report: {e}')
"

EX_CODE=$?
if [ $EX_CODE -ne 0 ]; then
    exit 1
fi

echo "✅ Pre-commit check passed!"
exit 0
"""

    hook_path.write_text(hook_content, encoding="utf-8")
    
    if os.name != 'nt':
        hook_path.chmod(0o755)

    print(f"✅ Git pre-commit hook installed successfully at: {hook_path}")

if __name__ == "__main__":
    install_git_hook()