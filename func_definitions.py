import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

"""Functions in this module take the argument 'data'. This is the name of a dataframe (in the format of Open Data Zürich's weekly public transport dataset, with information about stops merged into it, as is done in the notebook.)"""



def main_routes_of_line(line,data):
    """Function returns the two most common routes on the given line. Typically,
    these will be routes connecting endpoints of the line.
    """
    
    df=data[data["linie"]==line]
    return df["fw_lang"].value_counts().head(2).index.to_numpy()


def convert_short_to_long(name,data):
    """ Takes the short name (example: 'REHA') of a stop and returns its long name ('Rehalp'). """
    
    stops=data[["halt_lang","halt_kurz"]]
    stops=stops.reset_index(drop=True).set_index("halt_kurz")
    stops=stops["halt_lang"].str.replace("Zürich, ","").str.replace("Zürich,","")
    stops=stops.drop_duplicates()
    return stops.loc[name]


def stops_on_route(route,data):
    """ Given a route (example: 'BSTA - BUCH'), function returns an array of the stops along that route,
     including the first stop, but excluding the final stop. Names of stops are returned in their
     short form. """
    
    first_stop=route.split()[0]
    last_stop=route.split()[2]
    df=data[data["fw_lang"]==route]
    df=df[["halt_kurz_von1","halt_kurz_nach1"]]
    df=df.drop_duplicates(subset="halt_kurz_von1", keep="last")
    df=df.set_index("halt_kurz_von1")
    stops=[]
    current_stop=first_stop
    while current_stop!=last_stop:
        stops.append(current_stop)
        current_stop=df.loc[current_stop][0]
    return stops


def contributions(route,data):
    """ For a given route (example: 'REHA - ZAUZ'), function creates a dataframe that shows for each
    stop along the route the average holdups associated with the stop: First, the average holdup that occurs
    while the tram is at the stop. Second, the average holdup that occurs while the tram moves from this stop
    to the next stop. Third, the sum of these two holdups. """
    
    df=data[data["fw_lang"]==route]
    df=df[["halt_lang","halt_kurz_von1","holdup_stop","holdup_trajectory","total_holdup"]]
    conts=df.groupby(["halt_kurz_von1","halt_lang"]).mean()
    conts=conts.reset_index(level=conts.index.names)
    conts=conts.set_index(["halt_kurz_von1"])
    stops_in_order=stops_on_route(route,data)
    conts=conts.reindex(stops_in_order)
    return conts


def major_contributions(route,data,cutoff):
    """ For given route and cutoff, function creates a dataframe that holdup at stops, holdup on the following trajectory,
    and total holdup only on those stops along the given route where total holdup exceeds the cutoff."""
        
    conts=contributions(route,data)
    conts=conts[conts["total_holdup"]>cutoff]
    conts=conts[["halt_lang","holdup_stop","total_holdup"]]
    return conts


def major_contributions_line(line,data,cutoff,reverse=False):
    """ For given line and cutoff, function creates a dataframe that holdup at stops, holdup on the following trajectory,
    and total holdup only on those stops along the given line where total holdup exceeds the cutoff. Setting "reverse"
    to True reverses the direction of travel. Default: False."""    
    
    routes=main_routes_of_line(line,data)
    if reverse:
        idx=1
    else:
        idx=0
    route=routes[idx]
    return major_contributions(route,data,cutoff)
    

def number_of_stops(route,data):
    """ For each route (example: 'REHA - ZAUZ), function returns the number of stops
    on that route, excluding the final stop.
    """
    conts=contributions(route,data)
    return len(conts)

def delay_along_route(route,data,which_holdup="total",absolute=False):
    """ For a given route (example: 'REHA - ZAUZ'), function shows the aggregate delay that accumulates on
    an average tram ride along that entire route.

    If which_holdup='at_stop', function only aggregates the holdups that occur while the tram is at a stop.
    If which_holdup='on_trajectory', it only aggregates the holdups that occur while the tram is traveling
        between two stops.
    If which_holdup='total', both kinds of holdup are aggregated.
    Default: 'total'

    If absolute=False, then the absolute values of the holdups are aggregated instead of the holdups themselves.
    Hence, the result is not the delay at the endpoint but the sum of deviations from the timetable.
    Example: If a tram loses 10s somewhere on the route and gains 10s later, then this does not affect
    the function value if absolute=False but it increases it by 20s if absolute=True.
    Default: False
    """


    if which_holdup=="at_stop":
        idx=0
    elif which_holdup=="on_trajectory":
        idx=1
    else:
        idx=2

    conts=contributions(route,data)
    conts=conts.drop("halt_lang",axis=1)

    if absolute:
        conts=conts.abs()


    aggs=conts.sum()[idx]
    return aggs



