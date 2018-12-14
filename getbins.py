#!/usr/bin/python3

# Turn on debug mode.
import cgi, cgitb, telnetlib, time, os
cgitb.enable()

# Print necessary headers.
print("Content-Type: text/html", "|")
print()

# Updater code below

def TelnetLoginandGetPrompt(mxkip):
    mxktelnet = telnetlib.Telnet(mxkip)
    mxktelnet.read_until(b"login:")
    mxktelnet.write(b"admin\n")
    mxktelnet.read_until(b"password:")
    mxktelnet.write(b"zhone\n")
      
    # The prompt is extremely important in determining if a download has finished, among other things.
    # Here, I extract whatever comes up after login.
    prompt = str(mxktelnet.read_until(b"zSH>", 1))
    
    # Basically, theres a bunch of junk leftover from the read_until function above.
    # I know there will be exactly 8 characters of trash before and including the carriage return character ("\r").
    # I slice the first 8 characters off the string, and also remove any extra characters at the end, however unlikely.
    prompt = prompt[prompt.find("b' \n\r")+8:prompt.find(" '")]
    prompt = prompt.encode()
    
    return mxktelnet, prompt
                 
    
def CreateFolder(binname, chassistype, version):
    frosttelnet = telnetlib.Telnet("172.16.41.193")
      
    frosttelnet.read_until(b"login:")
    frosttelnet.write(b"scassaro\n")
    frosttelnet.read_until(b"Password:")
    frosttelnet.write(b"Passw0rd\n")
    frosttelnet.read_until(b"-bash-3.00$")
    
    findfolder = "find dl/" + chassistype + "_" + version + " -name '" + binname + "'\n"
    frosttelnet.write(findfolder.encode('ascii'))
    folder = str(frosttelnet.read_until(b"-bash-3.00$"))
    #folder[:18] == "find: stat() error" and 
    if(folder.find("No such file or directory") > -1):
        findfolder = "find gadl/" + chassistype + "_" + version + " -name '" + binname + "'\n"
        frosttelnet.write(findfolder.encode('ascii'))
        folder = str(frosttelnet.read_until(b"-bash-3.00$"))
    folder = folder[folder.find("/")+1:]
    return (folder[folder.find("/")+1:-16])
                              

def DetermineChassisType(mxktelnet, prompt):
         
    # Get "slots" output from the system.
    mxktelnet.write(b"slots\n")
    
    # If the system is an MXK Classic or 219/F, "MXK" will always be at index [1] when the output is split into an array of strings using ".split()".
    rawslots = (mxktelnet.read_until(prompt).decode('ascii')).split()
    
    # Check if "MXK" appears at index [1] of rawslots,
    if(rawslots[1] == "MXK"):
        
        # and if so, return "MXK",
        return("MXK")
    
    # otherwise its a 1U, return MX.
    else:
        return("MX")

def PrintBins(dirarray, form, chassistype):
    for i in range(len(dirarray) - 1):
        binary = dirarray[i]
        if(binary[-4:] == ".tar"):
            print(binary, "|")
        if (binary[-4:] == ".bin" and binary[-7:] != "rom.bin" and binary[-5:] != "_.bin"):
            print((CreateFolder(binary, chassistype, form.getvalue('version'))), "|")
            
def getbinsmain():
    form = cgi.FieldStorage()
    mxktelnet, prompt = TelnetLoginandGetPrompt(form.getvalue('IP'))
    mxktelnet.write(b"dir\r")
    dirarray = (mxktelnet.read_until(prompt).decode('ascii')).split()
    chassistype = DetermineChassisType(mxktelnet, prompt)
    print(chassistype, "|")
    PrintBins(dirarray, form, chassistype)
    mxktelnet.close()

if(__name__ == "__main__"):
    getbinsmain()
