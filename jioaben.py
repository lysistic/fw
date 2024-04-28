import requests
import time
import csv
import re

isTest = 0
num = 0

def has_test_case(line):
   assert isinstance(line, str)
   pattern = "^diff --git.*Test.*$"
   return bool(re.match(pattern, line))

def is_func(str):
    # 方法的修饰符用来判断一个方法
    funcs = ['public','protected','private','static','final','synchronized','native','abstract']
    for s in funcs:
        index = str.find(s)
        if (index != -1):
            return index
    return -1

def get_repo_contents(prj, path=""):
    url = f"https://api.github.com/repos/{prj}/contents/{path}"
    time.sleep(6)
    print(123)
    print("[prj]:",prj)
    print("[path]:",path)
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve repository contents for {path}.")
        return None

def get_test_files(prj, path="", goal = ""):
    def match_test_file(filename):
        assert isinstance(filename, str)
        pattern = "^Test" + re.escape(str) + "$"
        return bool(re.match(pattern, filename))
        # return True

    contents = get_repo_contents(prj, path)
    # file = open(output_file, "a")
    if contents is not None:
        for item in contents:
            if item['type'] == 'file' and match_test_file(item['name']):
                return True
            elif item['type'] == 'dir':
                return get_test_files(prj, item['path'])
                # file.write(item['name'])
    # file.close()
    return False

def deal_with_url( url ):
    res = requests.get(url)
    time.sleep(6)
    # 初始化部分
    s = res.text.splitlines(keepends = False)
    file = 0
    file_java = 0
    func = 0
    hunk = 0
    ischange = 0
    isTestcase = 0
    iscomment = 0
        # 使用set去重
    funcset = set()

    # 计算file,func,hunk
    for st in s:
        # 删除前导空格，方便后面的操作
        st = re.sub(r' {2,}', '', st) 
        # file
        if (st.startswith("diff") == True):
            isTestcase = 0
            match = re.search(r'/([^/]*)$', st)
            if match:
                filename = match.group(1)
            match = re.search(r'/([^/]*)$', url)
            if match:
                html_url = match.group(1)
            print(html_url)
            print(filename)
            if has_test_case(st) == False:
                file = file + 1 
                    # 单独计数java文件
                if (st.endswith(".java") == True): 
                    file_java = file_java + 1
                    # 如果不是test文件，就扫描仓库，找一下test文件
                if get_test_files(prj, html_url, filename) ==True:   
                    isTest = 1
            else :
                isTestcase = 1
                isTest = 1
                
        # 跳过test文件不计算func和hunk
        if isTestcase == 1:
            continue
        # func
        if st.startswith('-') == False and is_func(st) != -1 and st.find('(') != -1 and st.find(')') != -1 :
            index1 = is_func(st)
            index2 = st.find(')')
            stg = st[index1 : index2 + 1] 
            funcset.add(stg)
        # hunk
        # 不是修改行
        if (st.startswith('+') == 0) and (st.startswith('-') == 0):
            ischange = 0
        # 是修改行
        if  ((st.startswith("+") == True and st.startswith("+++") == False) 
            or (st.startswith("-") == True and st.startswith("---") == False)) and (ischange == 0):
            # 是import
            if (st.find("import") != -1) :
                pass
            # 跳过注释
                # 一行注释
            elif (st.find("//") == 1 ):
                pass
                # 是一段注释的开始
            elif (st.find('/**') == 1) or (st.find('/*') == 1):
                iscomment = 1
                pass
                # 正在一段注释中
            elif (iscomment == 1):
                pass
                # 一段注释结束
            elif (st.find('*/') != -1) and iscomment == 1:
                iscomment = 0
                pass
            # 跳过空语句
            elif (len(st) == 1):
                pass
            # 跳过无效修改
                # 阿巴阿巴现在还没有很好的想法
                # 考虑多种无效修改
            # 是有效注释
            else :
                ischange = 1
                hunk = hunk + 1

    func = len(funcset)

url='https://github.com/alibaba/fastjson/commit/f5903fa56497c00ed0703ac875b511f9bd5f1d8e'
prj='alibaba/fastjson'   


        # 输出file,func,hunk
deal_with_url(url + ".diff")
        
    
