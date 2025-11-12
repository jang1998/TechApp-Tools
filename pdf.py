from docx import Document
import re
import os
import comtypes.client
import comtypes.stream
import PyPDF3

def doc_to_pdf(word_path,pdf_path):
    
    word = comtypes.client.CreateObject('Word.Application')
    word.Visible = 0
    doc = word.Documents.Open(word_path)
    doc.SaveAs(pdf_path,FileFormat=17)
    doc.Close()
    word.Quit()
    del doc
    del word


def pdf_merge(files):
    fmerge = PyPDF3.PdfFileMerger()
    for pdf in files:
        fmerge.append(pdf)
        # os.remove(pdf)
    fmerge.write('merge.pdf')
    fmerge.close()
    del fmerge

    
pdf_files = []
for name in os.listdir('.'):
    if  name.split('.')[-1].lower() in ['doc','docx']:
        current_working_directory = os.getcwd()
        absolute_path_cwd = os.path.abspath(current_working_directory)
        doc_path = absolute_path_cwd + '\\' + name
        pdf_path = absolute_path_cwd + '\\' + name.split('.')[0]+'.pdf'
        doc_to_pdf(doc_path,pdf_path)
        pdf_files.append(pdf_path)
pdf_merge(pdf_files)
