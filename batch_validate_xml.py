#!/usr/bin/env python3
"""Validate a folder of XML files filtered using a regular expression.

This script is specificaly created as a back-up validation tool for when a
specific type/standard of XML file in a batch of digitized material needs to be
validated with a XML schema or Schematron.
e.g. validating all `^.*_mets.xml$` files in a batch with `kbdg_boeken_mets.xsd`.

Run:
    $ python3 batch_validate_xml.py

Output:
    A 'logs' folder is created in the same location as this script is run. Here
    a csv file for each validation is generated.
    File naming convention: `./logs/validate_xml-{BATCH_NAME}-{DATE_TIME}.csv`

TODO:
    - Schematron.
    - Print stdout to GUI.

*** INFO
    Version: 1.0.0
    Date: 2020-03-27
    Author: Thomas Haighton
    Company: KB | National Library of the Netherlands
"""
import os
import re
import time
import csv
import tkinter as tk
from tkinter import filedialog

from lxml import etree


class GetFiles:
    """Locate files in `path_batch` that match `regex`.

        Arguments:
            path_batch (str): path to folder with XML files.
            regex (str): Regular expressions.

        Returns:
            list: List of file path strings.
        """
    def __init__(self, path_batch, regex=r'^.*\.xml$'):
        self.path_batch = path_batch
        self.regex = regex
        self.fname = tk.StringVar()
        self.files = []

    def get_files(self, path_batch, regex):
        if os.path.exists(path_batch):
            for dirpath, dirnames, filenames in os.walk(path_batch):
                try:
                    for filename in filenames:
                        self.fname.set(filename)
                        if re.search(regex, filename):
                            print(f'Looking for files: {filename}',
                              end='\r', flush=True)
                            self.files.append(os.path.join(dirpath, filename))
                except (re.error):
                    print('\n\nInvalid regular expression.\
                          \nSee https://docs.python.org/3/library/re.html for usage.')
                    break
        else:
            print(f'\n{path_batch} does not exist.')
        return(self.files)


def validate_xml(files, schemaf):
    """Validate located XML files with `schemaf`."""
    validation_errors = {}
    try:
        xsd = etree.XMLSchema(etree.parse(schemaf))
        for xmlfile in files:
            print(f'Validating {os.path.basename(xmlfile)} with \
                  {os.path.basename(schemaf)}',
                  end='\r', flush=True)
            valid = xsd.validate(etree.parse(xmlfile))
            if valid:
                state = 'valid'
            else:
                state = 'invalid'
            validation_errors[os.path.basename(xmlfile)] = [state, xsd.error_log]
    except(OSError):
        print(f'`{schemaf}` can not be loaded.')
    return(validation_errors)