def measure_of_delay_line(line, data, which_holdup="total",absolute=False,per_stop=True):
    """ Function provides a measure of delay on a given line.

        First argument is the line of interest.

        If which_holdup='at_stop', function takes into account only the holdups that occur while the tram is at a stop.
        If which_holdup='on_trajectory', it takes into account only the holdups that occur while the tram is traveling
            between two stops.
        If which_holdup='total', both kinds of holdup are taken into account.
        Default: 'total'

        If absolute=False, then the absolute values of the holdups are taken into account instead of the holdups themselves.
        Example: If a tram loses 10s somewhere on the route and gains 10s later, then this is of no effect if
        absolute=False.
        Default: False

        If per_stop=False, the function returns the delay on the given line (both directions averaged).
        If per_stop=True, function returns this delay divided by the number of stops.
        Default: True

    """

    measures=[]
    for route in main_routes_of_line(line,data):
        num=delay_along_route(route,data,which_holdup=which_holdup,absolute=absolute)
        den=number_of_stops(route,data)
        if per_stop:
            measures.append(num/den)
        else:
            measures.append(num)
        return sum(measures)/len(measures)



def table_lines(lines, data, which_holdup="total",per_stop=True):
    """ Creates a table which contains information about holdups for each of the given lines.
    
        If which_holdup='at_stop', function takes into account only the holdups that occur while the tram is at a stop.
        If which_holdup='on_trajectory', it takes into account only the holdups that occur while the tram is traveling
            between two stops.
        If which_holdup='total', both kinds of holdup are taken into account.
        Default: 'total'
        
        If per_stop=False, the function returns the delay on the given line (both directions averaged).
        If per_stop=True, function returns this delay divided by the number of stops.
        Default: True """
    
    
    delays=[]
    deviations=[]
    for line in lines:
        delay=measure_of_delay_line(line, data,which_holdup=which_holdup,per_stop=per_stop)
        delays.append(delay)
        deviation=measure_of_delay_line(line,data,which_holdup=which_holdup,absolute=True)
        deviations.append(deviation)
    table=pd.DataFrame({"Line":lines, "Delay":delays, "Deviation":deviations})
    table=table.set_index("Line")
    return table




def figure_lines(lines, line_colors, data, which_holdup="total",what="delay",per_stop=True):
    """ Creates a plot comparing the amount of delay on different lines.
    
    The argument 'lines' specifies the lines to be considered for the comparison as an array.
    
    Argument 'line_colors' specifies an array of colors to be used to distinguish the lines.
    
    Optional arguments:
   
    If which_holdup='at_stop', function takes into account only the holdups that occur while the tram is at a stop.
    If which_holdup='on_trajectory', it takes into account only the holdups that occur while the tram is traveling
        between two stops.
    If which_holdup='total', both kinds of holdup are taken into account.
    Default: 'total'
    
    If what="delay", the plot compares delays.
    If what="deviation", the plot compares deviations from the timetable instead of delays.
    Default: 'delay'
        
    If per_stop=False, the function returns the delay on the given line (both directions averaged).
    If per_stop=True, function returns this delay divided by the number of stops.
    Default: True
    
    """

    table=table_lines(lines,data,which_holdup=which_holdup,per_stop=per_stop)
    colors=[]
    for line in lines:
        hex_color=line_colors[line]
        colors.append(hex_color)
    

    if which_holdup=="at_stop":
        explan=" (only holdups at stops)"
    elif which_holdup=="on_trajectory":
        explan=" (only holdups between stops)"
    else:
        explan=""
        plt.tight_layout()
        
    if what=="deviation":
        array=table["Deviation"]
        title="Which lines deviated most from the timetable?"+explan
    else:
        array=table["Delay"]
        title="Which lines had most delays from endpoint to endpoint?"+explan
    plt.bar(range(len(lines)), array, tick_label=table.index, color=colors)
    plt.title(title)

    if per_stop:
        plt.ylabel("Seconds per stop on the line")
    else:
        plt.ylabel("Seconds")

    
    
    plt.xlabel("Line")
    plt.show()


