#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Initialize an ast-grep project structure in the current or specified directory.

Creates sgconfig.yml, rules/, rule-tests/, and utils/ directories with example
rule files to get started quickly.

Usage:
    uv run scripts/init_project.py [target_dir]
    uv run scripts/init_project.py ./my-project --with-examples
"""

import argparse
import sys
from pathlib import Path

SGCONFIG_TEMPLATE = """\
ruleDirs:
  - rules
testConfigs:
  - testDir: rule-tests
    snapshotDir: __snapshots__
utilDirs:
  - utils
"""

EXAMPLE_RULE = """\
id: no-console-log
language: JavaScript
rule:
  pattern: console.log($$$ARGS)
message: "console.log statement found"
severity: warning
note: "Remove debug logging before production deployment"
fix: ""
"""

EXAMPLE_TEST = """\
id: no-console-log
valid:
  - "logger.info('message')"
  - "debug('test')"
invalid:
  - "console.log('test')"
  - "console.log(variable, 'data')"
"""

EXAMPLE_UTIL = """\
id: is-test-function
language: JavaScript
rule:
  kind: function_declaration
  has:
    kind: identifier
    regex: "^(test|it|describe)"
    field: name
"""


def init_project(target: Path, with_examples: bool = False) -> None:
    """Create ast-grep project structure."""
    target.mkdir(parents=True, exist_ok=True)

    sgconfig = target / "sgconfig.yml"
    if sgconfig.exists():
        print(f"sgconfig.yml already exists at {sgconfig}", file=sys.stderr)
        sys.exit(1)

    # Create directories
    dirs = ["rules", "rule-tests", "utils"]
    for d in dirs:
        (target / d).mkdir(exist_ok=True)
        print(f"  Created {d}/")

    # Write sgconfig.yml
    sgconfig.write_text(SGCONFIG_TEMPLATE, encoding="utf-8")
    print("  Created sgconfig.yml")

    if with_examples:
        # Write example rule
        rule_file = target / "rules" / "no-console-log.yml"
        rule_file.write_text(EXAMPLE_RULE, encoding="utf-8")
        print("  Created rules/no-console-log.yml")

        # Write example test
        test_file = target / "rule-tests" / "no-console-log-test.yml"
        test_file.write_text(EXAMPLE_TEST, encoding="utf-8")
        print("  Created rule-tests/no-console-log-test.yml")

        # Write example utility
        util_file = target / "utils" / "is-test-function.yml"
        util_file.write_text(EXAMPLE_UTIL, encoding="utf-8")
        print("  Created utils/is-test-function.yml")

    print(f"\nast-grep project initialized at {target.resolve()}")
    print("\nNext steps:")
    print("  1. Create rules in rules/ directory")
    print("  2. Add tests in rule-tests/ directory")
    print("  3. Run: ast-grep scan")
    print("  4. Test: ast-grep test")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize an ast-grep project structure"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target directory (default: current directory)",
    )
    parser.add_argument(
        "--with-examples",
        action="store_true",
        help="Include example rule, test, and utility files",
    )
    args = parser.parse_args()

    target = Path(args.target)
    print(f"Initializing ast-grep project in {target.resolve()}")
    init_project(target, args.with_examples)


if __name__ == "__main__":
    main()
