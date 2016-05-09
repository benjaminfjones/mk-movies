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
