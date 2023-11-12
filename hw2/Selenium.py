from selenium import webdriver
from bs4 import BeautifulSoup
import csv

# 使用Selenium開啟瀏覽器
url = "https://www.unews.com.tw/School/List"
driver = webdriver.Chrome()  # 記得將路徑更改為你的ChromeDriver的路徑
driver.get(url)

# 將整個網頁的HTML傳遞給BeautifulSoup處理
soup = BeautifulSoup(driver.page_source, 'html.parser')

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

# 關閉瀏覽器
driver.quit()

# 將資料寫入CSV檔案
with open('output_Selenium.csv', 'w', newline='', encoding='utf-8-sig') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',')

    # 寫入欄位名稱
    csvwriter.writerow(columns)

    # 寫入資料
    csvwriter.writerows(data)
