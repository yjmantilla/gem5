import os
import glob
import pandas as pd
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
    print(metad)
    dat=parse_stats_file_updated(fi)
    df_updated=dat.copy()
    print(dat)

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
    print(flattened_dict)

    metad.update(flattened_dict)
    return metad
    
DATAPATTERN='output/**/stats.txt'
DATAPATH='output'
files=glob.glob(DATAPATTERN,recursive=True)

print(files)

data=[dict_file(x) for x in files]

df=pd.DataFrame(data)
print(df)

df.to_csv(os.path.join(DATAPATH,'aggregation.csv'))



# Parse the provided file using the updated function
#df_updated = parse_stats_file_updated("/mnt/data/stats.txt")
#df_updated.head()
