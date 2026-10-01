#!/usr/bin/env python3
'''
Bump the PATCH section of __version__ in __init__.py and print the new version string to stdout.

Usage:
    python3 scripts/bump_version.py [PATH_TO_INIT_PY]

[PATH_TO_INIT_PY] is the path to the __init__.py file to modify (optional).
the default is __init__.py at the repo root (one directory up from this script).

'''

import sys
from pathlib import Path


def default_init_path():
    return Path(__file__).resolve().parent.parent / "__init__.py"


def bump_version_file(init_path):
    # Read the whole file line by line and translate it into a list of lines.
    # Example: "__version__ = '1.2.3'\n__all__ = []" -> ["__version__ = '1.2.3'", "__all__ = []"]
    lines = init_path.read_text(encoding='utf-8').split('\n')

    for i in range(len(lines)):
        line = lines[i]

        # Skip every line except the one that assigns __version__.
        # Example: "__all__ = []" -> does not start with "__version__", skipped.
        if not line.strip().startswith('__version__'):
            continue

        # Split the line into the part before "=" (name) and after it (value).
        # Example: "__version__ = '1.2.3'" -> name = "__version__ ", value = " '1.2.3'" -> "'1.2.3'"
        equals_index = line.find('=')
        name = line[:equals_index]
        value = line[equals_index + 1:]
        value = value.strip()

        # The value looks like 'X.Y.Z' or "X.Y.Z", so grab the quote character
        # and strip it off both ends to get the bare version string.
        # Example: "'1.2.3'" -> quote = "'", version = "1.2.3"
        quote = value[0]
        version = value.strip(quote)

        # Make sure the version is exactly three dot-separated numbers.
        # Example: "1.2.3" -> parts = ["1", "2", "3"] (ok); "1.2" or "1.2.x" would fail here.
        parts = version.split('.')
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise ValueError(f"invalid __version__: {version!r}")

        # Convert each part to a number and bump only the patch number.
        # Example: parts = ["1", "2", "3"] -> major=1, minor=2, patch=3 -> new_version = "1.2.4"
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2])
        new_version = f"{major}.{minor}.{patch + 1}"

        # Rebuild the line with the new version and put it back in the list.
        # Example: name="__version__ ", quote="'", new_version="1.2.4" -> "__version__ = '1.2.4'"
        lines[i] = name + "= " + quote + new_version + quote

        # Write all lines back to the file and report the new version.
        init_path.write_text('\n'.join(lines), encoding='utf-8')
        return new_version

    # No __version__ line was found in the whole file.
    raise ValueError(f"could not find __version__ assignment in {init_path}")


def main(argv):
    init_path = Path(argv[1]).resolve() if len(argv) > 1 else default_init_path()

    if not init_path.is_file():
        print(f"error: {init_path} does not exist or is not a file", file=sys.stderr)
        return 1

    try:
        new_version = bump_version_file(init_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(new_version)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
