"""Push script for iotSOFTWARE repository using Dulwich.

Usage:
    python push_to_github.py <GITHUB_TOKEN>
    or run interactively:
    python push_to_github.py
"""

import sys
import urllib.request
import urllib.error
import json
from dulwich import porcelain

repo_path = r"d:\_Projects\iot"

def test_token_permissions(token):
    # Check what user the token belongs to
    req_user = urllib.request.Request(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {token}", "User-Agent": "GitPythonPush/1.0"}
    )
    try:
        with urllib.request.urlopen(req_user) as resp:
            data = json.loads(resp.read().decode())
            username = data.get("login")
            print(f"Authenticated as GitHub user: {username}")
    except Exception as e:
        print(f"Token validation failed: {e}")
        return False

    return True

def main():
    if len(sys.argv) > 1:
        token = sys.argv[1].strip("<>\"' ")
    else:
        try:
            token = input("Enter your GitHub Personal Access Token: ").strip("<>\"' ")
        except EOFError:
            token = ""

    token = token.replace("\n", "").replace("\r", "").strip("<>\"' ")

    if not token:
        print("\nError: GitHub Personal Access Token is required to push.")
        print("Please generate a token at https://github.com/settings/tokens/new (check 'repo' scope).")
        sys.exit(1)

    print("\nValidating token with GitHub API...")
    if not test_token_permissions(token):
        print("Error: The token is invalid or expired.")
        sys.exit(1)

    remote_url = f"https://x-access-token:{token}@github.com/Pratik-Mangate/iotSOFTWARE.git"
    print("Pushing repository to https://github.com/Pratik-Mangate/iotSOFTWARE (branch: main)...")
    try:
        porcelain.push(repo_path, remote_url, "refs/heads/main")
        print("\n" + "="*60)
        print("SUCCESS! All code and the AI model have been pushed to:")
        print("https://github.com/Pratik-Mangate/iotSOFTWARE")
        print("="*60)
    except Exception as e:
        print(f"\nPush failed: {e}")
        if "403" in str(e) or "Unauthorized" in str(e) or "credentials" in str(e):
            print("\n" + "!"*60)
            print("REASON FOR ERROR 403:")
            print("Your token does not have 'Write' permission to the repository.")
            print("\nHOW TO FIX (Choose ONE):")
            print("1. EASIEST - Generate a Classic Token (starts with ghp_):")
            print("   Go to: https://github.com/settings/tokens/new")
            print("   Check the 'repo' box, click 'Generate token', and copy it.")
            print("\n2. OR update your existing Fine-Grained token (github_pat_):")
            print("   Go to: https://github.com/settings/tokens?type=beta")
            print("   Click on your token -> Under 'Repository permissions', set 'Contents' to 'Read and write'.")
            print("   Click 'Save changes'.")
            print("!"*60)
        sys.exit(1)

if __name__ == "__main__":
    main()
