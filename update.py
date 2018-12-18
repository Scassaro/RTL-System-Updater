#!/usr/bin/python3
# This line tells the CGI loader that this is a python script.

# Project: RTL Image Downloader
# Author: Stephen Cassaro
# Company: Dasan Zhone Solutions
# Description: This python program facilitates the downloading of files to a MX/MXK system for the RTLAutomation website.

# Import libraries:
# cgi = Allows us to use this program as a CGI program (runs under an apache page).
# cgitb = Enables more detailed logging (debug mode below).
# telnetlib = Handles telnet connecting, reading, and writing.
# time = Lets us use time functions.
# os = Enables operating system commands. Likely not needed, will probably remove later.

import cgi, cgitb, telnetlib, time, os

# Turn on debug mode.
cgitb.enable()

# Print necessary headers and table starting pieces to output result page.
print("Content-Type: text/html")
print()
print("<head><title>MXK Update Results</title></head>")
print("<style>table, th, td {border-collapse: collapse;border:1px solid black}</style>")
print("<table style='width:100%>'")
print("<tr><th>File Download String</th><th>Result</th></tr>")

# Zhone uses weird capitalizations in filenames.
# This extracts filenames from the development server to use for ftp.
# binname = Zhone MX/MXK binary name.
# chassistype = Either MX or MXK.
# version = Software version we wish to upgrade to.
def CreateFolder(binname, chassistype, version, frostsymlink):
       # Telnet to Frost (server that holds the binaries).
       frosttelnet = telnetlib.Telnet("172.16.41.193")
       
       # Login to frost.
       frosttelnet.read_until(b"login:")
       frosttelnet.write(b"scassaro\n")
       frosttelnet.read_until(b"Password:")
       frosttelnet.write(b"Passw0rd\n")
       frosttelnet.read_until(b"-bash-3.00$")
       
       # Use the Unix "find" command to get the path to the binary.
       # dl/ is used in non-GA loads, gadl/ used otherwise.
       findfolder = "find " + frostsymlink + chassistype + "_" + version + " -name '" + binname + "'\n"
       frosttelnet.write(findfolder.encode('ascii'))
       
       # The find command above gives too much info.
       # Here I inefficiently slice the string down to just folder and binary name.
       # Example: find dl/MXK_2.5.2.324.2 -name "mxlc24t1e1bond.bin"
       # Outputs -> dl/MXK_2.5.2.324.2/mxLc24T1E1Bond/mxlc24t1e1bond.bin
       folder = str(frosttelnet.read_until(b"-bash-3.00$"))
       
       # dl/MXK_2.5.2.324.2/mxLc24T1E1Bond/mxlc24t1e1bond.bin -> MXK_2.5.2.324.2/mxLc24T1E1Bond/mxlc24t1e1bond.bin
       folder = folder[folder.find("/")+1:]
       
       # Return MXK_2.5.2.324.2/mxLc24T1E1Bond/mxlc24t1e1bond.bin sliced to mxLc24T1E1Bond/mxlc24t1e1bond.bin.
       # Also had to slice the prompt off of the end.
       return (folder[folder.find("/")+1:-16])

# Downloading binaries is difficult without knowing if the system we are upgrading is a 1U or otherwise.
# This function is a heavy handed way of determining which it is.
def DetermineChassisType(mxktelnet, prompt):
       
       # Get "slots" output from the system.
       mxktelnet.write(b"slots\n")

       # If the system is an MXK Classic or 219/F, "MXK" will always be at index [1] when the output is split into an array of strings using ".split()".
       rawslots = (mxktelnet.read_until(prompt).decode('ascii')).split()
       
       # Check if "MXK" appears at index [1] of rawslots,
       if(rawslots[1] == "MXK"):

              if rawslots[2] == "823" or rawslots[2] == "819" or rawslots[2] == "319":
              # and if so, return "MXK" for chassis type and "Classic" for generation, if the chassis is a MXK Classic,
                     return("MXK", "Classic")
              # or return "MXK" and "F" if it is an MXK-F,
              else:
                     return("MXK", "F")
       
       # otherwise its a 1U, return MX for chassis type and 1U for generation (not used currently).
       else:
              return("MX", "1U")

