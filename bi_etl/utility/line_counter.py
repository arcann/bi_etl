#!/usr/bin/env python
import argparse
import mmap
import subprocess
from collections import defaultdict
from timeit import default_timer as timer


def mapcount(filename):
    f = open(filename, "r+")
    buf = mmap.mmap(f.fileno(), 0)
    lines = 0
    readline = buf.readline
    while readline():
        lines += 1
    return lines


def simplecount(filename):
    lines = 0
    for _ in open(filename):
        lines += 1
    return lines


# Fastest for small files
def bufcount(filename):
    f = open(filename)
    lines = 0
    buf_size = 1024 * 1024
    read_f = f.read  # loop optimization

    buf = read_f(buf_size)
    while buf:
        lines += buf.count('\n')
        buf = read_f(buf_size)

    return lines


# Fastest for big files
def wccount(filename):
    out = subprocess.Popen(['wc', '-l', filename],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT
                           ).communicate()[0]
    return int(out.partition(b' ')[0])


def itercount(filename):
    return sum(1 for _ in open(filename, 'rbU'))


def opcount(fname):
    line_number = 0
    with open(fname) as f:
        for line_number, _ in enumerate(f, 1):
            pass
    return line_number


def kylecount(fname):
    return sum(1 for _ in open(fname))


def clear_cache():
    """Clear disk cache on Linux."""
    # os.system("sync ; sudo /bin/sh -c 'echo 3 > /proc/sys/vm/drop_caches'")
    pass


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('---clear-cache', action="store_true")
    parser.add_argument('-n', type=int, default=3)
    parser.add_argument('filename')

    args = parser.parse_args()

    counts = defaultdict()

    if args.clear_cache:
        do_clear_cache = True
    else:
        do_clear_cache = False

    filename = args.filename
    for _ in range(args.n):
        for func in (f
                     for n, f in list(globals().items())
                     if n.endswith('count') and hasattr(f, '__call__')):
            if do_clear_cache:
                clear_cache()
            start_time = timer()
            # http://norvig.com/big.txt
            if filename == 'big.txt':
                assert func(filename) == 128457  # 128457 1095695 6488666 big.txt
            else:
                func(filename)
            counts[func].append(timer() - start_time)

    timings = {}
    for key, vals in list(counts.items()):
        timings[key.__name__] = sum(vals) / float(len(vals)), min(vals)
    width = max(len(n) for n in timings) + 1
    print(("%s %s %s %s" % (
        "function".ljust(width),
        "average, s".rjust(15),
        "min, s".rjust(15),
        "ratio".rjust(15))))
    absmin_ = min(x[1] for x in list(timings.values()))
    for name, (av, min_) in sorted(list(timings.items()), key=lambda x: x[1][1]):
        print(f"{name.ljust(width)} {av:15.4f} {min_:15.4f} {min_ / absmin_:15.4f}")


if __name__ == '__main__':
    main()

# function      average, s  min, s  ratio
# wccount            0.005  0.0042   1.00
# bufcount          0.0081  0.0081   1.91
# fadvcount         0.0094  0.0091   2.13
# opcount            0.018   0.015   3.42
# simplecount        0.019   0.016   3.66
# kylecount          0.019   0.017   4.03
# mapcount           0.027   0.021   4.97
# itercount          0.044   0.031   7.21

# python3.1 ginstrom.py
# function      average, s  min, s  ratio
# wccount           0.0049  0.0046   1.00
# itercount          0.021    0.02   4.47
# mapcount           0.023   0.023   5.09
# bufcount           0.034   0.032   7.02
# opcount            0.043   0.043   9.46
# simplecount         0.05   0.046  10.20
# kylecount           0.05    0.05  10.95

# python ginstrom.py /big/mkv/file
# function      average, s  min, s  ratio
# wccount             0.51    0.49   1.00
# opcount              1.8     1.8   3.58
# simplecount          1.8     1.8   3.66
# kylecount            1.9     1.9   3.75
# mapcount              19       2   4.01
# fadvcount            2.3     2.2   4.52
# bufcount             2.3     2.2   4.52
# wc /big/mkv/file
# 7137518   40523351 1836139137 /big/mkv/file

# with --clear-cache
# function      average, s  min, s  ratio
# simplecount         0.06   0.057   1.00
# opcount            0.067   0.057   1.00
# kylecount          0.057   0.057   1.00
# itercount           0.06   0.058   1.02
# mapcount           0.059   0.058   1.02
# fadvcount          0.064   0.058   1.02
# bufcount            0.07   0.062   1.09
# wccount            0.072   0.065   1.15

# python3.1 with --clear-cache
# function      average, s  min, s  ratio
# itercount          0.061   0.057   1.00
# simplecount        0.069   0.061   1.06
# mapcount           0.062   0.061   1.07
# wccount            0.067   0.064   1.11
# kylecount          0.067   0.065   1.12
# opcount            0.072   0.067   1.17
# bufcount           0.083   0.073   1.27
