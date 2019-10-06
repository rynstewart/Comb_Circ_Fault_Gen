from __future__ import print_function
import os

#global variable to hold something-in-somthing-SA-
unnamedSA = []
# Function List:
# 1. netRead: read the benchmark file and build circuit netlist
# 2. gateCalc: function that will work on the logic of each gate
# 3. inputRead: function that will update the circuit dictionary made in netRead to hold the line values
# 4. basic_sim: the actual simulation
# 5. main: The main function


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Reading in the Circuit gate-level netlist file:
def netRead(netName):
    # Opening the netlist file:
    netFile = open(netName, "r")

    # temporary variables
    inputs = []     # array of the input wires
    outputs = []    # array of the output wires
    gates = []      # array of the gate list
    inputBits = 0   # the number of inputs needed in this given circuit
    faults = []

    # main variable to hold the circuit netlist, this is a dictionary in Python, where:
    # key = wire name; value = a list of attributes of the wire
    circuit = {}

    # Reading in the netlist file line by line
    for line in netFile:
        # NOT Reading any empty lines
        if (line == "\n"):
            continue

        # Removing spaces and newlines
        line = line.replace(" ","")
        line = line.replace("\n","")
        line = line.upper()
        # NOT Reading any comments
        if (line[0] == "#"):
            continue

        # @ Here it should just be in one of these formats:
        # INPUT(x)
        # OUTPUT(y)
        # z=LOGIC(a,b,c,...)

        # Read a INPUT wire and add to circuit:
        if (line[0:5] == "INPUT"):
            # Removing everything but the line variable name
            line = line.replace("INPUT", "")
            line = line.replace("(", "")
            line = line.replace(")", "")

            #part1 add 1 pair of SA's
            faults.append(line + "-SA-0")
            faults.append(line + "-SA-1")
            
            # Format the variable name to wire_*VAR_NAME*
            line = "wire_" + line

            # Error detection: line being made already exists
            if line in circuit:
                msg = "NETLIST ERROR: INPUT LINE \"" + line + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
                print(msg + "\n")
                return msg

            # Appending to the inputs array and update the inputBits
            inputs.append(line)

            # add this wire as an entry to the circuit dictionary
            circuit[line] = ["INPUT", line, False, 'U']

            inputBits += 1
            print(line)
            print(circuit[line])
            continue

        # Read an OUTPUT wire and add to the output array list
        # Note that the same wire should also appear somewhere else as a GATE output
        if line[0:6] == "OUTPUT":
            # Removing everything but the numbers
            line = line.replace("OUTPUT", "")
            line = line.replace("(", "")
            line = line.replace(")", "")
            
            # Appending to the output array
            outputs.append("wire_" + line)
            continue

        # Read a gate output wire, and add to the circuit dictionary
        lineSpliced = line.split("=") # splicing the line at the equals sign to get the gate output wire
        gateOut = "wire_" + lineSpliced[0]
        tempOut = lineSpliced[0]
        # Error detection: line being made already exists
        if gateOut in circuit:
            msg = "NETLIST ERROR: GATE OUTPUT LINE \"" + gateOut + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
            print(msg+"\n")
            return msg

        # Appending the dest name to the gate list
        gates.append(gateOut)

        lineSpliced = lineSpliced[1].split("(") # splicing the line again at the "("  to get the gate logic
        logic = lineSpliced[0].upper()

        
        lineSpliced[1] = lineSpliced[1].replace(")", "")
        terms = lineSpliced[1].split(",")  # Splicing the the line again at each comma to the get the gate terminals
        
        #part1 add 1 pair of SA's
        faults.append(tempOut + "-SA-0")
        faults.append(tempOut + "-SA-1")
        for INS in terms:
            faults.append(tempOut+"-IN-"+ INS+"-SA-0")
            faults.append(tempOut+"-IN-"+ INS+"-SA-1")
        
        # Turning each term into an integer before putting it into the circuit dictionary
        terms = ["wire_" + x for x in terms]

        # add the gate output wire to the circuit dictionary with the dest as the key
        circuit[gateOut] = [logic, terms, False, 'U']
        print(gateOut)
        print(circuit[gateOut])

    # now after each wire is built into the circuit dictionary,
    # add a few more non-wire items: input width, input array, output array, gate list
    # for convenience
    
    circuit["INPUT_WIDTH"] = ["input width:", inputBits]
    circuit["INPUTS"] = ["Input list", inputs]
    circuit["OUTPUTS"] = ["Output list", outputs]
    circuit["GATES"] = ["Gate list", gates]
    circuit["FAULTS"] = ["Full Faults", faults]
    
    print("\n bookkeeping items in circuit: \n")
    print(circuit["INPUT_WIDTH"])
    print(circuit["INPUTS"])
    print(circuit["OUTPUTS"])
    print(circuit["GATES"])
    print(circuit["FAULTS"])

    return circuit


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: calculates the output value for each logic gate
def gateCalc(circuit, node):
    
    # terminal will contain all the input wires of this logic gate (node)
    terminals = list(circuit[node][1])  

    #temporarily changes a wire's value for -in-SA
    if len(unnamedSA) > 0:
        if node == unnamedSA[0]: #if same output wire of gate as SA
            for term in terminals: #find the input terminal that is SA
                if term == unnamedSA[1]:
                    holdTheWire = list(circuit[term]).copy() #copy the wire attributes before change
                    circuit[term][3] = unnamedSA[2] #change bit value of wire
                    continue

    # If the node is an Inverter gate output, solve and return the output
    if circuit[node][0] == "NOT":
        if circuit[terminals[0]][3] == '0':
            circuit[node][3] = '1'
        elif circuit[terminals[0]][3] == '1':
            circuit[node][3] = '0'
        elif circuit[terminals[0]][3] == "U":
            circuit[node][3] = "U"
        else:  # Should not be able to come here
            return -1
        return circuit

    # If the node is an AND gate output, solve and return the output
    elif circuit[node][0] == "AND":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a flag that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 at any input terminal, AND output is 0. If there is an unknown terminal, mark the flag
        # Otherwise, keep it at 1
        for term in terminals:  
            if circuit[term][3] == '0':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        return circuit

    # If the node is a NAND gate output, solve and return the output
    elif circuit[node][0] == "NAND":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 terminal, NAND changes the output to 1. If there is an unknown terminal, it
        # changes to "U" Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '0':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
                break

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        return circuit

    # If the node is an OR gate output, solve and return the output
    elif circuit[node][0] == "OR":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, OR changes the output to 1. Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        return circuit

    # If the node is an NOR gate output, solve and return the output
    if circuit[node][0] == "NOR":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, NOR changes the output to 0. Otherwise, keep it at 1
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        return circuit

    # If the node is an XOR gate output, solve and return the output
    if circuit[node][0] == "XOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there are an odd number of terminals, XOR outputs 1. Otherwise, it should output 0
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '1'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '0'
        return circuit

    # If the node is an XNOR gate output, solve and return the output
    elif circuit[node][0] == "XNOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there is a single 1 terminal, XNOR outputs 0. Otherwise, it outputs 1
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '0'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '1'
        return circuit

    circuit[unnamedSA[1]] = list(holdTheWire).copy()
    # Error detection... should not be able to get at this point
    return circuit[node][0]


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Updating the circuit dictionary with the input line, and also resetting the gates and output lines
def inputRead(circuit, line):
    # Checking if input bits are enough for the circuit
    if len(line) < circuit["INPUT_WIDTH"][1]:
        return -1

    # Getting the proper number of bits:
    line = line[(len(line) - circuit["INPUT_WIDTH"][1]):(len(line))]

    # Adding the inputs to the dictionary
    # Since the for loop will start at the most significant bit, we start at input width N
    i = circuit["INPUT_WIDTH"][1] - 1
    inputs = list(circuit["INPUTS"][1])
    # dictionary item: [(bool) If accessed, (int) the value of each line, (int) layer number, (str) origin of U value]
    for bitVal in line:
        bitVal = bitVal.upper() # in the case user input lower-case u
        circuit[inputs[i]][3] = bitVal # put the bit value as the line value
        circuit[inputs[i]][2] = True  # and make it so that this line is accessed

        # In case the input has an invalid character (i.e. not "0", "1" or "U"), return an error flag
        if bitVal != "0" and bitVal != "1" and bitVal != "U":
            return -2
        i -= 1 # continuing the increments

    return circuit

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: the actual simulation #
def basic_sim(circuit):
    # QUEUE and DEQUEUE
    # Creating a queue, using a list, containing all of the gates in the circuit
    queue = list(circuit["GATES"][1])
    i = 1

    while True:
        i -= 1
        # If there's no more things in queue, done
        if len(queue) == 0:
            break

        # Remove the first element of the queue and assign it to a variable for us to use
        curr = queue[0]
        queue.remove(curr)

        # initialize a flag, used to check if every terminal has been accessed
        term_has_value = True

        # Check if the terminals have been accessed
        for term in circuit[curr][1]:
            if not circuit[term][2]:
                term_has_value = False
                break
            
        ##part2 skip this cuz this is a SA wire    
        if circuit[curr][2] == True:
            continue
        
        if term_has_value:
            circuit[curr][2] = True
            circuit = gateCalc(circuit, curr)

            # ERROR Detection if LOGIC does not exist
            if isinstance(circuit, str):
                print(circuit)
                return circuit

            print("Progress: updating " + curr + " = " + circuit[curr][3] + " as the output of " + circuit[curr][0] + " for:")
            for term in circuit[curr][1]:
                print(term + " = " + circuit[term][3])
            #print("\nPress Enter to Continue...")
            #input()

        else:
            # If the terminals have not been accessed yet, append the current node at the end of the queue
            queue.append(curr)

    return circuit

