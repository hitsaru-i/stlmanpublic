#!/usr/bin/env python3
import os
import sqlite3
from config import EXTRACTED_LOCATION

# Path to the SQLite database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sqlitedbname = os.path.join(BASE_DIR, "../database/stlman.sqlite")


def createdb():
	try:
		conn = sqlite3.connect(sqlitedbname)
		cursor = conn.cursor()

		# Create stldata table
		cursor.execute("""
		CREATE TABLE IF NOT EXISTS stldata (
			row_id INTEGER PRIMARY KEY AUTOINCREMENT,
			Project TEXT,
			RootDir TEXT,
			Basefiles TEXT,
			ImgDir TEXT,
			FilesDir TEXT,
			ImgList TEXT,
			FilesList TEXT
		)""")
		conn.commit()

		# Create history table
		cursor.execute("""
		CREATE TABLE IF NOT EXISTS history (
			row_id INTEGER PRIMARY KEY AUTOINCREMENT,
			ProjectId TEXT,
			Date TEXT,
			InfillPercent TEXT,
			InfillPattern TEXT,
			PlasticType TEXT,
			Assessment TEXT,
			Note TEXT
		)""")
		conn.commit()

	except Exception as e:
		print(f"Error creating database: {e}")

def insertdb(insertlist):
	print("[---DB WRITE---]")
	try:
		conn = sqlite3.connect(sqlitedbname)
		cursor = conn.cursor()
		cursor.execute("""
		INSERT INTO stldata (
			Project,
			RootDir,
			Basefiles,
			ImgDir,
			FilesDir,
			ImgList,
			FilesList
		) VALUES (?, ?, ?, ?, ?, ?, ?)""", insertlist)
		conn.commit()
	except Exception as e:
		print(f"Error inserting into database: {e}")

def opendb():
	global conn
	global cursor
	conn = sqlite3.connect(sqlitedbname)
	cursor = conn.cursor()

def closedb():
	conn.commit()
	conn.close()

def checkdb(projecttitle):
	global projectcheck
	opendb()
	cursor.execute("SELECT * FROM stldata WHERE Project = ?", (projecttitle,))
	projectcheck = cursor.fetchall()
	closedb()

# --- Main process ---

makeDBcmd = input("Make new database? (y/n): ")
if makeDBcmd.lower() == 'y':
	print("..Making DB..")
	createdb()
elif makeDBcmd.lower() == 'n':
	print("..Skipping DB creation")
else:
	print("Invalid input. Exiting.")
	exit(0)

# Perform directory scan
extractedlocation = EXTRACTED_LOCATION
extracted = os.walk(extractedlocation)
it = iter(extracted)
next(it, None)  # skip root dir

for folderName, subfolders, filenames in it:
	insertlist = []
	fileslist = []
	imglist = []
	currentfolder = folderName

	if 'images' in currentfolder or 'files' in currentfolder:
		continue

	project = os.path.basename(currentfolder).replace(" ", "_")
	insertlist.append(project)               # Project
	insertlist.append(currentfolder)         # RootDir (absolute)
	insertlist.append(str(filenames))        # Basefiles

	files_dir = ''
	images_dir = ''

	# Scan for files/images subfolders
	for subfolder in subfolders:
		subwalkloc = os.path.join(currentfolder, subfolder)

		if 'files' in subfolder:
			files_dir = subwalkloc
		if 'images' in subfolder:
			images_dir = subwalkloc

		for _, _, subfilenames in os.walk(subwalkloc):
			for file in subfilenames:
				if 'images' in subfolder:
					imglist.append(file)
				elif 'files' in subfolder:
					fileslist.append(file)

	# Append absolute subfolder paths
	insertlist.append(images_dir)      # ImgDir (absolute)
	insertlist.append(files_dir)      # FilesDir (absolute)

	# Append file lists
	insertlist.append(str(imglist))
	insertlist.append(str(fileslist))

	# Check DB for existing entry
	projecttitle = insertlist[0]
	checkdb(projecttitle)
	if not projectcheck:
		print(f"[+] Inserting project: {projecttitle}")
		insertdb(insertlist)
	else:
		print(f"[=] Project exists: {projecttitle}, skipping.")

