# importing libraries
import pandas as pd # data manipulation

from tika import parser # pdf bill text extraction
from wwo_hist import retrieve_hist_data # weather data api
import re # text formatting with regex

import arrow # date formatting
import datetime as dt # date formatting

import env # encoded data

# creating function for extracting text 
def extract_pdf(filePath):
    '''
    Argument(s)
        - filePath (str): path to the pdf file to be extracted
    Returns 
        - text (str): extracted pdf text
    '''
    
    text = parser.from_file(filePath)['content']
    print(f'Text extraction from {filePath} complete.')
    
    return text


def extract_text(text, str_start, str_end):
    '''
    This functiont takes in a full text string and returns the text extracted from between the string start
    index and string end index. 
    '''
    start_index = text.index(str_start) + len(str_start)
    end_index = text.index(str_end, start_index)
    
    extracted_text = text[start_index:end_index]
    
    return extracted_text


def looped_FileExtraction(filePath_list):
    '''
    This function takes in a list of pdf file paths, loops through that list and stores the extracted
    text as dictionary values, creating associated key names based on the pdf name (bill month), and 
    reading that dictionary to pandas df.
    
    Args:
        - filePath_list (list): list of pdf file paths as strings
    
    Returns:
        - df: 
    '''
    # initiating empty dictionary to store extracted text as values and month labels as keys
    text_dict = {}

    # initializing empty list to store dictionary keys
    text_list = []

    # looping through each file path to extract text using extract_pdf() function
    for file in filePath_list:
        text_dict[f'{arrow.get(file[7:15], "YY-MM-DD".format("YYY-MM-DD"))}'[:10]] = extract_pdf(file)
        text_list.append(f'text_{arrow.get(file[7:15], "YY-MM-DD".format("YYY-MM-DD"))}')
        
    # writing dictionary to df
    df = pd.DataFrame.from_dict(text_dict, orient='index', columns = ['text'])
    df.reset_index(inplace = True)
    df.rename(columns = {'index':'bill_date'}, inplace = True)
    
    return df


def text_parse(df):
    '''
    This function takes in a df of a pdf bill date and that pdf's raw extracted text and
    parses out the bill's parts, storing parsed data in columns that are added to the 
    returned df.
    '''
    print()
    
    # initalizing empty lists to store values from loop for df
    bill_dates = []
    bills_starts = []
    bills_ends = []
    bill_periods = []
    
    meters = []
    consumptions = []
    peaks = []
    
    consumption_rates = []
    peak_rates = []
    fuel_rates = []
    regulatory_rates = []
    
    service_charges = []
    consumption_charges = []
    peak_charges = []
    fuel_charges = []
    regulatory_charges = []
    total_bills = []
    
    # looping through each bill
    for text in df.text:
    
        #################
        # BILLING INFO
        #################
        bill_date = extract_text(text, f'{env.zip}\n\n', '\n\nOn or Before')
        bill_dates.append(bill_date)
        print(f'Bill Date: {bill_date}')
        
        billing_data = extract_text(text, 'Billing Period ', '\nYour next')
        
        bill_start = arrow.get(billing_data.split('-')[0].strip(), 'MMM DD, YYYY').format('YYYY-MM-DD')
        bills_starts.append(bill_start)
        print(f'Bill Start: {bill_start}')
        
        bill_end = arrow.get(billing_data.split('-')[1].strip(), 'MMM DD, YYYY').format('YYYY-MM-DD')
        bills_ends.append(bill_end)
        print(f'Bill End: {bill_end}')
        
        bill_period = (pd.to_datetime(bill_end) - pd.to_datetime(bill_start)).days + 1
        bill_periods.append(bill_period)
        print(f'Bill Period: {bill_period} days')

        #################
        # BASE AMOUNTS
        #################
        list_ = extract_text(text, 'R-', '#6271330').replace(')', '').replace(',', '').split()
        
        meter = int(list_[1][:5])
        meters.append(meter)
        print(f'Meter Reading: {meter}')
        
        consumption = int(list_[2])
        consumptions.append(consumption)
        print(f'Consumption: {consumption}')
        
        try:
            peak = int(extract_text(text, 'Peak Capacity Charge ', '\n\n').split('\n')[0].split()[0])
        except:
            peak = 0
        peaks.append(peak)
        print(f'Actual Peak Consumption: {peak}')

        #################
        # RATES
        #################
        consumption_rate = float(extract_text(text, 'Energy Charge ', '\n$').split()[3][1:])
        consumption_rates.append(consumption_rate)
        print(f'Consumption Rate: {consumption_rate}')
        
        try:
            peak_rate = float(extract_text(text, 'Peak Capacity Charge ', '\n\n').split('\n')[0].split()[3][1:])
        except:
            peak_rate = 0
        peak_rates.append(peak_rate)
        print(f'Peak Rate: {peak_rate}')
        
        fuel_rate = float(extract_text(text, 'Fuel Adjustment', '\n').split()[-1][1:])
        fuel_rates.append(fuel_rate)
        print(f'Fuel Rate: {fuel_rate}')
        
        regulatory_rate = float(extract_text(text, 'Regulatory Adj', 'Total Electric Bill').split()[-2][1:])
        regulatory_rates.append(regulatory_rate)
        print(f'Regulatory Rate: {regulatory_rate}')

        #################
        # CHARGES
        #################
        service_charge = extract_text(text, 'Residential Electric\n\n$', 'Service Availability Charge\n$')
        service_charge = float(service_charge)
        service_charges.append(service_charge)
        print(f'Service Charge: {service_charge}')
        
        consumption_charge = consumption_rate * consumption
        consumption_charges.append(consumption_charge)
        print(f'Consumption Charge: {consumption_charge}')
        
        peak_charge = peak_rate * peak
        peak_charges.append(peak_charge)
        print(f'Peak Charge: {peak_charge}')
        
        fuel_charge = consumption * fuel_rate
        fuel_charges.append(fuel_charge)
        print(f'Fuel Charge: {fuel_charge}')
        
        regulatory_charge = consumption * regulatory_rate
        regulatory_charges.append(regulatory_charge)
        print(f'Regulatory Charge: {regulatory_charge}')
        
        total_bill = service_charge + consumption_charge + peak_charge + fuel_charge + regulatory_charge
        total_bills.append(total_bill)
        print(f'Total Bill: {total_bill}')
        print(f'********************** data for {bill_date} parsed **********************')
        print()

    #################
    # ADDING DF FIELDS
    #################
    df['bill_date'] = bill_dates
    df['bills_start'] = bills_starts
    df['bills_end'] = bills_ends
    df['bill_period'] = bill_periods
    
    df['meter'] = meters
    df['consumption'] = consumptions
    df['peak'] = peaks
    
    df['consumption_rate'] = consumption_rates
    df['peak_rate'] = peak_rates
    df['fuel_rate'] = fuel_rates
    df['regulatory_rate'] = regulatory_rates
    
    df['service_charge'] = service_charges
    df['consumption_charge'] = consumption_charges
    df['peak_charge'] = peak_charges
    df['fuel_charge'] = fuel_charges
    df['regulatory_charge'] = regulatory_charges
    df['total_bill'] = total_bills
    
    return df

def main(filePaths_):
    '''
    This function takes in a list of file paths for each pdf bill and applies each
    text extraction and parsing function to return a df comprised of each bill's data.
    '''
    return text_parse(looped_FileExtraction(filePaths_))