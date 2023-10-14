import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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
    try:
        fi2=fi.split('/')#os.path.split(fi)
        meta=fi2[-2]
        metad={}
        for x in meta.split('.'):
            if '@' in x:
                y = x.split('@')
            else:
                y = list(x)
            metad[y[0]]=''.join(y[1:])
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
    except:
        return None

def extract_values_from_log(filename):
    print(filename)
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

def time_to_seconds(time_str):
    '''Convert a time string of format XmY,Zs to seconds.'''
    minutes, seconds = time_str.split('m')
    # Replace the comma with a dot to handle the decimal and remove the 's' at the end
    seconds = seconds.replace(',', '.').replace('s', '')
    return float(minutes) * 60 + float(seconds)

def extract_data_from_timefile(file_path):
    '''Extract timing data from a file and return as a dictionary.'''
    with open(file_path, 'r') as file:
        lines = file.readlines()
        real_time = time_to_seconds(lines[1].split('	')[1].strip())
        user_time = time_to_seconds(lines[2].split('	')[1].strip())
        sys_time = time_to_seconds(lines[3].split('	')[1].strip())
        return {
            'filename': file_path,
            'realtime': real_time,
            'usertime': user_time,
            'systime': sys_time
        }


OUTPUTPATH='output'
if not os.path.isfile(os.path.join(OUTPUTPATH,'icp.csv')) or not os.path.isfile(os.path.join(OUTPUTPATH,'aggregation.csv')):

    DATAPATTERN='Z:/vms/arqui/arch/gem5/output/**/stats.txt'

    os.makedirs(OUTPUTPATH,exist_ok=True)
    files=glob.glob(DATAPATTERN,recursive=True)
    files=[x.replace('\\','/') for x in files]
    power_logs=[x.replace('stats.txt','power.log') for x in files]
    power_logs=[extract_values_from_log(x) for x in power_logs]
    power_times=[x.replace('stats.txt','power.time') for x in files]
    power_times=[extract_data_from_timefile(x) for x in power_times]
    data=[dict_file(x) for x in files]

    DATAPATTERN_INSPROFILE='Z:/vms/arqui/arch/gem5/outputProfile/**/stats.txt'
    files2=glob.glob(DATAPATTERN_INSPROFILE,recursive=True)
    files2=[x.replace('\\','/') for x in files2]
    # Extract data from each file
    icp_dicts = [dict_file(file) for file in files2]


    # Convert the list of dictionaries into a DataFrame
    dficp = pd.DataFrame(icp_dicts)
    dficp.to_csv(os.path.join(OUTPUTPATH,'icp.csv'))

    #print(power_logs)


    # TODO
    # add check that at least one output file is in the directory
    # that way we at least have an indication of the procedure running correctly
    #print(files)


    for ff,pw,pwt in zip(data,power_logs,power_times):
        try:
            ff.update(pw)
            ff.update(pwt)
        except:
            print('Power Error')
    df=pd.DataFrame(data)

    # Calculate the ratio based on the provided average real times
    ratio = 80 / 55 # When running one by one goes from 80 to 55 approximately
    df['usertime']=df['usertime']/ratio # Assume it was run over 10 parallel jobs, which was the case. 
    df['powerTime']=df['usertime']+df['systime']

    df['Energy']=df["Total Leakage"]+df["Runtime Dynamic"]
    df['EDP']=df['Energy']*(df['system.cpu.cpi']**2)



    df.to_csv(os.path.join(OUTPUTPATH,'aggregation.csv'),sep=';')
    df.to_pickle(os.path.join(OUTPUTPATH,'aggregation.pkl'))
    df.to_excel(os.path.join(OUTPUTPATH,'aggregation.xlsx'))
else:
    df=pd.read_csv(os.path.join(OUTPUTPATH,'aggregation.csv'),sep=';',low_memory=False)
    dficp=pd.read_csv(os.path.join(OUTPUTPATH,'icp.csv'),sep=',',low_memory=False)
#[print(x) for x in df.columns]
#print(df['EDP'])
# Parse the provided file using the updated function
#df_updated = parse_stats_file_updated("/mnt/data/stats.txt")
#df_updated.head()


###################### Instruction Class Profiling ###############################################

# df['system.cpu.commit.committedInstType_0::FloatAdd']

dfinst= df.filter(regex='system.cpu.commit.committedInstType_0::.*')
dfinst=dfinst.drop(columns=['system.cpu.commit.committedInstType_0::total'],inplace=False)
df_cleaned = df.copy()
df_orig=df.copy()

