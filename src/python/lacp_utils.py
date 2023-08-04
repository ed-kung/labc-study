import re
import pandas as pd

PREFIX_DATA = {
    'pfx_AA': ('Advisory Agency (AA)', ['AA']),
    'pfx_ADM': ('Administrative Review (ADM)', ['ADM']),
    'pfx_APC': ('Area Planning Commission (APC)', ['APCC','APCE','APCH','APCNV','APCS','APCSV','APCW']), 
    'pfx_CPC': ('City Planning Commission (CPC)', ['CPC']),
    'pfx_DIR': ('Director of Planning (DIR)', ['DIR']),
    'pfx_TT': ('Tentative Tract (TT/VTT)', ['TT','VTT']),
    'pfx_ZA': ('Zoning Administration (ZA)',['ZA']),
    'pfx_ENV': ('Environmental (ENV)',['ENV']),
}

SUFFIX_DATA = {
    'sfx_CE': ('Environmental Exemption (CE/SE)', ['CE','SE']),
    'sfx_DB': ('Density Bonus (DB)', ['DB']),
    'sfx_MND': ('EIR Mitigated/Negative Dec (MND/ND)', ['MND','ND']), 
    'sfx_SPR': ('Site Plan Review (SPR)', ['SPR']),
    'sfx_SPP': ('Specific Plan Permit Compliance (SPP*)', ['SPP','SPPA','SPPM']),
    'sfx_TOC': ('Transit Oriented Communities (TOC)', ['TOC']),
    'sfx_EAF': ('Environmental Assessment (EAF)', ['EAF']),
    'sfx_ZAA': ('Area/Height/Yard/Bldg Line Adjustments (ZAA)', ['ZAA']),
    'sfx_CPIOC': ('CPIO Clearance (CPIOC)', ['CPIOC']),
    'sfx_ZV': ('Zone Variance (ZV)', ['ZV']),
    'sfx_CU': ('Conditional User Permit (CU*)', ['CU','CUB','CUE','CUW','CUX','VCU']), 
    'sfx_OVR': ('Overlay Review (OVR)', ['OVR']), 
    'sfx_ZC': ('Zone Change (ZC)', ['ZC','VZC']),
    'sfx_ZCJ': ('Zone Change Measure JJJ (ZCJ)',['ZCJ','VZCJ']),
    'sfx_DRB': ('Design Review Board (DRB)', ['DRB']), 
    'sfx_CDO': ('Community Design Overlay (CDO)', ['CDO']), 
    'sfx_HCA': ('Housing Crisis Act (HCA)', ['HCA','VHCA']), 
    'sfx_PMEX': ('Parcel Map Exemption (PMEX)', ['PMEX']), 
    'sfx_WDI': ('Waiver of Dedication and Improvements (WDI)',['WDI']), 
    'sfx_PMLA': ('Parcel Map (PMLA)',['PMLA','PMUL']), 
    'sfx_PAB': ('Plan Approval Booze (PAB)',['PAB']), 
    'sfx_MCUP': ('Master Conditional Use Permit (MCUP)',['MCUP']), 
    'sfx_HD': ('Height District (HD)',['HD']), 
    'sfx_CLQ': ('Clarification of Q Conditions (CLQ)',['CLQ']), 
    'sfx_MPA': ('Master Plan Approval (MPA)',['MPA']), 
    'sfx_EIR': ('Environmental Impact Report (EIR)',['EIR']), 
    'sfx_GPA': ('General Plan Amendment (GPA)',['GPA']), 
    'sfx_COC': ('Certificate of Compliance (COC)',['COC']), 
    'sfx_SIP': ('Streamlined Infill Process (SIP)',['SIP']), 
    'sfx_TDR': ('Transfer Development Rights (TDR)',['TDR']),
    'sfx_ZAD': ('Zoning Administrator Determination (ZAD)',['ZAD','ZAI']),
    'sfx_PHP': ('Priority Housing Project (PHP)',['PHP']), 
    'sfx_RDP': ('Redevelopment Plan Project (RDP)',['RDP','RDPA']), 
    'sfx_CDP': ('Coastal Development Permit (CDP)',['CDP']), 
    'sfx_ADU': ('Accessory Dwelling Unit (ADU)',['ADU','ADUH','WVR']),
}

# PREFIX_MAP maps highly specific prefixes to broader groups
PREFIX_MAP = {}
for k, v in PREFIX_DATA.items():
    for prefix in v[1]:
        PREFIX_MAP[prefix] = k

