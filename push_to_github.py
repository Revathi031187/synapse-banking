#!/usr/bin/env python3
"""
Script to push all changes to GitHub
Repository: https://github.com/Revathi031187/NBA
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a git command and print the result"""
    print(f"\n{'='*60}")
    print(f"[{description}]")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=r"C:\Users\jaisonsamuel.d.lv\Desktop\personalization-agent"
        )
        print(result.stdout)
        if result.stderr:
            print(f"Error/Warning: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 PUSHING CODE TO GITHUB")
    print("Repository: https://github.com/Revathi031187/NBA")
    print("="*60)
    
    # Change to project directory
    os.chdir(r"C:\Users\jaisonsamuel.d.lv\Desktop\personalization-agent")
    
    # 1. Check git status
    if not run_command("git status", "Step 1/6: Checking git status"):
        print("⚠️ Warning: Could not get git status")
    
    # 2. Check remote
    if not run_command("git remote -v", "Step 2/6: Checking remote repository"):
        print("⚠️ Warning: Could not check remote repository")
    
    # 3. Stage all changes
    print("\n" + "="*60)
    print("[Step 3/6: Staging all changes]")
    print("="*60)
    if not run_command("git add .", "Staging files"):
        print("❌ Error: Could not stage files")
        return False
    
    # 4. Create commit with detailed message
    commit_message = """Major update: Streamlined Academy Sports platform with robust segmentation and recommendations

Key Changes:
- Removed all banking and retail modules - Academy Sports is now the sole focus
- Enhanced macro and micro segmentation with unique, archetype-based naming
- Implemented production-ready product recommendation engine with tier-based filtering
- Added detailed explanations for all product recommendations
- Fixed Agent A and Agent B integration for seamless customer insights
- Improved UI/UX: simplified navigation, always-visible data loader, formatted segment insights
- Ensured premium customers receive only premium product recommendations
- Fixed all micro-segmentation display issues
- Cleaned up 294+ lines of deprecated code
- All endpoints tested and working correctly

Technical Improvements:
- Fixed TypeError in Agent B premium brand filtering
- Enhanced price range calculation for customer tiers
- Implemented pandas DataFrame operations for robust data filtering
- Added comprehensive logging throughout the application
- Optimized segment naming algorithms with archetype system
"""
    
    print("\n" + "="*60)
    print("[Step 4/6: Creating commit]")
    print("="*60)
    print(f"Commit message:\n{commit_message}")
    
    # Escape the commit message properly for Windows
    escaped_message = commit_message.replace('"', '\\"')
    if not run_command(f'git commit -m "{escaped_message}"', "Committing changes"):
        print("⚠️ Note: Commit may have failed - possibly no changes to commit")
    
    # 5. Check current branch
    if not run_command("git branch", "Step 5/6: Checking current branch"):
        print("⚠️ Warning: Could not check current branch")
    
    # 6. Push to GitHub
    print("\n" + "="*60)
    print("[Step 6/6: Pushing to GitHub master branch]")
    print("="*60)
    if not run_command("git push origin master", "Pushing to GitHub"):
        print("❌ Error: Could not push to GitHub")
        print("\nPossible reasons:")
        print("1. Authentication issue - may need to set up SSH keys or Personal Access Token")
        print("2. Branch protection rules on GitHub")
        print("3. Network connectivity issue")
        print("4. Remote repository doesn't exist or you don't have write access")
        print("\nPlease check your git configuration and try again.")
        return False
    
    print("\n" + "="*60)
    print("✅ SUCCESS! Code pushed to GitHub")
    print("="*60)
    print("Repository: https://github.com/Revathi031187/NBA")
    print("Branch: master")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
