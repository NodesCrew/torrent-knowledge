# coding: utf-8
import os
import re
import json
import collections

from functools import lru_cache


def jsonify(obj):
    if isinstance(obj, (set,)):
        return list(sorted(obj))
    if isinstance(obj, (collections.Counter,)):
        return sorted(
            {mask: count for mask, count in obj.items() if count > 1}.items(),
            key=lambda x: x[1],
            reverse=True
        )
    return obj


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

        self.torrents_masks = dict()

        self._ch_punkt = chars_punkt or ":,!?"
        self._ch_spaces = chars_spaces or ".+-~_–\/=| "
        self._ch_blacklist = chars_blacklist or '*"\''
        self._ch_whitelist = chars_whitelist or ""

        self._train_mode = train_mode

        self._matchers = dict()
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
        def _enum(name):
            return self._create_re_group(name[:-1], getattr(self, name))

        _vars = dict(
                year="(?P<year>19\d\d|20\d\d)",
                space="(?:[\s]?)",
                series_name="(?P<series_name>[\w\d\s]*?[\w\d])",
                episode_name="(?P<episode_name>.*?)",
                season_no="(?P<season_no>\d{1,2})",
                episode_no="(?P<episode_no>\d{1,2})",

                audio_codec=_enum("audio_codecs"),
                audio_channel=_enum("audio_channels"),
                video_codec=_enum("video_codecs"),
                video_source=_enum("video_sources"),
                video_resolution=_enum("video_resolutions"),

                release_group=_enum("release_groups"),
        )
        _vars.update(extra)

        for m_id, options in self.torrents_masks.items():
            try:
                samples = options["samples"]
                template = options["pattern"]
            except KeyError:
                continue

            pattern = template.format(**_vars)

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
            self._matchers[matcher] = m_id
            for mask in options.get("masks") or ():
                try:
                    self._mask_matchers[mask]
                except KeyError:
                    self._mask_matchers[mask] = []
                self._mask_matchers[mask].append(matcher)

    @lru_cache()
    def mask_title(self, title):
        """ Create mask from title """
        return self.clean_title(title).translate(self._trans_table)

    @lru_cache()
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

    @lru_cache()
    def parse_title(self, title):
        """ Parse title """
        t_mask = self.mask_title(title)
        if t_mask not in self._mask_matchers:
            return None

        t_clean = self.clean_title(title)
        for matcher in self._mask_matchers[t_mask]:
            data = matcher.search(t_clean)
            if data:
                return data.groupdict()

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

    def _create_re_group(self, name, values):
        """ Create regular expression """
        print({
            value: info
            for value, info in
            sorted(values.items(),
                   key=lambda x: x[1].get("freq") or 0,
                     reverse=True)
            if (info.get("freq") or 0) > 0
        })
        return "(?P<{name}>{choices})".format(
            name=name,
            choices="|".join(
                re.escape(value.lower()) for value, info in
                sorted(
                    values.items(),
                    key=lambda x: x[1].get("freq") or 0, reverse=True
                )
                if (info.get("freq") or 0) > 0
            )
        )


class MaskTrainParser(MaskParser):
    __slots__ = MaskParser.__slots__

    def create_regexps(self, **extra):
        """ Create matcher objects """
        super().create_regexps(**extra)

        for m_id in self.torrents_masks:
            self.torrents_masks[m_id].update({
                "freq": 0, "masks": collections.Counter()})

    @lru_cache()
    def parse_title(self, title):
        """ Parse title """
        t_mask = self.mask_title(title)
        t_clean = self.clean_title(title)

        candidates = []
        if t_mask not in self._mask_matchers:
            self._mask_matchers[t_mask] = []

            for matcher, m_id in self._matchers.items():
                data = matcher.search(t_clean)
                if data:
                    self._mask_matchers[t_mask].append(matcher)
                    self._handle_match(data)
                    self.torrents_masks[m_id]["freq"] += 1
                    self.torrents_masks[m_id]["masks"][t_mask] += 1
                    candidates.append(data.groupdict())
        else:
            for matcher in self._mask_matchers[t_mask]:
                data = matcher.search(t_clean)
                if data:
                    m_id = self._matchers[matcher]
                    self._handle_match(data)
                    self.torrents_masks[m_id]["freq"] += 1
                    self.torrents_masks[m_id]["masks"][t_mask] += 1
                    candidates.append(data.groupdict())

        if candidates:
            # Todo: return best result, not first
            return candidates[0]

    def update_stats(self):
        """ Save features and masks statistics """
        for name in ("audio_codecs", "audio_channels", "video_codecs",
                     "video_sources", "video_resolutions", "release_props",
                     "release_groups"):
            file_path = "settings/{name}.json".format(name=name)
            assert os.path.exists(file_path)

            with open(file_path, "w+") as f:
                json.dump(getattr(self, name), f, indent=4, sort_keys=True)

        def clean_options(options):
            if not options.get("masks"):
                return options
            options["masks"] = collections.OrderedDict(
                sorted(
                    (
                        (mask, count)
                        for mask, count in options["masks"].items()
                        if count > 1
                    ),
                    key=lambda x: x[1],
                    reverse=True
                )
            )
            return options

        with open("settings/torrents_masks.json", "w+") as f:
            json.dump(
                {k: clean_options(v) for k, v in self.torrents_masks.items()},
                f,
                default=jsonify,
                indent=4
            )

    def _handle_match(self, match):
        """ Update features statistics """
        for key, value in match.groupdict().items():
            attr = getattr(self, key, None)
            if attr and value in attr:
                attr[value]["freq"] = (attr[value].get("freq") or 0) + 1

    def _create_re_group(self, name, values):
        """ Create regular expression """
        return "(?P<{name}>{choices})".format(
            name=name,
            choices="|".join(
                sorted(
                    set(re.escape(x.lower()) for x in values)
                )
            )
        )