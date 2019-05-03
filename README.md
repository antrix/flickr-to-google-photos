# Flickr to Google Photos

This repo contains couple of utilities that import albums from Flickr into Google Photos.

Flickr provides a complete data dump through their [Request my Flickr Data][0] option in account settings. 
This data dump includes all the photos and videos that you ever uploaded to Flickr, as well as lots of json files 
describing all of your albums, comments, and other activity on Flickr.

Google Photos provides a [basic API][1] to create albums and upload photos. 

The scripts in this repo help achieve the following:

* Update the EXIF metadata in photo files with the geo-tagging information in the Flickr json metadata. This enables Google Photos to correctly geo-tag uploaded photos.
* For each Flickr album, recreate the album in Google Photos and upload the contained photos and videos.
* Set the album description, album cover photo, and photo description, as best as the API allows.

**NOTE:** These scripts will not upload all the photos from the Flickr dump; only photos inside albums. 

[0]: https://help.flickr.com/en_us/download-photos-or-albums-in-flickr-HJeLjhQskX
[1]: https://developers.google.com/photos/library/guides/overview

## Installation

* Requires Python 3.4
* You may want to create a `virtualenv` first 
* Clone this repo

```
> pip install -r requirements.txt
```

## Google Photos API Access

First, follow the [Getting Started Guide][2] to enable the Photos API.

Next, create a Client ID by following the [setting up oauth 2.0 procedure][3] with _Application Type_ set to **Other**.

Finally, download the Client secret as `credentials.json` and save it on your local machine. It will look something like the following:

```json
{
    "installed": {
        "client_id": ".......apps.googleusercontent.com",
        "project_id": "flickrrestore-.......",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "...........",
        "redirect_uris": [
            "urn:ietf:wg:oauth:2.0:oob",
            "http://localhost"
        ]
    }
}
```

[2]: https://developers.google.com/photos/library/guides/get-started
[3]: https://support.google.com/cloud/answer/6158849

## Preparing the workspace

The Flickr dump includes a number of zip files. Unzip all the zip files in your workspace, which should result in a number of folders. One of these folders should contain a number `json` files while all the other folders should contain the actual photos and videos. In my data dump, there were 500 photos/videos per zip file. 

First, copy all the photos/videos from individual folders to a single folder.

Next, in the cloned repo, you'll find a `config.json` file. Open it for editing. 

```json
{
    "flickr_photo_dir": "c:\\media\\flickr-restore\\flickr-photos",
    "flickr_photo_json_dir": "c:\\media\\flickr-restore\\72157698068208210_90be50b743b6_part1",
    "flickr_albums_json": "c:\\media\\flickr-restore\\72157698068208210_90be50b743b6_part1\\albums.json",

    "client_secrets_file": "c:\\media\\flickr-restore\\credentials.json",
    "auth_token_file": "c:\\media\\flickr-restore\\auth-token.json"
}
```

Update the file contents as per the following:

* `flickr_photo_dir`: The single folder containing all the flickr photos/videos.
* `flickr_photo_json_dir`: The folder containing all the flickr json metadata files.
* `flickr_albums_json`: Path to the `albums.json` metadata file.
  *  You may supply a different `albums.json` file with a different set of albums for upload. 
* `client_secrets_file`: The client credentials file that you got after setting up Google Photos API access.
* `auth_token_file`: The file which will hold access tokens to the Photos API. 
  * This file will be created when you first run the upload process. For now, just provide the path to a non-existing file. 

## Updating GPS information 

I spent a lot of time manually geo-tagging thousands of photos over the years using the Flickr photo organizer. Thus, I wanted to retain that geo location information when migrating to Google Photos. 

Google Photos doesn't have an API to set geo location. However, it does honour any geo location information already present in the photo's exif metadata. 

The `exif-restore.py` utility does exactly this - take the geolocation information from each photo's metadata json file and update the file's exif information with the gps data. It only does this for photos which don't already have embedded GPS information.

**WARNING:** This process does an in-place update of photo files. Ensure you have a backup before running it!

To execute this process:

```
> exif-restore.py config.json
```

Progress info will be printed to console and more detailed logs written to `exif-restore.log`.

## Uploading to Google Photos

Now for the main course. All you need to start the upload is:

```
> flickr-restore.py config.json
```

The first time that you run this, it'll prompt you to give access to your Google Photos account. Follow the instructions to grant access. You only need to do it once and the access tokens are saved to the previously mentioned `auth_token_file`.

Progress info will be printed to console and more detailed logs written to `flickr-restore.log`.

**TIP:** You may want to create a brand new Google Account to test this out first, before you let it lose on your primary Google Photos account. That's what I did while developing this!

## Limitations

The upload utility works around various limitations in the Google Photos API and the Flickr data dump:

* While the Flickr dump has a metadata json per photo that describes everything about the photo, the one thing it doesn't specify is the actual file name of the photo on disk. So the uploader has to use some name based heuristics to map a flickr photo id to the photo file on disk. These heuristics have worked for my photo dump but may break for you!
* Google Photos doesn't provide an API to set the album cover image. So I just upload the Flickr album cover photo as the first photo in the Google album, which then becomes the default album cover.
* Google Photos API doesn't give a listing of album contents. So in case of an broken upload, the best we can do is to compare count of album contents and reupload the entire album if there's a mismatch. 

## Contributing

Uploading my Flickr photos to Google was a one time task, which these utilities helped to accomplish.

Now that the task is complete, I'm unlikely to update this repository or accept any pull requests. Thus, if you want to make changes, just fork the repo and hack away!

## License

[MIT](https://opensource.org/licenses/MIT)

Copyright 2019 Deepak Sarda

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.