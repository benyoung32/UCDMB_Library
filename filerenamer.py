import os
import glob

from sympy import false

def getSubFiles(paths: list[str], files:list[str] = [], 
                ignore_prefix:str = '', recursive:bool = True) -> list[str]:
    '''
    For each path in paths, append pdf path to files list. 
    If path is a folder, also apend all paths within folder.
    If recursive is true, check folders within folders
    Ignore any paths that contain ignore_prefix
    :param paths: Paths to search
    :param files: Currently found files (for recursion)
    :param ignore_prefix: Ignore any files containing this substring
    :param recursive: If true, recurse into subfolders as well 
    :return: List of pdf files found
    '''
    for f in paths:
        if os.path.exists(f):
            if os.path.isdir(f):
                if recursive:
                    getSubFiles(glob.glob(f + "/*"), files, ignore_prefix)
                else:
                    getSubFiles(glob.glob(f + '/*.pdf'),files, ignore_prefix)
            if '.pdf' in f and (not ignore_prefix or ignore_prefix not in f):
                files.append(f)
    return files

# Function to convert Roman numerals to integers
def roman_to_int(s):
    roman_dict = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    prev_value = 0
    for char in s[::-1]:
        value = roman_dict[char]
        if value < prev_value:
            result -= value
        else:
            result += value
        prev_value = value
    return result

# Function to replace Roman numerals with regular numbers in file names
def rename_files(folder_path):
    # Get a list of all files in the folder
    # files = os.listdir(folder_path)
    files = getSubFiles([folder_path], ignore_prefix=false)
    # Iterate through each file
    for file_name in files:
        # Construct the new file name
        buffer = 20
        new_file_name = file_name[-buffer:]
        # new_file_name = new_file_name.replace("III", "3")
        # new_file_name = new_file_name.replace("II", "2")
        # new_file_name = new_file_name.replace("I", "1")
        new_file_name = new_file_name.replace("Tenor Saxophone", "Tenor Sax")
        new_file_name = ''.join([file_name[:-buffer], new_file_name])
        # file_extension = os.path.splitext(file_name)[1]
        # name_without_extension = os.path.splitext(file_name)[0]
        # parts = name_without_extension.split()
        # new_file_name = ' '.join(parts[:-2])
        # new_file_name += ' '
        # for part in parts[-2:]:
        #     if part.isnumeric():
        #         new_file_name += part
        #     else:
        #         try:
        #             new_file_name += str(roman_to_int(part.upper()))
        #         except KeyError:
        #             # If it's not a Roman numeral, keep the original string
        #             new_file_name += part
        #     new_file_name += ' '

        # # Remove the extra underscore at the end
        # new_file_name = new_file_name[:-1]

        # # Add the file extension
        # new_file_name += file_extension

        # Rename the file
        src = os.path.join(folder_path, file_name)
        dest = os.path.join(folder_path, new_file_name)
        print(src, dest)
        if src != dest: os.rename(src, dest)

if __name__ == "__main__":
    # folder_path = input("Enter the folder path: ")
    folder_path = "D:\\Downloads2\\0022087 UCDMB scans"
    # folder_path = "D:\\Downloads2\\0022087 UCDMB scans\\Africa - Copy"
    # new_name = input("Enter the new name for the files: ")
    rename_files(folder_path)
