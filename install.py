#!/usr/bin/env python3
"""Cross-platform installer for gmail-reader.

  python install.py            # create .venv + install deps
  python install.py --link     # also put `gmail-reader` on your PATH

Run it with the Python interpreter you want the tool to use (>= 3.9).
Works on macOS, Linux, and Windows.
"""
import os
import subprocess
import sys

TOOL = "gmail-reader"
MODULE = "gmail_reader.py"
MIN_PY = (3, 9)
NEXT_STEPS = (
    "\nNext: save an OAuth Desktop client secret as credentials.json here,\n"
    "then run:  gmail-reader auth   (see README.md)."
)

HERE = os.path.dirname(os.path.abspath(__file__))
IS_WIN = os.name == "nt"
VENV = os.path.join(HERE, ".venv")
VENV_PY = os.path.join(
    VENV, "Scripts" if IS_WIN else "bin",
    "python.exe" if IS_WIN else "python",
)


def _path_dirs():
    return [d for d in os.environ.get("PATH", "").split(os.pathsep) if d]


def link_onto_path():
    home = os.path.expanduser("~")
    if IS_WIN:
        writable = [d for d in _path_dirs() if os.path.isdir(d) and os.access(d, os.W_OK)]
        target = writable[0] if writable else os.path.join(home, ".local", "bin")
        os.makedirs(target, exist_ok=True)
        shim = os.path.join(target, TOOL + ".bat")
        with open(shim, "w", newline="\r\n") as f:
            f.write('@echo off\n"{}" "{}" %*\n'.format(VENV_PY, os.path.join(HERE, MODULE)))
        print("Wrote shim:", shim)
        if target not in _path_dirs():
            print("Note: add", target, "to your PATH.")
    else:
        target = next(
            (d for d in (os.path.join(home, "bin"), os.path.join(home, ".local", "bin"),
                         "/usr/local/bin")
             if d in _path_dirs() and os.path.isdir(d) and os.access(d, os.W_OK)),
            None,
        )
        if target is None:
            target = os.path.join(home, ".local", "bin")
            os.makedirs(target, exist_ok=True)
            print('Note: add {} to your PATH: export PATH="{}:$PATH"'.format(target, target))
        link = os.path.join(target, TOOL)
        if os.path.islink(link) or os.path.exists(link):
            os.remove(link)
        os.symlink(os.path.join(HERE, TOOL), link)
        print("Linked:", link, "->", os.path.join(HERE, TOOL))


def main():
    if sys.version_info < MIN_PY:
        sys.exit("{} needs Python >= {}; you ran {}. Re-run with a newer "
                 "interpreter.".format(TOOL, ".".join(map(str, MIN_PY)),
                                       sys.version.split()[0]))
    print("Creating venv with", sys.version.split()[0], "...")
    subprocess.check_call([sys.executable, "-m", "venv", VENV])
    subprocess.check_call([VENV_PY, "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    subprocess.check_call([VENV_PY, "-m", "pip", "install", "--quiet", "-r",
                           os.path.join(HERE, "requirements.txt")])
    launcher = os.path.join(HERE, TOOL)
    if not IS_WIN and os.path.exists(launcher):
        os.chmod(launcher, 0o755)
    print("Dependencies installed.")
    if "--link" in sys.argv[1:]:
        link_onto_path()
    print(NEXT_STEPS)


if __name__ == "__main__":
    main()
