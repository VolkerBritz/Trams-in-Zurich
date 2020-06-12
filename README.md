# Delays of trams in Zürich

The city of Zürich provides extensive data on scheduled and actual times at which trams arrive and depart from stops. More specifically, each time a tram travels from one stop to another, detailed information about that trajectory is recorded: When exactly did the tram arrive at the former stop, when did it leave this stop, when did it arrive at the latter stop and leave from there again? On which route of which line was the tram traveling? 

This information is made available on a weekly basis via the city's open data website:

https://data.stadt-zuerich.ch/dataset/vbz_fahrzeiten_ogd

In this project, I create a Python module of functions that allow for fast analysis and visualization of the information contained in such a weekly dataset. 

In particular, one can use the module to visualize the amount of delays that occur on each line of Zürich's tram network, so as to quickly grasp which lines are most prone to delays. Furthermore, one can focus on a particular line and see how each part of that line's trajectory contributes to delays. Functions in the module come with optional arguments that allow us to focus on delays that occur due to excessive holdup *at* stops vs. delays that occur due to excessive time needed to travel *between* stops. It is also possible to choose whether one wants to focus on "delays" or "deviations."

(I use the following terminology: A *delay* refers to a tram arriving late at its final destination. If delay is negative, the tram is early. A *holdup* is the time a tram loses by spending too much time at a particular stop or traveling between two particular stops. If holdup is negative, the tram is "catching up." Holdups along the whole line sum up to delay. The absolute values of all holdups along the whole line sum up to the *deviation*. EXAMPLE: Imagine that a tram goes only from A to B to C. Suppose that, relative to timetable, it loses 20 seconds on the way from A to B, but gains 15 seconds relative to the timetable on the way from B to C. Then, its delay is 20-15=5 seconds, while its deviation is 20+15=35 seconds. 

The module also has functionality that allows us to define a threshold above which we want to consider a delay, holdup, or deviation "significant," and then compute the probability that such a significant delay occurs on any given line or at any given stop. We can also display distributions (density functions) of delays.

