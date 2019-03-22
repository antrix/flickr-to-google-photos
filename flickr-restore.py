#!/usr/bin/env python
import os
import re

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
                print("Could not process: ", file_path)

    print("Processed %d files" % count)
    print("Parsed %d photo identifiers" % len(cache))
    return cache

def main():
    # Parse all folders and create a dict of id -> fs path
    fs_cache = build_fs_cache("c:\\media\\flickr-restore\\test-data")
    
if __name__ == '__main__':
    main()