# SUFFIX_MAP maps highly specific suffixes to broader groups
SUFFIX_MAP = {}
for k, v in SUFFIX_DATA.items():
    for suffix in v[1]:
        SUFFIX_MAP[suffix] = k

# PREFIX_DUMMIES is the list of prefix dummies with their human-readable descriptions
PREFIX_DUMMIES = {}
for k, v in PREFIX_DATA.items():
    PREFIX_DUMMIES[k] = v[0]
        
# SUFFIX_DUMMIES is the list of suffix dummies with their human-readable descriptions
SUFFIX_DUMMIES = {}
for k, v in SUFFIX_DATA.items():
    SUFFIX_DUMMIES[k] = v[0]

def parse_casenum(casenum, raw=True):
    tokens = casenum.split('-')
    parsed = {'prefix':'', 'year':'', 'canonical_casenum':'', 'suffixes':[]}
    
    prefix = tokens[0]
    
    parsed['prefix'] = prefix
    
    if len(tokens)>1:
        token1 = tokens[1]
        if pd.to_numeric(token1, errors='coerce')<=2022:
            parsed['year'] = tokens[1]

        if len(tokens)<=2:
            parsed['canonical_casenum'] = '-'.join(tokens)
        else:
            parsed['canonical_casenum'] = '-'.join(tokens[0:3])
            parsed['suffixes'] = tokens[3:]

        return parsed
    else:
        parsed['canonical_casenum'] = tokens[0]
    
    return parsed

def count_prefixes(df, casenum_label, raw=True):
    cache = {}
    for idx, row in df.iterrows():
        casenum = row[casenum_label]
        parsed_casenum = parse_casenum(casenum)
        prefix = parsed_casenum['prefix']
        if not raw:
            prefix = PREFIX_MAP.get(prefix, 'OTHER')
        if prefix not in cache:
            cache[prefix] = {'count': 0}
        cache[prefix]['count'] += 1
    return pd.DataFrame.from_dict(cache, orient='index').sort_values(by='count', ascending=False)
        
def count_suffixes(df, casenum_label, raw=True):
    cache = {}
    for idx, row in df.iterrows():
        casenum = row[casenum_label]
        parsed_casenum = parse_casenum(casenum)
        suffixes = parsed_casenum['suffixes']
        for suffix in suffixes:
            if suffix not in cache:
                cache[suffix] = {'count': 0}
            cache[suffix]['count'] += 1
    return pd.DataFrame.from_dict(cache, orient='index').sort_values(by='count', ascending=False)
    
def get_prefix(casenum, raw=True):
    parsed_casenum = parse_casenum(casenum)
    prefix = parsed_casenum['prefix']
    if raw:
        return prefix
    else:
        return PREFIX_MAP[prefix]

def get_year(casenum):
    parsed_casenum = parse_casenum(casenum)
    year = parsed_casenum['year']
    return pd.to_numeric(year, errors='coerce')

def get_canonical(casenum):
    try:
        parsed_casenum = parse_casenum(casenum)
        canonical = parsed_casenum['canonical_casenum']
    except:
        canonical = ''
    return canonical
    
def attach_prefix_dummies(df, casenum_label):
    df = df.copy()
    colnames = []
    for dum in PREFIX_DUMMIES:
        df[f'{dum}'] = 0
        colnames.append(f'{dum}')
    for idx, row in df.iterrows():
        casenum = row[casenum_label]
        parsed = parse_casenum(casenum)
        prefix = parsed['prefix']
        if prefix in PREFIX_MAP:
            prefix = PREFIX_MAP[prefix]
        if prefix in PREFIX_DUMMIES:
            df.loc[idx, f'{prefix}'] = 1
    return df
    
def attach_suffix_dummies(df, casenum_label):
    df = df.copy()
    colnames = []
    for dum in SUFFIX_DUMMIES:
        df[f'{dum}'] = 0
        colnames.append(f'{dum}')
    for idx, row in df.iterrows():
        casenum = row[casenum_label]
        parsed = parse_casenum(casenum)
        suffixes = parsed['suffixes']
        for suffix in suffixes:
            if suffix in SUFFIX_MAP:
                suffix = SUFFIX_MAP[suffix]
            if suffix in SUFFIX_DUMMIES:
                df.loc[idx, f'{suffix}'] = 1
    return df


    
