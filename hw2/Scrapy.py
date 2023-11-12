import scrapy
import csv

class UNewsSpider(scrapy.Spider):
    name = 'unews'
    start_urls = ['https://www.unews.com.tw/School/List']

    def parse(self, response):
        # 找到學校表格
        table = response.css('table.table')

        # 提取表格標題
        columns = [th.css('::text').get().strip() for th in table.css('tr th')]

        # 存儲資料的列表
        data = []

        # 提取表格內容
        for row in table.css('tr')[1:]:
            school_data = [td.css('::text').get().strip() for td in row.css('td')]
            data.append(school_data)

        # 將資料寫入 CSV 檔案
        output_file = 'output_Scrapy.csv'
        self.log(f'正在將資料保存至 {output_file}')
        self.save_to_csv(output_file, columns, data)

    def save_to_csv(self, file_name, columns, data):
        with open(file_name, 'w', newline='', encoding='utf-8-sig') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',')
            
            # 寫入欄位名稱
            csvwriter.writerow(columns)

            # 寫入資料
            csvwriter.writerows(data)
