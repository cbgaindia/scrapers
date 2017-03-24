'Code for scrapping Delhi Budgets Data'

import argparse
from lxml import etree
import logging
from logging.config import fileConfig
import os
import re
from scrappers.scrapping_utils import ScrappingUtils
import sys, traceback

fileConfig('scrappers/logging_config.ini')
logger = logging.getLogger()
BASE_URL = "http://delhi.gov.in"
DOC_LINKS_XPATH = "//td[@class='subheading']/a"
DOC_DOWNLOAD_XPATH = "//iframe/@src"

class DelhiBudgetsScraper(ScrappingUtils):
    def get_files_from_url(self, url, out_dir):
        '''Downloads budget files and save in same folder hierarchy as web
        '''
        page_dom = self.get_page_dom(url)
        for link in page_dom.xpath(DOC_LINKS_XPATH):
            link_name = self.get_text_from_element(link)
            link_url = link.xpath("./@href")[0]
            if not "http" in link_url:
                link_url = BASE_URL + link_url
            if link_url != url:
                doc_links = self.get_links_from_url(link_url, DOC_DOWNLOAD_XPATH)
                if doc_links:
                    file_url = doc_links[0]
                    if not "http" in file_url:
                        file_url = BASE_URL + file_url 
                    self.fetch_and_save_file(file_url, out_dir + "/" + link_name + ".pdf")
                else:
                    self.get_files_from_url(link_url, out_dir + "/" + link_name) 
                    
                 
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrapes Delhi Budget Data from the Web \n URL:  http://delhi.gov.in/wps/wcm/connect/lib_finance/Finance/Home/Budget/Budget+2017_18")
    parser.add_argument("url", help="Input URL")
    parser.add_argument("out_dir", help="Output Directory to store documents")
    args = parser.parse_args()
    if not args.url or not args.out_dir: 
        print("Please pass input URL and output directory paths")
    else:
        obj = DelhiBudgetsScraper()
        obj.get_files_from_url(args.url, args.out_dir) 
