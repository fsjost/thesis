import ROOT
from array import array

#Specify which folder of the data
data_folder = '/data/HGTD/data/testbeam/'

#Open run log file
log_file = open(data_folder + 'april_2018/' + 'Database_RunInfoOctober2018.dat', "r")
log = [i.strip().split() for i in log_file.readlines()]

# Returns tracking
def getTrack(folder, batchnr):
	file_t = ROOT.TFile.Open(folder + 'Tracking-00-04-00/' + 'tree_April2018_' + str(batchnr) + '.root')
	tree = file_t.Get("tree")
	return file_t, tree

#Returns the specified tree
def getOsc(folder, run_num):
	#Open ROOT file with the data
	file_o = ROOT.TFile.Open(folder + 'april_2018/' + 'data_' + str(run_num) + '.tree.root')
	o = file_o.Get("oscilloscope")
	return file_o, o

# Creates an interval for SiPM/DUT for the ENTIRE batch
def getDeltaT(f, t):
    t.Draw("timeAtMax[{1}]-timeAtMax[{0}]>>h(1000,-100000,100000)".format(channel, sipm),"","goff")		# Given in ps
    #t.Draw("timeAtMax[{0}]>>h(260,0,52000)".format(channel, sipm))										# Given in ps
    hdelta = f.Get('h')
    maxt_low = hdelta.GetBinLowEdge(hdelta.GetMaximumBin())
    deltat = [(maxt_low-1000)/1000, (maxt_low+1200)/1000]												# Given in ps
    hdelta.SetLineWidth(1)
    hdelta.SetLineColor(418)
    hdelta.Draw()
    hdelta.SetTitle('Time at max; t [ps]; # events')
    #raw_input("PRESS ENTER TO CONTINUE.") 			# Tab out to see histogram
    return deltat

def plotAnEvent(tree, event):
    tree.GetEntry(event)							# Load the specified event
    command = "tree." + 'chan' + str(channel) 		# Create the wanted command using strings
    chan = eval(command)							# Gets the branch/channel
    n_time = len(chan)								# The number of data
    x, y = array( 'd' ), array( 'd' )
    for i in range(n_time):							# Put all the data in the y-vector
        x.append(i*0.1)
        y.append(chan[i]*-1000)
    canvas = ROOT.TCanvas("Canvas", "Title", 800, 600)
    g_ch = ROOT.TGraph(n_time, x, y)
    g_ch.SetTitle("An event with a pulse; Time [ns]; Voltage [mV]")
    g_ch.Draw()
    #raw_input("PRESS ENTER TO CONTINUE.")

# Creates a track for all pulses greater than 10 mV
def createTrack(f, t):
    #X = "{1}+(Xtr[{0}]-{1})*cos(pi/4)-(Ytr[{0}]-{2})*sin(pi/4)".format(channel, xmid, ymid)
    #Y = "{2}+(Xtr[{0}]-{1})*sin(pi/4)+(Ytr[{0}]-{2})*cos(pi/4)".format(channel, xmid, ymid)
    t.Draw("Ytr[{0}]:Xtr[{0}]>>h(700,100,800,700,100,800)".format(channel),"pulseHeight[{0}]>{1}".format(channel,vtres), "goff")
    #t.Draw("{1}:{0}>>h(700,100,800,700,100,800)".format(X,Y),"pulseHeight[{0}]>{1}".format(channel,vtres), "goff")
    h = f.Get('h')
    #h.SetTitle("Individual track and the sensor; X-position; Y-position")
    raw_input("PRE CLENSE")
    for i in range(1,h.GetNbinsX() + 1):
        for j in range(1,h.GetNbinsY() + 1):
            if h.GetBinContent(i,j) < 3:
                h.SetBinContent(h.GetBin(i,j),0)
    raw_input("POST CLEANSE")
    return h

# Checks beginning of an event for a trigger
def oscBeginning(tree, tracktree, trigg):
    tracktree.GetEntry(tracktree.eventNumber)	# Load the specified event
    tree.GetEntry(tracktree.eventNumber)		# Load the specified event
    command = "tree.chan{0}".format(channel) 	# Create the wanted command using strings
    chan = eval(command)	 					# Gets the branch/channel
    maxtime = tracktree.timeAtMax[sipm]/1000
    n_time = np.arange(0, maxtime, 0.1)
    y = array( 'd' )
    for i in n_time:							# Plots beginning of event
        if (chan[int(i.item()*10)]*-1000) > tracktree.noise[channel]*5:
            trigg += 1
            return trigg
    return trigg



# Examines the possible triggers based on pre-defined criteria
def checkTops(df, deltat, tree,trackPrint):
    triggers = 0
    runNumber = 0
    for iev in tree:
        if runNumber != tree.runNumber:
            file_o, osc = getOsc(df, tree.runNumber)
            runNumber = tree.runNumber
            print runNumber
        X = tree.Xtr[channel]
        Y = tree.Ytr[channel]
        #X = xmid+(tree.Xtr[channel]-xmid)*math.cos(math.pi/4)-(tree.Ytr[channel]-ymid)*math.sin(math.pi/4)
        #Y = ymid+(tree.Xtr[channel]-xmid)*math.sin(math.pi/4)+(tree.Ytr[channel]-ymid)*math.cos(math.pi/4)
        idelta = (tree.timeAtMax[sipm]-tree.timeAtMax[channel])/1000
        if (
                tree.pulseHeight[channel] < tree.noise[channel]*5 or
                deltat[0] <= idelta <= deltat[1] or
                (	494 < X < 556 and 236 < Y < 290   )
            ):
            continue
        else:
            if tree.timeAtMax[sipm]:
                triggers = oscBeginning(osc, tree, triggers)
            else:
                continue
    print "Total number of autotriggers:", triggers

# Batch for June 2018
batch = [103]

# Opens file connected to a specified batch, creates track-print connected to
# the batch. Finds the delta t-distribution and checks tops based on pre-defined
# criteria. Note active channel, SiPM, and mid-values for the x and y-coordinates
# must be manually inserted.
def mainNew(df, batch):
    global channel
    channel = 1
    global sipm
    sipm = 3
    global vtres
    vtres = 10
    global ymid
    ymid = 449.4
    global xmid
    xmid = 461.6
    for batchnr in batch:
		file_t, tree = getTrack(df,batchnr)
		trackPrint = createTrack(file_t, tree)
        print "Tracker made"
        deltat = getDeltaT(file_t, tree)
        print "Delta achieved:", deltat
        print "batch number", batchnr
        checkTops(df, deltat, tree, trackPrint)

mainNew(data_folder, batch)
