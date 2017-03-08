'Code for scrapping Assam Budgets Data'

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
DOC_LINKS_XPATH = '//a[@class="document-link"]'
DOC_DOWNLOAD_XPATH = '..//a[@class="taglib-icon"]/@href'
LOG_FILE = "/tmp/log"
MAX_PAGINATION_SLUG = '&_20_displayStyle=icon&_20_viewEntries=0&_20_viewFolders=0&_20_entryEnd=75&_20_entryStart=0&_20_folderEnd=20&_20_folderStart=0&_20_viewEntriesPage=1'
TEMP_INDEX_FILE = "/tmp/page.html"
TEMP_HTML_FILE = "/tmp/pages.html"

class AssamBudgetsScraper(ScrappingUtils):
    def get_files_from_url(self, url, out_dir, rename):
        '''Downloads budget files and save in same folder hierarchy as web
        '''
        page_dom = self.get_page_dom(url)
        for link in page_dom.xpath(DOC_LINKS_XPATH):
            is_link_folder = link.xpath("@data-folder")[0]
            link_name = self.get_text_from_element(link)
            if is_link_folder == "false":
                file_path = out_dir + "/" + link_name 
                download_link = link.xpath(DOC_DOWNLOAD_XPATH)[0]
                self.fetch_and_save_file(download_link, file_path)
                if rename and "grant" in link_name.lower():
                    self.rename_grant_file(link_name, out_dir, file_path)
            else:
                download_id = link.xpath("@data-folder-id")[0]
                download_link = link.xpath("@href")[0] + MAX_PAGINATION_SLUG
                self.get_files_from_url(download_link, out_dir + "/" + link_name + "/", rename)

    def rename_grant_file(self, file_name, out_dir, file_path):
        '''Parses grant document get complete Grant Name
        '''
        doc_name = file_name
        try:
            command = "pdftohtml -f '%s' -l '%s' '%s' '%s' > %s" % (1, 1, file_path, TEMP_INDEX_FILE, LOG_FILE)
            os.system(command)
            html_obj = open(TEMP_HTML_FILE, "rb")
            dom_tree = etree.HTML(html_obj.read())
            doc_name = dom_tree.xpath("//b/text()")[0].encode('utf-8').replace('\xa0', ' ').replace('\xc2', '').strip() 
            doc_name = re.sub('\s{2,}', ' ', doc_name)
            doc_name = doc_name.title().replace("-", " - ") + ".pdf"
            os.rename(file_path, out_dir + "/" + doc_name)
            logger.info("Renaming %s to %s" % (file_name, doc_name))
        except Exception, error_message:
            logger.error("Unable to retrive Grant name for %s due to error: %s" % (file_name, error_message))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrapes Assam Budget Data from URL like \n http://assam.gov.in/web/finance/budget-2017-18?_20_folderid=5235333&_20_displaystyle=icon&_20_viewentries=false&_20_viewfolders=1&_20_entryend=75&_20_entrystart=0&_20_folderend=20&_20_folderstart=0&p_p_id=20&p_p_lifecycle=0&_20_struts_action=%%2fdocument_library%%2fview&_20_action=browsefolder&_20_expandfolder=true")
    parser.add_argument("--rename", help="Rename Grants by parsing Titles from Grant documents")
    parser.add_argument("url", help="Input URL(Note: Do select max page limit)")
    parser.add_argument("out_dir", help="Output Directory to store documents")
    args = parser.parse_args()
    obj = AssamBudgetsScraper()
    if not args.url or not args.out_dir: 
        print("Please pass input URL and output directory paths")
    else:
        obj.get_files_from_url(args.url, args.out_dir, args.rename)            
