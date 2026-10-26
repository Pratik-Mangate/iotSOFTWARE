"""Push script for iotSOFTWARE repository using Dulwich.

Usage:
    python push_to_github.py <GITHUB_TOKEN>
    or run interactively:
    python push_to_github.py
"""

import sys
from dulwich import porcelain

repo_path = r"d:\_Projects\iot"

def main():
    if len(sys.argv) > 1:
        token = sys.argv[1].strip("<>\"' ")
    else:
        try:
            token = input("Enter your GitHub Personal Access Token: ").strip("<>\"' ")
        except EOFError:
            token = ""

    if not token:
        print("Error: GitHub Personal Access Token is required to push.")
        print("Create a token at https://github.com/settings/tokens with 'repo' scope.")
        sys.exit(1)

    # Strip any extra characters, spaces, or angle brackets
    token = token.replace("\n", "").replace("\r", "").strip("<>\"' ")

    remote_url = f"https://x-access-token:{token}@github.com/Pratik-Mangate/iotSOFTWARE.git"
    print("Pushing code to https://github.com/Pratik-Mangate/iotSOFTWARE (branch: main)...")
    try:
        porcelain.push(repo_path, remote_url, "refs/heads/main")
        print("\nSUCCESS! All code and models have been pushed to https://github.com/Pratik-Mangate/iotSOFTWARE")
    except Exception as e:
        print(f"\nPush failed: {e}")
        if "403" in str(e) or "Unauthorized" in str(e) or "credentials" in str(e):
            print("\nTip: If you used a Fine-Grained token (starting with github_pat_):")
            print("  1. Make sure under 'Repository access' you selected 'All repositories' or 'iotSOFTWARE'.")
            print("  2. Under 'Permissions' -> 'Repository permissions', set 'Contents' to 'Read and write'.")
            print("Alternatively, create a Classic Token (starts with ghp_) at https://github.com/settings/tokens (select 'repo' scope).")
        sys.exit(1)

if __name__ == "__main__":
    main()
