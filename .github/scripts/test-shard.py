#!/usr/bin/env python3
"""Print the comma-separated test classes of one shard of org.eclipse.jdt.ls.tests.

Usage: test-shard.py <shard> <total>   (shard is 1-based)

The candidate classes are the sources matching Tycho Surefire's default includes
(**/Test*.java, **/*Test.java, **/*Tests.java, **/*TestCase.java), so the union of
all shards is exactly the set of tests a non-sharded run selects. Classes are spread
over the shards by their recorded runtime (test-timings.txt) so the shards take
roughly the same time.
"""
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "org.eclipse.jdt.ls.tests", "src")
INCLUDE = re.compile(r"^(Test\w*|\w*Test|\w*Tests|\w*TestCase)\.java$")


def test_classes():
    names = set()
    for dirpath, _, files in os.walk(SRC):
        for f in files:
            if INCLUDE.match(f):
                name = f[:-len(".java")]
                if name in names:
                    sys.exit(f"duplicate test class name {name}: shards select tests by simple name")
                names.add(name)
    return sorted(names)


def timings():
    result = {}
    with open(os.path.join(HERE, "test-timings.txt")) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                name, seconds = line.split()
                result[name] = float(seconds)
    return result


def shards(total):
    known = timings()
    default = statistics.median(known.values())
    classes = test_classes()
    bins = [[0.0, i, []] for i in range(total)]
    # Longest processing time first: give each class to the currently lightest shard.
    for name in sorted(classes, key=lambda c: (-known.get(c, default), c)):
        lightest = min(bins, key=lambda b: (b[0], b[1]))
        lightest[0] += known.get(name, default)
        lightest[2].append(name)
    assert sorted(c for b in bins for c in b[2]) == classes
    return bins


def main():
    shard, total = int(sys.argv[1]), int(sys.argv[2])
    if not 1 <= shard <= total:
        sys.exit(f"shard must be between 1 and {total}")
    bins = shards(total)
    for seconds, i, names in bins:
        print(f"shard {i + 1}/{total}: {len(names)} classes, ~{seconds / 60:.1f} min", file=sys.stderr)
    print(",".join(sorted(bins[shard - 1][2])))


if __name__ == "__main__":
    main()