def plot_overview_for_line(line, line_colors, data, reverse=False, which_holdup="total", annotations=True):
    """Function plots an overview of holdups which occur on a given tram line.
    Required argument: The tram line of interest

    Optional arguments:

    If reverse=False, the holdups are plotted for that route on the line for which
    the dataset contains most information. If reverse=True, the same line is plotted in the opposite
    direction.
    Default: True

    which_holdup specifies whether to plot only the holdups in the time that a tram spends at a stop
    (which_holdup="at_stop"), or only the holdups which occur as the tram travels from the current stop
    to the next one (which_holdup="on_trajectory"). If which_holdup="total", then for each stop, the plot
    indicates all holdup from arrival at that stop until arrival at the next stop. In all three cases,
    note that nothing is plotted for the final stop of the route: By definition, there is no holdup there.
    Default: 'total'

    If annotations=True, the average holdup in seconds is shown in the plot, if annotations=False, this is
    omitted. Default: True

    """

    if which_holdup=="at_stop":
        col="holdup_stop"
        title="Holdups at stops"
    elif which_holdup=="on_trajectory":
        col="holdup_trajectory"
        title="Holdups on trajectories following stops"
    elif which_holdup=="total":
        col="total_holdup"
        title="Holdups from given stop to next stop"


    if reverse:
        dir_num=1
    else:
        dir_num=0

    routes=main_routes_of_line(line,data)
    route=routes[dir_num]


    conts=contributions(route,data)
    final_stop_short = route.split()[2]
    final_stop_long = convert_short_to_long(final_stop_short,data)
    stops_on_this_route=conts["halt_lang"]
    length_of_this_route=len(stops_on_this_route)
    plt.barh(range(length_of_this_route), conts[col],tick_label=stops_on_this_route,color=line_colors[line])
    plt.gca().invert_yaxis()

    plt.title("Tram {} (from {} to {}): {}".format(line,
                                                   conts["halt_lang"].iloc[0],
                                                   final_stop_long,
                                                   title))

    if annotations:
        for i,v in enumerate(conts[col]):
            if v<0:
                sv=" "+str(round(v,1))
                color="navy"
            else:
                sv="+"+str(round(v,1))
                color="red"
            plt.text(conts[col].max() *1.15, i+0.18, sv+" s", color=color)


    plt.tight_layout()
    plt.show()


def freq_major_delays_route(route,data,cutoff,per_stop=True,what="delay"):
    """ How frequent are delays longer than cutoff on this route?
    
    For a given route (ex: "REHA - ZAUZ") and given cutoff (in seconds), function outputs (i) how many observations are available
    for the delay that accumulates along that route, (ii) how many of these observations exceed the given cutoff, and (iii) what
    percentage of available observations exceed the cutoff.
    
    Optional arguments:
      
    If what="delay", the function considers delays.
    If what="deviation", the function considers deviations from the timetable instead of delays.
    Default: 'delay'
        
    If per_stop=False, function considers delay on the given route.
    If per_stop=True, function considers this delay divided by the number of stops.
    Default: True 
    
    which_holdup specifies whether to consider only the holdups in the time that a tram spends at a stop
    (which_holdup="at_stop"), or only the holdups which occur as the tram travels from the current stop
    to the next one (which_holdup="on_trajectory"). If which_holdup="total", then for each stop, all
    holdup from arrival at that stop until arrival at the next stop is considered. 
    Default: 'total'
        
    """
    
    df=data[data["fw_lang"]==route]
    stops_on_this_route=stops_on_route(route,data)
    length_of_route=len(stops_on_this_route)
    penultimate_stop=stops_on_this_route[-2]    
    df=df[df["halt_kurz"]==penultimate_stop]


    if per_stop:
        threshold=cutoff*length_of_route
    else:
        threshold=cutoff  
    
    number_observations=len(df)
    
    if what=="deviation":
        df=df[(df["delay_after_trajectory"]>threshold)|(df["delay_after_trajectory"]<-threshold)]
    else: 
        df=df[df["delay_after_trajectory"]>threshold]
      
    number_major_delays=len(df)
    percentage=(number_major_delays/number_observations)*100
    return number_observations, number_major_delays, round(percentage,2)


