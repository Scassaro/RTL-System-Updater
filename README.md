# RTL-System-Updater
This is the RTL System Updater for updating the software on a Dasan Zhone Solutions rack device. This program consists of four parts:

1. landingpage.html - This is an extremely simple HTML page that serves as the intermediate between the original RTL Automation page and my Apache automation site. This will eventually be replace with its own internal domain.

2. updater.html - This web page handles the input from the test engineer and builds interfaces to facilitate the type of update the engineer would like to do. Has some jQuery and Javascript elements to handle inputs and pass data to the CGI Python scripts.

3. getbins.py - This CGI program goes into the MXK to gather data for the Select Binaries update option. It also builds the HTML needed to display the table of checkboxes allowing an engineer to select binaries to add or remove from the update process. Borrows some functions created for update.py.

4. update.py - This CGI program is the backbone of the updater. It facilitates interactions with the development software release server and the system the engineer wants to update. It builds the HTML for the results page as well. 