# Use telnetlib to login to the MX/MXK and determine if the system has a custom prompt.
def TelnetLoginandGetPrompt(mxkip):
       
       # Login to system.
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
       
       # Return the telnet object and prompt to use elsewhere.
       return mxktelnet, prompt

# This function handles a scenario where the user inputs their own binaries through the checkbox system.
def SelectBinsUpdate(binary, downloadstring, flashstring, generation):
       
       # Finish the download string.
       # No need for folder finding, the folder finding is done by the HTML.
       downloadstring += binary + " /card1/"
       
       # If the binary string has a slash in it (any .bin file, because the folder is included in the string),
       if(binary.find("/") > -1):
              
              # add everything after the "/" (the .bin file name ) to the download string,
              downloadstring += binary[(binary.find("/")+1):] + "\n"
              
       # otherwise, its a http.tar file.
       else:
              
              # and add the entire binary string to the download string.
              downloadstring += binary + "\n"
              
       # If the binary is a RAW file and the device is an MXK Classic,
       if(binary[-7:] == "raw.bin" and generation == "Classic"):
                     # create a flash string to be sent to the telnet object.
                     flashstring = "image flash /card1/" + binary[(binary.find("/")+1):] + " 1 all\n"
              
       # Return the flash string and download string to main.
       return flashstring, downloadstring

# This function hadles a standard update, where all binaries in "dir" are updated.
def StandardUpdate(binary, downloadstring, version, chassistype, flashstring, generation, frostsymlink):
       
       # If the file has ".tar" in its name, and is not a tar which might be a backup,
       if(binary[-4:] == ".tar"):
              
              # add the entire binary string to the download string.
              downloadstring += binary + " /card1/" + binary + "\n\r"
              
       # If the file has ".bin" in its name, and is not a bin which might be a backup,
       if(binary[-4:] == ".bin" and binary[-7:] != "rom.bin" and binary[-5:] != "_.bin"):
              
              # complete the download string by calling CompleteFolder to get folder path and adding the binary name and Zhone system syntax.
              downloadstring += CreateFolder(binary, chassistype, version, frostsymlink) + " /card1/" + binary + "\n\r"
              
              # If the binary is a RAW file and the device is an MXK Classic,
              if(binary[-7:] == "raw.bin" and generation == "Classic"):
                            # create a flash string to be sent to the telnet object.
                            flashstring = "image flash /card1/" + binary + " 1 all\r"
                     
       # Return the flash string and download string to main.
       return flashstring, downloadstring

# Flash a raw file (if needed), reboot the system (if needed), and close the telnet connection.
def FlashRebootandClose(flashstring, mxktelnet, prompt, form):
       
       # If the flash string exists,
       if(flashstring != ""):
              
              # write flash string to the telnet object,
              mxktelnet.write(flashstring.encode('ascii'))

              # go through Zhone validation,
              mxktelnet.read_until(b"Continue? (yes or no) [no]")
              mxktelnet.write(b"yes\r")

              # and print it to the results page.
              print("<tr><td>" + flashstring + "</td>")

              # Analyze output from flash command.
              flashsuccess = (mxktelnet.read_until(prompt).decode('ascii')).split()

              # If the flashing worked,
              if(flashsuccess[len(flashsuccess)-2] == "successful"):

                     # print success,
                     print("<td style='color:green'>Success</td>")

              # otherwise,
              else:

                     # print failed.
                     print("<td style='color:red'>Failed</td>")
       
       # If the user indicated they would like to reboot,
       if(form.getvalue('reboot') == 'true'):
              
              # write the reboot command to telnet and go through the Zhone check.
              mxktelnet.write(b"systemreboot\r\n")
              mxktelnet.read_until(b"[no]")
              mxktelnet.write(b"yes\r\n")
              mxktelnet.read_until(b"[yes]")
              mxktelnet.write(b"no\r\n")
              mxktelnet.read_until(b"[no]")
              mxktelnet.write(b"yes\r\n")
              time.sleep(1)
              #mxktelnet.read_until(b"* * * * System Reboot * * * *")
              
       # Close the telnet connection.
       mxktelnet.close()
                     
