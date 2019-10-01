
def comparePyAna(folder):
	f = ROOT.TFile.Open("/mnt/c/Users/Mei-Li/cernbox/exjobb/test/data_1540353448.tree.root") #3k events from October 2018
	tree = f.Get("oscilloscope")
	pyAna_file, pyAna_tree = getTree(folder + 'october_osc/', '1540353448')
	chan = 0
	pulses = []
	pyAna_pulses = []

	for iev in tree:
		command = 'tree.chan' + str(chan)
		channel = eval(command)

		imax = np.argmin(channel)
		maxval = -channel[imax]*1000 #microvolts

		if maxval > 20:
			pulses.append([imax*100, maxval])

	for iev in pyAna_tree:
		time = pyAna_tree.timeAtMax[chan]
		maxval = pyAna_tree.pulseHeight[chan]

		if maxval > 20:
			pyAna_pulses.append([time, maxval])

	for i in range(len(pyAna_pulses)):
		if pulses[i][0] == pyAna_pulses[i][0]:
			print i, pulses[i], pyAna_pulses[i]

	print pulses
	print pyAna_pulses
	print len(pulses)
	print len(pyAna_pulses)


#Returns the most probable value of pulse height/noise for a certain voltage
def calculateSNMPV(folder, file_list, chan, tresmin, tresmax):
	h1 = ROOT.TH1F("h1", "; pulse height/noise; Number of pulses", 50, 0, 200)

	for run in file_list:

		if run == '1539954453' or run == '1540147821' or run == '1540182499' or run == '1540261900':	#Corrupted files...
			print 'skipped'

		else:
			print run

			root_file, tree = getTree(folder + 'october_osc/', run)

			for iev in tree:
				print tree.timeAtMax[chan], tresmin, tresmax
				if tree.timeAtMax[chan] > tresmin and tree.timeAtMax < tresmax:
					h1.Fill(tree.pulseHeight[chan]/tree.noise[chan])

	if h1.GetEntries()  == 0:	#If histogram is empty
		sn = 0
		sn_err = 0

	else:
		f = makeLandauGausFit(h1)
		h_fit = h1.Fit(f.GetName(), "S")

		#canvas = ROOT.TCanvas("Canvas","Title",800,600)
		#canvas.Draw()
		#canvas.WaitPrimitive()

		sn = h_fit.Parameter(1)		#The most probable value of the fit
		sn_err = h_fit.ParError(1)



	return sn, sn_err


#calculate SN
def calculateSN(folder, run_log, sensor_name):
	sn = []
	sn_err = []
	row_start, row_end, col, chan, tresmin, tresmax = getSensor(sensor_name)
	V, voltage_list = getVoltageAndRunList(run_log, sensor_name)	#List of the voltages, and the data file run numbers sorted by the voltages

	for file_list in voltage_list:
		sn_val, sn_std = calculateSNMPV(folder, file_list, chan, tresmin, tresmax)	#calculate the most probable value for a specific voltage
		sn.append(sn_val)
		sn_err.append(sn_std)

	V = np.array(V)
	sn = np.array(sn)
	sn_err = np.array(sn_err)
	V_err = np.zeros(len(V))

	return V, sn, V_err, sn_err


#PLOT PULSE HEIGHT / NOISE
def makeSN(folder, run_log, sensor_name):
		graph_list = [None]*len(sensor_list1)

		mg = ROOT.TMultiGraph()
		mg.SetTitle("veni vidi plotta; Voltage [V]; Charge")

		for s in range(len(sensor_list1)):
			print sensors[s]
			V, sn,  V_err, sn_err = calculateSN(folder, run_log, sensor_list1[s])
			graph_list[s] = ROOT.TGraphErrors(len(V), V, sn, V_err, sn_err)
			graph_list[s].SetMarkerStyle(20)
			graph_list[s].SetMarkerColor(s+1)
			graph_list[s].SetTitle(sensors[s])
			mg.Add(graph_list[s])

		return mg


#Calculate fraction of events with pulses
def TotalNumberOfPulses(folder, run_log, sensor_name):
	row_start, row_end, col, chan, tresmin, tresmax = getSensor(sensor_name)
	V, voltage_list = getVoltageAndRunList(run_log, sensor_name)	#List of the voltages, and the data file run numbers sorted by the voltages

	print sensor_name

	for i in range(len(V)):
		n = 0 							#Number of pulses for a certain voltage
		n_tot = 0

		for run in voltage_list[i]:
			#print run
			if run != '1539954453' and run != '1540147821' and run != '1540182499' and run != '1540261900':	#Corrupted files...
				f, tree = getTree(folder + 'october_osc/', run)
				n += numberOfPulses(tree, chan)
				n_tot += tree.GetEntries()

		print "Voltage: ", V[i], " Number of pulses: ", n, "Total number of events: ", n_tot


def amplitudeHistogram(folder, run, sensor_name):
	row_start, row_end, col, chan, tresmin, tresmax = getSensor(sensor_name)

	root_file, tree = getTree(folder + 'october_osc/', run)
	h1 = ROOT.TH1F("h1", "; Amplitude [mV]; Number of pulses", 25, 0, 150)

	for iev in tree:
		h1.Fill(tree.pulseHeightNoise[chan])
		#print tree.pedestal[chan], tree.noise[chan], tree.pulseHeight[chan], tree.pulseHeightNoise[chan]

	canvas = ROOT.TCanvas("Canvas","Title",800,600)
	h1.Draw()
	canvas.WaitPrimitive()

	return h1
