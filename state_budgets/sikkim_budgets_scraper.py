'Code for scrapping Sikkim Budgets Data'

from lxml import etree
import logging
from logging.config import fileConfig
from scrappers.scrapping_utils import ScrappingUtils

fileConfig('scrappers/logging_config.ini')
logger = logging.getLogger()
OUT_FOLDER = "state_budgets/Sikkim"
BASE_URL = "http://www.sikkimfred.gov.in/"
START_URL = "http://www.sikkimfred.gov.in/Budget_2016-17/Budget_Circular_2016-17.aspx"

class SikkimBudgetsScraper(ScrappingUtils):
    def extract_year_links(self):
        year_links = self.get_links_from_url(START_URL, "//a[@href='#' and contains(., '20')]")
        for year_link in year_links:
            url_dict = self.get_url_and_filepath(OUT_FOLDER, year_link)
            for url in url_dict:
                self.save_docs_from_url(url, url_dict[url]["file_path"], url_dict[url]["link"])

    def get_url_and_filepath(self, base_path, link):
        url_dict = {}
        file_path = base_path + "/" + link.xpath("./text()")[0]
        href = link.xpath("@href")[0] 
        if href == "#":
            for sub_link in link.xpath("../ul/li/a"):
                url_dict.update(self.get_url_and_filepath(file_path, sub_link))
        else:
            url = BASE_URL + href.split("../")[-1]
            url_dict[url] = {"file_path":file_path, "link":link}   
        return url_dict

    def save_docs_from_url(self, url, file_path, link):
        if not ".aspx" in url:
            doc_filetype = "." + url.split(".")[-1]
            doc_name = link.xpath("./text()")[0].strip() 
            doc_path = file_path + "/" + doc_name + doc_filetype 
            self.fetch_and_save_file(url, doc_path)
        else:
            doc_links = self.get_links_from_url(url, "//td[@class='Budget_Content_Links']/a")
            for doc_link in doc_links:
                doc_url = BASE_URL + doc_link.xpath("@href")[0].split("../")[-1]
                doc_filetype = "." + doc_url.split(".")[-1]
                doc_name = doc_link.xpath("./text()")[0].strip() 
                doc_path = file_path + "/" + doc_name + doc_filetype 
                self.fetch_and_save_file(doc_url, doc_path)

if __name__ == '__main__':
    obj = SikkimBudgetsScraper()
    obj.extract_year_links()
