'Code for scrapping Tamil Budgets Data'

import argparse
from lxml import etree
import logging
from logging.config import fileConfig
import os
import re
import simplejson as json
from scrappers.scrapping_utils import ScrappingUtils
import sys, traceback

fileConfig('scrappers/logging_config.ini')
logger = logging.getLogger()
BASE_URL = "http://www.tnbudget.tn.gov.in/"

class TamilNaduBudgetsScraper(ScrappingUtils):
    def get_files_from_url(self, url, out_dir):
        '''Downloads budget files and save in same folder hierarchy as web
        '''
        self.get_files_from_ddg(url + "/demands/Demand_head.htm", out_dir)
        self.get_files_from_menu(url + "/spi_files/spi_array.js", out_dir)
   
    def get_files_from_ddg(self, url, out_dir):
        '''Downloads DDG files and save in same folder hierarchy as web
        '''
        page_dom = self.get_page_dom(url)
        for file_element in page_dom.xpath("//td//a"):
            file_name = self.get_text_from_element(file_element)
            if file_name:
                file_name = out_dir + "/Demands for Grant/" + file_name.split(". ")[1].title().strip() + ".pdf"
            file_url = BASE_URL + "/demands/" + file_element.xpath("./@href")[0]
            self.fetch_and_save_file(file_url, file_name) 
    
    def get_files_from_menu(self, url, out_dir):
        '''Downloads files from top menu and save in same folder hierarchy as web
        '''
        page_text = self.fetch_page(url)
        menu_list = re.compile(r"menu\d+=").split(page_text)[1:]
        menu_headers = []
        for menu_index in range(len(menu_list)):
            menu_str = menu_list[menu_index]
            if menu_index == 0:
                for file_str in menu_str.split("]")[0].split("\r\n")[2:]:
                    if file_str.count(",") > 1: 
                        file_name = file_str.split(",")[0].strip()
                        if "&nbsp;" in file_name:
                            menu_headers.append(file_name.split("&nbsp;")[0].replace('"', ''))
            else:
                for file_str in menu_str.split("]")[0].split("\r\n")[2:]:
                    file_name = file_str.split(",")[0].replace('"', '').strip()
                    if file_name:
                        file_name = menu_headers[menu_index-1] + "/" + file_name
                        file_url = file_str.split(",")[1].replace('"', '').strip()
                        if not "http" in file_url:
                            file_url = BASE_URL + file_url  
                        if ".pdf" in file_url: 
                            self.fetch_and_save_file(file_url, out_dir + "/" + file_name) 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrapes Tamil Nadu Budget Data from URL like \n http://www.tnbudget.tn.gov.in/")
    parser.add_argument("url", help="Input URL")
    parser.add_argument("out_dir", help="Output Directory to store documents") 
    args = parser.parse_args()
    obj = TamilNaduBudgetsScraper()
    if not args.url or not args.out_dir: 
        print("Please pass input URL and output directory paths")
    else:
        obj.get_files_from_url(args.url, args.out_dir)
