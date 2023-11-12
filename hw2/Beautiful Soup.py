import requests
from bs4 import BeautifulSoup
import csv

url = "https://www.unews.com.tw/School/List"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# 找到學校表格
table = soup.find('table', class_='table')

# 提取表格標題
columns = [th.text.strip() for th in table.find('tr').find_all('th')]

# 存儲資料的列表
data = []

# 提取表格內容
for row in table.find_all('tr')[1:]:
    school_data = [td.text.strip() for td in row.find_all('td')]
    data.append(school_data)

# 將資料寫入CSV檔案
with open('output_Beautiful Soup.csv', 'w', newline='', encoding='utf-8-sig') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',')

    # 寫入欄位名稱
    csvwriter.writerow(columns)

    # 寫入資料
    csvwriter.writerows(data)

