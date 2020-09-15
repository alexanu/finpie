#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# finpie - a simple library to download some financial data
# https://github.com/peterlacour/finpie
#
# Copyright (c) 2020 Peter la Cour
#
# Licensed under the MIT License
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import time
import pandas as pd
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from finpie.base import DataBase

class MacrotrendsData( DataBase ):

    def __init__( self, ticker, freq = 'A' ):
        super.__init__(self)
        self.ticker = ticker
        self.freq = freq

    def income_statement(self):
        return self._download('income-statement')


    def balance_sheet(self):
        return self._download('balance-sheet')


    def cashflow_statement(self):
        return self._download('cash-flow-statement')


    def ratios(self):
        return self._download('financial-ratios')


    def _get_table(self, page_source):
        soup = bs(page_source, 'html5lib')
        rows = soup.find_all('div', attrs = { 'role': 'row' } )
        temp = []
        for row in rows:
            temp.append( [ cell.text for cell in row.find_all('div', attrs = { 'role': 'gridcell' } ) ] )
        df = pd.DataFrame( temp, columns = [ col.text for col in soup.find_all('div', attrs = { 'role': 'columnheader' } ) ] )
        df.drop('', axis = 1, inplace = True)
        df.columns = ['Item'] + df.columns[1:].to_list()
        df.index = df.Item
        df.drop('Item', axis = 1, inplace = True)
        return df


    def _download(self, sheet):

        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "none"
        driver = self._load_driver(caps = caps)
        if self.head == True:
            driver.minimize_window()
        url = f'https://www.macrotrends.net/stocks/charts/{self.ticker}'

        try:
            driver.get(url)
            time.sleep(2)
            url = driver.current_url + f'{sheet}?freq={self.freq.upper()}'
            driver.get(url)
            #print(driver.find_elements_by_xpath( '//div[@role="columnheader"]')[2].text)
            element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//div[@class="jqx-reset jqx-icon-arrow-right"]')))
        except:
            print('Failed to load page...')
            driver.quit()
            return None

        dfs = [ self._get_table(driver.page_source) ]
        bool, check, double_check = True, '', 0
        first = driver.find_elements_by_xpath( '//div[@role="columnheader"]')[2].text

        while bool:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@class="jqx-reset jqx-icon-arrow-right"]')))
            element = driver.find_element_by_xpath('//div[@class="jqx-reset jqx-icon-arrow-right"]')
            ActionChains(driver).click_and_hold(element).perform()
            time.sleep(2)
            first = driver.find_elements_by_xpath( '//div[@role="columnheader"]')[2].text
            ActionChains(driver).release(element).move_by_offset(-50, -50).perform()

            dfs.append( self._get_table(driver.page_source) )

            if check == first: #driver.find_elements_by_xpath( '//div[@role="columnheader"]')[-1].text:
                if double_check == 3:
                    bool = False
                double_check += 1

            check = first #driver.find_elements_by_xpath( '//div[@role="columnheader"]')[-1].text

        df = pd.concat(dfs, axis = 1)
        df = df.loc[:,~df.columns.duplicated()]
        driver.quit()

        df.replace('\$', '', regex = True, inplace = True)
        df.replace(',', '', regex = True, inplace = True)
        df.replace('-', '', regex = True, inplace = True)
        df = df.transpose()
        df.columns = [ col.replace(' ', '_').replace('/','_to_').replace('.', '').replace('__', '_').replace('-', '').replace('&', 'and').lower() for col in df.columns ]
        df.replace('', 'nan', inplace = True)
        df.index = pd.to_datetime(df.index, format = '%Y-%m-%d')
        df.sort_index(inplace = True)
        return self._col_to_float(df).astype('float')
