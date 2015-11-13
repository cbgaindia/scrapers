'Code for scrapping 2003-10 years Union Budget Data'

from datetime import date
import logging
from logging.config import fileConfig
from lxml import etree
import re
from scrapping_utils import ScrappingUtils
import xlwt

fileConfig('logging_config.ini')
logger = logging.getLogger()
BASE_URL = "http://indiabudget.nic.in/"
PREVIOUS_YEARS_URL = "http://indiabudget.nic.in/previousub.asp"
OUT_FOLDER = "union_budgets"
BUDGET_CATEGORIES_XPATH = "//table/tbody/tr/td[@class='h1' and @align]/../td/a[@href]"
SUB_CATEGORIES_XPATH = "//td[@align='left']//a[@href]|//td[@align='left']/../td//a[@href]"
TEXT_DOC_XPATH = "//table[@class='t1']//text()"
CHILD_LINKS_XPATH = "//div[@class='contentPanInner']//div[@class='content']//a"  
COLOUMS_XPATH = "//table[@bordercolor and not(@class='MsoNormalTable')]//tr[1]/td"
FILENAME_XPATH = ".//preceding::td[1]//text()"
PARENT_NODE_TEXT_XPATH = "./preceding::td[1]/text()"
DEFAULT_XLS_SHEET_NAME = "Sheet1"
TABLES_XPATH = ".//table[@class='t1' and not(@style)]/tbody" 
DEFAULT_STYLE = xlwt.easyxf("align: wrap on, vert centre, horiz left; border: left thin, right thin, bottom thin, top thin")
HEADING_STYLE = xlwt.easyxf("font: bold on; align: wrap on, vert centre, horiz center; border: left medium, right medium, bottom medium, top medium")
TABLE_STYLE = xlwt.easyxf("align: wrap on, vert centre, horiz left; border: left medium, right medium, bottom medium, top medium")
COLUMN_WIDTH_MULTIFIER = 260
LANGUAGE_TAGS = ["English", "Hindi"] 

