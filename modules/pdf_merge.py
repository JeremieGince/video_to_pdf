import os
from PyPDF2 import PdfFileMerger
import re


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [atoi(c) for c in re.split(r'(\d+)', text)]


path: str = r"D:\Documents\Laval_University\cours_H21\DeepLearning\Book"

x = [a for a in os.listdir(path) if a.endswith(".pdf")]
print(x)
x.sort(key=natural_keys)
print(x)

merger = PdfFileMerger()

for pdf in x:
    merger.append(open(path+'/'+pdf, 'rb'))

with open(f"{path}/DeepLearningBook.pdf", "wb") as fout:
    merger.write(fout)