if not os.path.isfile(os.path.join(OUTPUTPATH,'aggregation_cleaned.csv')):
    for i,row in dfinst.iterrows():
        #print(row)
        for j,col in enumerate(dfinst.columns):
            #print(dfinst[col][i],type(dfinst[col][i]))
            if type(dfinst[col][i])==str:
                val=eval(dfinst[col][i])
            elif isinstance(dfinst[col][i],list):
                val=dfinst[col][i]
            else:
                assert False
            dfinst[col][i]=float(val[1])
            df_cleaned[col][i]=float(val[1])
        if not np.sum(row)>99 or not np.sum(row)<101:
            print('Error in row ',i)
            print(row)
            print(np.sum(row))
        if i%10==0:
            print(i,np.sum(row))

    df_cleaned.to_csv(os.path.join(OUTPUTPATH,'aggregation_cleaned.csv'),sep=';')
else:
    df_cleaned=pd.read_csv(os.path.join(OUTPUTPATH,'aggregation_cleaned.csv'),sep=';',low_memory=False)
df=df_cleaned
df.drop(columns=[x for x in df.columns if 'Unnamed' in x],inplace=True)

inst_type_columns = [col for col in df.columns if 'system.cpu.commit.committedInstType' in col and 'total' not in col]

# Define the abbreviation maps from the provided code
ABBV_MAP = {
    'l1i_size': "l1is",
    'l2_lat': "l2l",
    'l3_size': "l3s",
    'issue_width': "issw",
    'rob_entries': "robe",
    'num_fu_intALU': "numfA",
    'workload': "wl",
}

ABBV_MAP_INV = {
    'wl':   'workload',
    'l1is': 'l1i_size',
    'l2l': 'l2_lat',
    'l3s': 'l3_size',
    'issw': 'issue_width',
    'robe': 'rob_entries',
    'numfA': 'num_fu_intALU'
}

# Rename the architecture parameters using ABBV_MAP_INV
df.rename(columns=ABBV_MAP_INV, inplace=True)

# Group by the workload and calculate the average for each instruction type column
workload_profile = df.groupby('workload')[inst_type_columns].mean()

# Function to generate the bar chart with error bars for each workload
def sorted_plot_workload_distribution(workload_data, workload_name):
    # Filter out instruction types with 0% for the workload
    non_zero_columns = workload_data[inst_type_columns].mean()
    non_zero_columns = non_zero_columns[non_zero_columns > 0].index.tolist()
    
    # Remove the long prefix from the instruction type names for better clarity
    shortened_columns = [col.replace('system.cpu.commit.committedInstType_0::', '') for col in non_zero_columns]
    workload_data_renamed = workload_data.rename(columns=dict(zip(non_zero_columns, shortened_columns)))
    
    # Calculate means and standard deviations for plotting
    means = workload_data_renamed[shortened_columns].mean(axis=0)
    std_devs = workload_data_renamed[shortened_columns].std(axis=0)
    
    # Get the sort order based on the means in descending order
    sorted_indices = means.sort_values(ascending=False).index
    
    # Reorder the data based on the sort order
    sorted_means = means[sorted_indices]
    sorted_std_devs = std_devs[sorted_indices]
    
    fig = plt.figure(figsize=(15, 10))
    
    # Plotting bar chart with error bars
    sns.barplot(x=sorted_indices, y=sorted_means, yerr=sorted_std_devs, ci="sd", capsize=0.2)
    plt.title(f'Instruction Type Distribution for {workload_name} Workload')
    plt.ylabel('Percentage')
    plt.xlabel('Instruction Type')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    return fig 

# Generate plots for each workload
for workload in df['workload'].unique():
    workload_data = df[df['workload'] == workload]
    fig = sorted_plot_workload_distribution(workload_data, workload)
    fig.savefig(os.path.join(OUTPUTPATH,f'ICPworkload_{workload}.pdf'))
    fig.savefig(os.path.join(OUTPUTPATH,f'ICPworkload_{workload}.png'))


plt.close('all')
########################### Simulation Times #######################################################################
df_profile=pd.concat([df['workload'],df['hostSeconds'],df['powerTime'],dficp['hostSeconds']],axis=1,keys=['wl','uArch Simulation','mcpat Simulation','Only ICP Simulation'])
df_profile=df_profile[df_profile['wl']=='h264dec']
df_profile=df_profile.drop(columns=['wl'])

