import os
import glob
import pandas as pd
import numpy as np
def parse_line(line):
    """
    Parse a single line based on the provided instructions.
    """
    # Initialize placeholders
    name, values, description = None, [], None
    
    # Splitting by '#'
    parts = line.split("#")
    if len(parts) > 1:
        description = parts[1].strip()

    # Parsing name and values
    items = parts[0].split()
    name = items[0]
    values = items[1:]
    
    return name, values, description

def parse_stats_file_updated(filename):
    with open(filename, "r") as file:
        lines = file.readlines()

    # Find the start and end lines based on the "----------" delimiter
    start_line = None
    end_line = None
    for idx, line in enumerate(lines):
        if "----------" in line:
            if start_line is None:
                start_line = idx
            else:
                end_line = idx
                break

    # Process the lines between the start and end
    data = []
    for line in lines[start_line+1:end_line]:
        # Check if line contains valid data
        if "#" not in line:
            continue

        name, values, description = parse_line(line)
        data.append([name, values, description])

    # Create the dataframe
    df = pd.DataFrame(data, columns=["Name", "Values", "Description"])
    
    return df

def try_convert_to_float(value):
    """
    Attempt to convert the value to a float.
    If unsuccessful, return the original value.
    """
    if isinstance(value,str) and '%' in value:
        value=value.replace('%','')
    try:
        return float(value)
    except ValueError:
        return value


def dict_file(fi):
    fi2=fi.split('/')
    meta=fi2[1]
    metad={}
    for x in meta.split('.'):
        y = x.split('@')
        metad[y[0]]=y[1]
    #print(metad)
    dat=parse_stats_file_updated(fi)
    df_updated=dat.copy()
    #print(dat)

    # Check if the names are unique
    are_names_unique = df_updated["Name"].nunique() == df_updated.shape[0]

    # If names are unique, convert the dataframe to the desired dictionary format
    assert are_names_unique

    df_dict = df_updated.set_index('Name').to_dict(orient='index')


    # Flatten the dictionary structure to "name: value(s)" format
    flattened_dict = {name: (values['Values'][0] if len(values['Values']) == 1 else values['Values']) 
                    for name, values in df_dict.items()}

    # Apply the conversion function to each value in the dictionary
    for key, value in flattened_dict.items():
        if isinstance(value, list):
            flattened_dict[key] = [try_convert_to_float(item) for item in value]
        else:
            flattened_dict[key] = try_convert_to_float(value)
    #print(flattened_dict)

    metad.update(flattened_dict)
    return metad


def extract_values_from_log(filename):
    if not os.path.isfile(filename):
        return {"Total Leakage":np.nan, "Runtime Dynamic":np.nan}
    with open(filename, 'r') as f:
        lines = f.readlines()
        
    # Flags to indicate the start and end of the processor section
    start_processor = False
    
    # Variables to store extracted values
    total_leakage = None
    runtime_dynamic = None
    
    for line in lines:
        stripped_line = line.strip()
        
        if "Processor:" in stripped_line:
            start_processor = True
        if "Total Cores:" in stripped_line:
            break
        
        if start_processor:
            if "Total Leakage" in stripped_line:
                total_leakage = stripped_line.split('=')[1].strip()
            elif "Runtime Dynamic" in stripped_line:
                runtime_dynamic = stripped_line.split('=')[1].strip()
    cleanit=lambda x:float(x.replace('W',''))
    return {"Total Leakage":cleanit(total_leakage), "Runtime Dynamic":cleanit(runtime_dynamic)}

DATAPATTERN='output/**/stats.txt'
DATAPATH='output'
files=glob.glob(DATAPATTERN,recursive=True)
power_logs=[x.replace('stats.txt','power.log') for x in files]
power_logs=[extract_values_from_log(x) for x in power_logs]
print(power_logs)


# TODO
# add check that at least one output file is in the directory
# that way we at least have an indication of the procedure running correctly
#print(files)

data=[dict_file(x) for x in files]
for ff,pw in zip(data,power_logs):
    try:
        ff.update(pw)
    except:
        print('Power Error')
df=pd.DataFrame(data)


df['Energy']=df["Total Leakage"]+df["Runtime Dynamic"]
df['EDP']=df['Energy']*(df['system.cpu.cpi']**2)


df.to_csv(os.path.join(DATAPATH,'aggregation.csv'))
[print(x) for x in df.columns]
print(df['EDP'])
# Parse the provided file using the updated function
#df_updated = parse_stats_file_updated("/mnt/data/stats.txt")
#df_updated.head()