def main():
       
       # Collect data contained in the URL (version, binary names, system IP).
       form = cgi.FieldStorage()

       # Blank flash string for returning if there isn't any RAW that needs flashing.
       flashstring = ""

       # Variable to store frost symlink string.
       # The frost symlink string is used in the frost release server to download files and determine folders for binaries.
       if(form.getvalue('GA') == "true"):
              frostsymlink = "gadl/"
       else:
              frostsymlink = "dl/"

       # Telnet to system, login, and create login string.
       mxktelnet, prompt = TelnetLoginandGetPrompt(form.getvalue('IP'))

       # If a list of binaries is in the URL,
       if("binFileList" in form):
              
              # store binaries in the URL to binList.
              dirarray = form.getvalue('binFileList')
              
       # Otherwise its a standard upgrade.
       else:
              
              # Write "dir" to the telnet,
              mxktelnet.write(b"dir\r\n")
              
              # extract the return value for use in parsing binary names.
              dirarray = (mxktelnet.read_until(prompt).decode('ascii')).split()
              
       # Run DetermineChassisType to figure out if its a 1U or MXK (nogen says to return just MX or MXK).
       chassistype, generation = DetermineChassisType(mxktelnet, prompt)

       # Iterate through the Array of binaries (or dir in the case of a standard upgrade),
       for i in range(len(dirarray)):
              
              # set binary to the current binary (or dir string) to process.
              binary = dirarray[i]
              
              # Create beginning part of the download string.
              downloadstring = "ftp user scassaro pass Passw0rd 172.16.41.193 get-bin " + frostsymlink + chassistype  + "_" + form.getvalue('version') + "/"
              
              # If user selected their own binaries, run SelectBinsUpdate,
              if("binFileList" in form):
                     flashstring, downloadstring = SelectBinsUpdate(binary, downloadstring, flashstring, generation)
                     
              # otherwise run StandardUpdate.
              else:
                     flashstring, downloadstring = StandardUpdate(binary, downloadstring, form.getvalue('version'), chassistype, flashstring, generation, frostsymlink)

              # Valid but not released binaries were causing issues, so I put this check to throw error messages.
              # If "directory" is found in the download string (means a "directory not found" error occurred),
              if(downloadstring.find("directory") > -1):

                     # split the download string into an array of strings,
                     splitdownloadstring = downloadstring.split()

                     # and print the error message.
                     print("<tr><td>No " + (splitdownloadstring[len(splitdownloadstring)-1])[7:] + " found for " + form.getvalue('version') + ".</td><td style='color:red'>Failed</td></tr>")

              # Essentially, if a standard update is chosen, there will be a "/" at the end of the downloadstring if the analyzed dir string is not a binary.
              # This "if" statement is meant to catch the not binary situation.
              if(downloadstring[len(downloadstring)-1] != "/"): # and downloadstring.find("directory") < 0):
                     
                     # Write the download string to the telnet if the dir string is a valid binary, or always write if bins were selected manually, separating into paragraphs.
                     mxktelnet.write(downloadstring.encode('ascii'))
                     print("<tr><td>")
                     print(downloadstring[:downloadstring.find("Passw0rd")] + "*******" + downloadstring[downloadstring.find("Passw0rd")+8:])
                     print("</td>")

                     # Turn results from the FTP download into to an array,
                     successorfail = (mxktelnet.read_until(prompt).decode('ascii')).split()

                     # and check to see if it failed.
                     if(successorfail[len(successorfail)-2] == "failed!"):

                        # If it failed, print failed,
                        print("<td style='color:red'>Failed</td>")
                     else:

                        # otherwise print success.
                        print("<td style='color:green'>Success</td>")
                     print("</tr>")
       # Flash raw if necessary, reboot if necessary, and close the telnet session.
       FlashRebootandClose(flashstring, mxktelnet, prompt, form)

       # End result table.
       print("</table>")
       
       return

if(__name__ == "__main__"):
       main()
