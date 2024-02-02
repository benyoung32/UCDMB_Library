def printDict(dict):
    for k,v in dict.items():
        print(k, end = ':\n')
        if v is list:
            for n in v:
                print(n)
        else:
            print(v)

def save_list(l:list, outfilepath:str) -> None:
    page_file = open(outfilepath, 'w+')
    for b in l:
        page_file.write(str(b) + '\n')
    page_file.close()