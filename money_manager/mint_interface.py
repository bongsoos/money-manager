#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
mint_interface.py

Money manager: Mint interfance tools

(C) bongsoos 2017
'''

from __future__ import division
import numpy as np
import pandas as pd
import pdb

pd.set_option("display.width", 1000)
pd.set_option("display.max_rows", 10000)
pd.set_option("display.max_columns", 30)

class MoneyManager( object ):
    def __init__( self, filepath ):
        '''
        filepath (str): /path/to/mint/downloaded/transaction/csv/file
        '''
        self._filepath = filepath
        self.df = pd.read_csv( filepath )
        reset_columns( self.df )
        self.dfs = {}
        self.summaries = {}

    def __repr__(self):
        class_name = self.__class__.__name__ + '\n' + '-' * len( self.__class__.__name__ )
        f_transact = "\nTransaction File: {}\n".format( self._filepath )
        summaries = '\nCategorical Summaries:\n- ' + ' \n- '.join( self.summaries.keys() )
        if ( self.summaries ):
            return class_name + f_transact + summaries
        else:
            return class_name + f_transact

    def view_summaries( self ):
        keys = [ key.split('-') for key in self.summaries ]
        keys.sort( key=lambda x: int(x[0])*int(x[1]) )
        for key in [ '-'.join(k) for k in keys ]:
            print key, self.summaries[key], '\n'

    def categorical_summary( self, year=None, month=None, day=None ):
        '''
        return money flow in categorical summary of year-month-day.
        results will be also stored in `summaries` dict type variable.

        Input
        -----
        year (int)
        month (int)
        day (int)

        Output
        ------
        cs (CatagoricalSummary)
        '''
        df = filter_timeperiod( self.df, year=year, month=month, day=day )

        cs = CategoricalSummary( df )

        if ( day ):
            self.summaries[ '-'.join([str(year), str(month), str(day)]) ] = cs
            self.dfs[ '-'.join([str(year), str(month), str(day)]) ] = df
        else:
            self.summaries[ '-'.join([str(year), str(month)]) ] = cs
            self.dfs[ '-'.join([str(year), str(month)]) ] = df

        return cs


def reset_columns( df ):
    '''
    reset columns of input DataFrame

    Input
    -----
    df (pd.DataFrame)
    '''
    df.columns = ['date', 'descr', 'orig_descr', 'amount', 'type', 'category', 'account', 'labels', 'notes']


def filter_timeperiod( df, year=None, month=None, day=None ):
    '''
    DataFrame filter based on year, month, day

    Input
    -----
    df (pd.DataFrame)
    year (int)
    month (int)
    day (int)

    Output
    ------
    df_ (pd.DataFrame): filtered DataFrame
    '''

    dates = [ d.split('/') for d in list(df.date)]

    if ( year and not month and not day ):
        cond = np.array([ int(d[2])==int( year ) for d in dates ])
        return df[ cond ]

    elif ( year and month and not day ):
        cond = np.array([ int(d[0])==int( month ) and int(d[2])==int( year ) for d in dates ])
        return df[ cond]

    elif ( year and not month and day ):
        cond = np.array([ int(d[1])==int( day ) and int(d[2])==int( year ) for d in dates ])
        return df[ cond]

    elif ( year and month and day ):
        cond = np.array([ int(d[0])==int( month ) and int(d[1])==int( day ) and int(d[2])==int( year ) for d in dates ])
        return df[ cond]

    elif ( not year and month and not day ):
        cond = np.array([ int(d[0])==int( month ) for d in dates ])
        return df[ cond]

    elif ( not year and not month and day ):
        cond = np.array([ int(d[1])==int( day ) for d in dates ])
        return df[ cond]

    elif ( not year and month and day ):
        cond = np.array([ int(d[0])==int( month ) and int(d[1])==int( day ) for d in dates ])
        return df[ cond]

    else:
        return df


class Type( object ):
    def __init__( self, df_debit, df_credit ):
        '''
        Input
        -----
        df_debit (pd.DataFrame)
        df_credit (pd.DataFrame)
        '''
        self.debit = df_debit
        self.credit = df_credit

    def __repr__(self):
        fmt = self.__dict__.keys()
        return self.__class__.__name__ + '\n- ' + ' \n- '.join(fmt)

class CategoricalSummary( object ):
    '''
    fields
    ------
    - spending
        - debit
        - credit
    - checking
        - debit
        - credit
    '''
    _fields = ['spending', 'checking']

    def __init__( self, df ):
        self._categorical_summary( df )
        self._net_spending, self._paycheck, self._tot_income, self._net_incomes = self._net_income()
        self._savings = self._get_savings( df )
        self._net = self._net_incomes
        self._net_spending -= self._savings

    @property
    def net(self):
        return {'spending':self._net_spending, 'tot-income': self._tot_income, 'paycheck': self._paycheck, 'savings': self._savings, 'net':self._net}

    def __repr__(self):
        fmt = '\n * '.join([ key + ': ' + str(self.net[key]) for key in ['tot-income', 'paycheck', 'spending', 'savings', 'net']])
        return self.__class__.__name__ + '\n- ' + ' \n- '.join( self._fields ) + '\n * ' + fmt

    def _net_income( self ):
        '''
        return net spending, paycheck (income), and net income
        only available after running `_categorical_summary`
        '''
        m = self.spending.credit.tot_amount.size

        credit = self.spending.credit.tot_amount.sum() if ( m ) else 0

        m = self.checking.debit.tot_amount.size
        checking_debit = self.checking.debit.tot_amount.sum() if ( m ) else 0

        spending_net = self.spending.debit.tot_amount.sum() + checking_debit - credit
        paycheck, tot_income = self._get_incomes()

        return spending_net, paycheck, tot_income, tot_income-spending_net

    def _get_savings( self, df ):
        '''
        '''
        # is_transfer = df.category == 'Transfer'
        is_barclay = [ 'Barclay' in descr for descr in df.descr ]
        is_type_debit = df.type == 'debit'
        is_checking = [ 'checking' in acc.lower() for acc in df.account ]

        df_temp = df[ ( is_barclay ) & ( is_type_debit ) & ( is_checking ) ]
        savings = df_temp.amount.sum() if ( df_temp.size ) else 0
        # savings = df[ (is_barclay) & (is_transfer) ].amount.sum()
        # savings = df[ is_barclay ].amount.sum()

        return savings

    def _get_incomes( self ):
        '''
        return `ndarray` of all incomes in checking.credit DataFrame
        only available after running `_categorical_summary`
        '''
        is_paycheck = self.checking.credit.category == 'Paycheck'
        is_income = self.checking.credit.category == 'Income'
        is_transfer = self.checking.credit.category == 'Transfer'

        paycheck = self.checking.credit[ is_paycheck ].tot_amount.values
        tot_income = self.checking.credit[ (is_paycheck) | (is_income) | (is_transfer)].tot_amount.values

        return paycheck.sum(), tot_income.sum()

    def _categorical_summary( self, df ):
        '''
        return categorical summary

        Input
        -----
        df (pd.DataFrame)

        Output
        ------
        df_ (pd.DataFrame): filtered DataFrame
        '''

        debit = 'debit'
        credit = 'credit'

        categories = df.category.unique()

        cols = ['category', 'tot_amount', 'num_entries', 'mean_amount', 'std_amount', 'min','q25', 'median_ammount', 'q75', 'max']

        checking = df.account.unique()[[ 'checking' in acc.lower() for acc in df.account.unique()]]
        not_checking = df.account.unique()[[ 'checking' not in acc.lower() for acc in df.account.unique()]]

        def categorical_summary_helper( df, cat, typ, table_list, is_checking=False ):

            exceptions = ['Credit Card Payment']

            if ( is_checking ):
                df_ = pd.concat( [ df[ ( df.category == cat ) & ( df.type == typ ) & ( df.account == acc ) ] for acc in checking ] )

            else:
                df_ = pd.concat( [ df[ ( df.category == cat ) & ( df.type == typ ) & ( df.account == acc ) ] for acc in not_checking ] )

            num_entries, _ = df_.shape
            if ( num_entries and cat not in exceptions ):
                amount_stats = df_.amount.describe()
                tup = [ cat, df_.amount.sum() ] + list( amount_stats )
                table_list.append( tup )

        table_list_checking_debit = []
        table_list_checking_credit = []
        table_list_debit = []
        table_list_credit = []
        for cat in categories:
            categorical_summary_helper( df, cat, debit, table_list_debit, is_checking=False )
            categorical_summary_helper( df, cat, credit, table_list_credit, is_checking=False )
            categorical_summary_helper( df, cat, debit, table_list_checking_debit, is_checking=True )
            categorical_summary_helper( df, cat, credit, table_list_checking_credit, is_checking=True )

        df_spending_debit = pd.DataFrame( table_list_debit, columns=cols ).sort_values( 'tot_amount', ascending=False )
        df_spending_credit = pd.DataFrame( table_list_credit, columns=cols ).sort_values( 'tot_amount', ascending=False )
        df_checking_debit = pd.DataFrame( table_list_checking_debit, columns=cols ).sort_values( 'tot_amount', ascending=False )
        df_checking_credit = pd.DataFrame( table_list_checking_credit, columns=cols ).sort_values( 'tot_amount', ascending=False )

        self.spending = Type( df_spending_debit, df_spending_credit )
        self.checking = Type( df_checking_debit, df_checking_credit )

class Accounts( object ):
    def __repr__(self):
        fmt = self.__dict__.keys()
        return self.__class__.__name__ + '\n- ' + ' \n- '.join(fmt)

class Categories( object ):
    def __repr__(self):
        fmt = self.__dict__.keys()
        return self.__class__.__name__ + '\n- ' + ' \n- '.join(fmt)

class AccountManager( object ):
    '''
    Sort into Checking accounts and Credit cards
    '''
    def __init__( self, df=None ):
        if ( isinstance( df, pd.DataFrame ) ):
            accounts_ischecking = sort_by_ischecking( df )

            self.df_checking, self.df_creditcards = accounts_ischecking.checking, accounts_ischecking.creditcards

            self.accounts_checking = sort_by_account( self.df_checking )

            accounts_creditcards = sort_by_account( self.df_creditcards )

            self.accounts_creditcards = Accounts()
            for key in accounts_creditcards.__dict__.keys():
                self.accounts_creditcards.__dict__[key] = sort_by_category( accounts_creditcards.__dict__[key] )

            self.categories_checking = sort_by_category( self.df_checking )
            self.categories_creditcards = sort_by_category( self.df_creditcards )


    def __repr__(self):
        fmt = self.__dict__.keys()
        return self.__class__.__name__ + '\n- ' + ' \n- '.join(fmt)

def sort_by_type( df ):
    '''
    return Accounts object ( debit vs. credit )
    items of the object are DataFrame
    '''
    debit = 'debit'
    credit = 'credit'

    accounts = Accounts()
    accounts.debit = df[ ( df.type == debit ) ]
    accounts.credit = df[ ( df.type == credit ) ]

    return accounts

def sort_into_account_type( df ):
    '''
    return Type objects of filtered DataFrames ( checking accounts, credit cards )
    '''
    debit = 'debit'
    credit = 'credit'

    is_checking = np.array( [ 'checking' in acc.lower() for acc in df.account ] )


    objtyp_checking = Type( df[ ( df.type == debit ) & ( is_checking ) ], df[ ( df.type == credit ) & ( is_checking ) ] )
    objtyp_not_checking = Type( df[ ( df.type == debit ) & ( ~is_checking ) ], df[ ( df.type == credit ) & ( ~is_checking ) ] )

    return objtyp_checking, objtyp_not_checking

def sort_by_ischecking( df ):
    '''
    return Accounts object ( checking vs. credit cards )
    items of the object are DataFrame
    '''
    is_checking = np.array( [ 'checking' in acc.lower() for acc in df.account ] )

    accounts = Accounts()
    accounts.checking = df[ ( is_checking ) ]
    accounts.creditcards = df[ ( ~is_checking ) ]

    return accounts

def sort_by_account( df ):
    '''
    return Accounts object
    items of the object are DataFrame
    '''
    accounts = Accounts()
    for account in df.account.unique():
        key = ''.join(e for e in account if e.isalnum())
        accounts.__dict__[key] = df[ ( df.account == account ) ]

    return accounts

def sort_by_category( df ):
    '''
    return Accounts object
    items of the object are DataFrame
    '''
    categories = Categories()
    for category in df.category.unique():
        key = ''.join(e for e in category if e.isalnum())
        categories.__dict__[key] = df[ ( df.category == category ) ]

    return categories

def sort_by_descr( df ):
    '''
    return Accounts object
    items of the object are DataFrame
    '''
    categories = Categories()
    for category in df.descr.unique():
        key = ''.join(e for e in category if e.isalnum())
        categories.__dict__[key] = df[ ( df.descr == category ) ]

    return categories



