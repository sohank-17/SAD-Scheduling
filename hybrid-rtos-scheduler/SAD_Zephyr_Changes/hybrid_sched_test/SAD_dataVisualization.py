# SAD_dataVisualization.py
# Recieves raw data from ZephyrOS scheduler testing framework, returns human
# readable data in the form of statistics (mean, median) and graphs
# Ally Smith
from statistics import median
from matplotlib import pyplot as plt
import csv

# Kernel data struct
class kernel:
    def __init__(self, data):
        self.ctx = int(data[0]) # Context Switches
        self.preempt = int(data[1]) # Number of Preemptions
        self.readyq_max = int(data[2]) # Max number of tasks waiting to be executed
        self.readyq_cur = int(data[3])

# Process data struct
class process:
    def __init__(self, data):
        self.task_id = int(data[0]) # kthread number. Essentially process id
        self.job_id = int(data[1]) # Category of thread/Job type
        self.release_ms = int(data[2]) # Same as arrival time
        self.start_ms = int(data[3]) # When the process starts on the CPU
        self.finish_ms = int(data[4]) # When the process finishes executing
        self.deadline_ms = int(data[5]) # Set deadline for each task
        self.deadline_met = int(data[6]) # Bool indicating if deadline was met


# Read Input ******************************************************************
# Function to read the results of the processes as well as the kernel information.
# One version for a text file and one version for a csv file. Both do the same
# thing.
# Parameters
#   infile_path: string
#       A path to the text file with the formatted output of the testing framework
# 
# Returns
#   kernel_data: struct array
#       Information about kernel at certain time slices
#   processes_data: struct array
#       Information about processes at the end of the simulation
# *****************************************************************************
def readTextFile(infile_path):
    # Initialize data arrays. Will be filled with kernel structs and process
    # structs respectively
    kernel_data = []
    processes_data = []

    # Open file and read line by line
    with open(infile_path) as infile:
        datasection = False
        for line in infile:
            if (line[0:7] == "task_id"):
                datasection = True
            elif (line[0:6] == "kstats"):
                temp = line.split(',')
                del temp[0]
                data = []
                for elem in temp:
                    data.append(elem.split('=')[1])
                kernel_data.append(kernel(data))
                datasection = False
                break
            elif (line != '\n' and datasection == True):
                data = line.split(',')
                # Strip newline from end
                data[-1] = data[-1][0]
                processes_data.append(process(data))

    return kernel_data, processes_data


def readCSV(infile_path):
    # Initialize data arrays. Will be filled with kernel structs and process
    # structs respectively
    kernel_data = []
    processes_data = []

    # Open file and read line by line, avoiding non-data rows
    with open(filename, newline='') as csvfile:
        datasection = False
        file_reader = csv.reader(csvfile, delimiter=',')
        for line in file_reader:
            if (line != [] and line[0] == 'task_id'):
                datasection = True
            elif (line != [] and line[0] == 'kstats'):
                data = []
                for i in range(1,len(line)):
                    data.append(line[i].split('=')[1])
                kernel_data.append(kernel(data))
                datasection = False
                break
            elif (line != [] and datasection == True):
                processes_data.append(process(line))

    return kernel_data, processes_data

# Intermediate processing *****************************************************
# Loop over arrays and create other information
# Parameters
#   kernel_data: kernel array
#
#   processes_data: process array
#
# Returns
#   stats: array of numbers, or, alternatively, a dictionary of results and their keywords
# *****************************************************************************
def calculations(kernel_data, processes_data):
    deadlines_missed = 0
    average_wait_time = 0
    median_wait_time = 0
    wait_time = []

    for proc in processes_data:
        # Calculate wait time. Currently uses each entry of the process as opposed
        # to each process themselves
        wait = proc.start_ms - proc.release_ms
        wait_time.append(wait)
        average_wait_time += wait

        # Set flag for if a deadline was missed
        # -> does a deadline being missed ever mean the process just didn't finish? (assuming no)
        if proc.deadline_met == 0:
            deadlines_missed += 1
    
    average_wait_time = average_wait_time/len(processes_data)
    median_wait_time = median(wait_time)
    
    # If we implement kernel snapshots at many points in time
    #for each kernel snapshot
        # Tasks in Queue v.s. Cores
            # add number of tasks in queue to an array

    stats = {"All deadlines were met": True if deadlines_missed == 0 else False,
             "(Missed deadlines)": deadlines_missed,
             "Average Wait Time (ms)": average_wait_time,
             "Median Wait Time (ms)" : median_wait_time,
             "Max Number of Tasks in Queue" : kernel_data[0].readyq_max,
             "Tasks in Queue at Completion": kernel_data[0].readyq_cur}
    graphs = {"Wait Time per Process": [range(0, len(processes_data)),wait_time,"Process","Time (ms)"]}
    return stats, graphs


# Output **********************************************************************
# Prints results to console in a nicely readable format, displays
# graphs of other appropriate data
# Parameters
#   stats: dictionary
#       Contains all data for output. Organized by name and the value.
#
#   graphs: dictionary
#       Contains all data for graphs. Organized by graph title, then an array of
#       the x array and y array.
# *****************************************************************************
def output(stats, graphs):
    # Do all graph things here. Just spawn all of them
    for key in graphs.keys():
        plt.plot(graphs[key][0], graphs[key][1])
        plt.title(key)
        plt.xlabel(graphs[key][2])
        plt.ylabel(graphs[key][3])
        plt.show()

    # To be printed to the console
    print("**********************************************")
    for key in stats.keys():
        print(key + ": " + str(stats[key]))
    print("**********************************************")
    




# Script
filename = input("Enter full file path: ")
data_k, data_p = readCSV(filename)
statistics, graphs = calculations(data_k, data_p)
output(statistics, graphs)
