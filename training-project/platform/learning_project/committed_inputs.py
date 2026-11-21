"""Compare working files to a final commit using Git's path-aware clean rules."""
import subprocess
from pathlib import Path


def matches_committed_file(root: Path, path: Path, final_commit: str) -> bool:
    """Honor Git text/binary attributes without modifying the index or working tree."""
    if not path.is_file() or path.is_symlink():
        return False
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    recorded = subprocess.run(
        ['git', '-C', str(root), 'rev-parse', '--verify', final_commit + ':' + relative],
        capture_output=True,
    )
    if recorded.returncode:
        return False
    # Unlike a raw byte comparison, this applies the same path-aware normalization
    # as git add (including core.autocrlf and .gitattributes). No object is written.
    current = subprocess.run(
        ['git', '-C', str(root), 'hash-object', '--path=' + relative, '--stdin'],
        input=path.read_bytes(), capture_output=True,
    )
    return current.returncode == 0 and current.stdout.strip() == recorded.stdout.strip()
