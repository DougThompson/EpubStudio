#!/usr/bin/env python
'''Subclass of MainFrameBase, which is generated by wxFormBuilder.'''

'''
Copyright (c) 2011-2012 Doug Thompson

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import wx
import gui
import os
from EpubTools import EpubProcessor
from EpubTools import EpubBook
import xmlpp
import re

class Directory:
	'''Simple class for using as the data object in the DirTreeCtrl'''
	__name__ = 'Directory'
	def __init__(self, directory=''):
		self.directory = directory

# Implementing MainFrameBase
class MainFrame( gui.MainFrameBase ):
	tempdirs = []
	lastSearchPos = -1
	matchObj = None
	
	def __init__( self, parent ):
		gui.MainFrameBase.__init__( self, parent )
		
		self.Bind(wx.EVT_CLOSE, self.onCloseWindow)

	def m_mniOpenClick( self, event ):
		'''
		Browse for a file to open
		'''
		# Open the File Open dialog, grab the file name, and decide which
		# mode to open the file as: create (and parse) or edit
		self.m_statusBar.SetStatusText('')
		fdlg = wx.FileDialog(self,'Choose a file', 'Open file', wx.EmptyString, '*.*', wx.FD_OPEN | wx.FD_FILE_MUST_EXIST);
		if fdlg.ShowModal() == wx.ID_OK:
			# Create an EpubBook instance and process the file
			self.book = EpubBook(fdlg.GetPath(), self.m_statusBar, self.m_cbxCoverImage)
			self.book.process()
			# Collect the temp folders for later disposal
			self.tempdirs.append(self.book.baseDir)
			# Add the file list to the tree control
			self.populateTree(self.book.baseEpubDir, self.book.epubFileName)
			
			# Enable buttons and menus
			self.m_mniAddImages.Enable()
			self.m_mniRebuildContent.Enable()
			self.m_mniAddToLibrary.Enable()
				
	def m_mniSaveClick( self, event ):
		'''
		Save a file
		'''
		# Save a file to disk
		self.m_statusBar.SetStatusText('')
		if self.curFileName <> '':
			f = open(self.curFileName, 'w')
			f.write(self.m_txtMain.GetValue())
			f.close()		
			self.m_statusBar.SetStatusText('File saved.')

	def m_mniSaveEpubClick( self, event ):
		'''
		Save the EPUB to disk
		'''
		fdlg = wx.FileDialog(self,'Choose a file', 'Save file', self.book.title + '.epub', '*.epub', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT);
		
		if fdlg.ShowModal() == wx.ID_OK:
			saveEpubAs = fdlg.GetPath()
			# No epub file ext, then add one
			if os.path.splitext(saveEpubAs)[1].lower() != '.epub':
				saveEpubAs += '.epub'
			
			# Use a static method to create and save the EPUB
			EpubProcessor.createArchive(self.book.baseEpubDir, saveEpubAs)
			self.m_statusBar.SetStatusText('EPUB successfully saved.')
			
	def m_mniExitClick( self, event ):
		'''
		Clean up all temp folders and then Exit
		'''
		try:
			self.removeAllTempDirs()
		finally:	
			self.Close(True)
	
	def m_mniReformatClick( self, event ):
		'''
		Use pretty print to reformat xml-valid files
		'''
		self.m_statusBar.SetStatusText('')
		# Grab the file text and send it to the slightly
		# modified xmlpp to prettify
		body = self.m_txtMain.GetValue()
		body = xmlpp.get_pprint(body)
		self.m_txtMain.SetValue(body)

	def m_mniAddImagesClick( self, event ):
		'''
		Add images
		'''
		self.addImages()
	
	def m_mniRebuildContentClick( self, event ):
		'''
		Rebuild the EPUB content files
		'''
		self.rebuild()
		
	def m_mniAddToLibraryClick( self, event ):
		self.book.addToLibrary()
	
	def m_mniAboutClick( self, event ):
		'''
		Simple about dialog
		'''
		wx.MessageBox('EPUB Studio by Doug Thompson.','EPUB Studio')
	
	def m_btnAddCoverTagClick( self, event ):
		'''
		Add a Cover Tag to the OPF file
		'''
		if self.m_cbxCoverImage.GetStringSelection() <> '':
			### TODO: Implement functionality
			pass

	def rebuild(self):
		'''
		Rebuild the EPUB structure and details
		'''
		self.book.createContentOpf()
		self.book.createTOC()
		self.populateTree(self.book.baseEpubDir, self.book.epubFileName)

	def addImages(self):
		'''
		Add images to the OPF
		'''
		self.m_statusBar.SetStatusText('')
		fdlg = wx.FileDialog(self,'Choose one or more image files', 'Open file(s)', wx.EmptyString, '*.jpg', wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
		
		if fdlg.ShowModal() == wx.ID_OK:
			self.book.addImages(fdlg.GetPaths())
		
		# Re-populate the tree with the updated file list
		self.populateTree(self.book.baseEpubDir, self.book.epubFileName)
		
	def m_treeFilesSelChanged( self, event ):
		'''
		Simplified text editor functionality
		'''
		self.m_statusBar.SetStatusText('')
		
		# Grab the filename and make sure it is not an image
		# If not an image, then load the file and display
		filename = self.getItemPyData(event.GetItem()).directory
		extension = os.path.splitext(filename)[1]
		imgs = ['.jpg', '.jpeg', '.gif', '.png', '.bmp']

		self.m_txtMain.Value = ''
		self.curFileName = ''
		if os.path.isfile(filename):
			if extension.lower() not in imgs:
				self.curFileName = filename
				contents = open(filename, 'r').read()
				self.m_txtMain.Value = contents
			else:
				self.m_txtMain.Value = 'Not a valid text file'

	def m_btnDeleteClick( self, event ):
		'''
		Delete a selected file
		'''
		# Grab the filename and make sure it is not an image
		# If not an image, then load the file and display

		if len(self.curFileName) > 0:
			os.remove(self.curFileName)
			self.populateTree(self.book.baseEpubDir, self.book.epubFileName)
		
	def populateTree(self, root, rootDisplay):
		'''
		Build the EPUB file structure tree
		'''
		# Clear tree and prepare for data
		self.m_treeFiles.DeleteAllItems()
		rootEntry = self.m_treeFiles.AddRoot(rootDisplay)
		self.m_treeFiles.SetPyData(rootEntry, Directory(os.path.join(root, root)))
		
		# Loop through each file and add filenames and sub-folders
		ids = {root : rootEntry}
		for (dirpath, dirnames, filenames) in os.walk(root):
			for dirname in dirnames:
				fullpath = os.path.join(dirpath, dirname)
				ids[fullpath] = self.m_treeFiles.AppendItem(ids[dirpath], dirname)
				self.m_treeFiles.SetPyData(ids[fullpath], Directory(os.path.join(dirpath, dirname)))
			for filename in sorted(filenames):
				child = self.m_treeFiles.AppendItem(ids[dirpath], filename)
				self.m_treeFiles.SetPyData(child, Directory(os.path.join(dirpath, filename)))
		
		self.m_treeFiles.ExpandAll()
		
	'''
	Tree support functions
	'''
	def getItemText(self, item):
		# Get the text of an item
		if item:
			return self.m_treeFiles.GetItemText(item)
		else:
			return ''

	def getItemPyData(self, item):
		# Get the data of an item
		if item:
			return self.m_treeFiles.GetPyData(item)
		else:
			return ''
	
	def onCloseWindow(self, event):
		'''
		Clean up all temp folders and then Exit
		'''		
		try:
			self.removeAllTempDirs()
		finally:
			self.Destroy()

	def removeAllTempDirs(self):
		'''
		Recursively remove files and folders
		'''
		for dir in self.tempdirs:
			for root, dirs, files in os.walk(dir, topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
				for name in dirs:
					os.rmdir(os.path.join(root, name))
			os.rmdir(dir)
		
		self.tempdirs = []

	'''
	Rudimentary Find/Replace features
	'''
	def m_mniFindClick( self, event ):
		self.Find()

	def m_btnFindClick( self, event ):
		self.Find()
	
	def m_mniReplaceClick( self, event ):
		self.Replace()

	def m_btnReplaceClick( self, event ):
		self.Replace()
	
	def Find(self):
		'''
		Find text functions supporting Regular Expressions
		'''
		editor = self.m_txtMain
		self.matchObj = None
		
		if editor != None:
			# Grab the text, the find text, and the find methods
			textToSearch = editor.GetValue()
			findText = self.m_txtFind.GetValue()
			searchDown = True
			
			### TODO: support wholeWord functionality
			wholeWord = self.m_chkWholeWord.GetValue()
			matchCase = self.m_chkMatchCase.GetValue()
			useRegEx = self.m_chkRegEx.GetValue()
			
			# Get the caret position to start searching
			caret = editor.GetInsertionPoint()
			if self.lastSearchPos == caret:
				caret += 1
			
			# Make sure the caret values are within bounds
			if caret < 0:
				caret = 0
			if caret > len(textToSearch):
				caret = len(textToSearch) -1
			
			# Reset find variables to walk-thru text in the correct
			# search direction
			findPos = -1
			findLength = len(findText)
			if searchDown:
				if useRegEx:
					# Compile the RegEx and collect matches
					regex = re.compile(findText)
					match = regex.search(textToSearch, caret)
					if match <> None:
						# Get the text extent info for the current match
						self.matchObj = match
						findPos = match.start(0)
						findLength = match.end(0) - match.start(0)
				else:
					# Match without RegEx
					# If not matching case, the set to lower case... not sure
					# if this is the best option, but seems to be okay
					if matchCase:
						findPos = textToSearch.find(findText, caret)
					else:
						findPos = textToSearch.lower().find(findText.lower(), caret)
				
				# If there is a chunk found, then highlight it
				if findPos >= 0:
					editor.SetSelection(findPos, findPos + findLength)
					self.m_txtMain.SetFocus()
					self.lastSearchPos = findPos
			else:
				# Search up (not fully implemented)
				### TODO: finish implementing the functionality
				findPos = textToSearch[:caret].rfind(findText)
				if findPos >= 0:
					editor.SetSelection(findPos, findPos + len(findText))
					self.m_txtMain.SetFocus()
					self.lastSearchPos = findPos

	def Replace(self):
		'''
		Replace functionality
		'''
		# Grab the text, the find text, and the replace options
		findText = self.m_txtFind.GetValue()
		replaceText = self.m_txtReplace.GetValue()
		selectedText = self.m_txtMain.GetSelection()
		textToSearch = self.m_txtMain.GetValue()
		useRegEx = self.m_chkRegEx.GetValue()
		
		# Make sure something has bee found first.
		if (selectedText[0] <> selectedText[1]) & (self.lastSearchPos > -1):
			if useRegEx:
				# Get the groups to replace and do the replace with the matched replace text
				replaceGroups = len(self.matchObj.groups())
				if replaceText.find('\\' + str(replaceGroups)) >= 0:
					newReplaceText = replaceText
					for i in xrange(replaceGroups):
						newReplaceText = newReplaceText.replace('\\' + str(i+1), self.matchObj.group(i+1))
					
					textToSearch = textToSearch[:selectedText[0]] + newReplaceText + textToSearch[selectedText[1]:]
					self.m_txtMain.SetValue(textToSearch)
					self.m_txtMain.SetInsertionPoint(self.lastSearchPos)
			else:
				# Replace the selected text with the replace text
				textToSearch = textToSearch[:selectedText[0]] + replaceText + textToSearch[selectedText[1]:]
				self.m_txtMain.SetValue(textToSearch)
				self.m_txtMain.SetInsertionPoint(self.lastSearchPos)
			
			self.Find()