def write_errors(validation_errors, path_batch, files):
    """Write validation errors to txt file."""
    if not os.path.exists('./logs'):
        os.mkdir('./logs')
    output_name = ('validate_xml-' + os.path.basename(path_batch) + '-' +
                   time.strftime("%Y%m%d_%H%M%S") + '.csv')
    output_file = os.path.join(r'./logs', output_name)
    print(f'\nWriting errors to {output_file}.')
    with open(output_file, 'w') as errorlog:
        csv_writer = csv.writer(errorlog, delimiter=',', quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(['filename', 'valid', 'error'])
        if len(validation_errors) > 0:
            for obj_id, error in validation_errors.items():
                csv_writer.writerow([obj_id, error[0], str(error[1])])
    errorlog.close()


class MainApplication(tk.Frame):
    """GUI ROW 0: Main GUI class.

    Widgets:
        `[button QUIT]   [button VALIDATE]`
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.bt_quit = tk.Button(parent,
                                 text='QUIT',
                                 fg='red',
                                 command=parent.quit).grid(row=0,
                                                           column=0,
                                                           sticky='w')
        self.bt_validate = tk.Button(parent,
                                     text='VALIDATE',
                                     fg='blue',
                                     command=self.validate).grid(row=0,
                                                                 column=1,
                                                                 sticky='e')
        # BatchFrame.
        self.batchframe = BatchFrame(parent)
        self.batchframe.grid(row=1)

        # Filter rows.
        self.createrow = CreateRow(parent, self.batchframe.var)
        self.createrow.grid(row=2)

        self.getfilesclass = GetFiles(self.batchframe.var.get(),
                                      self.createrow.re1.get())

        # TODO: LABEL show progress not working yet?
        self.printtext = tk.StringVar()
        self.guiprint = tk.Label(parent, textvariable=self.printtext).grid(row=4, column=1, sticky='w', padx=10, pady=10)

    # START VALIDATION PROCESS.
    def validate(self):
        self.printtext.set('Searching for files')
        self.getfiles = self.getfilesclass.get_files(self.batchframe.var.get(),
                                                     self.createrow.re1.get())

        # Call Validate files function
        self.printtext.set('Validating files')
        validation_errors = validate_xml(self.getfilesclass.files,
                                         self.createrow.sch_loc.get())

        # Call Write log file function.
        self.printtext.set('Writing log file.')
        write_errors(validation_errors,
                     self.batchframe.var.get(),
                     self.getfilesclass.files)
        self.printtext.set('DONE!')

        print('\nDONE!')


class BatchFrame(tk.Frame):
    """GUI ROW 1: Choose parent folder of XML files to validate.

    Widgets:
        `XML Folder [entry ./batch][button browse folder]`
    """
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        # LABEL: text 'XML folder'.
        tk.Label(parent,
                 text='XML folder',
                 font='Arial 11 bold').grid(row=1, column=0)

        # ENTRY: Text field path batch.
        self.var = tk.StringVar()
        self.xml_folder = tk.Entry(root,
                                   textvariable=self.var,
                                   width=40).grid(row=1, column=1, pady=10)

        # BUTTON: Browse for XML folder.
        self.patch_batch = tk.Button(parent,
                                     text='Choose Folder',
                                     command=self.get_path_batch,)
        self.patch_batch.grid(row=1, column=2, sticky='w')

    # filedialog path_batch.
    def get_path_batch(self):
        dir_name = filedialog.askdirectory(initialdir='.',
                                           title='Select XML folder')
        if dir_name:
            self.var.set(dir_name)


class CreateRow(tk.Frame):
    """GUI ROW 2: Widgets for adding regex with schema's.

    Widgets:
        `Regex [entry regex] Schema [entry ./schema.xsd][button browse xsd]`
    """
    def __init__(self, parent, dirname):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        # LABEL: 'Regex' label text
        tk.Label(parent,
                 text='Regex',
                 font='Arial 11 bold').grid(row=2,
                                            column=0,
                                            sticky='w')

        # ENTRY: Regular Expression / Filter box.
        v = tk.StringVar(value=r'^.*\.xml$')
        self.re1 = tk.Entry(parent, width=40, textvariable=v)
        self.re1.grid(row=2, column=1, sticky='w')

        # LABEL: 'Schema' label text.
        tk.Label(parent,
                 text='Schema',
                 font='Arial 11 bold').grid(row=3, column=0, sticky='w')

        # ENTRY: Schema location.
        self.sch_loc = tk.StringVar()
        self.sch_loc_entry = tk.Entry(parent,
                                      textvariable=self.sch_loc,
                                      width=40).grid(row=3,
                                                     column=1,
                                                     sticky='w')

        # BUTTON: Browse for schema file.
        self.path_schema = tk.Button(parent,
                                     text='Choose File',
                                     command=self.get_path_schema)
        self.path_schema.grid(row=3, column=2, sticky='w')

    # filedialog xsd sch schemas.
    def get_path_schema(self):
        sch_file = filedialog.askopenfilename(initialdir='.',
                                              title='Select schema',
                                              filetypes=[('Schema files',
                                                          '.xsd .sch')])
        if sch_file:
            self.sch_loc.set(sch_file)


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('548x168')
    root.title('Batch Validate XML v1.0.0')
    app = MainApplication(root)
    root.mainloop()
