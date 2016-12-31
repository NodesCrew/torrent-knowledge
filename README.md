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

user@mbpro$ wc -l datasets/torrents_titles.csv
 6596398 datasets/torrents_titles.csv

user@mbpro$ ./main.py -vvv -t
 ...

user@mbpro$ wc -l /tmp/torrents.json
  165976 /tmp/torrents.json

user@mbpro$ ./main.py -vvv
...
[log] root - DEBUG - Read Lines per second: 41899.2952
[log] root - DEBUG - Complete in 314.00

user@mbpro$ wc -l /tmp/torrents.json
  161551 /tmp/torrents.json

user@mbpro$ wc -l settings/torrents_masks.json
   18666 settings/torrents_masks.json
</pre>