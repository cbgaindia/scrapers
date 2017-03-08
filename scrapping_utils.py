'Class for basic scrapping utility functions'

import logging
from logging.config import fileConfig
from lxml import etree
import os
import re
import requests
from requests.adapters import HTTPAdapter
import shutil

fileConfig('scrappers/logging_config.ini')
logger = logging.getLogger()
DEFAULT_XPATH = ".//text()"
MAX_URL_RETRIES = 25
SAMPLE_URL = "http://www.cbgaindia.org/"
TEXT_DOC_XPATH = "//text()"

class ScrappingUtils(object):
    def __init__(self):
        '''Initializes session for scrapping utils
        '''
        self.session = requests.Session()
        self.session.mount(SAMPLE_URL, HTTPAdapter(MAX_URL_RETRIES))

    def fetch_page(self, url):
        '''Fetches URL and return its textual content, in case of error returns empty text
        '''
        page_text = ''
        try:
            response = self.session.get(url, stream=True)
            page_text = response.text
        except Exception, error_message:
            logger.error("Unable to fetch following URL: %s, error message: %s" % (url, error_message))
        return page_text

    def check_and_create_file_path(self, file_path):
        '''Check if filepath exists else create it
        '''
        try:
            dir_path = os.path.dirname(os.path.realpath(file_path))
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        except Exception, error_message:
            logger.error("Unable to create filepath: %s, error message: %s" % (file_path, error_message))  

    def fetch_and_save_file(self, url, file_path):
        '''Fetches URL and save it as file
        '''
        try:
            self.check_and_create_file_path(file_path)
            response = self.session.get(url, stream=True)
            if response.status_code == 200:
                with open(file_path, 'wb') as file_obj:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, file_obj)
        except Exception, error_message:
            logger.error("Unable to fetch file at following URL: %s, error message: %s" % (url, error_message)) 

    def get_page_dom(self, url):
        '''Fetches page from URL and returns dom tree
        '''
        dom_tree = None
        page_text = self.fetch_page(url)
        if page_text:
            dom_tree = etree.HTML(page_text)
        return dom_tree
    
    def get_links_from_dom(self, dom_tree, xpath):
        '''Fetches links from Page DOM by the xpaths
        '''
        return dom_tree.xpath(xpath)

    def get_links_from_url(self, url, xpath):
        '''Fetches links from URL by the xpaths
        '''
        links = []
        dom_tree = self.get_page_dom(url)
        if dom_tree is not None:
            links = self.get_links_from_dom(dom_tree, xpath)
        return links

    def get_text_from_element(self, element, remove_new_lines=True, xpath=None, join_operator=None):
        '''Retrives text from a etree element in a customizable way
        '''
        if not xpath:
            xpath = DEFAULT_XPATH
        if not join_operator:
            join_operator = ' '
        element_text = join_operator.join(element.xpath(xpath))
        if remove_new_lines:
            element_text = re.sub(r"\s{2,}|\r\n", " ", element_text).strip()
        else:
            element_text = re.sub(r" {2,}|\r\n", " ", element_text).strip()
        return element_text

    def save_file_as_txt(self, page_text, file_path, xpath=TEXT_DOC_XPATH):
        '''Saves HTML page text as TXT file document
        '''
        dom_tree = etree.HTML(page_text)
        doc_text = self.get_text_from_element(dom_tree, remove_new_lines=False, xpath=xpath, join_operator="\n")
        doc_text = re.sub(r"\n{2,}", "\n", doc_text)
        txt_file = open(file_path, "wb")
        txt_file.write(doc_text)
        txt_file.close()    