df_profile=df_profile.apply(lambda x: np.log10(x))
import matplotlib.pyplot as plt
import seaborn as sns


# Calculate means and IQRs for each series
def bars(df_combined):
    means = df_combined.mean()
    q1 = df_combined.quantile(0.25)
    q3 = df_combined.quantile(0.75)
    iqr = q3 - q1

    # Create a bar plot with error bars representing the IQR
    fig=plt.figure(figsize=(12, 7.5))
    bars = plt.bar(df_combined.columns, means, yerr=iqr, color=['blue', 'green', 'red'], alpha=0.7, capsize=10)

    # Annotate with the mean values
    for bar in bars:
        yval = bar.get_height()
        inv_log_val = 10**yval
        label = f"Mean: {round(yval, 2)}\n({round(inv_log_val, 2)} seconds)"
        plt.text(bar.get_x() + bar.get_width()/1.3, yval, label, ha='center', va='bottom', fontweight='bold')

    plt.title("Profiling Results for workload h264dec")
    plt.ylabel("log10(seconds)")
    plt.tight_layout()
    return fig


fig=bars(df_profile)
fig.savefig(os.path.join(OUTPUTPATH,'simtime.pdf'))
fig.savefig(os.path.join(OUTPUTPATH,'simtime.png'))
#plt.show()

plt.close('all')

[print(x) for x in df.columns[:100]]

df.columns[:10]


##################### Performances #########################################################

# Selecting a discrete and contrasting color palette
colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00']  # Colors chosen from the Set1 palette for good distinction

# Function to sort values that might contain 'kB' or 'MB'
def sort_key(value):
    if 'kB' in str(value):
        return int(value.replace('kB', ''))
    elif 'MB' in str(value):
        return int(value.replace('MB', '')) * 1000  # Convert MB to kB for consistent sorting
    elif pd.api.types.is_numeric_dtype(value):
        return value
    else:
        return str(value)