class UnionBudgetsScrapper2003_10(ScrappingUtils):
    def fetch_docs_for_year(self, year, base_url=BASE_URL):
        '''Fetches all documents for a budget year
        '''
        links = self.get_links_from_url(base_url, BUDGET_CATEGORIES_XPATH)
        for link in links:
            out_link = "/".join(base_url.split("/")[:-1]) + "/" + link.xpath('@href')[0] 
            link_text = self.get_text_from_element(link)
            download_dir = "%s/%s/%s" % (OUT_FOLDER, year, link_text)
            self.fetch_child_section_docs(out_link, download_dir, base_url)

    def get_text_from_element(self, element, remove_new_lines=True, xpath=None, join_operator=None):
        '''Extends parent class functionality to take care of text formatting
        '''
        element_text = super(UnionBudgetsScrapper2003_10, self).get_text_from_element(element, remove_new_lines, xpath, join_operator)
        element_text = element_text.replace(">", "").replace(u"\xa0","")
        element_text = element_text.replace("/", "|")
        element_text = element_text.encode('utf-8').strip()
        return element_text

    def fetch_child_section_docs(self, url, download_dir, base_url):
        '''Fetches child section of a HTML document
        '''
        child_links = self.get_links_from_url(url, BUDGET_CATEGORIES_XPATH + "|" + SUB_CATEGORIES_XPATH)
        for child_link in child_links:
            link_text = self.get_text_from_element(child_link)
            child_href = child_link.xpath('@href')[0] 
            if child_link is None or not link_text:
                continue
            if ".." in child_href:
                child_url = BASE_URL + child_href.split("..")[-1]
            else:
                child_url = "/".join(url.split("/")[:-1]) + "/" + child_href 
            if ".htm" in child_url:
                out_dir = download_dir + "/" + link_text
                out_links = self.fetch_child_section_docs(child_url, out_dir, base_url)
                if not out_links:
                    page_text = self.fetch_page(child_url)
                    self.check_and_create_file_path(out_dir)
                    file_path = out_dir + ".xls"
                    if not self.save_file_as_xls(page_text, file_path):
                        file_path = file_path.replace(".xls", ".txt")
                        self.save_file_as_txt(page_text, file_path)
            else:
                self.save_link_as_file(child_link, download_dir, url)
        return child_links

    def get_file_name_for_link(self, link):
        '''Derive file name from the HTML link element
        '''
        file_name = self.get_text_from_element(link)
        file_name_found = False
        file_language = None
        while not file_name_found:
            language_tag_found = False
            for language_tag in LANGUAGE_TAGS:
                if language_tag in file_name:
                    file_name = self.get_text_from_element(link, xpath=FILENAME_XPATH)
                    FILENAME_XPATH = "./." + FILENAME_XPATH
                    language_tag_found = True
                    if not file_language:
                        file_language = language_tag
                    break
            if not language_tag_found:        
                file_name_found = True
                break
        if file_language:
            temp_file_name = re.sub(r"\[|\]", "", file_language)
            if file_name:
                previous_arrow_node = link.xpath("./preceding::tr[not(contains(.,'%s'))][1]/td[contains(.,'>')][1]" % file_language)
                current_node_text = " ".join(link.xpath(PARENT_NODE_TEXT_XPATH))
                if not ">" in current_node_text and previous_arrow_node:
                    precursor_name = self.get_text_from_element(link, xpath="./preceding::tr[1]/td[1]//text()")
                    file_name = precursor_name + " " +file_name    
                file_name = temp_file_name + "/" + file_name
            else:
                file_name = temp_file_name
        return file_name

    def save_link_as_file(self, link, download_dir, base_url=BASE_URL, file_name=None):
        '''Fetches link as a file and save it on the disk
        '''
        if not file_name:
            file_name = self.get_file_name_for_link(link) 
        sub_link = link.xpath("@href")[0] 
        base_url = "/".join(base_url.split("/")[:-1])
        file_link = base_url + "/" + sub_link
        file_path = download_dir + "/" + file_name + "." + file_link.split(".")[-1]
        self.fetch_and_save_file(file_link, file_path)

    def sanitize_page_text(self, page_text):
        '''Remove HTML elements that cause trouble in XPATHs
        '''
        page_text = re.sub(r"<strong>|</strong>|&nbsp;", " ", page_text)
        page_text = re.sub(r"<br>", "\n", page_text)
        return page_text

    def save_file_as_xls(self, page_text, out_xls_filepath):
        '''Saves HTML page text as XLS file document  
        '''
        is_htm_xls = False
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(DEFAULT_XLS_SHEET_NAME)
        page_text = self.sanitize_page_text(page_text)
        dom_tree = etree.HTML(page_text)
        max_col_count = len(dom_tree.xpath(COLOUMS_XPATH)) 
        if max_col_count == 0:
            return is_htm_xls
        is_htm_xls = True
        tables = dom_tree.xpath(TABLES_XPATH)
        row_counter = 0
        for table_node in tables:
            row_counter = self.write_tabular_data(table_node, row_counter, worksheet, max_col_count)
        workbook.save(out_xls_filepath)
        return is_htm_xls

    def get_rows_to_write(self, table_node):
        '''Create list of rows to be written in XLS file
        '''
        row_list = []
        row_elements = table_node.xpath("./tr")
        for row in row_elements:
            columns = row.xpath('./td')
            if columns:
                row_value = []
                for cell in columns:
                    child_tables = cell.xpath('.//table[@class]')
                    data_desc_nodes = cell.xpath('./p[../div/table]|./blockquote[../div/table]')
                    coloumn_class = cell.xpath('./@class') 
                    if child_tables:
                        row_list += self.get_rows_to_write(child_tables[0])
                    else:
                        if coloumn_class == ["h1"]:
                            data_desc_nodes.append(cell)
                        else:
                            cell_text = self.get_text_from_element(cell)
                            row_value.append(cell_text)
                    if data_desc_nodes:
                        for data_desc_node in data_desc_nodes:
                            cell_text = self.get_text_from_element(data_desc_node, remove_new_lines=False).strip()
                            for cell_value in cell_text.split("\n"):
                                if cell_value.strip():
                                    row_list.append([cell_value.strip()])
                if "".join(row_value).strip():
                    row_list.append(row_value)
        return row_list

    def write_tabular_data(self, table_node, row_counter, worksheet, max_col_count=1):
        '''Write data rows in XLS file
        '''
        rows = self.get_rows_to_write(table_node)
        if not rows:
            return row_counter
        max_col_len = []
        for row in rows:
            if len(row) == 1:
                if row_counter == 0:
                    worksheet.write_merge(row_counter, row_counter, 0, max_col_count-1, row[0], HEADING_STYLE)            
                else:
                    worksheet.write_merge(row_counter, row_counter, 0, max_col_count-1, row[0], DEFAULT_STYLE)            
            else:
                col_counter = 0
                for cell in row:
                    worksheet.write(row_counter, col_counter, cell, TABLE_STYLE)
                    if len(max_col_len) == col_counter:
                        max_col_len.append(len(cell))
                    if len(cell) > max_col_len[col_counter]:
                        max_col_len[col_counter] = len(cell)
                    worksheet.col(col_counter).width = int(max_col_len[col_counter]*COLUMN_WIDTH_MULTIFIER)
                    col_counter += 1    
            row_counter += 1
        return row_counter

    def fetch_all_union_budget_docs(self):
        '''Fetches all the Union Budget docs from home page
        '''
        links = self.get_links_from_url(PREVIOUS_YEARS_URL, CHILD_LINKS_XPATH)
        for link in links:
            link_text = link.text 
            start_year = int(link_text.split("-")[0])
            if start_year >= 2003 and start_year <= 2010:
                link_url = BASE_URL + link.xpath("@href")[0] 
                logger.info("Fetching Union Budget Documents for year: %s from URL: %s" % (link_text, link_url))
                self.fetch_docs_for_year(link_text, link_url)

if __name__ == '__main__':
    obj = UnionBudgetsScrapper2003_10()
    obj.fetch_all_union_budget_docs()
