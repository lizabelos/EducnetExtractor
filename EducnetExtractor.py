#!/bin/python3

import argparse
from pyunpack import Archive
from os import listdir, mkdir, system
from os.path import isfile, isdir, join, dirname, basename
import shutil
import re


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
    candidates = [join(path, f) for f in listdir(path) if f.endswith(".cpp")]
    if len(candidates) > 0:
        return [(path, candidates)]

    result = []
    dirs = [join(path, f) for f in listdir(path) if isdir(join(path, f))]
    for dir in dirs:
        result = result + findDirsWithCpp(dir)

    return result


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
        else:
            print("Automatic CMake generation for " + outputdirname)
            cppdirs = findDirsWithCpp(dir)
            mkdir(outputdirname)
            for cppdir, cppfiles in cppdirs:
                shutil.move(cppdir, join(outputdirname, basename(cppdir)))
            cppdirs = findDirsWithCpp(outputdirname)
            # todo : generate the CMakeLists.txt
            cmakelistcontent = "cmake_minimum_required(VERSION 2.6)\r\nfile(TO_CMAKE_PATH \"$ENV{IMAGINEPP_ROOT}/CMake\" p)\r\nlist(APPEND CMAKE_MODULE_PATH \"${p}\") #For old Imagine++\r\nlist(APPEND CMAKE_SYSTEM_FRAMEWORK_PATH /Library/Frameworks) #Mac, why not auto?\r\nfind_package(Imagine REQUIRED)\r\n\r\nproject(EducnetExtractor)\n\n\n"
            for cppdir, cppfiles in cppdirs:
                cppfilesfrombase = ["'" + join(basename(cppdir), basename(file)) + "'" for file in cppfiles]
                projectname = re.sub(r'\W+', '', basename(cppdir))
                cmakelistcontent = cmakelistcontent + "add_executable(" + projectname + " " + " ".join(cppfilesfrombase) + ")\n"
                cmakelistcontent = cmakelistcontent + "ImagineUseModules(" + projectname + " Graphics)\n"

            with open(join(outputdirname, "CMakeLists.txt"), "w") as text_file:
                text_file.write(cmakelistcontent)

        system("cd '" + outputdirname + "' && mkdir build && cd build && cmake .. >/dev/null 2>/dev/null && make >/dev/null 2>/dev/null")

    shutil.rmtree(tmpdst)


if __name__ == '__main__':
    main()
