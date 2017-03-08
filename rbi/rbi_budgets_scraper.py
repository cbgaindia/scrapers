'Code for scrapping RBI Data'

from datetime import date
from lxml import etree
import logging
from logging.config import fileConfig
from scrappers.scrapping_utils import ScrappingUtils

fileConfig('scrappers/logging_config.ini')
logger = logging.getLogger()
OUT_FOLDER = "rbi"

class RBIBudgetScraper(ScrappingUtils):
    def fetch_docs_for_year(self, url, year=None):
        '''Fetches all documents for a budget year
        '''
        if not year:
            current_year = date.today().year
            year = "%s" % (current_year)
        page_dom = self.get_page_dom(url)
        title = self.get_text_from_element(page_dom, xpath="//h2[@class='page_title']/text()") 
        download_dir = "%s/%s/%s" % (OUT_FOLDER, year, title)
        file_dir = download_dir
        for node in page_dom.xpath("//table[@class='tablebg']/tr"):
            node_title = self.get_text_from_element(node, xpath="./td[@class='tableheader']//text()")
            if node_title:
                file_dir = "%s/%s" % (download_dir, node_title)
                continue
            node_title = self.get_text_from_element(node, xpath="./td[@style]//text()")
            file_path = "%s/%s" % (file_dir, node_title)
            file_link = node.xpath("./td[2]/a[@target]/@href")
            if file_link:
                self.fetch_and_save_file(file_link[0].replace('http://', 'https://'), file_path + ".xls")
            file_link = node.xpath("./td[3]/a[@target]/@href")
            if file_link:
                self.fetch_and_save_file(file_link[0].replace('http://', 'https://'), file_path + ".pdf")         

if __name__ == '__main__':
    obj = RBIBudgetScraper()
    for year in range(2002,2015):
        year = str(year)
        url1 = "https://www.rbi.org.in/scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20Economy"
        url2 = "https://rbi.org.in/Scripts/AnnualPublications.aspx?head=State+Finances+%3a+A+Study+of+Budgets"
        obj.fetch_docs_for_year(url1, year)
        obj.fetch_docs_for_year(url2, year)
