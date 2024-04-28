import csv
import json
import time
import requests
from urllib.parse import urlparse


def extract_cwe_repo_commit_urls(json_data):
    try:
        # 解析JSON数据
        data = json.loads(json_data)

        # 提取CWE编号
        cwe_list = []
        vulnerabilities = data['vulnerabilities']

        for vuln in vulnerabilities:
            cve_id = vuln['cve']['id']

            # 获取Primary CWE
            primary_cwe = None
            for weakness in vuln['cve']['weaknesses']:
                if weakness['type'] == 'Primary':
                    primary_cwe = weakness['description'][0]['value']
                    cwe_list.append(primary_cwe)
                    break

            # 获取Secondary CWE
            secondary_cwes = []
            for weakness in vuln['cve']['weaknesses']:
                if weakness['type'] == 'Secondary':
                    secondary_cwes.append(weakness['description'][0]['value'])
                    cwe_list.extend(secondary_cwes)

        # 如果没有 CWE 编号，添加一个空字符串表示缺失
        if not cwe_list:
            cwe_list.append('')

        # 提取仓库和对应的commit URL
        references = data['vulnerabilities'][0]['cve'].get('references', [])
        repo_commit_urls = []
        for reference in references:
            if 'commit' in reference['url']:
                repo_commit_urls.append({
                    'repo': reference['url'].split('/commit/')[0],
                    'commit_url': reference['url']
                })
        print(f"CWE list: {cwe_list}")
        print(f"Repo commit URLs: {repo_commit_urls}")
        return cwe_list, repo_commit_urls
    except Exception as e:
        print("An error occurred while extracting CWE, repo, and commit URLs:", str(e))
        return [], []


# 打开并读取JSON文件
with open(r'G:\\Code\\Code\\附件\\Repair\\project_KB_cvelist_fliter.json', 'r') as f:
    data = json.load(f)

# 打开一个新的CSV文件
with open('output.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)

    # 写入CSV文件的头部
    writer.writerow(['Index', 'CVE ID', 'CWE', 'GitHub commit URL', 'Repository'])

    # 初始化索引
    index = 0
    url_prefix = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId="

    # 遍历JSON数据中的CVE ID列表
    for cve_id in data['test']:
        # 索引加一
        index += 1
        full_url = url_prefix + cve_id
        response = requests.get(full_url)
        if response.status_code == 200:
            json_data = response.json()
            # 提取CVE信息
            print(f"JSON data for CVE {cve_id}: {json.dumps(json_data)}")
            cwe_list, repo_commit_urls = extract_cwe_repo_commit_urls(json.dumps(json_data))

            # 如果未找到仓库信息，则跳过当前CVE
            if repo_commit_urls:
                # 写入CSV文件
                if cwe_list:
                    for cwe in cwe_list:
                        writer.writerow(
                            [index, cve_id, cwe, repo_commit_urls[0]['commit_url'], repo_commit_urls[0]['repo']])
                else:
                    writer.writerow([index, cve_id, '', repo_commit_urls[0]['commit_url'], repo_commit_urls[0]['repo']])

                # 打印信息
                print(
                    f'Index: {index}, CVE ID: {cve_id}, CWE: {", ".join(cwe_list)}, GitHub commit URL: {repo_commit_urls[0]["commit_url"]}, Repository: {repo_commit_urls[0]["repo"]}')
            else:
                print(f'Index: {index}, CVE ID: {cve_id} - No repository found, skipping.')
        # 休眠2秒
        time.sleep(2)
