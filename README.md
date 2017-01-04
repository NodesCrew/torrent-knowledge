# Torrent Knowledge


## Command line arguments
<pre>usage: main.py [-h] [-v] [-t]

Run torrent-knowledge cli

optional arguments:

  -h, --help        show this help message and exit
  -v, --verbose     increase log verbosity via -vvv
  -t, --train-mode  update features frequency from dataset
 </pre>


## Train
<pre>
user@mbpro$ wc -l settings/torrents_masks.json
     121 settings/torrents_masks.json

user@mbpro$ wc -l datasets/torrents.csv
 6808916 datasets/torrents.csv

user@mbpro$ ./main.py -vvv -t
 ...
[log] root - DEBUG - Read Lines per second: 6090.1864
[log] root - DEBUG - Complete in 1745.80


user@mbpro$ wc -l /tmp/torrents.json
  165976 /tmp/torrents.json

user@mbpro$ ./main.py -vvv
...
[log] root - DEBUG - Read Lines per second: 42184.1250
[log] root - root - DEBUG - Complete in 252.09

user@mbpro$ wc -l /tmp/torrents.json
  161551 /tmp/torrents.json

user@mbpro$ wc -l settings/torrents_masks.json
   18666 settings/torrents_masks.json
</pre>