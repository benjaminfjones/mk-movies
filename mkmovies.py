"""
mkmovies.py
===========

This program searches the current diectory for 'jpg' images, groups them by
temporal locality (see 'MAX_GAP'), and produces movies from the groups.

For example, if the current directory contains the following files:

    % ls -l --full-time
    -rw-r--r-- 1 bj bj  51912 2016-05-09 09:57:53.348306617 -0700 hummingbird2016050909575301.jpg
    -rw-r--r-- 1 bj bj  50507 2016-05-09 09:57:53.541637925 -0700 hummingbird2016050909575302.jpg
    -rw-r--r-- 1 bj bj  50263 2016-05-09 09:57:53.848301379 -0700 hummingbird2016050909575303.jpg
    -rw-r--r-- 1 bj bj  57534 2016-05-09 09:58:08.934810045 -0700 hummingbird2016050909580804.jpg
    -rw-r--r-- 1 bj bj  54861 2016-05-09 09:59:35.350568588 -0700 hummingbird2016050909593501.jpg

The program will produce two movies, 'movie_001.mp4' and 'movie_002.mp4' where the
first is made up of the first four images and the second is made up of only the last image
(since it's timestamp is more than 'MAX_GAP' from the last of the first four.

Dependencies
------------

    - ffmpeg
    - GNU mktemp
    - Python 2.7.x or Python 3.x
"""

from __future__ import absolute_import, division, print_function

from contextlib import contextmanager
import datetime
import os
import re
import subprocess
import sys

### GLOBALS

MAX_GAP = 30                         # maximum gap in time between frames
FFMPEG_RATE = 4                      # number of frames / second
FFMPEG_OPTS = '-r 4'                 # codec and rate options for ffmpeg
INPUT_FMT = '06d'                    # format of tmp links to image files
INPUT_PAT = re.compile(r'.+\.jpg$')  # regex pattern matching input images
OUTPUT_FMT = '03d'                   # format for number part of output file names


def modification_time(filename):
    """
    Get modification time of the given filename (string) as a 'datetime'
    object
    """
    mtime = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(mtime)

def compute_gap(time0, time1):
    """
    Compute the time difference between the given datetime objects in
    seconds (rounded to the nearest second.
    """
    tdelta = abs(time1 - time0)
    return round(tdelta.total_seconds())

def get_files():
    """
    Return an association list (:: [(time, filepath)]) of the files in the
    current directory along with their modification times
    """
    return [(modification_time(f), f) for f in os.listdir('.')
            if INPUT_PAT.match(f)]

def group_by_mtime(alist, gap):
    """
    Take an association list of (mtime, filename) and return a grouped list of
    lists where the entries in each group are sorted by mtime and have
    consecutive mtimes no more than 'gap' (seconds :: int) apart.
    """
    outlist = []
    alist = sorted(alist, key=lambda x: x[0])
    for nextitem in alist:
        if len(outlist) == 0:
            outlist = [[nextitem]]
        else:
            lastgroup = outlist[-1]
            assert isinstance(lastgroup, list) and len(lastgroup) > 0
            lastitem = lastgroup[-1]
            assert isinstance(lastitem, tuple) and len(lastitem) == 2
            if compute_gap(lastitem[0], nextitem[0]) >= gap:
                # make a new group
                outlist = outlist + [[nextitem]]
            else:
                # add 'nextitem' to most recent group
                lastgroup = outlist[-1]
                lastgroup.extend([nextitem])
    return outlist

@contextmanager
def sequential_links(fpaths):
    """
    Context manager that takes a list of (absolute) filepaths and creates
    a temp dir containing symbolic links to the filepaths whose names are
    sequentially increasing non-negative integers.

    The location of the tmp directory is yielded.
    """
    mkdir_cmd = "mktemp -d -p /tmp make_movie.XXXXXX".split()
    try:
        tmp = subprocess.check_output(mkdir_cmd).decode('utf-8').strip()
    except subprocess.CalledProcessError as exc:
        msg = "ERROR: failed to create tmp dir. (rc = {})"
        print(msg.format(exc.returncode))
        sys.exit(1)

    print("Made tmp dir {0}".format(tmp))
    for idx, fpath in enumerate(fpaths):
        link = tmp + "/{0:" + INPUT_FMT + "}.jpg"
        link = link.format(idx)
        try:
            subprocess.call(["ln", "-s", fpath, link])
        except subprocess.CalledProcessError as exc:
            msg = "ERROR: failed to link file {} -> {}. (rc = {})"
            print(msg.format(fpath, link, exc.returncode))
            sys.exit(1)

    link_list = subprocess.check_output(['ls', '-l', tmp]).decode('utf-8')
    print(link_list)
    yield tmp

    # cleanup
    print("Cleaning up tmp dir")
    subprocess.call(["rm", "-rf", tmp])

def assemble_movie(fpaths, name):
    """
    Use 'ffmpeg' to combine the image files given in 'fpaths' into an mp4 movie
    called 'name' in the current directory.
    """
    in_files = [x for sublist in [["-i", f] for f in fpaths]
                for x in sublist
                if x[-3:] == "jpg"]
    if len(in_files) == 0:
        print("Abort: no jpg files found in group!")
        return 1

    cwd = os.getcwd()
    full_files = [cwd + "/" + f for f in in_files]
    with sequential_links(full_files) as tmp:
        args = "ffmpeg -f image2 -i {t}/%" + INPUT_FMT + ".jpg -r {r} {n}.mp4"
        args = args.format(t=tmp, r=FFMPEG_RATE, n=name)
        print("Assembling movie {n}.mp4 ...".format(n=name))
        print("Running: " + args)
        ret = subprocess.call(args.split())

    return ret

def main():
    """
    Main entry point of the script.
    """
    grps = group_by_mtime(get_files(), MAX_GAP)
    for idx, grp in enumerate(grps):
        print("Group {}, size {}".format(idx, len(grp)))
        mname = ("movie_{:" + OUTPUT_FMT + "}").format(idx)
        ret = assemble_movie([y[1] for y in grp], mname)
        print("rc = {}".format(ret))

if __name__ == '__main__':
    main()
