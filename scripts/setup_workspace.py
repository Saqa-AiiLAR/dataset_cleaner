#!/usr/bin/env python3
"""
Setup script for creating workspace folder structure.

This script ensures that required workspace directories exist with proper
.gitignore and .gitkeep files to track folder structure in Git while
ignoring their contents.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


# Required workspace folders
REQUIRED_FOLDERS = [
    "workspace/input",
    "workspace/archive",
]

# Optional workspace folders
OPTIONAL_FOLDERS = [
    "workspace/logs",
    "workspace/results",
]

# All folders to create
ALL_FOLDERS = REQUIRED_FOLDERS + OPTIONAL_FOLDERS


def ensure_repo_root(root: Path) -> None:
    """
    Verify that the given path is a Git repository root.
    
    Args:
        root: Path to check
        
    Raises:
        RuntimeError: If path is not a Git repository root
    """
    if not (root / ".git").exists():
        raise RuntimeError(
            f"Path {root} does not appear to be a Git repository root "
            "(no .git directory found)."
        )
    
    if not (root / "README.md").exists():
        raise RuntimeError(
            f"Path {root} does not appear to be the project root "
            "(no README.md found)."
        )


def create_gitignore_content() -> str:
    """
    Generate content for local .gitignore files.
    
    Returns:
        Content string for .gitignore file
    """
    return """# Ignore all files in this folder
*

# But track .gitkeep and .gitignore files
!.gitkeep
!.gitignore

# Security: prevent accidental commits of secrets
*.env
*.key
*.pem
*.crt

