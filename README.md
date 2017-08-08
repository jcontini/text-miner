# Text Miner

This script extracts text from PDFs, Office documents, images, and many other types of files including audio (mp3, wav) with speech-to-text. Extracted file text and metadata are saved as a rows in a single SQLite database, and file metadata can be extracted to CSV for analysis.

## What it does

- Traverses every file in specified directory, including subfolders
- Records file path, type (extension), size, modified/created dates
- Records file owner (who put the file there– useful for shared drives)
- Where possible, extracts text from document with textract
- Records datestamp of when file was scanned
- Saves all data to local SQLite database (extract.db)
- If interrupted & run again, picks up where it left off, scanning files only once
- To start fresh, just delete the generated extract.db & run script again

## Installing
1. Clone the repository to your computer.
2. run ```pip install -r requirements.txt```
3. To enable OCR, speech-to-text, and better support for other filetypes, install additional packages with these commands:
    1. ```brew cask install xquartz```
    2. ```brew install poppler antiword unrtf tesseract sox```
    3. ```pip install https://github.com/mattgwwalker/msg-extractor/zipball/master```

Text extraction relies heavily on [textract](https://github.com/deanmalmgren/textract) and the libraries beneath it. If you are having trouble extracting text from certain file types, be sure to install the libraries listed in the [textract documentation](https://textract.readthedocs.io/en/stable/).

## How to Use

### Extracting text from files in a folder

To traverse a folder (and subfolders) & extracting text from files, just run:
    ```python mine.py /path/to/folder```

- You should see output of scanning progress, and a ```extract.db``` file should appear immediately in the same directory. This is a SQLite database that you can open with the open source [DB Browser for SQLite](http://sqlitebrowser.org/).
- You can open the file anytime while the script is running to see what is being collected. It won't interrupt the script unless you write a new change to the file.
- If a file is taking a long time and you want to skip it, just press ctrl-c once and it should jump to the next file.
- If the script is interrupted for any reason, it will continue where it left off, so it's OK if you need to cancel.

## Exporting Metadata to CSV

Once you've run the script and have an ```extract.db``` file generated, you can export the file metadata to a CSV by simply running the script without a folder argument:
    ```python mine.py```

This will create a CSV with the following fields:

- File path
- File name
- File type (extension)
- File size
- Date modified
- Date created
- Owner (who put the file there; useful when scanning network drives)
- Transcription Status (1 = success, 0 = failed/skipped)
- Date scanned

# Future Plans

I'd love to create a GUI for this so folks can configure settings without having to edit the script. I was thinking of creating a Flask web app or a simple GUI with Tkinter or similar. If you make any improvements, please submit a pull request!

If building a web app, I'd think about adding tools to download and mine the content of entire websites or RSS feeds.
