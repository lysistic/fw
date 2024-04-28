#处理veracode_fliter.csv文件，提取cve_id，然后请求nvd的api，获取cwe，然后写入out.csv文件
import requests
import csv
from urllib.parse import urlparse

def open_out_file():  #打开输出文件 最后要记得销毁，关闭文件
    out_file=open(r"./out.csv",mode="w")
    out_file.write("index,cwe,cve_id,file,func,hunk,note,repo,url,test\n")
    return out_file

def open_outjson_file():
    outjson_file=open(r"./out.json",mode="w")
    return outjson_file

class CSVReader:     #csv迭代器
    def __init__(self, filename):
        self.file = open(filename, 'r')
        self.reader = csv.reader(self.file)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self.reader)
        except StopIteration:
            self.file.close()
            raise StopIteration

def find_cwe_from_json(data):   #这个还需要改进
    try:
        vulnerabilities = data['vulnerabilities']
        vul = vulnerabilities[0]
        # 获取Primary CWE
        cwe = []
        for weakness in vul['cve']['weaknesses']:
            cwe.append(weakness['description'][0]['value'])
        return cwe
    except (KeyError, IndexError):
        # 如果没有找到相关字段，返回空列表
        return []

index=1
out_file=open_out_file()
outjson_file=open_outjson_file()
url_prefix="https://services.nvd.nist.gov/rest/json/cves/2.0?cveId="
csv_reader = CSVReader('../veracode_fliter.csv')
for row in csv_reader:
    cve_id=row[0]
    url=row[3]
    parsed_uri = urlparse(url)
    path_fileds=parsed_uri.path.split('/')
    repo=path_fileds[1]+"/"+path_fileds[2]    #那么这里的repo就是项目名
    full_url=url_prefix+cve_id    #这是用来请求nvd的api的url
    response=requests.get(full_url)
    if response.status_code==200:
        #返回成功
        json_data=response.json()
    else:
        print(f"Request {cve_id} failed with status code: {response.status_code}")
        continue
    cwe=find_cwe_from_json(json_data)
    if not cwe:
        print(f"Failed to find CWE for {cve_id}")

    out_file.write(f"{index},{cve_id},{cwe}, , , ,{repo},{url}, ,\n")
    index+=1
    print(f"Processed {cve_id}")

out_file.close()
outjson_file.close()





