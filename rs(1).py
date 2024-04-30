import os #用来改变目录
import requests #用来网络请求
import csv #用来处理csv表格
import re #用来正则匹配
import time
import subprocess #用来执行powershell命令并把输出重定向
from concurrent.futures import ThreadPoolExecutor #多线程池
access_token='input your token'
base_path1='E:\\REPO' #存放所有仓库的地方，一般是硬盘的目录
input_csv="D:\\大创\\fw\\java_repos.csv" #java_repos.csv
output_csv = "D:\\大创\\fw\\a.csv" #a.csv
def clone_repository(url, output_dir):
    try:
        # 从URL中提取仓库名
        repository_name = re.search(r'/([^/]+/[^/]+)/commit/', url).group(1)
        repo = re.search(r'[^/]+$', repository_name).group()
        # 构造仓库地址
        repository_url = f"https://{access_token}@github.com/{repository_name}"
        print(repo)
        # 检查目录下是否已经存在该仓库
        if os.path.exists(os.path.join(output_dir, repo)):
            print(f"Repository {repo} already exists, skipping...")
            return
        # 在指定目录下执行git clone命令
        subprocess.run(["git", "clone", repository_url])
        print(f"Successfully cloned {url}")
        print(repository_name)
        # 延迟一段时间，避免频繁请求
        time.sleep(2)  # 可根据需要调整延迟时间
    except Exception as e:
        print(f"Error cloning {url}: {e}")


def extract_commit_hash(url):
    # 匹配 commit hash
    match = re.search(r'/commit/([^/#]+)', url)
    if match:
        commit_hash = match.group(1)
        return commit_hash
    else:
        return None
def test_finder(url):
    repository_name = re.search(r'/([^/]+/[^/]+)/commit/', url).group(1)
    repo = re.search(r'[^/]+$', repository_name).group()
    # 构造仓库地址
    repository_url = f"https://github.com/{repository_name}"
    os.chdir(os.path.join(base_path1, repo))
    commit_hash = extract_commit_hash(url)
    git_ls_tree = f'git ls-tree -r {commit_hash} | Select-String "test"'
    result = subprocess.run(['powershell', '-Command', git_ls_tree], capture_output=True, text=True)
    output = result.stdout
    if output:
        return True
    else:
        return False

class DiffParser:
    def __init__(self, diff_output):
        self.lines = diff_output.splitlines(keepends=False)
        self.diff_output = diff_output

    def parse_hunk(self):
        pointer = -1
        hunk = 0  # 计算Hunk
        is_comment = 0
        is_test_case = 0
        current_hunk = None
        for index, line in enumerate(self.lines, start=1):

            if line.startswith("diff"):
                is_test_case = 0
                pattern = "^diff --git.*[Tt][eE][Ss][Tt].*$"
                ans = re.search(pattern, line)
                if ans != None:
                    is_test_case = 1
            if is_test_case == 1:
                continue
            if line.find('*/') != -1 and is_comment == 1:
                is_comment = 0
                continue
            if line.find("/**") != -1:
                is_comment = 1

                continue
            if line.find("/*") != -1:
                is_comment = 1
                continue
            if is_comment == 1:
                continue
            if len(line) >= 1:
                if line.find("import") == -1:
                    if line[0] == '-' or line[0] == "+":
                        if line.find('//') == 1:
                            continue
                        if line.startswith("+++"):
                            continue
                        if line.startswith("+ *"):
                            continue
                        if line.startswith("+/*"):
                            continue
                        if line.startswith("-/*"):
                            continue
                        if line.startswith("- *"):
                            continue

                        if line.startswith("---"):
                            continue
                        if len(line) <= 2:
                            continue

                        if pointer == -1:
                            pointer = index
                            hunk = hunk + 1
                        else:
                            if index == (pointer + 1):
                                pointer = index
                                # print(line)
                            else:
                                # print("\n\n\n\n\n\n\n\n")
                                # print(line)
                                pointer = index
                                hunk = hunk + 1
        print(hunk)
        return hunk

    def parse_file(self):
        file = 0
        java_file = 0
        is_test_case = 0
        test_in_commit = 0
        for line in self.lines:
            # print(line)
            if line.startswith("diff"):
                is_test_case = 0
                pattern = "^diff --git.*[Tt][eE][Ss][Tt].*$"
                ans = re.search(pattern, line)
                if ans != None:
                    is_test_case = 1
            if is_test_case == 1:
                test_in_commit = 1
                continue
            ##到这里跳过测试集
            if line.startswith("diff"):
                file = file + 1  # 现在一定不是测试文件，一定是一个文件
                if line.endswith(".java"):
                    java_file = java_file + 1
        print("[java_file]:", java_file)
        print("[file]:", file)
        print("[test_in_commit]:",test_in_commit)
        return file, java_file,test_in_commit

    def extract_functions(self):
        functions = []
        diff_blocks = self.diff_output.split('diff --git')
        for block in diff_blocks:
            if 'test' not in block.lower():  # 跳过测试文件
                function_matches = re.findall(r'(\b[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\s*(?:throws\s+\w+\s*)?\{[^}]*\})',
                                              block)
                functions.extend(function_matches)
        return functions
    

def get_commit_subject(commit_hash, repo_path):
    path_str = "E:\\REPO\\{}".format(repo_path)
    command = ["git", "-C", path_str, "show", "--format=%s", "-s", commit_hash]
    print(command)
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        print("Failed to get commit subject")
        return None

if __name__ == '__main__':

    max_workers=5
    import csv

    with open(input_csv) as csvfile:
            reader=csv.reader(csvfile)
            urls=[row[3] for row in reader]
        
    os.chdir(base_path1)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for url in urls:
            executor.submit(clone_repository,url,base_path1)

    with open(output_csv, 'w') as f:
        f.write("url,repo,file,java_file,func,hunk,test,note\n")


    for url in urls:
        commit_hash=extract_commit_hash(url)
        repo=repository_name = re.search(r'/([^/]+/[^/]+)/commit/', url).group(1)
        repo = re.search(r'[^/]+$', repository_name).group()
        note = get_commit_subject(commit_hash,repo)
        os.chdir(os.path.join(base_path1, repo))
        diff_command = f'git diff {commit_hash}^..{commit_hash}'  # 注意添加了空格
        diff_output = subprocess.run(['powershell', '-Command', diff_command], capture_output=True, text=True, encoding='utf-8').stdout
        if len(diff_output)<1:
            print("the repo local is bad")
            diff_url=url+'.diff'
            res=requests.get(diff_url).text
            if res!=None:
                print("it is solved")
                diff_output=res
        parser=DiffParser(diff_output)
        with open(output_csv, 'a') as f:
            file, java_file,test_in_commit = parser.parse_file()
            hunk = parser.parse_hunk()
            functions = len(parser.extract_functions())
            
            string = "URL: {}   Repo: {}   file: {}   java_file: {}   functions: {}   hunk: {}@@@@@\n".format(url, repo, file, java_file, functions, hunk)
            test_in_repo = 0
            if(test_in_commit == 0):
                if test_finder(url):
                    test_in_repo = 1
            
            string = "{},{},{},{},{},{},{},{}\n".format(url, repository_name, file, java_file, functions, hunk, test_in_commit|test_in_repo,note)
            f.write(string)

