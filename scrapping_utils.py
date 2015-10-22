'Class for basic scrapping utility functions'

import logging
from logging.config import fileConfig
from lxml import etree
import os
import requests
import shutil

fileConfig('logging_config.ini')
logger = logging.getLogger()

class ScrappingUtils():
    def fetch_page(self, url):
        '''Fetches URL and return its textual content, in case of error returns empty text
        '''
        page_text = ''
        try:
            response = requests.get(url, stream=True)
            page_text = response.text
        except Exception, error_message:
            logger.error("Unable to fetch following URL: %s, error message: %s" % (url, error_message))
        return page_text

    def fetch_and_save_file(self, url, file_path):
        '''Fetches URL and save it as file
        '''
        try:
            dir_path = os.path.dirname(os.path.realpath(file_path))
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(file_path, 'wb') as file_obj:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, file_obj)
        except Exception, error_message:
            logger.error("Unable to fetch file at following URL: %s, error message: %s" % (url, error_message)) 

    def get_links_from_url(self, url, xpath):
        '''Fetches links from URL by the xpaths
        '''
        links = []
        page_text = self.fetch_page(url)
        if page_text:
            dom_tree = etree.HTML(page_text)
            links = dom_tree.xpath(xpath)
        return links 
