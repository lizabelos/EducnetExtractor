#!/bin/python3

# Please install patool, p7zip, rar, unrar

import argparse
from pyunpack import Archive
from os import listdir, mkdir, system
from os.path import isfile, isdir, join, dirname, basename
import shutil


def recusriveFindCMakeLists(path):
    candidates = [join(path, f) for f in listdir(path) if f == "CMakeLists.txt"]
    if len(candidates) > 0:
        return candidates[0]

    dirs = [join(path, f) for f in listdir(path) if isdir(join(path, f))]
    for dir in dirs:
        result = recusriveFindCMakeLists(dir)
        if result is not None:
            return result

    return None


def findDirsWithCpp(path):
    pass


def main():
    parser = argparse.ArgumentParser("EductnetExtractor by Thomas Belos")
    parser.add_argument("-z", "--zip", nargs='+', help='<Required> One or more zip file', required=True)
    parser.add_argument("-d", "--dst", help='<Required> Destination directory', required=True)
    args = parser.parse_args()

    dst = args.dst
    tmpdst = "/tmp/educnetextractor"

    try:
        shutil.rmtree(tmpdst)
    except:
        pass

    mkdir(tmpdst)

    for file in args.zip:
        print("Extracting " + file)
        Archive(file).extractall(tmpdst)

    dirs = [join(tmpdst, f) for f in listdir(tmpdst) if isdir(join(tmpdst, f))]
    files = []
    for dir in dirs:
        files = files + [join(dir, f) for f in listdir(dir) if isfile(join(dir, f))]

    for file in files:
        print("Extracting " + file)
        out = join(dirname(file), "out")
        try:
            mkdir(out)
        except:
            pass
        try:
            Archive(file).extractall(out)
        except Exception as e:
            print(e)
            pass

    for dir in dirs:
        cmakepath = recusriveFindCMakeLists(dir)
        outputdirname = basename(dir)
        if cmakepath is not None:
            cmakedirname = dirname(cmakepath)
            shutil.move(cmakedirname, outputdirname)
            system("cd '" + outputdirname + "' && mkdir build && cd build && cmake .. && make")
        else:
            print("CMake not found for " + dir)
            shutil.move(dir, outputdirname)

    shutil.rmtree(tmpdst)



if __name__ == '__main__':
    main()
