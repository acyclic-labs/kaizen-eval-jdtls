#!/usr/bin/env python3
"""Split the org.eclipse.jdt.ls.tests test classes into CI shards.

Usage: test-shards.py SHARD TOTAL   (SHARD is 1-based)

Prints the Maven argument that selects SHARD's classes. Classes are spread
over the shards by their run time in test-shard-timings.txt (classes missing
from it count as DEFAULT_SECONDS). Shards 1..TOTAL-1 run an explicit list of
classes; the last shard runs Tycho's default includes minus every class given
to the other shards, so no test class can be left out of the run.
"""

import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'org.eclipse.jdt.ls.tests', 'src')
TIMINGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test-shard-timings.txt')
DEFAULT_SECONDS = 5.0
# Tycho's default includes: **/Test*.class, **/*Test.class, **/*Tests.class, **/*TestCase.class
TEST_NAME = re.compile(r'^(Test.*|.*Test|.*Tests|.*TestCase)\.java$')


def test_classes():
	classes = []
	for dirpath, _, filenames in os.walk(SRC):
		for name in filenames:
			if TEST_NAME.match(name):
				path = os.path.relpath(os.path.join(dirpath, name), SRC)
				classes.append(path[:-len('.java')].replace(os.sep, '/'))
	return sorted(classes)


def timings():
	seconds = {}
	with open(TIMINGS) as f:
		for line in f:
			if line.strip() and not line.startswith('#'):
				name, value = line.split()
				seconds[name.replace('.', '/')] = float(value)
	return seconds


def shards(total):
	seconds = timings()
	weight = lambda c: seconds.get(c, DEFAULT_SECONDS)
	buckets = [[0.0, []] for _ in range(total)]
	# Longest first, each to the least loaded shard.
	for c in sorted(test_classes(), key=lambda c: (-weight(c), c)):
		bucket = min(buckets, key=lambda b: b[0])
		bucket[0] += weight(c)
		bucket[1].append(c)
	return [sorted(b[1]) for b in buckets]


def main():
	shard, total = int(sys.argv[1]), int(sys.argv[2])
	if not 1 <= shard <= total:
		sys.exit('shard must be between 1 and %d' % total)
	split = shards(total)
	if shard < total:
		print('-Dtest.shard.includes=' + ','.join('**/' + c + '.class' for c in split[shard - 1]))
	else:
		others = ['**/' + c + '.class' for s in split[:-1] for c in s]
		# Setting excludes replaces Tycho's default exclude of inner classes, so keep it.
		print('-Dtest.shard.excludes=' + ','.join(['**/*$*'] + others))


if __name__ == '__main__':
	main()
