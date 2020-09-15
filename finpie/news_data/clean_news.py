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

import numpy as np
import pandas as pd
import datetime as dt
from finpie.base import DataBase

class CleanNews(DataBase):

    def __init__(self):
        DataBase.__init__(self)
        self.months = { 'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06', \
                       'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12' }
        self.weekdays = [ 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun' ]
        self.dayz = [ 'Today', 'Yesterday' ]
        self.filterz = [ ' ' ]

    def _format_date( self, date ):
        '''

        '''
        y = str(date.year)
        if len(str(date.month) ) < 2:
            m = '0' + str(date.month)
        else:
            m = str(date.month)
        if len(str(date.day) ) < 2:
            d = '0' + str(date.day)
        else:
            d =  str(date.day)
        return y, m, d

    def _clean_dates(self, data):
        '''

        '''
        data['Datetime'] = np.nan
        hour = [ (idx, hour.split(' ')[0]) for idx, hour in enumerate(data.Date) if 'hour' in hour.lower() ]
        for i, h in hour:
            data.Datetime.iloc[i] = data.Date_Retrieved.iloc[i] - dt.timedelta( hours = int(h) )

        week = [ (idx, w.split(' ')[1:]) for idx, w in enumerate(data.Date) if any(wd in w.split(' ')[0] for wd in self.weekdays) ]
        for i, w in week:
            if len(w) == 2:
                data.loc[i, 'Datetime'] = pd.to_datetime( w[1].replace(',', '')  + '/' + self.months[w[0][:3].lower()] + '/' + str(dt.datetime.today().year), format = '%d/%m/%Y' )
            else:
                data.loc[i, 'Datetime'] = pd.to_datetime( w[1].replace(',', '')  + '/' + self.months[w[0][:3].lower()] + '/' + str(w[2]), format = '%d/%m/%Y' )

        day = [ (idx, w.split(' ')[0].replace(',', '')) for idx, w in enumerate(data.Date) if any(wd in w.split(' ')[0].replace(',', '') for wd in self.dayz) ]
        for i, w in day:
            if w == 'Today':
                data.Datetime.iloc[i] = pd.to_datetime( dt.datetime.strftime(dt.datetime.today(),  format = '%d/%m/%Y'), format = '%d/%m/%Y' )
            elif w == 'Yesterday':
                data.Datetime.iloc[i] = pd.to_datetime( dt.datetime.strftime(dt.datetime.today() - dt.timedelta(days = 1),  format = '%d/%m/%Y'), format = '%d/%m/%Y' )

        hes = [ (idx, hour.split(' ')[0]) for idx, hour in enumerate(data.Date) if 'h ago' in hour.lower() ]
        for i, h in hes:
            data.Datetime.iloc[i] = data.Date_Retrieved.iloc[i] - dt.timedelta( hours = int(h.replace('h', '')) )


        for source in np.unique(data.Source):
            if source == 'sa':
                pass
            elif source == 'nyt':
                yes = [ (idx, d.split(' ')[:2]) for idx, d in enumerate(data.Date) if len(d.split(' ')[-1]) < 3 ]
                for i, y in yes:
                    data.Datetime.iloc[i] = pd.to_datetime( y[1] + '/' + self.months[y[0][:3].lower()] + '/' + str(dt.datetime.today().year), format = '%d/%m/%Y')
            elif source in ['ft', 'bloomberg']:
                data['Datetime'][ data.Source == source ] = list(pd.to_datetime( [ d.split(' ')[1][:-1] + '/' +  self.months[ d.split(' ')[0][:3].lower().replace('.', '') ] + '/' + d.split(' ')[-1] \
                                                                                             for d in data[ data.Source == source ].Date ], format = '%d/%m/%Y' ))
            elif source in ['barrons', 'wsj']:
                data['Datetime'][ data.Source == source ] = list(pd.to_datetime( [ d.split(' ')[1][:-1] + '/' +  self.months[ d.split(' ')[0][:3].lower().replace('.', '') ] + '/' + d.split(' ')[2] \
                                                                                                     for d in data[ data.Source == source ].Date ], format = '%d/%m/%Y' ))
            elif source == 'reuters':
                data['Datetime'][ data.Source == source ] = list(pd.to_datetime( [ d.split(' ')[1][:-1] + '/' +  self.months[ d.split(' ')[0][:3].lower().replace('.', '') ] + '/' + d.split(' ')[2] \
                                                                                                     for d in data[ data.Source == source ].Date ], format = '%d/%m/%Y' ))
            elif source == 'cnbc':
                data['Datetime'][ data.Source == source ] = list(pd.to_datetime( [ d.split(' ')[0].split('/')[1] + '/' + d.split(' ')[0].split('/')[0] + '/' + d.split(' ')[0].split('/')[2] \
                                                                                                     for d in data[ data.Source == source ].Date ], format = '%d/%m/%Y' ))
        data.Datetime = data.Datetime.dt.strftime('%d/%m/%Y')
        data.index = data.Datetime
        data.drop('Datetime', inplace = True, axis = 1)
        return data


    def _clean_duplicates(self, data):
        '''

        '''
        columns = [ col for col in data.columns if col != 'Date_Retrieved' ]
        data.drop_duplicates(columns, inplace = True)
        data.reset_index(drop = True, inplace = True)
        return data

    def filter_data(self, data):
        '''

        '''
        filtered = []
        for i, n in enumerate(data.Headline):
            for f in self.filterz:
                if f in n.lower():
                    filtered.append( data.ID.iloc[i] )
                elif f in data.Description.iloc[i].lower():
                    filtered.append( data.ID.iloc[i] )
                else:
                    continue

        data = data[ data.ID.isin(filtered) ]
        data.reset_index(drop = True, inplace = True)
        return data
