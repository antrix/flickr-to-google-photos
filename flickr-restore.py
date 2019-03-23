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
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes=scopes)
        creds = flow.run_console()

    session = AuthorizedSession(creds)
    save_credentials(creds, auth_token_file)
    return session

def get_or_create_album(album_title, session):
    
    params = {'excludeNonAppCreatedData': True}

    while True:
        albums = session.get('https://photoslibrary.googleapis.com/v1/albums', params=params).json()
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
    
    
def upload_album(flickr_album, fs_cache, session):
    # get or create google album
    # Add enrichment as description.
    # Use google album's mediaItemsCount to decide where to resume
    # for each photo:
    #   1. upload the cover photo with description and add to album
    #   2. upload the rest of the photos with description and add to album
    logging.info("Going to upload: '%s'" % flickr_album["title"])
    
    album = get_or_create_album(flickr_album["title"], session)

    if not album or not album["title"]:
        logging.error("Failed to create album. Exiting.")
        raise SystemExit

    logging.info("Starting upload of photos to: '%s'" % album["title"])


def upload_all_albums(flickr_albums_json, fs_cache, session):
    with open(flickr_albums_json, "r") as json_file:
        flickr_albums = json.load(json_file)
        for album in flickr_albums["albums"]:
            upload_album(album, fs_cache, session)


def main():
    # Parse all folders and create a dict of id -> fs path
    fs_cache = build_fs_cache("c:\\media\\flickr-restore\\test-data")

    session = get_authorized_session("c:\\media\\flickr-restore\\credentials.json", "c:\\media\\flickr-restore\\auth-token.json")

    upload_all_albums(
        "c:\\media\\flickr-restore\\test-albums.json", fs_cache, session)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
