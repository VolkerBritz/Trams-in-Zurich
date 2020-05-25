

def main_routes_of_line(line):
    """Takes a line number as input. Returns the two most common routes on that line. Typically,
    these will be the routes connecting both final stops. More routes exist per line: For instance,
    when the tram goes from one endpoint of its line to the depot."""
    df=trams[trams["linie"]==line]
    return df["fw_lang"].value_counts().head(2).index.to_numpy()


def convert_short_to_long(name,stops):
    """ Takes the short name (example: 'REHA') of a stop and returns its long name ('Rehalp'), using the information
    provided by 'haltestelle.csv'. """

    stops=stops.reset_index(drop=True).set_index("halt_kurz")
    stops=stops["halt_lang"].str.replace("Zürich, ","").str.replace("Zürich,","")
    return stops.loc[name]


def stops_on_route(route):
    """ Given a route (example: 'BSTA - BUCH'), function returns an array of the stops along that route,
     including the first stop, but excluding the final stop. Names of stops are returned in their
     short form. """
    first_stop=route.split()[0]
    last_stop=route.split()[2]
    df=trams[trams["fw_lang"]==route]
    df=df[["halt_kurz_von1","halt_kurz_nach1"]]
    df=df.drop_duplicates(subset="halt_kurz_von1", keep="last")
    df=df.set_index("halt_kurz_von1")
    stops=[]
    current_stop=first_stop
    while current_stop!=last_stop:
        stops.append(current_stop)
        current_stop=df.loc[current_stop][0]
    return stops


def contributions(route):
    """ For a given route (example: 'REHA - ZAUZ'), function creates a dataframe that shows for each
    stop along the route the average holdups associated with the stop: First, the average holdup that occurs
    while the tram is at the stop. Second, the average holdup that occurs while the tram moves from this stop
    to the next stop. Third, the sum of the above two holdups. """
    df=trams[trams["fw_lang"]==route]
    df=df[["halt_lang","halt_kurz_von1","holdup_stop","holdup_trajectory","total_holdup"]]
    conts=df.groupby(["halt_kurz_von1","halt_lang"]).mean()
    conts=conts.reset_index(level=conts.index.names)
    conts=conts.set_index(["halt_kurz_von1"])
    stops_in_order=stops_on_route(route)
    conts=conts.reindex(stops_in_order)
    return conts


def number_of_stops(route):
    """ For each route (example: 'REHA - ZAUZ), function returns the number of stops
    on that route, excluding the final stop.
    """
    conts=contributions(route)
    return len(conts)

def delay_along_route(route,which_holdup="total",absolute=False):
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

    conts=contributions(route)
    conts=conts.drop("halt_lang",axis=1)

    if absolute:
        conts=conts.abs()


    aggs=conts.sum()[idx]
    return aggs





def measure_of_delay_line(line, which_holdup="total",absolute=False,per_stop=True):
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
        If per_stop=True, function returns this delay divided by the number of stops, making comparisons between
            lines more meaningful.
        Default: True

    """

    measures=[]
    for route in main_routes_of_line(line):
        num=delay_along_route(route,which_holdup=which_holdup,absolute=absolute)
        den=number_of_stops(route)
        if per_stop:
            measures.append(num/den)
        else:
            measures.append(num)
        return sum(measures)/len(measures)



def table_lines(lines=all_lines, which_holdup="total",per_stop=True):
    delays=[]
    deviations=[]
    for line in lines:
        delay=measure_of_delay_line(line, which_holdup=which_holdup,per_stop=per_stop)
        delays.append(delay)
        deviation=measure_of_delay_line(line,which_holdup=which_holdup,absolute=True)
        deviations.append(deviation)
        print("Success with line "+" "+str(line))
    table=pd.DataFrame({"Line":lines, "Delay":delays, "Deviation":deviations})
    table=table.set_index("Line")
    return table

def figure_lines(lines=all_lines, which_holdup="total",what="delay",per_stop=True):

    table=table_lines(lines=lines,which_holdup=which_holdup,per_stop=per_stop)
    colors=[]
    for line in lines:
        hex_color=line_colors[line]
        colors.append(hex_color)
    if what=="deviation":
        array=table["Deviation"]
        title="Which lines deviated most from the timetable?"
    else:
        array=table["Delay"]
        title="Which lines had most delays from endpoint to endpoint?"
    plt.bar(range(len(lines)), array, tick_label=table.index, color=colors)
    plt.title(title)

    if per_stop:
        plt.ylabel("Seconds per stop on the line")
    else:
        plt.ylabel("Seconds")


    plt.xlabel("Line")
    plt.tight_layout()
    plt.show()


def plot_overview_for_line(line, reverse=False, which_holdup="total", annotations=True):
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

    routes=main_routes_of_line(line)
    route=routes[dir_num]


    conts=contributions(route)
    final_stop_short = route.split()[2]
    final_stop_long = convert_short_to_long(final_stop_short,stops)
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











