# dataVisualization.py
# Recieves raw data from ZephyrOS scheduler testing framework, returns human
# readable data in the form of statistics (mean, median) and graphs
# Ally Smith
from statistics import median
from matplotlib import pyplot as plt
import csv

# *****************************************************************************
# Kernel data will be organized into one dictionary with entries
#   - ctx:        The number of context switches
#   - preempt:    The number of preemptions
#   - readyq_max: The maximum number of tasks waiting in the ready queue
#   - readyq_cur: The number of tasks in the ready queue at halt
#
# Task/Thread/Process data will be a dictionary of arrays of dictionaries
# The outermost dictionary represents each Task/Thread/Process
# The next array represents all the jobs spawned by that Task
# Finally, the innermost dictionaries contain information for each job:
#   - task_id: 
#   - job_id: 
#   - release_ms:
#   - start_ms:
#   - finish_ms:
#   - deadline_ms:
#   - deadline_met:
# *****************************************************************************


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
    processes_data = {}

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
                kernel = {"ctx": int(data[0]),
                          "preempt": int(data[1]),
                          "readyq_max": int(data[2]),
                          "readyq_cur": int(data[3])}
                kernel_data.append(kernel)
                datasection = False
                break # If we have more than one kernel output, get rid of this
            elif (line != '\n' and datasection == True):
                data = line.split(',')
                # Strip newline from end
                data[-1] = data[-1][0]
                new_job = {
                    "task_id": int(data[0]),
                    "job_id": int(data[1]),
                    "release_ms": int(data[2]),
                    "start_ms": int(data[3]),
                    "finish_ms": int(data[4]),
                    "deadline_ms": int(data[5]),
                    "critical": int(data[6]),
                    "deadline_met": int(data[7])
                }
                task_no = data[0]
                if task_no in processes_data:
                    # Add to the existing array
                    processes_data[task_no].append(new_job)
                else:
                    # Initialize: Make a new array
                    processes_data[task_no] = [new_job]

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
def calculations_and_graphs(kernel_data, processes_data):
    deadlines_missed = 0
    critical_deadlines_missed = [0, 0]
    non_critical_deadlines_missed = [0, 0]
    average_wait_overall = 0
    median_wait_overall = 0
    average_wait_process = []
    median_wait_process = []
    wait_time = [] # per process per job
    median_wait = []
    overall_visual = []
    num_total_jobs = 0

    for i in range(0, len(processes_data)):
        proc = processes_data[str(i)]
        temp_wait_time = []
        temp_visual = []

        for j in range(0, len(proc)):
            num_total_jobs += 1
            # Calculate wait time. Currently uses each entry of the process as opposed
            # to each process themselves
            wait = proc[j]["start_ms"] - proc[j]["release_ms"]
            temp_wait_time.append(wait)
            average_wait_overall += wait
            median_wait.append(wait)

            # Set flag for if a deadline was missed
            # -> does a deadline being missed ever mean the process just didn't finish? (assuming no)
            if (proc[j]["deadline_met"] == 0):
                deadlines_missed += 1

            if (proc[j]["critical"] == 1):
                critical_deadlines_missed[1] += 1
                if (proc[j]["deadline_met"] == 0):
                    critical_deadlines_missed[0] += 1
            else:
                non_critical_deadlines_missed[1] += 1
                if (proc[j]["deadline_met"] == 0):
                    non_critical_deadlines_missed[0] += 1

            # Add release time, start time, and finish time to an array for better visualization
            temp_visual.append([proc[j]["start_ms"], proc[j]["finish_ms"]])
        
        wait_time.append(temp_wait_time)
        overall_visual.append(temp_visual)

        average_wait_process.append(sum(temp_wait_time)/len(temp_wait_time))
        median_wait_process.append(median(temp_wait_time))

    average_wait_overall = average_wait_overall/num_total_jobs
    median_wait_overall = median(median_wait)

    # If we implement kernel snapshots at many points in time
    #for each kernel snapshot
        # Tasks in Queue v.s. Cores
            # add number of tasks in queue to an array

    stats = {"All deadlines were met": True if deadlines_missed == 0 else False,
             "(Missed deadlines)": str(deadlines_missed) + "/" + str(num_total_jobs),
             "Missed Critical Deadlines": str(critical_deadlines_missed[0]) + "/" + str(critical_deadlines_missed[1]),
             "Missed non-Critical Deadlines": str(non_critical_deadlines_missed[0]) + "/" + str(non_critical_deadlines_missed[1]),
             "Average Wait Time (ms)": average_wait_overall,
             "Avgs per Task (ms)": average_wait_process,
             "Median Wait Time (ms)" : median_wait_overall,
             "Meds per Task (ms)": median_wait_process,
             "Max Number of Tasks in Queue" : kernel_data[0]["readyq_max"],
             "Tasks in Queue at Completion": kernel_data[0]["readyq_cur"],
             "Total preemptions": kernel_data[0]["preempt"],
             "Total context switches": kernel_data[0]["ctx"]}

    for i in range(0, len(processes_data)):
        plt.plot(range(0, len(wait_time[i])), wait_time[i])
        plt.title("Wait time for each job in each task")
        plt.xlabel("Job Id")
        plt.ylabel("Time (ms)")
    plt.show()

    colors = [['b','c'],['r','m']]
    for i in range(0, len(processes_data)):
        for j in range(0, len(overall_visual[i])):
            plt.plot(overall_visual[i][j], [i,i], marker='.', color=colors[i%2][j%2])
            plt.title("Overview of Events")
            plt.xlabel("Time (ms)")
            plt.ylabel("Task/Process")
    plt.show()
    graphs = {"Wait Time per Process": [1, wait_time, range(0, len(processes_data)),wait_time,"Process","Time (ms)"],
              "Overview of Events": [1, overall_visual, range(0,len(processes_data)),"Time (ms)","Task"]}
    return stats#, graphs

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
def output(stats):
    colors = ['b','m','g','c']
    # Creates and displays each graph
    #   Graph 1: Wait time per process
    #for key in graphs.keys():
    #    # Standard plot. Assume given two arrays to graph directly
    #    if (graphs[key][0] == 0):
    #        plt.plot(graphs[key][1], graphs[key][2])
    #    # More specialized plots below
    #    # Graph 2: For each task, plot the lifecycle of each job
    #    elif (graphs[key][0] == 1):
    #        for i in range(0,len(graphs[key][1])):
    #            plt.plot(graphs[key][1][i][0], graphs[key][1][i][1], marker='.',color=colors[graphs[key][1][i%4][1][0]])
    #        
    #    # Standard across all graphs
    #    plt.title(key)
    #    plt.xlabel(graphs[key][3])
    #    plt.ylabel(graphs[key][4])
    #    plt.show()

    # To be printed to the console
    print("**********************************************")
    for key in stats.keys():
        print(key + ": " + str(stats[key]))
    print("**********************************************")
    

# Script
filename = input("Enter full file path: ")
data_k, data_p = readTextFile(filename)
statistics = calculations_and_graphs(data_k, data_p)
output(statistics)