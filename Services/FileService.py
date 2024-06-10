
import csv
import os
from datetime import datetime
import pytz


def write_file(epc, freq_mhz, antenna_id, pc_list, rssi, epc_data):
        # Save each record to a CSV file
    with open('files/epc_records.csv', mode='a', newline='') as file:
        fieldnames = ['EPC', 'Antenna ID', 'Frequency (MHz)', 'PC List', 'RSSI List', 'Read Count','Timestamp','LocalTime']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if file.tell() == 0:  # Check if file is empty
            writer.writeheader()

        writer.writerow({
            'EPC': epc,
            'Frequency (MHz)': freq_mhz,
            'Antenna ID': antenna_id + 1,
            'PC List': pc_list,
            'RSSI List': rssi,
            'Read Count': epc_data,
            'Timestamp': utc_timestamp(),
            'LocalTime': local_time()
        })

def local_time():
    utc_now = datetime.now()
    chile_tz = pytz.timezone('America/Santiago')
    local_time = utc_now.astimezone(chile_tz)
    return local_time.strftime('%Y-%m-%d %H:%M:%S')

def utc_timestamp():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

def make_csv():
    if not os.path.exists('./files/epc_records.csv'):
        with open('./files/epc_records.csv', mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['EPC','Frequency', 'AntennaID', 'PCList', 'RSSIList', 'ReadCount','Timestamp','LocalTime'])
            writer.writeheader()