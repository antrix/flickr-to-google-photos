#!/usr/bin/env python
import json
import os
import re
import logging

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def build_fs_cache(root_folder):
    cache = {}
    count = 0
    ID_PATTERN_1 = re.compile(r".*_(\d+)_o.(?:jpg|png|gif)$")
    ID_PATTERN_2 = re.compile(r"(\d+)_.*_o.(?:jpg|png|gif)$")

    for dirpath, dirnames, filenames in os.walk(root_folder):
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
    def __init__(self, flickr_albums_json, fs_cache, session):
        self.flickr_albums_json = flickr_albums_json
        self.fs_cache = fs_cache
        self.session = session

    def upload_all_albums(self):
        with open(self.flickr_albums_json, "r") as json_file:
            flickr_albums = json.load(json_file)
            for album in flickr_albums["albums"]:
                self.upload_album(album)

    def upload_album(self, flickr_album):
        # get or create google album
        # Add enrichment as description.
        # Use google album's mediaItemsCount to decide where to resume
        # for each photo:
        #   1. upload the cover photo with description and add to album
        #   2. upload the rest of the photos with description and add to album
        logging.info("Going to upload: '%s'" % flickr_album["title"])

        album = self.get_or_create_album(flickr_album["title"])

        if not album or not album["title"]:
            logging.error("Failed to create album. Exiting.")
            raise SystemExit

        logging.info("Starting upload of photos to: '%s'" % album["title"])

        for flickr_photo_id in flickr_album["photos"]:
            self.upload_photo(flickr_photo_id, album["id"])

    def get_or_create_album(self, album_title):

        params = {'excludeNonAppCreatedData': True}

        while True:
            albums = self.session.get('https://photoslibrary.googleapis.com/v1/albums', params=params).json()
            logging.debug("Retrieved album list: %s" % albums)
            for album in albums.get("albums", []):
                if album["title"].lower() == album_title.lower():
                    logging.debug("Found existing album: %s" % album)
                    return album

            if 'nextPageToken' in albums:
                params["pageToken"] = albums["nextPageToken"]
            else:
                break

        # No albums found. Create new.
        logging.info("Creating new album: '%s'" % album_title)
        r = self.session.post('https://photoslibrary.googleapis.com/v1/albums', json={"album": {"title": album_title}})
        logging.debug("Create album response: {}".format(r.text))
        r.raise_for_status()
        return r.json()

    def upload_photo(self, flickr_photo_id, google_album_id):
        flickr_photo_fspath = self.fs_cache[flickr_photo_id]
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
                    "description": "TODO: add real description",
                    "simpleMediaItem": {"uploadToken": upload_token}
                }
            ]}

        self.session.post("https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate", json=create_request_body).raise_for_status()


def main():
    # Parse all folders and create a dict of id -> fs path
    fs_cache = build_fs_cache("c:\\media\\flickr-restore\\test-data")

    session = get_authorized_session("c:\\media\\flickr-restore\\credentials.json", "c:\\media\\flickr-restore\\auth-token.json")

    uploader = PhotoUploader("c:\\media\\flickr-restore\\test-albums.json", fs_cache, session)
    uploader.upload_all_albums()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
