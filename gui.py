# -*- coding: utf-8 -*-

# Copyright or © or Copr. Thomas Duchesne <thomas@duchesne.io>, 2014-2015
# 
# This software was funded by the Van Allen Foundation <http://fondation-va.fr>.
# 
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use, 
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info". 
# 
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability. 
# 
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security. 
# 
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

"""Manages the graphical user interface.

The Application class generates the program's widgets that interact width the
tle module (toselect the satellite, the output file, the input files, and to
give access to the user manual).

The start() function construct the window border giving its size and draws the
widgets in it, then starts the window.
"""

from tkinter import *
from tkinter.messagebox import showwarning, showinfo, showerror, askyesno
from tkinter.filedialog import askopenfilename, askopenfilenames, asksaveasfilename
from tkinter.font import Font
from tkinter.ttk import Treeview, Progressbar
import webbrowser
import logging
import datetime
import threading
import time
import re
import copy

import log
import tle

logger = logging.getLogger("root")

class Application(Frame):
    """Construction of the window's widgets.
    
    This class defines the graphical user interface of STOPE and the actions
    associated with the widgets, e. g. asking for files, start the extraction or
    displaying the user manual.
    
    ..note:: :class:`Application` objets do not start the window itself.
    ..seealso:: :func:`start`
    """
    
    def __init__(self, master):
        Frame.__init__(self, master)
        
        self.master = master
        
        # Building the menu bar.
        self.menubar = Menu(self)
        file_menu = Menu(self.menubar, tearoff=0)
        help_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New extraction", command=self.clear_interface)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=master.destroy)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User manual", command=self.show_help)
        help_menu.add_command(label="About STOPE", command=self.show_about_dialog)
        master.config(menu=self.menubar)
        
        # Building the extraction setup (cospar + output file) frame.
        self.setup_frame = Frame(self)
        self.extraction_mode = StringVar()
        self.cospar_designator = StringVar()
        self.cospar_radiobutton = Radiobutton(self.setup_frame, text="International designator", variable=self.extraction_mode, value="one", command=self.update_mode_selection)
        self.full_extract_radiobutton = Radiobutton(self.setup_frame, text="Full extraction", variable=self.extraction_mode, value="all", command=self.update_mode_selection)
        self.cospar_radiobutton.select() # By default, the program extracts data for one satellite.
        self.full_extract_radiobutton.deselect()
        self.cospar_label = Label(self.setup_frame, text="International designator")
        self.cospar_entry = Entry(self.setup_frame, textvariable=self.cospar_designator)
        self.output_file_label = Label(self.setup_frame, text="Output file")
        self.output_file_name = StringVar()
        self.output_file_entry = Entry(self.setup_frame, state="readonly", textvariable=self.output_file_name)
        self.output_file_button = Button(self.setup_frame, text="Select file", command=self.select_output_file)
        
        # Building the tooblox for the list of input files.
        self.list_of_files_toolframe = Frame(self)
        self.add_files_button = Button(self.list_of_files_toolframe, text="Add files", command=self.add_files)
        self.delete_selected_files_button = Button(self.list_of_files_toolframe, text="Delete selected files", command=self.delete_selected_files) 
        self.files_counter_text = StringVar()
        self.files_counter_label = Label(self.list_of_files_toolframe, textvariable=self.files_counter_text)
        
        # Building the list of input files.
        self.list_of_files_frame = Frame(self)
        self.list_of_files_scrollbar = Scrollbar(self.list_of_files_frame, orient=VERTICAL)
        self.list_of_files_listbox = Listbox(self.list_of_files_frame, selectmode="extended")
        self.list_of_files_listbox.config(yscrollcommand=self.list_of_files_scrollbar.set)
        self.list_of_files_scrollbar.config(command=self.list_of_files_listbox.yview)
        
        # Building the button that starts the extraction.
        self.run_button = Button(self, text="Run the extraction", command=self.run_extraction, height=2, bg="#FFCC66")
        
        # Positioning the widgets.
        # The widgets are expanded to fit the window size.
        self.pack(fill=BOTH, expand=1)
        
        self.setup_frame.pack(fill=X, padx=5, pady=5)
        self.cospar_radiobutton.grid(row=0, column=0, sticky=W, padx=(0,5), pady=(0,5))
        self.cospar_entry.grid(row=0, column=1, padx=(0,5))
        self.full_extract_radiobutton.grid(row=0, column=2, sticky=W)
        self.output_file_label.grid(row=1, column=0, sticky=W, padx=(0,5))
        self.output_file_entry.grid(row=1, column=1)
        self.output_file_button.grid(row=1, column=2, padx=(5,0), sticky=W)
        
        self.list_of_files_toolframe.pack(fill=X, padx=5, pady=(0,5))
        self.add_files_button.pack(fill=X, side=LEFT, padx=(0,5))
        self.delete_selected_files_button.pack(fill=X, side=LEFT)
        self.files_counter_label.pack(side=RIGHT)
        
        self.list_of_files_listbox.pack(side=LEFT,fill=BOTH, expand=1)
        self.list_of_files_scrollbar.pack(side=RIGHT, fill=Y)
        self.list_of_files_frame.pack(fill=BOTH, expand=1, padx=5, pady=5)
        
        self.run_button.pack(fill=BOTH, padx=5, pady=(0,5))
        
    def add_files(self):
        """Asks the user to select TLE files"""
        
        for filename in askopenfilenames(title="Select TLE files"):
            # Add the file only if not already present.
            if filename not in self.list_of_files_listbox.get(0, END):
                self.list_of_files_listbox.insert(END, filename)
                
        self.update_files_counter()
        
    def delete_selected_files(self):
        """
        Called when clicking on the 'Delete selected files' button.
        Does nothing when there is no selected files in the list box.
        """
            
        for index in self.list_of_files_listbox.curselection():
            self.list_of_files_listbox.delete(index)
            
        self.update_files_counter()
        
    def select_output_file(self):
        """Called when the 'Select files' button is clicked."""
        
        self.output_file_name.set(asksaveasfilename(title="Select the output file name", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]))
    
    def run_extraction(self):
        """
        Called when the 'Run the extraction' button is clicked.
        This functions runs the extraction using the tle module functions,
        measures the duration of the extraction and shows the user some warnings
        about what happened.
        """
        correct_input = True
        
        if self.extraction_mode.get() == "one":
            cospar = self.cospar_designator.get().strip().upper()
        else:
            cospar = None
        files = self.list_of_files_listbox.get(0, END)
        
        if self.extraction_mode.get() == "one":
            if cospar == "":
                correct_input = False
                showerror("Error", "You must specify an international designator.")
            elif not re.match("\d\d\d\d\d[A-Z]{1,3}", cospar, re.ASCII):
                correct_input = False
                showerror("Error", "The entered international designator is invalid.")
            
        if self.output_file_name.get() == "":
            correct_input = False
            showerror("Error", "You must specify an output file.")
        
        if len(files) == 0:
            correct_input = False
            showerror("Error", "You must specify at least one data file.")
            
        if correct_input:
            extration_start_time = datetime.datetime.now()
            
            extraction_success = tle.data_extract(cospar, files, self.output_file_name.get())
            
            extraction_duration = datetime.datetime.now() - extration_start_time
            
            days = extraction_duration.days
            hours = extraction_duration.seconds // 3600
            minutes = (extraction_duration.seconds // 60) - 60 * hours
            seconds = extraction_duration.seconds - 60 * minutes
            microseconds = extraction_duration.microseconds
            
            extraction_duration_str = ""
            
            if days != 0:
                extraction_duration_str += str(days) + " days "
            if hours != 0:
                extraction_duration_str += str(hours) + " h "
            if minutes != 0 or hours != 0:
                extraction_duration_str += str(minutes) + " min "
            
            extraction_duration_str += str(seconds)
            if microseconds != 0:
                extraction_duration_str += "." + str(microseconds)
                
            extraction_duration_str += " s"
            
            extraction_duration_str.strip()
            
            if extraction_success:
                showinfo("Extraction complete", "The data extraction of orbital parameters for was successful and lasted " + extraction_duration_str + ". You should check " + log.log_file_path + " before using the extracted data.")
            else:
                showwarning("No data extracted", "The extraction of the orbital parameters for couldn't be completed because unexpected events occured. Please check " + log.log_file_path + " to know more about this.")
                    
    def show_about_dialog(self):
        """Called when the About 'STOPE' menu is clicked."""
        
        # Building the modal fixed-size window.
        about_dialog = Toplevel(bg="#FFFFFF")
        about_dialog.title("About STOPE")
        about_dialog.resizable(width=FALSE, height=FALSE)
        
        about_dialog.grid() # Doesn't work without this.
        
        # Font definitions.
        title_font = Font(family="Times", size=36, weight="bold", slant="italic")
        description_font = Font(size=12, weight="bold")
        catchphrase_font = Font(size=12, slant="italic")
        notice_font = Font(size=10, slant="italic")
        
        # Building the widgets.
        program_title = Label(about_dialog, text="STOPE", font=title_font, bg="#336699", fg="#FFCC66")
        program_description = Message(about_dialog, text="Simple Tool for Orbital Parameters Extraction", width=300, font=description_font, justify="center", bg="#FFFFFF", fg="#003366")
        program_catchphrase = Label(about_dialog, text="Stop doing it manually with STOPE!", font=catchphrase_font,bg="#FFFFFF", fg="#336699")
        copyright_notice = Label(about_dialog, text="© 2014 Thomas Duchesne\nFunded by the Van Allen Foundation", bg="#FFFFFF", fg="#336699")
        license_notice = Label(about_dialog, text="Licensed under the terms of the\nCeCILL 2.1 license", bg="#FFFFFF", fg="#336699")
        program_version = Label(about_dialog, text="Version 1.0", fg="#003366", bg="#FFFFFF")
        close_button = Button(about_dialog, text="Close", command=about_dialog.destroy, width=10)
        
        # Positioning the widgets.
        program_title.pack(fill=X, padx=10, pady=10, ipadx=10, ipady=10)
        program_description.pack(padx=10, pady=(0,5))
        program_catchphrase.pack(padx=10, pady=(0,5))
        copyright_notice.pack(padx=10)
        license_notice.pack(padx=10)
        program_version.pack(side=LEFT, padx=10, pady=10)
        close_button.pack(side=RIGHT, padx=10, pady=10)
        
        # The about dialog box should be centered in the main window.
        main_window_posx = self.master.winfo_rootx()
        main_window_posy = self.master.winfo_rooty()
        main_window_width = self.master.winfo_width()
        main_window_height = self.master.winfo_height()
        about_dialog_width = self.master.winfo_width()
        about_dialog_height = self.master.winfo_height()
        
        about_dialog_posx = int(main_window_posx + (main_window_width - about_dialog_width) / 2)
        about_dialog_posy = int(main_window_posy + (main_window_height - about_dialog_height) / 2)
        
        about_dialog.geometry("+{x}+{y}".format(x=about_dialog_posx, y=about_dialog_posy))
        
        # Displaying the window.
        about_dialog.transient(self.master)
        about_dialog.grab_set()
        self.master.wait_window(about_dialog)
        
    def show_help(self):
        """Called when the 'User manual' menu is clicked."""
        
        webbrowser.open("doc/user_manual.html")
        
    def update_files_counter(self):
        """Called when input files are added."""
        
        counter = len(self.list_of_files_listbox.get(0, END))
        if counter == 0:
            self.files_counter_text.set("No files selected")
        elif counter == 1:
            self.files_counter_text.set("1 file selected")
        else:
            self.files_counter_text.set(str(counter) + " files selected")
            
    def update_mode_selection(self):
        """Called when radio buttons are manipulated."""
        
        if self.extraction_mode.get() == "one":
            self.cospar_entry.config(state=NORMAL)
        else:
            self.cospar_entry.config(state=DISABLED)
            
    def clear_interface(self):
        """Clears the interface.
        
        Empties the COSPAR text field, the output file text file and the list of
        input files.
        """
        
        self.cospar_radiobutton.select()
        self.cospar_entry.config(state=NORMAL)
        self.cospar_designator.set("")
        self.output_file_name.set("")
        self.list_of_files_listbox.delete(0, END)
        self.update_files_counter()
    
def start():
    """Main window initialisation before displaying it.
    
    ..seealso:: :class:`Application`
    """ 
    
    logger.debug("Starting the GUI.")
    main_window = Tk()
    main_window.title("Simple Tool for Orbital Parameters Extraction")
    main_window.geometry("600x800")
    #main_window.iconbitmap("stope_icon.ico")
    gui = Application(main_window)
    gui.update_files_counter() # Sets the TLE files counter to zero.
    
    gui.mainloop()
