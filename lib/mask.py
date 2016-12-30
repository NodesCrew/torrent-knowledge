# coding: utf-8
import os
import re
import json
import functools


class MaskParser(object):
    __slots__ = ("audio_codecs",
                 "audio_channels",
                 "video_codecs",
                 "video_sources",
                 "video_resolutions",
                 "release_props",
                 "release_groups",

                 "torrents_masks",
                 "_train_mode",
                 "_trans_table",
                 "_ch_set",
                 "_ch_punkt",
                 "_ch_spaces",
                 "_ch_blacklist",
                 "_ch_whitelist",
                 "_matchers",
                 "_mask_matchers"
                 )

    def __init__(self,
                 chars_punkt=None,
                 chars_spaces=None,
                 chars_whitelist=None,
                 chars_blacklist=None,

                 train_mode=None
                 ):
        self._ch_punkt = chars_punkt or ":,!?"
        self._ch_spaces = chars_spaces or ".+-~_–\/=| "
        self._ch_blacklist = chars_blacklist or '*"\''
        self._ch_whitelist = chars_whitelist or ""

        self._train_mode = train_mode

        self._matchers = list()
        self._mask_matchers = dict()

        self._trans_table = str.maketrans(
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789" +
            self._ch_punkt +
            self._ch_spaces,

            "aaaaaaaaaaaaaaaaaaaaaaaaaa"
            "9999999999" +
            "p" * len(self._ch_punkt) +
            "_" * len(self._ch_spaces)
        )

        self._ch_set = 'ap_9%s' % self._ch_whitelist

        for name in self.__slots__:
            if not name.startswith("_"):
                self._read_values(name)

    def create_regexps(self, **extra):
        """ Create regular expressions """

        def _enum_group(name):
            """ Create regular expression """
            return "(?P<{name}>{choices})".format(
                name=name,
                choices="|".join(
                    sorted(set(re.escape(x.lower())
                               for x in getattr(self, name)))
                )
            )

        pattern_vars = {
            **dict(
                year="(?P<year>19\d\d|20\d\d)",
                space="(?:[\s]?)",
                series_name="(?P<series_name>[\w\d\s]*?[\w\d])",
                episode_name="(?P<episode_name>.*?)",
                season_no="(?P<season_no>\d{1,2})",
                episode_no="(?P<episode_no>\d{1,2})",

                audio_codec=_enum_group("audio_codecs"),
                audio_channel=_enum_group("audio_channels"),
                video_codec=_enum_group("video_codecs"),
                video_source=_enum_group("video_sources"),
                video_resolution=_enum_group("video_resolutions"),

                release_group=_enum_group("release_groups"),
            ),
            **extra
        }

        for options in self.torrents_masks.values():
            try:
                samples = options["samples"]
                template = options["pattern"]
            except KeyError:
                continue

            pattern = template.format(*("{%d}" for d in range(0, 10)),
                                      **pattern_vars)

            try:
                matcher = re.compile(pattern)
            except:
                print("Unable to compile template\n{}\npattern\n{}\n"
                      .format(template, pattern))
                raise

            for sample in samples:
                sample_clean = self.clean_title(sample)
                try:
                    matcher.search(sample_clean).groups()
                except:
                    print(sample_clean, " -> ",
                          matcher.pattern, " -> ",
                          matcher.search(sample_clean))
                    raise
            self._matchers.append(matcher)

    @functools.lru_cache(maxsize=2048)
    def mask_title(self, title):
        """ Create mask from title """
        return self.clean_title(title).translate(self._trans_table)

    @functools.lru_cache(maxsize=2048)
    def clean_title(self, title):
        """ Make title clean """
        return " ".join(
            c0 for c0 in (
                "".join(
                    c1 for c1 in (
                        " " if c2 in self._ch_spaces else c2
                        for c2 in title.lower().strip()
                    ) if c1 not in self._ch_blacklist
                ).strip().split()
            ) if c0
        )

    @functools.lru_cache(maxsize=2048)
    def parse_title(self, title):
        """ Parse title """
        t_mask = self.mask_title(title)
        t_clean = self.clean_title(title)

        if t_mask not in self._mask_matchers:
            self._mask_matchers[t_mask] = list()

            for matcher in self._matchers:
                data = matcher.search(t_clean)
                if data:
                    self._mask_matchers[t_mask].append(matcher)
                    self._handle_match(data)
                    return data.groupdict()

        for matcher in self._mask_matchers[t_mask]:
            data = matcher.search(t_clean)
            if data:
                self._handle_match(data)
                return data.groupdict()

    def _handle_match(self, match):
        """ Update usage statistics """
        for key, value in match.groupdict().items():
            attr = getattr(self, key, None)
            if attr and value in attr:
                attr[value]["freq"] = (attr[value].get("freq") or 0) + 1

    def _read_values(self, name):
        """ Read settings into object properties """
        file_path = "settings/{name}.json".format(name=name)
        assert name in self.__slots__
        assert os.path.exists(file_path), "Bad file: {name}".format(name=name)

        with open(file_path) as f:
            try:
                setattr(self, name, json.load(f))
            except json.decoder.JSONDecodeError:
                print("Unable to parse {file_path}: bad json".format(
                      file_path=file_path))
                exit(-1)

