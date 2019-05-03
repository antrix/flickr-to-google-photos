#!/usr/bin/env python
import json
import os
import re
import sys
import logging

from exif import GeoHelper
from flickr import FlickrHelper

class ExifRestorer:
    def __init__(self, flickr):
        self.flickr = flickr

    def update_all_exif(self):
        albums = self.flickr.get_all_albums()
        count, total = 1, len(albums)
        
        for flickr_album in albums:
            logging.info("Going to update exif for all photos in album: '{}' [{}/{}]".format(flickr_album["title"], count, total))
            for flickr_photo_id in flickr_album["photos"]:
                if self.flickr.is_photo_valid(flickr_photo_id):
                    self.update_exif(flickr_photo_id)
                else:
                    logging.warning("Skipping invalid photo id: {}".format(flickr_photo_id))
            count += 1

    def update_exif(self, flickr_photo_id):
        logging.debug("Going to update exif for photo: '%s'" % flickr_photo_id)
        geo = self.flickr.get_photo_lat_lon(flickr_photo_id)
        if geo:
            gh = GeoHelper(geo, self.flickr.get_photo_fspath(flickr_photo_id))
            gh.update_geo_exif()

def main(config):
    flickr = FlickrHelper(
        config["flickr_photo_dir"],
        config["flickr_photo_json_dir"],
        config["flickr_albums_json"]
    )

    restorer = ExifRestorer(flickr)    
    restorer.update_all_exif()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='exif-restore.log',
                    filemode='w')
    
    # define a Handler which writes INFO messages or higher to the sys.stderr
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    if len(sys.argv) != 2:
        logging.error("Missing argument: config.json")
        exit(1)

    with open(sys.argv[1], "r") as f:
        config = json.load(f)
        main(config)