def freq_major_holdups_stop(line,stop,cutoff,data,what="delay",reverse=False,which_holdup="total"):
    """ This function is used to find out how frequent major holdups are at any given stop.
    
    Inputs: The line and the stop of interest, the cutoff that defines a major delay (Example: If 'cutoff'=5,
    then delays greater than 5 seconds will be considered).
    
    Optional arguments:
    
    Setting reverse=True changes the direction of travel on the line that is considered.
    Default: False
    
    If what="delay", the function considers delays.
    If what="deviation", the function considers deviations from the timetable instead of delays.
    Default: 'delay'
        
    If per_stop=False, function considers delay on the given route.
    If per_stop=True, function considers this delay divided by the number of stops.
    Default: True 
    
    which_holdup specifies whether to consider only the holdups in the time that a tram spends at a stop
    (which_holdup="at_stop"), or only the holdups which occur as the tram travels from the current stop
    to the next one (which_holdup="on_trajectory"). If which_holdup="total", then for each stop, all
    holdup from arrival at that stop until arrival at the next stop is considered. 
    Default: 'total'
    
    
    
    
    """
    
    
    routes=main_routes_of_line(line,data)
    
    if reverse:
        route=routes[1]
    else:
        route=routes[0]
     
    
    df=data[data["fw_lang"]==route]
    df=df[(df["halt_kurz"]==stop)|(df["halt_lang"]==stop)]
    num_obs=len(df)

    if which_holdup=="at_stop":
        col="holdup_stop"
        title="Holdups at stops"
    elif which_holdup=="on_trajectory":
        col="holdup_trajectory"
        title="Holdups on trajectories following stops"
    elif which_holdup=="total":
        col="total_holdup"
        title="Holdups from given stop to next stop"
          
    if what=="deviation":
        ndf=df[(df[col]>cutoff)|(df[col]<(-1)*cutoff)]
    else:
        ndf=df[df[col]>cutoff]

    num_maj_obs=len(ndf)
    return (num_maj_obs/num_obs)*100
          

def freq_major_holdups_all_stops(line,cutoff,data,what="delay",reverse=False,which_holdup="total"):
    """ Function creates a dataframe that shows the frequency of major holdup at any stop along the given line.
    
    Inputs: The number of the line to consider, and the cutoff that defines a major holdup (Example: If cutoff=5, then a holdup longer
        than 5 seconds is considered major.
        
    Optional Arguments:
    
    Setting reverse=True changes the direction of travel on the line that is considered.
    Default: False
    
    If what="delay", the function considers delays.
    If what="deviation", the function considers deviations from the timetable instead of delays.
    Default: 'delay'
        
   
    which_holdup specifies whether to consider only the holdups in the time that a tram spends at a stop
    (which_holdup="at_stop"), or only the holdups which occur as the tram travels from the current stop
    to the next one (which_holdup="on_trajectory"). If which_holdup="total", then for each stop, all
    holdup from arrival at that stop until arrival at the next stop is considered. 
    Default: 'total'
    
    
    """
    
    
    
    
    routes=main_routes_of_line(line,data)
    
    if reverse:
        route=routes[1]
    else:
        route=routes[0]
        
    rel_stops=stops_on_route(route,data)
    dictionary={}
    for stop in rel_stops:
        percentage=freq_major_holdups_stop(line,stop,cutoff,data,what=what,reverse=reverse,which_holdup=which_holdup)
        stop_long=convert_short_to_long(stop,data)
        dictionary[stop_long]=percentage
    df=pd.DataFrame.from_dict(dictionary,orient="index",columns=["Percentage"])
    return df



def fig_major_holdups_line(line,cutoff,line_colors,data,what="delay",reverse=False,which_holdup="total"):
    
    """ Function creates a plot that shows the frequency of major holdup at each stop along a line. 
    
    Inputs: The number of the line to consider, and the cutoff that defines a major holdup (Example: If cutoff=5, then a holdup longer
        than 5 seconds is considered major.
        
    Optional Arguments:
    
    Setting reverse=True changes the direction of travel on the line that is considered.
    Default: False
    
    If what="delay", the function considers delays.
    If what="deviation", the function considers deviations from the timetable instead of delays.
    Default: 'delay'
        
   
    which_holdup specifies whether to consider only the holdups in the time that a tram spends at a stop
    (which_holdup="at_stop"), or only the holdups which occur as the tram travels from the current stop
    to the next one (which_holdup="on_trajectory"). If which_holdup="total", then for each stop, all
    holdup from arrival at that stop until arrival at the next stop is considered. 
    Default: 'total'
    
    """
    
    df=freq_major_holdups_all_stops(line,cutoff,data,what=what,reverse=reverse,which_holdup=which_holdup)
    
    color=line_colors[line]
    
    plt.barh(range(len(df)), df["Percentage"],tick_label=df.index,color=line_colors[line])
    plt.gca().invert_yaxis()
    plt.title("How likely is a major holdup (>{}s)?".format(cutoff))
    plt.tight_layout()
    plt.show()

    
    
    
    
    




