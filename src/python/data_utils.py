import os
import sys
import pandas as pd

'''
Import data on new DBS building permits
'''
def get_dbs_new(multifamily_only=True):
    
    df = pd.read_csv("../../data/New_Building_Permits__2010_to_Present.csv")
    
    # Clean date vars
    for col in ['SUBMITTED_DATE', 'ISSUE_DATE', 'COFO_DATE']:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        
    # Select multifamily only
    if multifamily_only:
        df = df.loc[ df['PERMIT_SUB_TYPE']!='1 or 2 Family Dwelling'].reset_index(drop=True)
        R_USES = [
            'Apartment', 
            'Condo-Multi Family', 
            'Homeless Shelter', 
            'Dwelling - multiple', 
            'Dwelling - Single Family', 
            'Accessory Dwelling Unit',
            'Duplex',
            'Apartment House', 
            'Apartment Hotel', 
            'Home for the Aged with special care', 
            'Joint Living and Working Quarters', 
            'Condo-Duplex', 
            'State Approved Dwelling/Mobile Home', 
            'Fraternity House', 
            'Accessory Living Quarters', 
            'Dwelling watchman or caretaker', 
            'Boarding Home for Aged with special care', 
            'Special Care Home'
        ]
        df = df.loc[ df['USE_DESC'].isin(R_USES)].reset_index(drop=True)
        
    # Duplicates in permit numbers, keep the row with more dwelling units
    dfg = df.groupby('PERMIT_NBR').agg(max_du = ('DU_CHANGED','max')).reset_index()
    df = df.merge(dfg, on='PERMIT_NBR', how='left')
    df = df.loc[ df['DU_CHANGED']==df['max_du']].reset_index(drop=True)
    df = df.drop(labels=['max_du'], axis=1).reset_index(drop=True)    
    
    return df

'''
Import data from PDIS
'''
def get_pdis():
    
    df = pd.read_csv("../../data/pdis_data.csv")
    
    # columns with mostly null values
    null_cols = [
        'EIR_NOTICE_DATE',
        'EIR_CIRCULATION_START_DATE',
        'EIR_CIRCULATION_END_DATE',
        'FINAL_EIR_DISTRIBUTION_DATE',
        'ZA_STAFF_ASSIGNMENT_DATE',
        'AZA_ASSIGNMENT_DATE'
    ] 
    
    # date columns
    date_cols = [
        'FILING_DATE',
        'CASE_DEEMED_COMPLETE_DATE',
        'COMPLETION_DATE',
        'ENV_CLEARANCE_DATE',
        'HEARING_DATE',
        'STAFF_ASSIGNMENT_DATE'
    ]
    
    # Drop columns with lots of nulls
    df = df.drop(labels=null_cols, axis=1)
    
    # Format date variables
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # For cases marked completed but with missing completion date, let the completion date 
    # be the max of filing date, staff assignment date, and case deemed complete date
    idx = (df['COMPLETED']=='Y') & (df['COMPLETION_DATE'].isnull())
    df.loc[idx, 'COMPLETION_DATE'] = df.loc[idx, ['FILING_DATE', 'CASE_DEEMED_COMPLETE_DATE', 'STAFF_ASSIGNMENT_DATE']].max(axis=1)
    
    # if completed date is less than filing date, make it filing date
    idx = (df['COMPLETION_DATE'].notnull()) & (df['COMPLETION_DATE'] < df['FILING_DATE'])
    df.loc[idx, 'COMPLETION_DATE'] = df.loc[idx, 'FILING_DATE']    
    
    # drop if both completion date and filing date are null
    idx = (df['COMPLETION_DATE'].isnull()) & (df['FILING_DATE'].isnull())
    df = df.loc[~idx].reset_index(drop=True)
    
    return df

    