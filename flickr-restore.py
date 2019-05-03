#!/usr/bin/env python
import json
import os
import re
import sys
import logging

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from flickr import FlickrHelper

def save_credentials(creds, auth_token_file):
    creds_dict = {
        'refresh_token': creds.refresh_token,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret
    }

    with open(auth_token_file, 'w', encoding='utf-8') as f:
        json.dump(creds_dict, f)


def get_authorized_session(client_secrets_file, auth_token_file):

    scopes = ['https://www.googleapis.com/auth/photoslibrary']

    creds = None
    try:
        creds = Credentials.from_authorized_user_file(auth_token_file, scopes)
    except Exception as err:
        logging.debug("Error opening auth token file: {}".format(err))

    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes=scopes)
        creds = flow.run_console()

    session = AuthorizedSession(creds)
    save_credentials(creds, auth_token_file)
    return session


class PhotoUploader:
    def __init__(self, flickr, session):
        self.flickr = flickr
        self.session = session

    def upload_all_albums(self):
        albums = self.flickr.get_all_albums()
        count, total = 1, len(albums)
        for album in albums:
            logging.info("Going to upload: '{}' [{}/{}]".format(album["title"], count, total))
            self.upload_album(album)
            count += 1
            
    def upload_album(self, flickr_album):
        album = self.get_or_create_album(flickr_album)

        if not album or not album["title"]:
            logging.error("Failed to create album. Exiting.")
            raise SystemExit

        logging.info("Starting upload of photos to: '%s'" % album["title"])

        cover_photo_id = flickr_album["cover_photo"].rpartition("/")
        if cover_photo_id[1] == "/":
            cover_photo_id = cover_photo_id[2]
        else:
            cover_photo_id = None

        for flickr_photo_id in flickr_album["photos"]:
            if self.flickr.is_photo_valid(flickr_photo_id):
                self.upload_photo(flickr_photo_id, album["id"], flickr_photo_id == cover_photo_id)
            else:
                logging.warning("Skipping invalid photo id: {}".format(flickr_photo_id))

    def get_or_create_album(self, flickr_album):

        params = {'excludeNonAppCreatedData': True}

        while True:
            albums = self.session.get('https://photoslibrary.googleapis.com/v1/albums', params=params).json()
            logging.debug("Retrieved album list: %s" % albums)
            for album in albums.get("albums", []):
                if album["title"].lower() == flickr_album["title"].lower():
                    logging.info("Found existing album: %s" % album)
                    return album

            if 'nextPageToken' in albums:
                params["pageToken"] = albums["nextPageToken"]
            else:
                break

        # No albums found. Create new.
        logging.info("Creating new album: '%s'" % flickr_album["title"])
        r = self.session.post("https://photoslibrary.googleapis.com/v1/albums", json={"album": {"title": flickr_album["title"]}})
        logging.debug("Create album response: {}".format(r.text))
        r.raise_for_status()
        google_album = r.json()

        if flickr_album["description"]:
            self.set_album_description(google_album["id"], flickr_album["description"])

        return google_album

    def set_album_description(self, google_album_id, description):
        enrich_req_body = {
            "newEnrichmentItem": {
                "textEnrichment": {
                    "text": description
                }
            },
            "albumPosition": {
                "position": "FIRST_IN_ALBUM"
            }
        }
        r = self.session.post("https://photoslibrary.googleapis.com/v1/albums/%s:addEnrichment" % google_album_id, json=enrich_req_body)
        logging.debug("Enrich album response: {}".format(r.text))

    def upload_photo(self, flickr_photo_id, google_album_id, is_cover_photo):
        flickr_photo_fspath = self.flickr.get_photo_fspath(flickr_photo_id)
        logging.info("Uploading photo: '%s: %s'" % (flickr_photo_id, flickr_photo_fspath))

        upload_token = None
        with open(flickr_photo_fspath, 'rb') as f:
            headers = {
                "X-Goog-Upload-File-Name": os.path.basename(flickr_photo_fspath),
                "X-Goog-Upload-Protocol": "raw"
            }
            resp = self.session.post("https://photoslibrary.googleapis.com/v1/uploads", data=f, headers=headers)
            resp.raise_for_status()
            upload_token = resp.text
            logging.debug("Received upload token: %s" % upload_token)

        create_request_body = {
            "albumId": google_album_id,
            "newMediaItems": [
                {
                    "description": self.flickr.get_photo_description(flickr_photo_id),
                    "simpleMediaItem": {"uploadToken": upload_token}
                }
            ]}

        if is_cover_photo:
            create_request_body["albumPosition"] = {"position": "FIRST_IN_ALBUM"}

        self.session.post("https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate", json=create_request_body).raise_for_status()


def main(config):
    flickr = FlickrHelper(
        config["flickr_photo_dir"],
        config["flickr_photo_json_dir"],
        config["flickr_albums_json"]
    )

    session = get_authorized_session(
        config["client_secrets_file"],
        config["auth_token_file"]
    )

    uploader = PhotoUploader(flickr, session)
    uploader.upload_all_albums()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='flickr-restore.log',
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
