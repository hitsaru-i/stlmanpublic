from flask import Blueprint, render_template, request, redirect, abort, send_file, url_for, current_app
import ast
import os
import sqlite3
import subprocess
import threading

bp = Blueprint('main', __name__)

# --- Thread-safe Database Helpers ---
def get_project_by_name(project_name):
	with sqlite3.connect('./database/stlman.sqlite', timeout=10) as conn:
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM stldata WHERE Project = ?", (project_name,))
		return cursor.fetchone()

def get_all_projects():
	with sqlite3.connect('./database/stlman.sqlite', timeout=10) as conn:
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM stldata")
		return cursor.fetchall()

def get_projects_paginated(offset, limit):
	with sqlite3.connect('./database/stlman.sqlite', timeout=10) as conn:
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM stldata LIMIT ? OFFSET ?", (limit, offset))
		return cursor.fetchall()

def get_total_project_count():
	with sqlite3.connect('./database/stlman.sqlite', timeout=10) as conn:
		cursor = conn.cursor()
		cursor.execute("SELECT COUNT(*) FROM stldata")
		return cursor.fetchone()[0]

def get_history_by_project_id(rowid):
	with sqlite3.connect('./database/stlman.sqlite', timeout=10) as conn:
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM history WHERE ProjectId = ?", (rowid,))
		return cursor.fetchall()

# --- Routes ---

@bp.route('/')
@bp.route('/index')
def index():
	return render_template('index.html', title="INDEX", page="INDEX")

@bp.route('/longlist')
def longlist():
	alldata = get_all_projects()
	return render_template('longlist.html', title="LONGPAGE", page="LONGPAGE", alldata=alldata)

@bp.route('/paginate')
@bp.route('/paginate/<int:page>')
def paginate(page=1):
	per_page = 15
	total_projects = get_total_project_count()
	total_pages = (total_projects // per_page) + (1 if total_projects % per_page > 0 else 0)

	if page < 1 or page > total_pages:
		page = 1

	offset = (page - 1) * per_page
	paginated_data = get_projects_paginated(offset, per_page)

	return render_template('paginate.html', title="PAGINATE", page="PAGINATE", data=paginated_data, currentpage=page, pages=total_pages)

@bp.route('/filepage/<file>')
def filepage2(file):
	project = get_project_by_name(file)

	if not project:
		return "Project not found", 404

	rowid    = project['row_id']
	filepath = project['RootDir']
	filesdir = project['FilesDir']
	imgpath  = project['ImgDir']
	images   = ast.literal_eval(project['ImgList'])
	files    = ast.literal_eval(project['FilesList'])

	return render_template('filepage.html',
		title="Details Page",
		page="File Details",
		rowid=rowid,
		file=file,
		filedata=dict(project),
		filepath=filepath,
		imgpath=imgpath,
		imglist=images,
		filesdir=filesdir,
		filelist=files)

@bp.route('/history/<rowid>')
def history(rowid):
	historydata = get_history_by_project_id(rowid)
	return render_template('history.html', rowid=rowid, historydata=historydata)

@bp.route('/updatehistory/<rowid>')
def updatehistory(rowid):
	return render_template('updatehistory.html', rowid=rowid)

@bp.route('/updateaction/', methods=["POST"])
def updateaction():
	rowid         = request.values['rowid']
	date          = request.values['Date']
	infillpercent = request.values['InfillPercent']
	infillpattern = request.values['InfillPattern']
	plastictype   = request.values['PlasticType']
	assessment    = request.values['Assessment']
	note          = request.values['Note']

	submitlist = [rowid, date, infillpercent, infillpattern, plastictype, assessment, note]

	with sqlite3.connect('./database/stlman.sqlite') as conn:
		cursor = conn.cursor()
		cursor.execute("""
			INSERT INTO history(ProjectId, Date, InfillPercent, InfillPattern, PlasticType, Assessment, Note)
			VALUES (?, ?, ?, ?, ?, ?, ?)
		""", submitlist)
		conn.commit()
	return redirect(url_for('main.history', rowid=rowid))


@bp.route('/image/<path:project>/<filename>')
def serve_image(project, filename):
	try:
		project_data = get_project_by_name(project)
		if not project_data:
			return abort(404)

		img_dir = project_data['ImgDir']
		full_path = os.path.join(img_dir, filename)

		if not os.path.exists(full_path):
			return abort(404)

		return send_file(full_path)

	except Exception as e:
		print(f"Error serving image: {e}")
		return abort(500)

@bp.route('/search', methods=["POST"])
def search():
	searchphrase = request.form.get('searchphrase', '').strip()

	if not searchphrase:
		return render_template("longlist.html", title="Search", page="Search Results", alldata=[])

	keywords = searchphrase.lower().split()
	sql_query = "SELECT * FROM stldata WHERE " + " AND ".join(["LOWER(Project) LIKE ?"] * len(keywords))
	params = [f"%{kw.replace(' ', '_')}%" for kw in keywords]

	with sqlite3.connect('./database/stlman.sqlite') as conn:
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute(sql_query, params)
		alldata = cursor.fetchall()

	return render_template("longlist.html", title="Search Results", page="Search Results", alldata=alldata)

@bp.route('/searchform')
def searchform():
	return render_template('search.html')

@bp.route('/statuspage')
def statuspage():
	statusmessage = request.args.get('msg', 'No message provided')
	return render_template('statuspage.html', title="Status Page", page="Status Page", statusmessage=statusmessage)

# --- Global Lock for Updatedb ---
updatedb_lock = threading.Lock()
updatedb_running = False

@bp.route('/updatedb')
def updatedb():
	global updatedb_running

	def run_thread():
		run_updatedb()

	with updatedb_lock:
		if updatedb_running:
			status = "Database update is already running..."
			return render_template("statuspage.html", statusmessage=status)
		updatedb_running = True

	thread = threading.Thread(target=run_thread)
	thread.start()

	status = "Database update has started. This may take quite some time depending on the size of your library..."
	return render_template('statuspage.html', statusmessage=status)

def run_updatedb():
	global updatedb_running
	try:
		process = subprocess.Popen(
			['python3', './scripts/init_db.py'],
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)
		output, error = process.communicate(input='y\n', timeout=300)

		if process.returncode == 0:
			msg = "Database update running successfully. Results may take time. Performance may be impacted during this time."
		else:
			msg = f"Script returned error code {process.returncode}: {error}"

		print(msg)

	except subprocess.TimeoutExpired:
		print("Timeout during database update script initialization.")

	except Exception as e:
		print(f"Exception in update: {e}")

	finally:
		updatedb_running = False

@bp.route('/runcura', methods=["POST"])
def runcura():
	filepath = request.form.get("filepath", "").strip()

	if not filepath.endswith(".stl") or not os.path.isfile(filepath):
		print("Invalid or missing STL file path.")
		statusmessage = f"Invalid STL file path: {filepath}"
		return redirect(url_for('main.statuspage', msg=statusmessage))

	try:
		print(f"Launching Cura with: {filepath}")
		subprocess.Popen(["cura", filepath])
		statusmessage = f"Cura launched with {filepath}"
		return redirect(url_for('main.statuspage', msg=statusmessage))
	except Exception as e:
		print(f"Error launching Cura: {e}")
		statusmessage = f"Error launching Cura: {e}"
		return redirect(url_for('main.statuspage', msg=statusmessage))

