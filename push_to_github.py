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
        token = sys.argv[1].strip()
    else:
        try:
            token = input("Enter your GitHub Personal Access Token: ").strip()
        except EOFError:
            token = ""

    if not token:
        print("Error: GitHub Personal Access Token is required to push.")
        print("Create a token at https://github.com/settings/tokens with 'repo' scope.")
        sys.exit(1)

    remote_url = f"https://{token}@github.com/Pratik-Mangate/iotSOFTWARE.git"
    print("Pushing code to https://github.com/Pratik-Mangate/iotSOFTWARE (branch: main)...")
    try:
        porcelain.push(repo_path, remote_url, "refs/heads/main")
        print("\nSuccess! All code and models have been pushed to https://github.com/Pratik-Mangate/iotSOFTWARE")
    except Exception as e:
        print(f"\nPush failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