# System files
.DS_Store
Thumbs.db
"""


def setup_folder(
    folder_path: Path,
    root: Path,
    dry_run: bool = False
) -> Tuple[bool, str]:
    """
    Set up a workspace folder with .gitkeep and .gitignore files.
    
    Args:
        folder_path: Path to the folder (relative to root)
        root: Repository root path
        dry_run: If True, only show what would be done
        
    Returns:
        Tuple of (created_new, message)
    """
    # #region agent log
    with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"setup_workspace.py:104","message":"setup_folder entry","data":{"folder_path":str(folder_path),"root":str(root),"dry_run":dry_run},"timestamp":int(__import__('time').time()*1000)})+'\n')
    # #endregion
    full_path = root / folder_path
    gitkeep_path = full_path / ".gitkeep"
    gitignore_path = full_path / ".gitignore"
    
    # #region agent log
    with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"setup_workspace.py:110","message":"Paths computed","data":{"full_path":str(full_path),"exists":full_path.exists(),"is_file":full_path.is_file() if full_path.exists() else None,"is_dir":full_path.is_dir() if full_path.exists() else None},"timestamp":int(__import__('time').time()*1000)})+'\n')
    # #endregion
    
    created_new = False
    actions = []
    
    # Create folder if it doesn't exist
    if not full_path.exists():
        if not dry_run:
            # #region agent log
            with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"setup_workspace.py:116","message":"Before mkdir","data":{"full_path":str(full_path)},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                # #region agent log
                with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"setup_workspace.py:120","message":"After mkdir success","data":{"full_path":str(full_path)},"timestamp":int(__import__('time').time()*1000)})+'\n')
                # #endregion
            except (OSError, PermissionError, FileExistsError) as e:
                # #region agent log
                with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"setup_workspace.py:124","message":"mkdir error","data":{"full_path":str(full_path),"error_type":type(e).__name__,"error_msg":str(e)},"timestamp":int(__import__('time').time()*1000)})+'\n')
                # #endregion
                raise
        actions.append("created folder")
        created_new = True
    else:
        # #region agent log
        with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"setup_workspace.py:130","message":"Path exists check","data":{"full_path":str(full_path),"is_file":full_path.is_file(),"is_dir":full_path.is_dir()},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        if full_path.is_file():
            # #region agent log
            with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"setup_workspace.py:133","message":"Path is file not dir","data":{"full_path":str(full_path)},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            raise RuntimeError(f"Path exists but is a file, not a directory: {full_path}")
        actions.append("folder exists")
    
    # Create .gitkeep if it doesn't exist
    if not gitkeep_path.exists():
        if not dry_run:
            # #region agent log
            with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"setup_workspace.py:143","message":"Before touch .gitkeep","data":{"gitkeep_path":str(gitkeep_path)},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            try:
                gitkeep_path.touch()
                # #region agent log
                with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"setup_workspace.py:147","message":"After touch success","data":{"gitkeep_path":str(gitkeep_path)},"timestamp":int(__import__('time').time()*1000)})+'\n')
                # #endregion
            except (OSError, PermissionError, FileExistsError) as e:
                # #region agent log
                with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"setup_workspace.py:151","message":"touch error","data":{"gitkeep_path":str(gitkeep_path),"error_type":type(e).__name__,"error_msg":str(e)},"timestamp":int(__import__('time').time()*1000)})+'\n')
                # #endregion
                raise
        actions.append("created .gitkeep")
        created_new = True
    else:
        actions.append(".gitkeep exists")
    
    # Create/update .gitignore
    gitignore_content = create_gitignore_content()
    needs_update = True
    
    if gitignore_path.exists():
        # #region agent log
        with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"setup_workspace.py:163","message":"Before read .gitignore","data":{"gitignore_path":str(gitignore_path)},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        try:
            existing_content = gitignore_path.read_text(encoding='utf-8')
            # #region agent log
            with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"setup_workspace.py:167","message":"After read success","data":{"gitignore_path":str(gitignore_path),"content_length":len(existing_content)},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            if existing_content == gitignore_content:
                needs_update = False
                actions.append(".gitignore exists")
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            # #region agent log
            with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"setup_workspace.py:174","message":"read .gitignore error","data":{"gitignore_path":str(gitignore_path),"error_type":type(e).__name__,"error_msg":str(e)},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            raise
    
    if needs_update:
        if not dry_run:
            # #region agent log
            with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"setup_workspace.py:182","message":"Before write .gitignore","data":{"gitignore_path":str(gitignore_path)},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            try:
                gitignore_path.write_text(gitignore_content, encoding='utf-8')
                # #region agent log
                with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"setup_workspace.py:186","message":"After write success","data":{"gitignore_path":str(gitignore_path)},"timestamp":int(__import__('time').time()*1000)})+'\n')
                # #endregion
            except (OSError, PermissionError, FileExistsError) as e:
                # #region agent log
                with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"setup_workspace.py:190","message":"write .gitignore error","data":{"gitignore_path":str(gitignore_path),"error_type":type(e).__name__,"error_msg":str(e)},"timestamp":int(__import__('time').time()*1000)})+'\n')
                # #endregion
                raise
        actions.append("created/updated .gitignore")
        created_new = True
    
    # #region agent log
    with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"setup_workspace.py:197","message":"setup_folder exit","data":{"created_new":created_new,"actions":actions},"timestamp":int(__import__('time').time()*1000)})+'\n')
    # #endregion
    message = f"{folder_path}: {', '.join(actions)}"
    return created_new, message


def main() -> int:
    """Main entry point for the setup script."""
    parser = argparse.ArgumentParser(
        description="Set up workspace folder structure with .gitkeep and .gitignore files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --dry-run
  %(prog)s --quiet
  %(prog)s --root /path/to/repo
        """
    )
    
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root path (default: current directory)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without making changes"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress INFO messages, only show errors"
    )
    
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Also create optional folders (logs, results)"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.quiet:
        logger.setLevel(logging.ERROR)
    
    # Resolve root path
    root = args.root.resolve()
    
    try:
        # Verify we're in a Git repository root
        ensure_repo_root(root)
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
        
        created_any = False
        
        # Set up workspace root .gitkeep first
        workspace_root = root / "workspace"
        workspace_gitkeep = workspace_root / ".gitkeep"
        # #region agent log
        with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"setup_workspace.py:210","message":"Before workspace root setup","data":{"workspace_root":str(workspace_root),"exists":workspace_root.exists(),"is_file":workspace_root.is_file() if workspace_root.exists() else None,"is_dir":workspace_root.is_dir() if workspace_root.exists() else None},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        if not workspace_gitkeep.exists():
            if not args.dry_run:
                if workspace_root.exists() and workspace_root.is_file():
                    # #region agent log
                    with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"setup_workspace.py:215","message":"workspace root is file","data":{"workspace_root":str(workspace_root)},"timestamp":int(__import__('time').time()*1000)})+'\n')
                    # #endregion
                    raise RuntimeError(f"workspace path exists but is a file, not a directory: {workspace_root}")
                # #region agent log
                with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"setup_workspace.py:220","message":"Before workspace mkdir","data":{"workspace_root":str(workspace_root)},"timestamp":int(__import__('time').time()*1000)})+'\n')
                # #endregion
                try:
                    workspace_root.mkdir(parents=True, exist_ok=True)
                    workspace_gitkeep.touch()
                    # #region agent log
                    with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"setup_workspace.py:225","message":"After workspace mkdir success","data":{"workspace_root":str(workspace_root)},"timestamp":int(__import__('time').time()*1000)})+'\n')
                    # #endregion
                except (OSError, PermissionError, FileExistsError) as e:
                    # #region agent log
                    with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"setup_workspace.py:229","message":"workspace mkdir error","data":{"workspace_root":str(workspace_root),"error_type":type(e).__name__,"error_msg":str(e)},"timestamp":int(__import__('time').time()*1000)})+'\n')
                    # #endregion
                    raise
            # #region agent log
            with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"setup_workspace.py:233","message":"Logging workspace created","data":{"quiet":args.quiet},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            logger.info("workspace/: created .gitkeep")
            created_any = True
        else:
            # #region agent log
            with open('/Users/user/Projects/SaqaParser/.cursor/debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"setup_workspace.py:238","message":"Logging workspace exists","data":{"quiet":args.quiet},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            logger.info("workspace/: .gitkeep exists")
        
        # Determine which folders to create
        folders_to_create = REQUIRED_FOLDERS
        if args.include_optional:
            folders_to_create = ALL_FOLDERS
        
        # Set up each folder
        for folder in folders_to_create:
            created, message = setup_folder(
                Path(folder),
                root,
                dry_run=args.dry_run
            )
            if created:
                created_any = True
            logger.info(message)
        
        if args.dry_run:
            logger.info("DRY RUN complete - no changes made")
        elif created_any:
            logger.info("Workspace structure setup complete!")
        else:
            logger.info("Workspace structure already exists - nothing to do")
        
        return 0
    
    except RuntimeError as e:
        logger.error(str(e))
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

