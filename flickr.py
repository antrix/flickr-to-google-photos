import json
import os
import re
import logging

class FlickrHelper:
    def __init__(self, flickr_photo_dir, flickr_photo_json_dir, flickr_albums_json=None):
        self.flickr_photo_dir = flickr_photo_dir
        self.flickr_photo_json_dir = flickr_photo_json_dir

        self.flickr_albums_json = flickr_albums_json if flickr_albums_json else os.path.join(flickr_photo_json_dir, "albums.json")

        self.fs_cache = self._build_fs_cache()

    def _build_fs_cache(self):
        cache = {}
        count = 0
        ID_PATTERN_1 = re.compile(r".*_(\d+)_o.(?:jpg|png|gif)$")
        ID_PATTERN_2 = re.compile(r"(\d+)_.*_o.(?:jpg|png|gif)$")

        for dirpath, _, filenames in os.walk(self.flickr_photo_dir):
            for name in filenames:
                count = count + 1
                file_path = os.path.join(dirpath, name)

                for pattern in (ID_PATTERN_1, ID_PATTERN_2):
                    match = re.match(pattern, name.lower())
                    if match and match.lastindex == 1:
                        cache[match.group(1)] = file_path
                        break
                else:
                    logging.warn("Could not process: %s" % file_path)

        logging.debug("Processed %d files" % count)
        logging.debug("Parsed %d photo identifiers" % len(cache))
        return cache

    def get_all_albums(self):
        with open(self.flickr_albums_json, "r") as json_file:
            flickr_albums = json.load(json_file)
            return flickr_albums["albums"]

    def get_photo_fspath(self, photo_id):
        return self.fs_cache[photo_id]

    def get_photo_description(self, photo_id):
        photo_json = self.get_photo_json(photo_id)
        description = "\n\n".join(filter(len, (photo_json["name"], photo_json["description"])))
        return description

    def get_photo_lat_lon(self, photo_id):
        photo_json = self.get_photo_json(photo_id)
        geo = photo_json["geo"]
        return geo

    def get_photo_json(self, photo_id):
        photo_json_file = os.path.join(self.flickr_photo_json_dir, "photo_%s.json" % photo_id)
        try:
            with open(photo_json_file, "r") as json_file:
                photo_json = json.load(json_file)
                return photo_json
        except Exception as err:
            logging.warn("Could not find photo json file: {}".format(photo_json_file))
            logging.warn("Exception was: {}".format(err))
            raise err
