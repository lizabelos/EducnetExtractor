#!/bin/python3

import argparse
import os
import re
import shutil
import tempfile
import requests
import statistics

from os import listdir, mkdir, system
from os.path import isfile, isdir, join, dirname, basename

from pyunpack import Archive
from pysimilar import compare


def getGradesTable():
    table = requests.get("http://imagine.enpc.fr/~monasse/Info/TPs/NotesExos.html").content
    table = re.sub(r'<([a-zA-Z\/]*)[^>]*>', r'<\1>', table.decode("utf-8"))
    table = table.replace("\n", "")
    table = table.replace("\t", "")
    begin = table.find("<table>") + len("<table>")
    end = table.find("</table>")
    table = table[begin:end]
    table = table.replace("<font>", "")
    table = table.replace("</font>", "")
    table = table.replace("<colgroup>", "")
    table = table.replace("</colgroup>", "")
    table = table.replace("<br>", "")
    table = table.replace("</tr>", "")
    table = table.replace("</td>", "")
    table = table.split("<tr>")
    table = [[y for y in x.split("<td>") if y != ""] for x in table]
    table = [x for x in table if len(x) > 0]
    return table


def getStudentsList():
    table = getGradesTable()
    table = [[x[0].lower(), x[1].lower()] for x in table if not x[0].startswith("Groupe")]
    return table


def recursiveFindCMakeLists(path):
    candidates = [join(path, f) for f in listdir(path) if f == "CMakeLists.txt"]
    if len(candidates) > 0:
        return candidates[0]

    dirs = [join(path, f) for f in listdir(path) if isdir(join(path, f))]
    for dir in dirs:
        result = recursiveFindCMakeLists(dir)
        if result is not None:
            return result

    return None


def findStudentsListInDir(path, studentslist):
    candidates = [join(path, f) for f in listdir(path) if f.endswith(".cpp") or f.endswith(".h") or f.endswith(".hpp")]
    result = []
    for candidate in candidates:
        try:
            f = open(candidate, "r")
            c = f.read()
            f.close()
            c = c.lower()
            for s in studentslist:
                if c.find(s[0] + " ") >= 0 or c.find(s[0] + "\n") >= 0 or c.find(s[0] + "\t") >= 0 or c.find(s[0] + "\r") >= 0:
                    result.append(s[0])
        except:
            print("Can't open " + candidate + " for student list")
            # todo
            pass
    return list(dict.fromkeys(result))

def findDirsWithCpp(path):
    candidates = [join(path, f) for f in listdir(path) if f.endswith(".cpp") or f.endswith(".h") or f.endswith(".hpp")]
    if len(candidates) > 0:
        return [(path, candidates)]

    result = []
    dirs = [join(path, f) for f in listdir(path) if isdir(join(path, f))]
    for dir in dirs:
        result = result + findDirsWithCpp(dir)

    return result


def findExecutables(path):
    dirs = [join(path, f) for f in listdir(path) if isdir(join(path, f))]
    executables = [join(path, f) for f in listdir(path) if
                   isfile(join(path, f)) and os.access(join(path, f), os.X_OK) and not f.endswith(
                       ".bin") and not f.endswith(".out")]

    for dir in dirs:
        executables = executables + findExecutables(dir)

    return executables

def launchEditor(filelist):
    command = "gedit " + " ".join(["\"" + x + "\"" for x in filelist])
    system(command)


