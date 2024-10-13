from math import ceil
import shutil

import pdf_reader as reader
import tkinter as tk
import fitz
import json
import os
import argparse
import sys
import my_file_utils as utils
from part import Part, getPartFromFilepath, ERROR_PART

PATH_ERROR = "no_match"
folderlist = ""
files = None

DRUMS = [Part(drum) for drum in ["snare", "quads", "cymbals", "basses"]]
PART_NUMBERS = ["1", "2", "3", "4", "5"]
PART_NUMBERS_FANCY = ["1st", "2nd", "3rd", "4th", "5th"]
IGNORED_WORDS = ["full"]

all_parts = [
    "flute",
    "clarinet",
    "alto",
    "tenor",
    "baritone sax",
    "trumpet",
    "mellophone",
    "trombone",
    "baritone",
    "sousaphone",
    "glock",
    "snare",
    "cymbal",
    "quads",
    "basses",
]
SCORE_ORDER = [Part(p) for p in all_parts]


class Packet:
    """This class defines a set of songs and parts, with a mapping between each part
    and its corresponding PDF for each song. This is used to build 'packets' which
    can be printed and distributed."""

    def __init__(
        self,
        parts: list[Part],
        filepaths: dict[Part, list[str]],
        combined_name: str = "all_parts",
    ) -> None:
        self.parts = parts
        self.combined_name = combined_name
        self.unique_parts = getUniqueParts(parts)
        self.instrument_groups = groupInstruments(self.parts)
        self.sortInstrumentGroupsByScoreOrder()
        self.filepaths = filepaths

    def saveGroupJSON(self, out_filepath="groups.json") -> None:
        output_dict = {}
        json_groups = {}

        max_count = 0
        for v in self.filepaths.values():
            max_count = max(max_count, len(v))
        output_dict["song count"] = max_count

        for group in self.instrument_groups:
            lead_instrument = group[0].instrument
            json_groups[lead_instrument] = {}
            for part in group:
                files = self.filepaths[part]
                if type(files) is not list:
                    files = [files]
                json_groups[lead_instrument][str(part)] = {}
                json_groups[lead_instrument][str(part)]["files"] = files
                json_groups[lead_instrument][str(part)]["count"] = self.parts.count(
                    part
                )
        output_dict["groups"] = json_groups

        json_str = json.dumps(output_dict, indent=4)
        f = open(out_filepath, "w")
        f.write(json_str)
        f.close()
        return

    def sortInstrumentGroupsByScoreOrder(self) -> None:
        sorted = []
        for p in SCORE_ORDER:
            for group in self.instrument_groups:
                if group[0].instrument == p.instrument:
                    sorted.append(group)
        self.instrument_groups = sorted

    def buildDocument(self) -> fitz.Document:
        combined_doc = fitz.Document()
        total_page_count = self.getNonDrumPageCount()
        page = 0
        top = True
        w, h = reader.FORMAT.width, reader.FORMAT.height
        combined_doc.new_page(width=w, height=h)  # type: ignore

        top_rect = combined_doc[0].bound()
        top_rect.y1 = top_rect.y1 / 2
        bot_rect = combined_doc[0].bound()
        bot_rect.y0 = bot_rect.y1 / 2
        r = top_rect
        print("building ...")
        for group in self.instrument_groups:
            for part in group:
                docs = self.getPartDocs(part)

                # insert full page pdf for drums instead of only top half
                if part in DRUMS:
                    for i in range(self.getSongCount()):
                        if i >= len(docs):
                            break
                        for _ in range(self.parts.count(part)):
                            combined_doc.insert_pdf(docs[i])
                    continue

                imgs = topHalfPixmaps(docs)
                for _ in range(self.parts.count(part)):
                    for img in imgs:
                        print(part, page)
                        combined_doc[page].insert_image(r, pixmap=img)  # type: ignore
                        page += 1

                        if page > total_page_count - 1:
                            top = False
                            page = 0
                            r = bot_rect
                        if top:
                            combined_doc.new_page(width=w, height=h)  # type: ignore
                for doc in docs:
                    doc.close()
        return combined_doc

    def getSongCount(self) -> int:
        songs = 0
        for part in self.unique_parts:
            songs = max(len(self.getPartDocs(part)), songs)
        return songs

    def getPartDocs(self, part: Part) -> list[fitz.Document]:
        return reader.openDocuments(self.filepaths[part])

    def getNonDrumPageCount(self) -> int:
        page_count = 0
        non_drums = [part for part in self.unique_parts if part not in DRUMS]
        for part in non_drums:
            for doc in self.getPartDocs(part):
                page_count += 0.5 * doc.page_count * self.parts.count(part)
                doc.close()

        return ceil(page_count)

    def saveUniqueParts(self, output_path="all parts.pdf"):
        final_doc = fitz.Document()
        for part in self.unique_parts:
            part_docs = self.getPartDocs(part)
            for doc in part_docs:
                final_doc.insert_pdf(doc)
        reader.saveDocument(final_doc, output_path)

    def getGroupPartDocs(self, compressed=False) -> dict[Part, fitz.Document]:
        out = {}
        for group in self.instrument_groups:
            for part in group:
                sub_packet = Packet([part], self.filepaths, str(part))
                if compressed:
                    out[part] = sub_packet.buildDocument()
                else:
                    out[part] = reader.combineDocuments(self.getPartDocs(part))
        return out

    def moveFilesByPart(self, output_folder: str):
        for p in self.parts:
            files = self.filepaths[p]
            files = [file for file in files if file != PATH_ERROR]
            part_name = str(p)
            new_folder = output_folder + "\\" + part_name
            try:
                os.mkdir(new_folder)
            except Exception:
                print("folder already exists")
            for file in files:
                shutil.copy(file, new_folder + "\\" + os.path.basename(file))

    def moveFilesBySong(self, output_folder: str) -> None:
        for part in self.parts:
            for path in self.filepaths[part]:
                if path == PATH_ERROR:
                    continue
                subdirname = os.path.basename(os.path.dirname(path))
                new_folder = output_folder + "\\" + subdirname
                try:
                    os.mkdir(new_folder)
                except Exception:
                    pass

                old_names = {
                    Part("flute"): "Piccolo-Flute",
                    Part("alto sax 1"): "Alto Sax 1",
                    Part("alto sax 2"): "Alto Sax 2",
                    Part("bari sax"): "Bari Sax",
                    Part("Baritone BC"): "Baritone BC",
                    Part("Glock"): "Glock",
                    Part("Tenor sax"): "Tenor Sax",
                }

                if part in old_names.keys():
                    name = old_names[part]
                else:
                    name = part.__str__()
                shutil.copy(
                    path, new_folder + "\\" + subdirname + " - " + name + ".pdf"
                )


