import logging
import math
import piexif

class GeoHelper:
    def __init__(self, flickr_geo_json, photo_fspath):
        self.latitude = int(flickr_geo_json["latitude"])
        self.longitude = int(flickr_geo_json["longitude"])
        self.photo_fspath = photo_fspath

    def update_geo_exif(self):        
        latitude = self.latitude / 1000000  # Flickr geo json doesn't have decimals!
        longitude = self.longitude / 1000000  # Flickr geo json doesn't have decimals!

        try:
            exif_dict = piexif.load(self.photo_fspath)
            if exif_dict.get("GPS"):
                logging.debug("Skipping photo with pre-existing GPS Exif tag: {}".format(self.photo_fspath))
                return
            
            exif_dict["GPS"] = _create_gps_tag(latitude, longitude)
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, self.photo_fspath)
        except Exception as err:
            logging.warn("Could not set exif for file ({}): {}".format(self.photo_fspath, err))

def _create_gps_tag(latitude, longitude):
    gps = {}
    gps[piexif.GPSIFD.GPSLatitudeRef] = 'S' if latitude < 0 else 'N'
    gps[piexif.GPSIFD.GPSLatitude] = _deg_to_dms(latitude)
    gps[piexif.GPSIFD.GPSLongitudeRef] = 'W' if longitude < 0 else 'E'
    gps[piexif.GPSIFD.GPSLongitude] = _deg_to_dms(longitude)
    logging.debug("converted ({}, {}) to gps: {}".format(latitude, longitude, gps))
    return gps

def _deg_to_dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    dms = [(abs(d), 1), (m, 1), (round(sd * 1000), 1000)]
    return dms

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    assert _create_gps_tag(1.272, 103.81153) == {1: 'N', 2: [(1, 1), (16, 1), (19200, 1000)], 3: 'E', 4: [(103, 1), (48, 1), (41508, 1000)]}
    assert _create_gps_tag(-33.610045, -62.753906) == {1: 'S', 2: [(33, 1), (36, 1), (36162, 1000)], 3: 'W', 4: [(62, 1), (45, 1), (14062, 1000)]}
    assert _create_gps_tag(40.731421, -74.172821) == {1: 'N', 2: [(40, 1), (43, 1), (53116, 1000)], 3: 'W', 4: [(74, 1), (10, 1), (22156, 1000)]}
