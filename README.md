STLMan (STL Manager)

This project is created and distributed under the CC BY-NC-SA License.
A copy of this license is included in this repo.

Developers:
2023 Ian Hill,
2025 Ian and Connie Hill
2025 ChatGPT

special thanks to ChatGPT and the OpenAI team
for helping me refactor my old code and giving me the will
to finish and publish this project.
(Hey, folks, attribution is important: give credit where credit is due.
like all machines, LLMs can be really useful, WHEN THEY WORK)

STL Manager is a self serving web application intended to facilitate easy viewing, record
keeping, and use of STL files for 3D printing. The applicaiton is intended to
run on a Linux based workstation connected to a 3D printer.

The application is a Python Flask web application that serves and references STL
files from a specified network share. The application allows the user to browse
and search for STL file projects, see the associate files, displays the images
associated with the files, and allows users to call specific stl files directly
to Ultimaker Cura slicer from the web browser on the local machine. The functionality
also includes a history log so that users can record print attempts and critical
settings used.

IMPORTANT:
The file format and extracted zip structure is EXPECTED to be that of THINGIVERSE
zip file formats at time of writing. Raw, unassociated stls or zip files without
all of the required elements will not be extracted or recorded into the STLMan database.



Workflow:
Clone this repo:

git clone WHEREEVERTHISENDSUP/stlman.git

Create your network share and folders:
This application assumes the use of a network share. Ensure that the share is created
and that the host system serving STLMan has access to the share. Two directories in
the fileshare are necessary:
RAWZIPS - a location for all of your raw zip files
UNZIPPED - destination location for extracted files

Create both directories on your share and populate your RAWZIPS directory
with your THINGIVERSE zip file downloads.

Designate your network share and mount point:
edit the mount.conf file to set the root of your MOUNT_POINT and SHARE to designate
the location of the network share.

If the network share is accessed with a 'guest' user, no further configuration
is needed with the network share. If the network share requires a specialized
username and password, please note that the ./depoy and ./run.sh scripts will
ask for a username and password. 

Deploy:

./deploy.sh

(check requirements.txt for requirement versions. This information will
necessarily change in the future and must be updated accordingly)

On first run the script will offer to run the 1B-extractor.py file. This script will
extract all zip files from the RAWZIPS directory on your mounted file share
to the UNZIPPED directory. Each time you add new files to your RAWZIPS directory, you
will need to extract them using the 1B-extractor.py script. Extraction can take quite
some time depending on how many files you are extracting.

If running the first time, the script will ask if you wish to make a database.
Enter 'y' and enter and the deploy script will generate a sqlite database
mapping the files and file routes of the files for reference in the application. This
should be done after you have extracted all files.

Run STLMan:

./run.sh

Use:

Direct your browser to 127.0.0.1:5000

Note: You can change the settings for the Flask application in run.sh.
You may wish to set a different port or change the server to production.

