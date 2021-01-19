import os
from PyPDF2 import PdfFileMerger

path: str = r"D:\Documents\Laval_University\cours_H21\DeepLearning\Book"

x = [a for a in os.listdir(path) if a.endswith(".pdf")]
x.sort()

merger = PdfFileMerger()

for pdf in x:
    merger.append(open(path+'/'+pdf, 'rb'))

with open(f"{path}/DeepLearningBook.pdf", "wb") as fout:
    merger.write(fout)
