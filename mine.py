import os, sys, sqlite3, datetime, time, re, textract, csv
from sys import argv

# Options ---------------------------------------------------------------------
extract_text = 1
skip_types = ['CSS','JS', 'DS_STORE', 'DB'] #Always use uppercase here

# Database Operations ---------------------------------------------------------
conn = sqlite3.connect('extract.db')
c = conn.cursor()

#Check if table exists, if not then create
def prep_db():
	#Files Table
	tb_files = "SELECT name FROM sqlite_master WHERE type='table' AND name='files'"
	if not c.execute(tb_files).fetchone():
		print 'Creating database table: FILES'
		c.execute('''CREATE TABLE files(
		file_path text, file_name text, file_type text, file_size integer, date_modified date,
		date_created date, owner text, errors text, transcribed integer, content text, date_scanned date)
		''')
	else:
		print 'FILES table already exists, appending...'
	#Scans Table
	tb_scans = "SELECT name FROM sqlite_master WHERE type='table' AND name='scans'"
	if not c.execute(tb_scans).fetchone():
		print 'Creating database table: SCANS'
		c.execute('''CREATE TABLE scans(
		scan_start date, scan_duration text, folder text, total_files integer, new_files integer, new_extractions integer)
		''')
	else:
		print 'SCANS table already exists, appending...'

#See which records already exist so they can be skipped
def load_records():
	conn.text_factory = str
	c.execute("SELECT file_path FROM files")
	existing_records = [r[0] for r in c.fetchall()]
	return existing_records

#Write results to a new row in the DB
def write_db(file):
	items = [file['filepath'],file['filename'],file['filetype'],file['filesize'],file['datemod'],file['datecreate'],
		file['owner'],file['errors'],file['transcribed'], file['text_content'], file['date_scanned']]
	c.execute("INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?,?,?)", items)
	conn.commit()

#Append a log of the scan to the Scans table
def write_scans():
	scan = {
		'scan_start': startTime.replace(microsecond=0),
		'scan_duration': str(datetime.datetime.now().replace(microsecond=0)-startTime),
		'folder': folder,
		'total_files': len(files),
		'new_files': len(files)-len(skipped),
		'new_extractions': len(extractions),
		} 
	scan_stats = [scan['scan_start'],scan['scan_duration'],scan['folder'],
					scan['total_files'],scan['new_files'],scan['new_extractions']]
	c.execute("INSERT INTO scans VALUES(?,?,?,?,?,?)", scan_stats)
	conn.commit()

	print 'Done!'
	print 'Time to complete: %s' % scan['scan_duration']
	print '%i Files Scanned' % scan['total_files']
	print '%i New since last scan (%i skipped).' % (scan['new_files'],len(skipped))
	print '%i Successful new text extractions' % scan['new_extractions']

#Export file metadata to CSV (For BI analysis, etc)
def write_csv(csvfile):
	print 'Generating %s...' % (csvfile)
	#Write CSV Headers
	writer = csv.writer(open(csvfile, 'wb'))
	header_row = ['File_Path','File_Name','File_Type','File_Size',
					'Date_Modified','Date_Created','Owner','Transcribed','Date Scanned']
	writer.writerow(header_row)

	#Export from DB to CSV
	conn.text_factory = str
	c.execute("SELECT file_path, file_name, file_type, file_size, date_modified, date_created, owner, transcribed, date_scanned FROM files")
	for file in c.fetchall():
		writer.writerow(file)

# Scan Files ------------------------------------------------------------------
files = []
skipped = []
extractions = []
startTime = datetime.datetime.now()
def find_files(folder):
	print 'Scanning for new files...'
	for root, dirnames, filenames in os.walk(folder):
		for filename in filenames:
			filepath = os.path.join(root, filename).decode(sys.stdin.encoding)
			filetype = os.path.splitext(filepath)[1].replace(".", "").upper()

			files.append({'file':filepath})

			if filepath.encode(sys.stdin.encoding) in existing_records:
				skipped.append({'file':filepath})
			else:
				print ('-'*20+'\n%i) %s\n'+'-'*20) % (len(files), os.path.basename(filename))
				error = ''
				text_extract = ''
				transcribed = 0
				if extract_text == 1: #Extract Text
					if filetype in skip_types:
						error += "Skipping %s. " % filetype
					else:
						try:
							extracted = textract.process(filepath)
							print 'Transcription SUCCESS'
							try:
								text_extract = extracted #.encode('utf-8', 'ignore')
								transcribed = 1
								extractions.append({'file':filepath})
							except:
								error += 'Unicode encoding error. '
								pass
						except:
							print 'Transcription FAILED'
							pass

				try: #Get File Details
					(mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(filepath)
				except:
					mtime = 0
					ctime = 0
					size = 0
					error += "Filestats error. "
					pass

				#Get Owner information
				if os.name == 'nt': #If Windows
					try:
						sd = win32security.GetFileSecurity(filepath, win32security.OWNER_SECURITY_INFORMATION)
						owner_sid = sd.GetSecurityDescriptorOwner()
						user_name, domain, type = win32security.LookupAccountSid(None, owner_sid)
					except:
						error += "Owner error. "
						user_name = ""
						pass
				else: #If not Windows
					try:
						user_name = getpwuid(stat(filepath).st_uid).pw_name
					except:
						error += "Owner error. "
						user_name = ""
						pass

				file = {
				'filepath': filepath,
				'filename': filename.decode(sys.stdin.encoding),
				'filetype': filetype,
				'filesize': size,
				'datemod': datetime.datetime.fromtimestamp(mtime),
				'datecreate': datetime.datetime.fromtimestamp(ctime),
				'owner': user_name.encode('utf-8', 'ignore'),
				'errors': error,
				'transcribed': transcribed,
				'text_content': text_extract,
				'date_scanned': datetime.datetime.now().replace(microsecond=0)
				}

				print error
				write_db(file)
	print '------------------------------------'

# Run the script---------------------------------------------------------------

# Check OS version
if os.name == 'nt':
	import win32api, win32con, win32security # To get file owner
	os.system('cls')
else:
	from os import stat
	from pwd import getpwuid
	os.system('clear')

if len(argv) == 1:
	#Create a CSV export of the data
	now = datetime.datetime.now()
	csvout = "Extract_%s.csv" % now.strftime("%Y-%m-%d_%H%M")
	print 'No folder specified, exporting database to CSV as %s...' % csvout
	write_csv(csvout)
	print 'Done! If you want to traverse a folder, please specify one as the first argument.'
else:
	#Traverse folder & update DB
	filename, folder = argv #Set folder to specified in CLI
	prep_db()
	existing_records = load_records()
	find_files(folder)
	write_scans()
	conn.close() 