def get_reference_value(column, df):
    """Utility function to get the reference value for a given column."""
    unique_vals = df[column].unique()
    if len(unique_vals) == 2:
        return unique_vals[0]
    elif 'kB' in str(unique_vals[0]) or 'MB' in str(unique_vals[0]) or column=='workload':
        # Sort values based on numeric content or kB/MB suffix and return the middle value
        sorted_vals = sorted(unique_vals, key=sort_key)
        return sorted_vals[len(sorted_vals) // 2]
    else:
        return df[column].median()

def plot_variations_with_updated_reference(targets, column, reference=None, rename=None, df=df,var_columns=df.columns[:7]):
    # Defaulting to previous method for values not in reference
    inferred_reference = {
        col: get_reference_value(col, df)
        for col in var_columns if col not in reference
    }
    
    # Combining provided reference with inferred reference
    combined_reference = {**inferred_reference, **reference}
    
    figs={}
    for target in targets:
        # Filter the dataframe based on combined_reference values for all columns except the current one
        filtered_df = df
        for key, value in combined_reference.items():
            if key != column:
                filtered_df = filtered_df[filtered_df[key] == value]

        # Generate legend text
        if rename is None:
            rename={k:k for k in combined_reference.keys()}

        def roundit(x):
            if isinstance(x,float) or isinstance(x,np.float64) or isinstance(x,np.float32):
                return int(round(x,0))
            else:
                return x
        legend_text = 'REF : ' + ", ".join([f"{rename.get(k, k)}={roundit(v)}" for k, v in combined_reference.items() if k != column])

        # Calculate dynamic y-axis limits
        target_diff = filtered_df[target].max() - filtered_df[target].min()
        target_ylim = [filtered_df[target].min() - target_diff, filtered_df[target].max() + target_diff] if target_diff != 0 else None

        # Unique x-axis values and positions, sorted based on sort_key function
        unique_x = sorted(filtered_df[column].unique(), key=sort_key)
        positions = range(len(unique_x))

        # Plot
        fig=plt.figure(figsize=(12, 7.5))
        
        bars = plt.bar(positions, [filtered_df[filtered_df[column] == x_val][target].values[0] for x_val in unique_x], width=0.6, color=colors[:len(unique_x)])
        plt.title(f"Variation of '{target}' with {rename.get(column, column)}")
        plt.xlabel(rename.get(column, column))
        plt.ylabel(target)
        plt.annotate(legend_text, xy=(0.95, 0.95), xycoords='axes fraction', fontsize=12, verticalalignment='top', horizontalalignment='right')
        #plt.legend([legend_text], loc='upper right', title="Constant Values",color='white')
        plt.xticks(positions, unique_x, rotation=45, ha='right')
        if target_ylim:
            plt.ylim(target_ylim)
        
        plt.tight_layout()

        figs[target]=fig
    return figs

reference_values = {'workload': 'mp3_enc'}
rename_dict = None#{'numfA': 'Number of Alus'}
targets = ['system.cpu.cpi', 'simSeconds']
var_columns = df.columns[:7]

for col in var_columns:
    figs=plot_variations_with_updated_reference(targets, col, reference=reference_values, rename=rename_dict,var_columns=var_columns)
    for target,fig in figs.items():
        fig.savefig(os.path.join(OUTPUTPATH,f'perf_{target}_{col}.pdf'))
        fig.savefig(os.path.join(OUTPUTPATH,f'perf_{target}_{col}.png'))

plt.close('all')


###################### 2D Performance Plot by workload #####################################################################

def plot_optimal_points_with_results_by_workload(df,variables = ['wl', 'l1is', 'l2l', 'l3s', 'issw', 'robe', 'numfA'],targets=['system.cpu.cpi', 'Energy'],scaled=True, threshold=0.5,colors = {'h264dec': 'red', 'jpeg2k_enc': 'green', 'mp3_enc': 'blue'}, circle_sizes = {'h264dec': 120, 'jpeg2k_enc': 80, 'mp3_enc': 50},figsize=(6, 12),already_scaled=False):
    # first of variables should be workload
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    
    # Load the dataset
    df.drop(columns=[col for col in df.columns if "Unnamed" in col], inplace=True)
    wl_variable = variables[0]
    df = df[variables + targets]
    
    # Save the original values
    for col in targets:
        df['original_' + col] = df[col]
    
    # Scale the target values
    if not already_scaled:
        for col in targets:
            df[col] = df.groupby(wl_variable)[col].transform(lambda x: (x - x.min()) / (x.max() - x.min()))
    
    # Compute the distance to the origin
    df['distance_to_origin'] = np.sqrt(sum(df[col]**2 for col in targets))
    
    # Identify the best points based on the criteria
    def find_constrained_best_point(subset,columns_list=targets):
        # Filter points where both dimensions are below the threshold
        filtered_points = subset[subset[columns_list].apply(lambda row: all(val <= threshold for val in row), axis=1)]
        if not filtered_points.empty:
            return filtered_points.nsmallest(1, 'distance_to_origin')
        else:
            return subset.nsmallest(1, 'distance_to_origin')
    best_points_constrained = df.groupby(wl_variable).apply(find_constrained_best_point).reset_index(drop=True)
    
    workloads = df[wl_variable].unique()
    # Plotting the 2D scatter plots with the best points encircled
    fig, axes = plt.subplots(nrows=len(workloads), figsize=figsize)
    if len(workloads) == 1:
        axes = [axes]
    for ax, workload in zip(axes, workloads):
        subset = df[df[wl_variable] == workload]
        if scaled:
            ax.scatter(subset[targets[0]], subset[targets[1]], alpha=0.6, color='black', s=20)
        else:
            ax.scatter(subset['original_'+targets[0]], subset['original_'+targets[1]], alpha=0.6, color='black', s=20)
        for best_wl, best_row in best_points_constrained.iterrows():
            if isinstance(best_wl,int):
                best_wl=best_row[wl_variable]
            matching_point = subset[(subset[variables[1:]] == best_row[variables[1:]].values).all(axis=1)]
            if scaled:
                ax.scatter(matching_point[targets[0]], matching_point[targets[1]], s=circle_sizes[best_wl], facecolors='none', edgecolors=colors[best_row[wl_variable]], linewidth=1.5, marker='o')
            else:
                ax.scatter(matching_point['original_'+targets[0]], matching_point['original_'+targets[1]], s=circle_sizes[best_row[wl_variable]], facecolors='none', edgecolors=colors[best_row[wl_variable]], linewidth=1.5, marker='o')
        ax.set_title(f'{wl_variable}: {workload}')
        ax.set_xlabel(f'{targets[0]}' + (' (scaled)' if scaled else ''))
        ax.set_ylabel(f'{targets[1]}' + (' (scaled)' if scaled else ''))
        ax.grid(True)
    plt.tight_layout()
    
    
    # Create the results dictionary
    results = {}
    for _, row in best_points_constrained.iterrows():
        workload = row[wl_variable]
        results[workload] = {
            targets[1]: row[f'original_{targets[1]}'],
            f'Scaled {targets[1]}': row[targets[1]],
            targets[0]: row[f'original_{targets[0]}'],
            f'Scaled {targets[0]}': row[targets[0]],
            'Combination': {var: row[var] for var in variables[1:]}
        }
    
    return results,fig

    
# Define circle sizes
# Demonstrate the function with scaled data
targets=['system.cpu.cpi', 'Energy']
results,fig = plot_optimal_points_with_results_by_workload(df,variables=var_columns.tolist(),targets=targets,scaled=False, threshold=0.5,colors = {'h264dec': 'magenta', 'jpeg2k_enc': 'lime', 'mp3_enc': 'yellow'}, circle_sizes ={'h264dec': 120, 'jpeg2k_enc': 90, 'mp3_enc': 50})
fig.savefig(os.path.join(OUTPUTPATH,f'perf_2d.pdf'))
fig.savefig(os.path.join(OUTPUTPATH,f'perf_2d.png'))

def savejson(path,d):
    import json
    with open(path, 'w') as fp:
        json.dump(d, fp,indent=4)    

savejson(os.path.join(OUTPUTPATH,'results2D.json'),results)

targets=['system.cpu.cpi', 'EDP']
results,fig = plot_optimal_points_with_results_by_workload(df,variables=var_columns.tolist(),targets=targets,scaled=False, threshold=0.5,colors = {'h264dec': 'magenta', 'jpeg2k_enc': 'lime', 'mp3_enc': 'yellow'}, circle_sizes ={'h264dec': 120, 'jpeg2k_enc': 90, 'mp3_enc': 50})
fig.savefig(os.path.join(OUTPUTPATH,f'perf_2deDP.pdf'))
fig.savefig(os.path.join(OUTPUTPATH,f'perf_2deDP.png'))

savejson(os.path.join(OUTPUTPATH,'results2DeDP.json'),results)

### Optimize over all workloads #########################################

wl_variable = 'workload'
targets=['system.cpu.cpi', 'Energy']
dfnorm=df.copy()
for col in targets:
    dfnorm[col] = df.groupby(wl_variable)[col].transform(lambda x: (x - x.min()) / (x.max() - x.min()))

# Group by the variables except 'wl' and compute the mean for 'Energy' and 'system.cpu.cpi'
mean_df = dfnorm.groupby(var_columns.tolist()[1:])[targets].mean().reset_index()

# Add a column for the 'mean workload'
mean_df[wl_variable] = 'mean_workload'


results,fig = plot_optimal_points_with_results_by_workload(mean_df,variables=var_columns.tolist(),targets=targets,scaled=True, threshold=0.5,colors = {'mean_workload': 'magenta'}, circle_sizes = {'mean_workload':120},figsize=(6, 6),already_scaled=True)
fig.savefig(os.path.join(OUTPUTPATH,f'perf_2dmean.pdf'))
fig.savefig(os.path.join(OUTPUTPATH,f'perf_2dmean.png'))
savejson(os.path.join(OUTPUTPATH,'results2Dmean.json'),results)

wl_variable = 'workload'
targets=['system.cpu.cpi', 'EDP']
dfnorm=df.copy()
for col in targets:
    dfnorm[col] = df.groupby(wl_variable)[col].transform(lambda x: (x - x.min()) / (x.max() - x.min()))

# Group by the variables except 'wl' and compute the mean for 'Energy' and 'system.cpu.cpi'
mean_df = dfnorm.groupby(var_columns.tolist()[1:])[targets].mean().reset_index()

# Add a column for the 'mean workload'
mean_df[wl_variable] = 'mean_workload'


results,fig = plot_optimal_points_with_results_by_workload(mean_df,variables=var_columns.tolist(),targets=targets,scaled=True, threshold=0.5,colors = {'mean_workload': 'magenta'}, circle_sizes = {'mean_workload':120},figsize=(6, 6),already_scaled=True)
fig.savefig(os.path.join(OUTPUTPATH,f'perf_2dmeaneDP.pdf'))
fig.savefig(os.path.join(OUTPUTPATH,f'perf_2dmeaneDP.png'))
savejson(os.path.join(OUTPUTPATH,'results2DmeaneDP.json'),results)
