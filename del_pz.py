import win32com.client as win32  
import os
def remove_comments(doc_path, output_path):  
    word = win32.gencache.EnsureDispatch('Word.Application')  
    word.Visible = False  # 不显示 Word 界面  
    doc = word.Documents.Open(doc_path)  
    
    # 遍历所有批注并删除  
    for comment in doc.Comments:  
        comment.Delete()  
    # 更新所有字段，包括目录 
    doc.Fields.Update()
    doc.SaveAs(output_path)  
    doc.Close()  
    word.Quit()  

# remove_comments('C:\\Users\\lijie\\Desktop\\神秘代码\\example.docx', 'C:\\Users\\lijie\\Desktop\\神秘代码\\example.docx')

for name in os.listdir('.'):
    if name.split('.')[-1].lower() in ['doc', 'docx']:
        doc_path = os.path.abspath(name)
        # output_path = os.path.splitext(doc_path)[0] + '.docx'
        print(doc_path)
        remove_comments(doc_path,doc_path)