def table_delays_lines(lines,data):
    """ Produces a dataframe with all observations of delay that happen along the entire line (both directions/routes),
    for each of the specified lines.
    
    Input: An array of lines.    
    
    """
    
    dictionary={}
    for line in lines:
        routes=main_routes_of_line(line,data)
        array=[]
        for route in routes:
            df=data[data["fw_lang"]==route]
            stops_on_this_route=stops_on_route(route,data)
            length_of_route=len(stops_on_this_route)
            penultimate_stop=stops_on_this_route[-2]    
            df=df[df["halt_kurz"]==penultimate_stop]
            col=df["delay_after_trajectory"]
            for item in col:
                array.append(item)
        dictionary[line]=array
        
    ddf = pd.DataFrame({ key:pd.Series(value) for key, value in dictionary.items() })
    return ddf





def dist_lines(lines,data,line_colors):
    """ For each of the given lines, plots the distribution (estimated density function) of the delay
    that accumulates over the entire line.
    
    Inputs: An array of lines and a dictionary that associates a color to each line.
    
    """
    
    
    df=table_delays_lines(lines,data)
    for line in lines:
        sns.kdeplot(df[line],shade=True,color=line_colors[line])
    plt.yticks([])
    plt.xlabel("Seconds of delay at line's endpoint")
    plt.title("Distribution of delays accumulated until line's endpoint")
    plt.show()



    

    

    
    

    
    
    
    

def freq_major_delays_line(line,data,cutoff,per_stop=True,what="delay"):
    
    """ Function computes the probability with which delays accumulating on a given line exceed some cutoff.
    
    Inputs: The line of interest and the cutoff to consider.
    
    Optional arguments:
    
    If per_stop=False, function considers delay on the given route.
    If per_stop=True, function considers this delay divided by the number of stops.
    Default: True 
    
    If what="delay", the function considers delays.
    If what="deviation", the function considers deviations from the timetable instead of delays.
    Default: 'delay'
    
    
    """
    
    
    one_route,other_route=main_routes_of_line(line,data)
    total_obs=freq_major_delays_route(one_route,data,cutoff,per_stop=per_stop,what=what)[0]+freq_major_delays_route(other_route,data,cutoff,per_stop=per_stop,what=what)[0]
    total_major_delays=freq_major_delays_route(one_route,data=data,cutoff=cutoff,per_stop=per_stop,what=what)[1]+freq_major_delays_route(other_route,data,cutoff,per_stop=per_stop,what=what)[1]
    return (total_major_delays/total_obs)*100




def table_major_delays_lines(lines,data,cutoff,per_stop=True,what="delay"):
    
    """ Produces a dataframe that shows, for each of the given lines, how likely it is that
    a tram arrives at the line's endpoint with a major delay.
    
    Inputs: An array of lines to consider and a cutoff point (in seconds) above which a delay is
        to be considered major.
    
    Optional arguments:
    
    If per_stop=False, function considers delay on the given route.
    If per_stop=True, function considers this delay divided by the number of stops.
    Default: True 
    
    If what="delay", the function considers delays.
    If what="deviation", the function considers deviations from the timetable instead of delays.
    Default: 'delay'
    
    
    """
        
        
    
    percentages=[]
    for line in lines:
        percentage=freq_major_delays_line(line,data,cutoff,per_stop=per_stop,what=what)
        percentage=round(percentage,2)
        percentages.append(percentage)
    table=pd.DataFrame({"Line":lines,"Percentage":percentages})
    table=table.set_index("Line")
    return table


def plot_major_delays_lines(lines,line_colors,data,cutoff,per_stop=True,what="delay"):
    
    """ Creates a plot that illustrates, for each of the given lines, how likely it is that a tram
    reaches the endpoint of the line with a major delay.
    
    Inputs: An array of lines to consider and a cutoff point (in seconds) above which a delay is
        to be considered major.
    
    Optional arguments:
    
    If per_stop=False, function considers delay on the given route.
    If per_stop=True, function considers this delay divided by the number of stops.
    Default: True 
    
    If what="delay", the function considers delays.
    If what="deviation", the function considers deviations from the timetable instead of delays.
    Default: 'delay'  
    
    
    
    """
    
    table=table_major_delays_lines(lines,data,cutoff,per_stop=per_stop,what=what)
    colors=[]
    for line in lines:
        hex_color=line_colors[line]
        colors.append(hex_color)
    
    plt.bar(range(len(lines)),table["Percentage"],tick_label=table.index,color=colors)
    
    if per_stop:
        unit=" s (per stop)"
    else:
        unit=" s"

    if what=="deviation":
        plt.title("Percentage of trams with >{}{} deviation from timetable".format(cutoff,unit))
    else:
        plt.title("Percentage of trams with >{}{} delay".format(cutoff,unit))
    
    plt.xlabel("Line")
    plt.show()

 

        

    
    
    