def getUniqueParts(parts: list[Part]):
    unique_parts = list(set(parts))
    unique_parts.sort()
    # insert drum parts to the back
    drum_parts = [drum for drum in unique_parts if drum in DRUMS]
    unique_parts = [part for part in unique_parts if part not in drum_parts]
    unique_parts.extend(drum_parts)
    return unique_parts


def openFiles(
    parts: list[Part], filepaths: dict[Part, list[str]]
) -> dict[Part, list[fitz.Document]]:
    docs = {}
    for part in parts:
        # skip repeats
        if part not in docs:
            files = filepaths[part]
            files = [file for file in files if file != PATH_ERROR]
            docs[part] = reader.openDocuments(files)
    return docs


def loadJSON(json_path: str) -> Packet:
    f = open(json_path)
    part_json = json.load(f)
    parts = []
    filepaths = {}
    for group in part_json["groups"].values():
        for part_str, values in group.items():
            part = Part(part_str)
            filepaths[part] = values["files"]
            for _ in range(values["count"]):
                parts.append(part)
    return Packet(parts, filepaths)


def groupInstruments(parts: list[Part]) -> list[list[Part]]:
    instrument_groups = []
    group = []
    unique_parts = getUniqueParts(parts)
    for p in unique_parts:
        if group == [] or p.instrument == group[0].instrument:
            group.append(p)
        else:
            instrument_groups.append(group)
            group = [p]
    if group != []:
        instrument_groups.append(group)
    return instrument_groups


def getPageTopHalf(page: fitz.Page) -> fitz.Pixmap:
    r = page.bound()
    r.y1 /= 2
    page.set_cropbox(r)
    out = page.get_pixmap(dpi=300)  # type: ignore
    r.y1 *= 2
    page.set_cropbox(r)
    return out


def topHalfPixmaps(docs: list[fitz.Document]) -> list[fitz.Pixmap]:
    out = []
    for doc in docs:
        for page in doc:
            out.append(getPageTopHalf(page))
    return out


