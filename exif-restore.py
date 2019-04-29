#!/usr/bin/env python
import json
import os
import re
import logging

from exif import GeoHelper
from flickr import FlickrHelper

class ExifRestorer:
    def __init__(self, flickr):
        self.flickr = flickr

    def update_all_exif(self):
        for flickr_album in self.flickr.get_all_albums():
            logging.info("Going to update exif for all photos in album: '%s'" % flickr_album["title"])
            for flickr_photo_id in flickr_album["photos"]:
                if self.flickr.is_photo_valid(flickr_photo_id):
                    self.update_exif(flickr_photo_id)
                else:
                    logging.warning("Skipping invalid photo id: {}".format(flickr_photo_id))

    def update_exif(self, flickr_photo_id):
        logging.debug("Going to update exif for photo: '%s'" % flickr_photo_id)
        geo = self.flickr.get_photo_lat_lon(flickr_photo_id)
        if geo:
            gh = GeoHelper(geo, self.flickr.get_photo_fspath(flickr_photo_id))
            gh.update_geo_exif()

def main():
    flickr = FlickrHelper(
                          "c:\\media\\flickr-restore\\flickr-photos"
                          #"c:\\media\\flickr-restore\\test-data"
                          ,"c:\\media\\flickr-restore\\72157698068208210_90be50b743b6_part1"
                          ,"c:\\media\\flickr-restore\\72157698068208210_90be50b743b6_part1\\albums.json" 
                          #,"c:\\media\\flickr-restore\\test-albums.json"
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
    
    main()