#this will update the circuit list will the fault found in the line passed into the function
def readFaults(line, circuit):
    line = line.split("-")
    if(len(line) == 3):
        circuit["wire_"+line[0]][2] = True
        circuit["wire_"+line[0]][3] = line[2]
    elif(len(line) == 5):
        global unnamedSA
        unnamedSA = []
        unnamedSA = ["wire_"+line[0], "wire_"+line[2], line[4]]
    return circuit

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: read_flist
def read_flist(flist_Input):
    flistFile = open(flist_Input, "r")
    fault_list = list()
    
    for line in flistFile:
        if (line == "\n"):
            continue
        if (line[0] == "#"):
            continue
        # Removing the the newlines at the end and then output it to the txt file
        line = line.replace("\n", "")
        # Removing spaces
        line = line.replace(" ", "")
        line = line.upper()
        fault_list.append(line)
    
    flistFile.close()
    return fault_list

#reset the circuit for a new simulation
def resetCircuit(circuit):
    for key in circuit:
        if (key[0:5]=="wire_"):
            circuit[key][2] = False
            circuit[key][3] = 'U'
    return circuit            

#function that will loop through all faults and simulate SA faults <----------------
def sa_Fault_Simulator(flist, circuit, line, newCircuit, outputFile, output):
    detectedFaults = []
    detectedouputs = []
    #simulate for each SA fault
    #line will have current TV #aFault will have current SA fault
    for aFault in flist:
        print("\n ---> Now ready to simulate INPUT = " + line + "@" + aFault)
        #circuit = newCircuit
        circuit = inputRead(circuit, line)
        if circuit == -1:
            print("INPUT ERROR: INSUFFICIENT BITS")
            outputFile.write(" -> INPUT ERROR: INSUFFICIENT BITS" + "\n")
            # After each input line is finished, reset the netList
            circuit = newCircuit
            print("...move on to next input\n")
            continue
        elif circuit == -2:
            print("INPUT ERROR: INVALID INPUT VALUE/S")
            outputFile.write(" -> INPUT ERROR: INVALID INPUT VALUE/S" + "\n")
            # After each input line is finished, reset the netList
            circuit = newCircuit
            print("...move on to next input\n")
            continue
        #simulate faults and calculate output
        circuit = readFaults(aFault, circuit)
        circuit = basic_sim(circuit)
        print("\n *** Finished simulation - resulting circuit: \n")
        print(circuit)
        SA_output = "" #create a variable to hold the output of the SA fault
        for y in circuit["OUTPUTS"][1]:
            if not circuit[y][2]:
                SA_output = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                break
            SA_output = str(circuit[y][3]) + SA_output

        print("\n *** Summary of simulation: ")
        print(aFault+ " @" + line + " -> " + SA_output + " written into output file. \n")
        outputFile.write(aFault + " @" + line + " -> " + SA_output + "\n")
        if output != SA_output:
            detectedFaults.append(aFault)
            detectedouputs.append(SA_output)
        # After each input line is finished, reset the circuit
        print("\n *** Now resetting circuit back to unknowns... \n")
        resetCircuit(circuit)
    return [detectedFaults,detectedouputs]


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Main Function
def main():
    # **************************************************************************************************************** #
    # NOTE: UI code; Does not contain anything about the actual simulation

    # Used for file access
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

    print("Circuit Simulator:")

    # Select circuit benchmark file, default is circuit.bench
    while True:
        cktFile = "circuit.bench"   
        print("\n Read circuit benchmark file: use " + cktFile + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            break
        else:
            cktFile = os.path.join(script_dir, userInput)
            if not os.path.isfile(cktFile):
                print("File does not exist. \n")
            else:
                break

    print("\n Reading " + cktFile + " ... \n")
    circuit = netRead(cktFile)
    print("\n Finished processing benchmark file and built netlist dictionary: \n")
    print(circuit)

    # keep an initial (unassigned any value) copy of the circuit for an easy reset
    newCircuit = circuit
    
    # Select fault list file, default is f_list.txt
    while True:
        flistName = "f_list.txt"
        print("\n Read fault: use " + flistName + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":

            break
        else:
            flistName = os.path.join(script_dir, userInput)
            if not os.path.isfile(flistName):
                print("File does not exist. \n")
            else:
                break
    # saving the fault list        
    flist = read_flist(flistName)
    totalNumFaultsPossible=len(flist)
    # Select input file, default is input.txt
    while True:
        inputName = "input.txt"
        print("\n Read input vector file: use " + inputName + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":

            break
        else:
            inputName = os.path.join(script_dir, userInput)
            if not os.path.isfile(inputName):
                print("File does not exist. \n")
            else:
                break
 #JEM-Creating fault sim result file to write,read, append to
    fs_result = open("fault_sim_result.txt","w+")
    fs_result.write("#input: " + cktFile+"\n")
    fs_result.write("#input: " + inputName + "\n")
    fs_result.write("#input: " + flistName +"\n")
    fs_result.write("\n")


    # Select output file, default is output.txt
    while True:
        outputName = "output.txt"
        print("\n Write output file: use " + outputName + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            break
        else:
            outputName = os.path.join(script_dir, userInput)
            break
        
    # Select full fault file, default is output.txt
    while True:
        fault_out = "full_f_list.txt"
        print("\n Write full fault file: use " + fault_out + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            break
        else:
            fault_out = os.path.join(script_dir, userInput)
            break

    # Note: UI code;
    # **************************************************************************************************************** #

    print("\n *** Simulating the" + inputName + " file and will output in" + outputName + "*** \n")

    fault_out = open(fault_out, "w")
    fault_out.write("# circuit.bench\n #fullSSA fault list\n\n")
    for f in circuit['FAULTS'][1]:
        fault_out.write(f + '\n')
    fault_out.write("\n #total faults: " + repr(len(circuit['FAULTS'][1])))    
    fault_out.close()

    inputFile = open(inputName, "r")
    outputFile = open(outputName, "w")
    flistName = open(flistName, "r")
    tvNumber=0

    #initializing list to add faults found
    faults_Found= []

    # Runs the simulator for each line of the input file
    for line in inputFile:
        # Reset circuit before start
        print("\n *** Reseting circuit with unknowns... \n")
        resetCircuit(circuit)
        # Empty the "good" output value for each TV
        output = ""
        tvNumber=tvNumber+1
        # Do nothing else if empty lines, ...
        if (line == "\n"):
            continue
        # ... or any comments
        if (line[0] == "#"):
            continue

        # Removing the the newlines at the end and then output it to the txt file
        line = line.replace("\n", "")
        outputFile.write(line) #write the TV to the output 
        
        # Removing spaces
        line = line.replace(" ", "")

        #Getting ready to simulate no faults circuit
        print("\n before processing circuit dictionary...")
        print(circuit)
        print("\n ---> Now ready to simulate INPUT = " + line)
        circuit = inputRead(circuit, line)
        print(circuit)

        if circuit == -1:
            print("INPUT ERROR: INSUFFICIENT BITS")
            outputFile.write(" -> INPUT ERROR: INSUFFICIENT BITS" + "\n")
            # After each input line is finished, reset the netList
            circuit = newCircuit
            print("...move on to next input\n")
            continue
        elif circuit == -2:
            print("INPUT ERROR: INVALID INPUT VALUE/S")
            outputFile.write(" -> INPUT ERROR: INVALID INPUT VALUE/S" + "\n")
            # After each input line is finished, reset the netList
            circuit = newCircuit
            print("...move on to next input\n")
            continue

        #simulate no faults circuit
        circuit = basic_sim(circuit)
        print("\n *** Finished simulation - resulting circuit: \n")
        print(circuit)
        #Jasmine-this shows output
        for y in circuit["OUTPUTS"][1]:
            if not circuit[y][2]:
                output = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                break
            output = str(circuit[y][3]) + output
        #^^^^^^^^^"output" will hold the "good" circuit output value
        print("\n *** Summary of simulation: ")
        print(line + " -> " + output + " written into output file. \n")
        outputFile.write(" -> " + output + "\n")
        
        # After each input line is finished, reset the circuit
        print("\n *** Now resetting circuit back to unknowns... \n")
        resetCircuit(circuit)     
        
        
        ########################################################
        #detectedFaultsforCurrentTV will be updated with all the detected SA faults in the current TV.
        current_TV_Detected_Faults = sa_Fault_Simulator(flist, circuit, line, newCircuit, outputFile, output)
        fs_result.write("\ntv"+ str(tvNumber) +" = " + line + " -> "+str(output) + " (good)\n") #JEM
        #getting length of first dimension of list JEM
        lengthList=len(current_TV_Detected_Faults[0])
        #iterating through list to print output of TV @ fault JEM
        fs_result.write("detected:\n")
        i = 0
        print("length of list: "+ str(lengthList)+"\n")
        while i < lengthList:
            fs_result.write(current_TV_Detected_Faults[0][i]+":  "+line +" -> "+current_TV_Detected_Faults[1][i]+"\n")
            #print("current_detected_faults[0][i]="+current_TV_Detected_Faults[0][i]+"\n") debug
            #print("faults found list now:") debug
            #print(*faults_Found, sep =",") debug
            if (current_TV_Detected_Faults[0][i] not in faults_Found):
                #add to faults_Found JEM DEBUG
                faults_Found.append(current_TV_Detected_Faults[0][i])
                #print("current_detected_faults[0][i]="+current_TV_Detected_Faults[0][i]+"\n") debug
                #print("faults found list now:")debug
                #print(*faults_Found, sep =",")debug
            i=i+1
        
        outputFile.write('%s\n' % current_TV_Detected_Faults)
        
        # After each input line is finished, reset the circuit
        print("\n *** Now resetting circuit back to unknowns... \n")
        resetCircuit(circuit)
        
        print("\n circuit after resetting: \n")
        print(circuit)
        print("\n*******************\n")
        
    outputFile.close()

    #JEM printing summary of faults found 
    #delete flist as u find faults/add to faults_Found
    for i in faults_Found:
        if (i in flist):
                #add to faults_Found JEM DEBUG
                flist.remove(i)
    undetectedFaults=len(flist)
    total_faults_found=len(faults_Found)
    #make list of undetected faults JEM
    fs_result.write("\n\ntotal detected faults: "+str(total_faults_found)+"\n")
    #for detected_fault in faults_Found: #debug
        #fs_result.write('%s\n' % detected_fault) #debug
    #print(*faults_Found, sep ="\n") debug
    
    fs_result.write("\n\nundetected faults: "+str(undetectedFaults)+"\n")
    for undetected_fault in flist:
        fs_result.write('%s\n' % undetected_fault)
    #fs_result.write(*flist, sep ="\n")
    #print fault list JEM DEBUG
    percentFaultsFound=100*float(total_faults_found)/float(totalNumFaultsPossible)
    fs_result.write("\n\nfault coverage: "+ str(total_faults_found)+"/"+str(totalNumFaultsPossible)+" = "+str(percentFaultsFound)+ "% \n") #JEM 
    
    #closing fault sim result file
    fs_result.close()

    #exit()


if __name__ == "__main__":
    main()