def process_dir(dir, target_directory, student_list, onlyprintstudent=False, execute=False):
    cmakepath = recursiveFindCMakeLists(dir)
    outputdirname = join(target_directory, basename(dir).split("_")[0])
    cppdirs = findDirsWithCpp(dir)
    students = []
    for cppdir in cppdirs:
        print(cppdir[0])
        students = students + findStudentsListInDir(cppdir[0], student_list)

    if cmakepath is not None:
        cmakedirname = dirname(cmakepath)
        shutil.move(cmakedirname, outputdirname)
        cppdirs = findDirsWithCpp(outputdirname)
    else:
        print("Automatic CMake generation for " + outputdirname)
        mkdir(outputdirname)
        for cppdir, cppfiles in cppdirs:
            shutil.move(cppdir, join(outputdirname, basename(cppdir)))
        cppdirs = findDirsWithCpp(outputdirname)
        cmakelistcontent = "cmake_minimum_required(VERSION 2.6)\r\nfile(TO_CMAKE_PATH \"$ENV{IMAGINEPP_ROOT}/CMake\" p)\r\nlist(APPEND CMAKE_MODULE_PATH \"${p}\") #For old Imagine++\r\nlist(APPEND CMAKE_SYSTEM_FRAMEWORK_PATH /Library/Frameworks) #Mac, why not auto?\r\nfind_package(Imagine REQUIRED)\r\n\r\nproject(EducnetExtractor)\n\n\n"
        for cppdir, cppfiles in cppdirs:
            cppfilesfrombase = ["\"" + join(basename(cppdir), basename(file)) + "\"" for file in cppfiles]
            projectname = re.sub(r'\W+', '', basename(cppdir))
            cmakelistcontent = cmakelistcontent + "add_executable(" + projectname + " " + " ".join(
                cppfilesfrombase) + ")\n"
            cmakelistcontent = cmakelistcontent + "ImagineUseModules(" + projectname + " Graphics)\n"

        with open(join(outputdirname, "CMakeLists.txt"), "w") as text_file:
            text_file.write(cmakelistcontent)

    system(
        "cd '" + outputdirname + "' && mkdir build && cd build && cmake .. >/dev/null 2>/dev/null && make >/dev/null 2>/dev/null")

    executables = findExecutables(outputdirname)
    new_executables = []
    for executable in executables:
        shutil.move(executable, outputdirname + "/exe_" + basename(executable))
        new_executables.append(outputdirname + "/exe_" + basename(executable))

    executables = new_executables

    if onlyprintstudent or execute:
        if not onlyprintstudent:
            cls()

        while True:
            print(basename(dir).split("_")[0])
            print("Found other students : " + str(students))
            print(" ")
            print(" ")

            if onlyprintstudent:
                break

            for i in range(0, len(executables)):
                print(str(i) + " : " + basename(executables[i]))
            print("[vide] : Passer à l'eleve suivant")
            print("s : Editer les fichiers sources")

            print(" ")
            print(" ")

            if cmakepath is None:
                print("Aucun CMake trouvé. Il a été généré automatiquement.")

            if len(executables) == 0:
                print("Aucun executable trouvé :(")

            print(" ")
            print(" ")

            i = input("=> ")
            if i == "":
                break
            if i == "s":
                filelist = []
                for cppdir in cppdirs:
                    filelist = filelist + cppdir[1]
                print(filelist)
                launchEditor(filelist)
                continue
            try:
                i = int(i)
            except:
                continue
            if i < 0 or i >= len(executables):
                continue

            cls()
            print(":'" + executables[i] + "'")
            system("'" + executables[i] + "'")

    return outputdirname


def detectPlagiatBetweenFiles(f1, f2):
    if f1 == f2:
        return 0
    return compare(f1, f2, isfile=True)

def detectPlagiatInFolder(src1, src2):
    cppdirs1 = findDirsWithCpp(src1)
    cppdirs2 = findDirsWithCpp(src2)
    filelist1 = []
    for cppdir in cppdirs1:
        filelist1 = filelist1 + cppdir[1]
    filelist2 = []
    for cppdir in cppdirs2:
        filelist2 = filelist2 + cppdir[1]
    values = []
    for f1 in filelist1:
        value = 0
        for f2 in filelist2:
            value = max(detectPlagiatBetweenFiles(f1, f2), value)
        values.append(value)
    return statistics.mean(values)

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def main():
    parser = argparse.ArgumentParser("EductnetExtractor by Thomas Belos")
    parser.add_argument("-z", "--zip", nargs='+', help='<Required> One or more zip file', required=True)
    parser.add_argument("-d", "--dst", help='<Required> Destination directory', required=True)
    parser.add_argument("-e", "--execute", help='execute the file', type=bool)
    parser.add_argument("-s", "--student", help='only print students', type=bool)

    args = parser.parse_args()

    dst = args.dst
    with tempfile.TemporaryDirectory(suffix="_educnetextractor") as tmpdst:
        for file in args.zip:
            print("Extracting " + file)
            Archive(file).extractall(tmpdst)

        dirs = [join(tmpdst, f) for f in listdir(tmpdst) if isdir(join(tmpdst, f))]
        output_dirs = []
        files = []
        for dir in dirs:
            files = files + [join(dir, f) for f in listdir(dir) if isfile(join(dir, f))]

        for file in files:
            print("Extracting " + file)
            out = join(dirname(file), "out")
            try:
                mkdir(out)
                Archive(file).extractall(out)
            except OSError:
                print("Impossible de créer " + out)
            except Exception as exc:
                print(exc)

        student_list = getStudentsList()
        for dir in dirs:
            output = process_dir(dir, dst, student_list, onlyprintstudent=args.student, execute=args.execute)
            output_dirs = output_dirs + [output]

        for dir1 in output_dirs:
            max_value = 0
            max_dir = ""
            for dir2 in output_dirs:
                if dir1 == dir2:
                    continue
                value = detectPlagiatInFolder(dir1, dir2)
                if value > max_value:
                    max_dir = dir2
                    max_value = value
            print("%s ==> %s Similarity %d" % (dir1, max_dir, max_value * 100))


if __name__ == '__main__':
    main()