def findPartFiles(folder_paths: list[str], parts: list[Part]) -> dict[Part, list[str]]:
    """
    From a list of folders (folder_paths) and a list of parts
    find a match from each folder for each part in parts.
    :param folder_paths: list of folder paths to search in
    :param parts: list of parts to search for
    :return: Returns a dictionary with a key for each part with value
    containing list of found parts
    """
    folders = []
    part_dict = {}
    # iterate over subfolders
    for path in folder_paths:
        folders = utils.getSubFolders([path])
        for folder in folders:
            files = utils.getSubFiles([folder], [], ignore_prefix="", recursive=False)
            if len(files) == 0:  # no files found
                print(
                    "no pdf files found: " + os.path.basename(os.path.normpath(folder))
                )
                continue
            for k, v in createPartDictFromPaths(files, parts).items():
                if k not in part_dict.keys():
                    part_dict[k] = []
                for subpath in v:
                    part_dict[k].append(subpath)
    return part_dict


def createPartDictFromPaths(paths: list[str], parts: list[Part]) -> dict[Part, str]:
    """
    From list of filepaths, paths, matches each path to a part name,
    searching for parts in parts list
    :param paths: list of paths to match to a part name
    :param parts: list of parts to search for
    :return: Returns a dict with a key for each part in parts,
    with a list of matching paths as the value
    """
    part_path_dict = {}
    found_parts = {}
    # build dict mapping the part of each filepath
    for path in paths:
        part = getPartFromFilepath(path)
        part_path_dict[part] = path
    # find matches for each requested part
    for part in parts:
        # no part number specified, return all parts
        found_parts[part] = []
        if part.number == str(0):
            number_range = [0, *PART_NUMBERS]
        else:
            number_range = range(int(part.number), -1, -1)
        for n in number_range:
            try_part = Part(part.instrument + " " + str(n))
            if try_part in part_path_dict.keys():
                found_parts[part].append(part_path_dict[try_part])
                if not part.number == str(0):
                    break
        # nothing was found
        if found_parts[part] == []:
            print(
                "|| WARNING || no file found for:",
                part,
                "in folder:",
                '"' + os.path.dirname(os.path.normpath(paths[0])) + '"',
            )
            found_parts[part] = [PATH_ERROR]

    return found_parts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument(
        "songs",
        type=str,
        nargs="?",
        default="",
        help="""Filepath to text file containing on 
                        each line a folder to search through for files matching to 
                        parts contained in the parts file.
                        Subfolders will also be searched""",
    )

    parser.add_argument(
        "parts",
        type=str,
        nargs="?",
        default="",
        help="""Filepath to text file containing on 
                        each line a part to find.
                        If using combine, duplicate parts will be included 
                        multiple times in final output file""",
    )

    parser.add_argument(
        "output",
        nargs="?",
        type=str,
        default=".\\pdfs\\folder",
        help="""Filepath to folder to store output files""",
    )

    parser.add_argument(
        "-c",
        dest="combine",
        action="store_true",
        help="Combine found files into one file",
    )

    parser.add_argument(
        "-m",
        dest="move",
        action="store_true",
        help="Copy found files into one folder per part",
    )
    parser.add_argument(
        "-j",
        "-json",
        dest="json_path",
        help="""Load a packet stored in JSON and build the combined documents.
                                Folder list and request list will be ignored""",
    )

    args = parser.parse_args()
    output_folder = args.output
    if args.json_path:
        packet = loadJSON(args.json_path)
    else:
        if args.songs == "" or args.parts == "":
            parser.print_help()
            raise Exception(
                "Folder paths and parts list is required if no JSON was provided"
            )
        parts = utils.readFile(args.parts)
        parts = [Part(s) for s in parts if s != ERROR_PART]
        songs = utils.readFile(args.songs)
        print(songs)
        filepaths = findPartFiles(songs, parts)
        packet = Packet(parts, filepaths)
        packet.saveGroupJSON(output_folder + "\\groups.json")
        # packet.moveFilesBySong(output_folder + "\\songs")

    if args.combine:
        reader.saveDocument(packet.buildDocument(), output_folder + "\\all_parts.pdf")
    if args.move:
        packet.moveFilesByPart(output_folder)
    compress = False
    group_docs = packet.getGroupPartDocs(compressed=compress)

    # save combined parts

    for part, doc in group_docs.items():
        #     reader.addPageNumbers(doc, compress, start = 1)
        reader.saveDocument(doc, output_folder + "\\" + str(part) + ".pdf")
