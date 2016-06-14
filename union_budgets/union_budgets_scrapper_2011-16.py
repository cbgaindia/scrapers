'Code for scrapping 2011-16 years Union Budget Data'

from datetime import date
import logging
from logging.config import fileConfig
from scrapping_utils import ScrappingUtils

fileConfig('scrappers/logging_config.ini')
logger = logging.getLogger()
BASE_URL = "http://indiabudget.nic.in/"
PREVIOUS_YEARS_URL = "http://indiabudget.nic.in/previousub.asp"
OUT_FOLDER = "union_budgets"
IGNORE_URLS_WITH_TEXT = ["Previous", "Next"]
BUDGET_CATEGORIES_XPATH = "//div[@class='sidePanels budget']/div[@class='content']/ul/li/a|//div[@class='sidePanels sidePanelsInner budget']//h3[@class='menuheader budget']/a" 
CHILD_LINKS_XPATH = "//div[@class='contentPanInner']//div[@class='content']//a"  
DOCUMENT_FORMATS = ["PDF","EXCEL"]

class UnionBudgetsScrapper2011_16(ScrappingUtils):
    def fetch_docs_for_year(self, year=None, base_url=BASE_URL):
        '''Fetches all documents for a budget year
        '''
        if not year:
            current_year = date.today().year
            year = "%s-%s" % (current_year, current_year%100+1)
        download_dir = "%s/%s" % (OUT_FOLDER, year)
        links = self.get_links_from_url(base_url, BUDGET_CATEGORIES_XPATH)
        for link in links:
            if ".asp" in base_url:
                base_url = "/".join(base_url.split("/")[:-1]) + "/"
            if link.xpath("@target"):
                self.save_link_as_file(link, download_dir, base_url)
            else:
                self.fetch_child_section_docs(link, download_dir, base_url)
    
    def fetch_child_section_docs(self, link, download_dir, base_url=BASE_URL):
        '''Fetches child section of a HTML document
        '''
        if "?" in base_url: 
            child_dir = download_dir
            child_url = base_url
        else:
            child_dir = download_dir + "/" + link.text.strip()
            child_url = base_url + link.xpath("@href")[0]
        links = self.get_links_from_url(child_url, CHILD_LINKS_XPATH)
        link_name = ""
        for link in links:
            link_text = ' '.join(link.xpath(".//text()")).strip()
            if link.xpath("@target"):
                file_name = link_text.strip()
                if file_name[0] == "[": 
                    file_name = link_name
                elif file_name in DOCUMENT_FORMATS:
                    file_name = link.xpath("./../../*[1]/text()")[0].strip()
                else:
                    link_name = file_name
                self.save_link_as_file(link, child_dir, base_url, file_name)    
            else:
                try:
                    int(link.text)
                    if "?" in child_url:
                        continue
                    url_to_fetch = child_url + link.xpath("@href")[0] 
                except ValueError:
                    url_to_fetch = base_url 
                if link.text in IGNORE_URLS_WITH_TEXT:
                    continue
                self.fetch_child_section_docs(link, child_dir, url_to_fetch)
                
    def save_link_as_file(self, link, download_dir, base_url=BASE_URL, file_name=None):
        '''Fetches link as a file and save it on the disk
        '''
        if not file_name:
            file_name = link.text.strip()
        sub_link = link.xpath("@href")[0] 
        if "?" in base_url:
            base_url = "/".join(base_url.split("/")[:-1])
        file_link = base_url + "/" + sub_link
        file_path = download_dir + "/" + file_name + "." + file_link.split(".")[-1]
        self.fetch_and_save_file(file_link, file_path)
    

    def fetch_all_union_budget_docs(self):
        '''Fetches all the Union Budget docs from home page
        '''
        self.fetch_docs_for_year()
        '''
        links = self.get_links_from_url(PREVIOUS_YEARS_URL, CHILD_LINKS_XPATH)
        for link in links:
            self.fetch_docs_for_year(link.text, BASE_URL + link.xpath("@href")[0])
        '''

if __name__ == '__main__':
    obj = UnionBudgetsScrapper2011_16()
    obj.fetch_all_union_budget_docs()
