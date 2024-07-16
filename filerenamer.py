import os
import glob
import my_file_utils as utils

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
    files = utils.getSubFiles([folder_path])
    # Iterate through each file
    for file_name in files:
        # Construct the new file name
        buffer = 20
        new_file_name = file_name[-buffer:]
        new_file_name = new_file_name.replace("Tenor Saxophone", "Tenor Sax")
        new_file_name = ''.join([file_name[:-buffer], new_file_name])

        # Rename the file
        src = os.path.join(folder_path, file_name)
        dest = os.path.join(folder_path, new_file_name)
        print(src, dest)
        if src != dest: os.rename(src, dest)

if __name__ == "__main__":
    folder_path = "D:\\Downloads2\\0022087 UCDMB scans"
    rename_files(folder_path)
