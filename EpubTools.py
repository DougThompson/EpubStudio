#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import os
import re
import shutil
import tempfile
import hashlib
import zipfile
import unzip
import xmlpp
import codecs

from time import strftime
from mako.template import Template
from xml.etree import ElementTree as ET

class EpubItem:
    '''
    EPUB Item class, more of a structure, however.
    '''
    def __init__(self):
        self.id = ''
        self.title = ''
        self.name = ''
        self.level = 0
        self.text = []
        self.srcPath = ''
        self.destPath = ''
        self.mimeType = ''
        self.linear = 'yes'
        self.children = []
        self.nameNotIndented = ''
        self.authorLastHash = ''
        self.titleHash = ''
        
class EpubBook:
    '''
    EPUB Book Class
    '''
    
    # Some global variables and initialization to assist with file structure 
    baseDir = ''
    baseEpubDir = ''
    opsDir = ''
    metaDir = ''
    cssDir = ''
    imagesDir = ''
        
    def __init__(self, fileName, statusBar, imageCombo):
        '''
        Initialize the class and set the EPUB properties and variables
        '''
        self.fileName = fileName
        self.epubFileName = ''
        self.epubFileNameHash = ''
        self.title = ''
        self.titleHash = ''
        self.author = ''
        self.authorSort = ''
        self.authorHash = ''
        self.coverage = ''
        self.description = ''
        self.identifier = ''
        self.origPublishDate = ''
        self.publisher = ''
        self.rights = ''
        self.source = ''
        self.subject = ''
        self.coverImageSource = ''
        self.coverImage = ''
        self.chapters = []
        self.images = []
        self.css = []
        self.fonts = []
        self.toc = ''
        self.href = ''
        self.statusBar = statusBar
        self.imageCombo = imageCombo
        
        self.dateCreated = strftime('%Y-%m-%d') #%H:%M:%S')
        self.creator = "EPUB Author";
        self.language = "en-US";
    
    def process(self):
        '''
        Choose mode: Edit or Create
        '''
        if os.path.splitext(self.fileName)[1].lower() == ".epub":
            self.parseEpub(self.fileName)
        else:
            self.createEpub(self.fileName)
    
    def dirEntries(self, dir_name, subdir, *args):
        '''
        Get a list of files in a directory
        '''
        fileList = []
        for fname in os.listdir(dir_name):
            dirfile = os.path.join(dir_name, fname)
            if os.path.isfile(dirfile):
                if not args:
                    fileList.append(dirfile)
                else:
                    if os.path.splitext(dirfile)[1][1:].lower() in args:
                        fileList.append(dirfile)
            # recursively access file names in subdirectories
            elif os.path.isdir(dirfile) and subdir:
                #print "Accessing directory:", dirfile
                fileList.extend(self.dirEntries(dirfile, subdir, *args))
        return fileList

    def addAllImageFiles(self, path):
        '''
        Add images to the image dropdown
        '''
        fileList = self.dirEntries(path, True, 'jpg', 'jpeg', 'gif', 'png', 'bmp')
        self.imageCombo.Clear()
        for fname in fileList:
            self.imageCombo.Append(os.path.basename(fname))

    def addImages(self, paths):
        '''
        Add one or more images
        '''
        for image in paths:
            self.addImage(image)
    
    def addImage(self, fileName):
        '''
        Add an image to the EPUB
        '''
        # Grab the details for the image to be used later in creating
        # the EPUB OPF file
        justFileName = os.path.basename(fileName)
        image = EpubItem()
        image.id = os.path.splitext(justFileName)[0]
        image.name = justFileName
        image.href = 'images/' + image.name
        image.destPath = image.name
        image.srcPath = fileName
        self.images.append(image)
        
        # Copy the file to the temp dir for later archiving        
        shutil.copy(fileName, os.path.join(self.imagesDir, image.name))

    def createEpub(self, fileName):
        '''
        Create an EPUB file
        '''
        
        # Grab the file name and split it
        # Expecting the following format:
        #   {Book Name} - {Author Last, First} - {Publisher(s) Name(s)} - {Year} - {Subject(s)}
        justFileName = os.path.splitext(os.path.basename(fileName))[0]
        justPath = os.path.dirname(fileName)
        info = justFileName.split(" - ")

        # Has all info been provided?
        if len(info) >= 4:
            # All info should be present, so parse the name and assign values
            self.title = info[0].strip()
            self.titleHash = EpubProcessor.getShortHash(self.title)
            self.authorSort = info[1].strip()
            self.authorHash = EpubProcessor.getShortHash(self.authorSort)
            self.identifier = EpubProcessor.getShortHash(self.authorSort + self.title)
            self.author = info[1].split(',')[1].strip() + ' ' + info[1].split(',')[0].strip()
            self.publisher = info[2].strip()
            self.origPublishDate = info[3].strip()
            if len(info) >= 5:
                self.subject = info[4].strip()
        else:
            # Some info missing, so do the best -- this may be a test
            # run to make sure the HTML file has been built correctly
            self.title = ''
            self.titleHash = ''
            self.author = ''
            self.authorSort = ''
            self.authorHash = ''
            self.coverage = ''
            self.description = ''
            self.identifier = ''
            self.origPublishDate = ''
            self.publisher = ''
            self.rights = ''
            self.source = ''
            self.subject = ''
        
        # Grab the list of chapters
        self.chapters = EpubProcessor.parseHtml(fileName, self.statusBar)
        
        # Create some default names and hashes (which will be used if obfuscating an ATOM library)
        defEpubName = info[1].split(',')[0].strip() + '_' + self.title.title()
        defEpubName = defEpubName.replace(' ', '')
        self.epubFileName = defEpubName + '.epub'
        self.epubFileNameHash = EpubProcessor.getShortHash(defEpubName)
                
        # Ready to start building EPUB file structure, so get a temp dir
        # and build some folders
        self.baseDir = tempfile.mkdtemp()
        self.baseEpubDir = os.path.join(self.baseDir, defEpubName)
        self.opsDir = os.path.join(self.baseEpubDir, EpubProcessor.getOpsDirName(self.baseEpubDir))
        self.metaDir = os.path.join(self.baseEpubDir, 'META-INF')
        self.cssDir = os.path.join(self.opsDir, 'css')
        self.imagesDir = os.path.join(self.opsDir, 'images')
        
        os.makedirs(self.baseEpubDir)
        os.makedirs(self.opsDir)
        os.makedirs(self.metaDir)
        os.makedirs(self.cssDir)
        os.makedirs(self.imagesDir)
        
        # Start copying some default files from the support directory
        shutil.copy(os.path.join('support', 'mimetype'), os.path.join(self.baseEpubDir, 'mimetype'))
        shutil.copy(os.path.join('support', 'main.css'), os.path.join(self.cssDir, 'main.css'))
        shutil.copy(os.path.join('support', 'container.xml'), os.path.join(self.metaDir, 'container.xml'))
                
        # Check to see if a default cover image exists
        # Expecting:  {AuthorLast}_{Title(no spaces)}.jpg
        if os.path.isfile(os.path.join(justPath, defEpubName + ".jpg")):
            self.coverImage = defEpubName + ".jpg"
            self.coverImageSource = os.path.join(justPath, defEpubName + ".jpg")
        
        # Default cover not found, so look for cover.jpg
        if self.coverImage == '':
            if os.path.isfile(os.path.join(justPath, "cover.jpg")):
                self.coverImage = "cover.jpg"
                self.coverImageSource = os.path.join(justPath, "cover.jpg")
        
        # A cover has been found, so setup the EPUB details
        if self.coverImage <> '':
            image = EpubItem()
            image.id = 'cover'
            image.name = self.coverImage
            image.href = 'images/' + self.coverImage
            image.destPath = self.coverImage
            image.srcPath = self.coverImageSource
            self.images.append(image)

            shutil.copy(self.coverImageSource, os.path.join(self.imagesDir, self.coverImage))
            self.imageCombo.Clear()
            self.imageCombo.Append(image.name)

        ### TODO: fully implement additional auto-discovery of images
        # Copy all of the images
        #for image in self.images:
        #    if image.id <> 'cover':
        #        shutil.copy(image.srcPath, os.path.join(self.imagesDir, image.name))
        #    
        #    self.imageCombo.Clear()
        #    self.imageCombo.Append(image)
        
        # Start creating the EPUB files themselves by splitting the supplied HTML file
        self.createTitlePage()
        self.createChapters()
        self.createContentOpf()
        self.createTOC()
        
        # Alert the user the file has been processed
        self.statusBar.SetStatusText('Done.')

    def createContentOpf(self):
        '''
        Create the OPF file
        '''
        # Use Mako to update the template
        self.statusBar.SetStatusText('Creating OPF file...')
        contentOPF = Template(filename='support/content.opf').render(book=self)
        contentOPF = re.sub("\r?\n", "\n", contentOPF)

        with open(os.path.join(self.opsDir, 'content.opf') , 'w') as f:
            f.write(contentOPF)

    def createTitlePage(self):
        '''
        Create the Title page
        '''
        # Use Mako to update the template
        self.statusBar.SetStatusText('Creating Title Page...')
        titlePage = Template(filename='support/title.xml').render(book=self)
        titlePage = re.sub("\r?\n", "\n", titlePage)
        with open(os.path.join(self.opsDir, 'titlepage.xml') , 'w') as f:
            f.write(titlePage)
        
    def createChapters(self):
        '''
        Create each chapter
        '''
        for chapter in self.chapters:
            # Use Mako to update the template
            # May have some issues with encoding, so be sure to remove special characters (or use UTF-8?)
            self.statusBar.SetStatusText('Creating Chapter file: ' + chapter.name)
            chapterText = Template(filename='support/chapter.xml').render(title=self.title, chapter=chapter)
            chapterText = re.sub("\r?\n", "\n", chapterText)
            with open(os.path.join(self.opsDir, chapter.destPath) , 'w') as f:
                f.write(chapterText)

    def createTOC(self):
        '''
        Create the Table of Contents
        '''
        # Use Mako to update the template
        self.statusBar.SetStatusText('Creating TOC file...')
        tocNCX = Template(filename='support/toc.ncx').render(book=self)
        tocNCX = re.sub("\r?\n", "\n", tocNCX)
        with open(os.path.join(self.opsDir, 'toc.ncx') , 'w') as f:
            f.write(tocNCX)

    def parseEpub(self, fileName):
        '''
        Read the non-DRM EPUB file contents
        '''
        # Unzip the EPUB file to the temp dir
        self.baseDir, self.baseEpubDir, self.epubFileName = EpubProcessor.unzipEpub(fileName)
        
        self.metaDir = os.path.join(self.baseEpubDir, 'META-INF')
        # Figure out the OPF file name and location using the container.xml        
        self.opsDir = os.path.join(self.baseEpubDir, EpubProcessor.getOpsDirName(self.baseEpubDir))                   
        self.cssDir = os.path.join(self.opsDir, 'css')
        self.imagesDir = os.path.join(self.opsDir, 'images')
        
        self.addAllImageFiles(self.baseDir)

    def addToLibrary(self):
        '''
        Add the EPUB file to an ATOM file
        '''
        
        ### TODO: Finish implementing feature
        epub = EpubProcessor.getEpubDetails(self)
        EpubProcessor.addToLibraryFile(r'tests{0}authoral.atom'.format(os.sep), self)
        
'''
A Class of static methods to create/process/update EPUB files/details
'''
class EpubProcessor:
    @staticmethod
    def getEpubDetails(epub):
        '''
        Parse an existing non-DRM EPUB file
        '''
        # Necessary namespaces
        ns = {
            'pkg':'{http://www.idpf.org/2007/opf}',
            'dc':'{http://purl.org/dc/elements/1.1/}'
        }
        
        # Open the content.opf file and parse the root
        with open(os.path.join(epub.opsDir, r'content.opf'), 'r') as fp:
            root = ET.parse(fp).getroot()

        # Grab the common one-to-one elements
        elems = ['title', 'identifier', 'language', 'publisher', 'description', 'coverage', 'source', 'rights']
        for item in elems:
            epub.__dict__[item] = root.find('{0}metadata/{1}{2}'.format(ns['pkg'], ns['dc'], item)).text
        
        # Find the creator(s)
        epub.creator = root.find('{0}metadata/{1}{2}'.format(ns['pkg'], ns['dc'], 'creator')).attrib['{0}file-as'.format(ns['pkg'])]
        
        # Find the publication date
        for date in root.findall('{0}metadata/{1}{2}'.format(ns['pkg'], ns['dc'], 'date')):
            if date.attrib['{0}event'.format(ns['pkg'])] == 'original-publication':
                epub.origPublishDate = date.text
                break;
        
        # Find all subjects
        for subject in root.findall('{0}metadata/{1}{2}'.format(ns['pkg'], ns['dc'], 'subject')):
            epub.subject += subject.text + ', '
        
        # Strip an ending ', '
        if epub.subject[-2:] == ', ':
            epub.subject = epub.subject[:-2]
        
        # Now, build the TOC by parsing all manifest items based on the media type
        epub.toc = ''
        for manifestItems in root.findall('{0}manifest/'.format(ns['pkg'])):
            for item in manifestItems:
                mediaType = item.attrib['media-type']
                if mediaType == 'application/x-dtbncx+xml':
                    epub.toc = item.attrib['href'] 
                elif mediaType == 'text/css':
                    epub.css.append(item.attrib['href'])
                elif mediaType == 'image/jpeg':
                    imageName = item.attrib['href']
                    imageDir = ''
                    pos = imageName.find('/')
                    if pos > -1:
                        imageDir = imageName[:(pos + 1)]
                        imageName = imageName[(pos + 1):]
                    image = EpubItem()
                    image.id = os.path.splitext(imageName)[0]
                    image.name = imageName
                    image.href = imageDir + image.name
                    image.destPath = image.name
                    image.srcPath = ''
                    epub.images.append(image)
        
        ### TODO: Need to add TOC processing to build chapter list
        
        # Hash the author and title to be used in an obfuscated library
        epub.titleHash = EpubProcessor.getShortHash(epub.title)
        epub.authorHash = EpubProcessor.getShortHash(epub.creator)
        
        return epub
    
    @staticmethod
    def getOpsDirName(rootDir):
        '''
        Parse the container.xml file to get the OPS dir
        '''
        container = os.path.join(os.path.join(rootDir, 'META-INF'), 'container.xml')
        opsDir = 'OPS'
        
        if os.path.isfile(container):        
            with open(container, 'r') as fp:
                root = ET.parse(fp).getroot()
            
            # Now find the OPS dir and return
            rootfile = root.find('{0}rootfiles/{0}rootfile'.format('{urn:oasis:names:tc:opendocument:xmlns:container}'))
            opsDir = rootfile.attrib['full-path']
            opsDir = opsDir[:opsDir.find('/')]
        
        return opsDir
    
    @staticmethod
    def addToLibraryFile(libraryFile, epubData):
        '''
        Add an EPUB to an ATOM library file
        '''
        ### TODO: Finish implementing functionality
        newAuthor = epubData['creator']
        newTitle = epubData['title']

        baseEntry = ['    <entry>',
                     '        <id>{0}</id>'.format(epubData['identifier']),
                     '        <title>{0}</title>'.format(epubData['title']),
                     '        <author>',
                     '            <name>{0}</name>'.format(epubData['creator']),
                     '        </author>',
                     '        <content type="xhtml">',
                     '            <div xmlns="http://www.w3.org/1999/xhtml">Published: {0}, Language: {1}, Subject: {2}</div>'.format(epubData['published'], epubData['language'], epubData['subject']),
                     '        </content>',
                     '        <summary>{0}</summary>'.format(epubData['description']),
                     '        <updated>{0}Z</updated>'.format(strftime('%Y-%m-%d %H:%M:%S')),
                     '        <link type="application/epub+zip" href="{0}/{1}.epub" />'.format(epubData['authorHash'], epubData['titleHash']),
                     '        <link rel="http://opds-spec.org/opds-cover-image-thumbnail" type="image/jpeg" title="cover thumbnail" href="{0}/{1}_tn.jpg" />'.format(epubData['authorHash'], epubData['titleHash']),
                     '        <link rel="http://opds-spec.org/opds-cover-image" type="image/jpeg" title="cover image" href="{0}/{1}.jpg" />'.format(epubData['authorHash'], epubData['titleHash']),
                     '        <link rel="x-stanza-cover-image-thumbnail" type="image/jpeg" href="{0}/{1}_tn.jpg" />'.format(epubData['authorHash'], epubData['titleHash']),
                     '        <link rel="x-stanza-cover-image" type="image/jpeg" href="{0}/{1}.jpg" />'.format(epubData['authorHash'], epubData['titleHash']),
                     '    </entry>']
        
        with open(libraryFile, 'r') as libFile:
            atom = libFile.read()
        
        # Pretty print and standardize the ATOM file to make parsing a little easier
        atom = xmlpp.get_pprint(atom)
        atom = atom.replace('\r\n', '\n')
        entries = atom.split('\n')
        
        # Consider using xml rather than RegEx to parse the file
        i = 0
        for line in entries:
            if line.strip() == '<entry>':
                # Check to find the Alpha location in the file
                match = re.search('<.*>(.*)</.*>', entries[i + 1])
                curTitle = match.groups()[0]
                match = re.search('<.*>(.*)</.*>', entries[i + 7])
                curAuthor = match.groups()[0]
                
                if newAuthor > curAuthor:
                    pass
                elif newAuthor == curAuthor:
                    if newTitle > curTitle:
                        pass
                    elif newTitle == curTitle:
                        end = i + 1
                        while entries[end].strip() <> '</entry>':
                            end += 1
                            
                        entries[i:end + 1] = baseEntry
                        break;
                    else:
                        entries[i:1] = baseEntry
                        break
                elif newAuthor < curAuthor:                 
                    entries[i:1] = baseEntry
                    break
            i += 1
        
        # Now write the file out
        with open(libraryFile, 'w') as f:
            atom = '\n'.join(entries)[1:]
            f.write(atom)
        
    @staticmethod
    def formatParagraph(paragraph):
        '''
        Format a text paragraph into HTML
        '''
        ### NOT USED, should consider removing
        paragraph = paragraph.replace('--', '¡ª')
        paragraph = re.sub(r' +', ' ', paragraph)
        paragraph = re.sub(r'_(.+?)_', r'<em>\1</em>', paragraph)
        return paragraph
    
    @staticmethod
    def gethash(inputText):
        '''
        Get a simple SHA-1 hash and split into chunks
        '''
        hashInput = hashlib.sha1(inputText).hexdigest()
        return '{0}-{1}-{2}-{3}-{4}'.format(hashInput[:8], hashInput[8:12], hashInput[12:16], hashInput[16:20], hashInput[20:32])
    
    @staticmethod
    def getShortHash(inputText):
        '''
        Get a shortened SHA-1 hash
        '''
        hashInput = hashlib.sha1(inputText).hexdigest()
        return '{0}'.format(hashInput[:8])
    
    @staticmethod
    def stripTags(inputText):
        '''
        Strip all HTML tags from a line of text
        '''
        cleaned = re.compile(r'<[^<]*?/?>')
        return cleaned.sub('', inputText)
    
    @staticmethod
    def stripSingleTag(inputText, tag):
        '''
        Strip a specific HTML tag from a line of text
        '''
        cleaned = re.compile(r'<[/]?(' + tag + r'|[' + tag + r']:\w+)[^>]*?>')
        return cleaned.sub('', inputText)
        
    @staticmethod
    def parseHtml(path, statusBar):
        '''
        Parse the HTML file to create EPUB Chapters
        '''
        # Start at the BODY tag
        foundBody = False
        
        # Build the chapter heading RegEx and sections holder
        sectionLevels = {'<h1>': 1, '<h2>': 2, '<h3>': 3}
        sectionStart = re.compile(r'<h[1-3]')
        sections = []
        
        r = re.compile(r'[^a-zA-Z0-9]')
        with open(path) as fin:
        #f = codecs.open('unicode.rst', encoding='utf-8')
        #with codecs.open(path, encoding='utf-8') as fin:
            for line in fin:
                if foundBody == True:
                    line = line.strip()
                    if sectionStart.match(line):
                        # Here is a chapter of some form
                        section = EpubItem()
                        section.level = sectionLevels[line[:4]]
                        section.mimeType = 'application/xhtml+xml'
                        # Parse the section name
                        section.name, section.title = EpubProcessor.splitChapterLine(EpubProcessor.stripTags(line))
                        
                        ### TODO: Add more processing for Appendix, Epilogue, Introduction, etc...
                        # Is it a footnotes section?
                        if section.name.lower() == 'footnotes':
                            section.linear = 'no'
                        
                        # Decide how to process the level: Chapter or a sub-Chapter
                        if section.level > 1:
                            # This is a sub-Chapter
                            section.id = (EpubProcessor.findParentIds(sections, section.level) + section.name).replace(' ', '')
                            section.id = r.sub('', section.id)
                            
                            # Some EPUB viewers cannot handle nested Chapters in the TOC
                            # So, use an ugly hack to indent
                            if section.level == 2:
                                section.nameNotIndented = '....' + section.name
                            elif section.level == 3:
                                section.nameNotIndented = '........' + section.name
                            else:
                                section.nameNotIndented = '{0}{1}'.format(EpubProcessor.findParentNames(sections, section.level), section.name)
                            
                            # Build the name
                            section.name = '{0}{1}'.format(EpubProcessor.findParentNames(sections, section.level), section.name)
                        else:
                            # Top level Chapter
                            section.id = section.name.replace(' ', '')
                            section.id = r.sub('', section.id)
                        
                        # Create the xml file for the EPUB
                        section.destPath = section.id + '.xml'
                        
                        # Get the parent and append this to it for nested navigation
                        parent = EpubProcessor.findParentIndex(sections, section.level)
                        if parent > -1:
                            sections[parent].children.append(section)
                        sections.append(section)
                        
                        statusBar.SetStatusText('Found chapter: ' + section.id)
                    elif line[:6].lower() <> r'</body' and line[:6].lower() <> r'</html':
                        # Not at the end of the document, and not a new section, so keep adding
                        # lines to the file to create the chapter body
                        section.text.append(line)
                
                # Keep parsing until the BODY tag is found
                if foundBody == False:
                    if line[:5].lower() == r'<body':
                        foundBody = True
                
        statusBar.SetStatusText('Done processing chapters.')
        return sections
    
    @staticmethod
    def findParentIndex(itemList, curItemLevel):
        '''
        Get the parent of an item in the list
        '''
        for i in xrange(len(itemList) - 1, -1, -1):
            if itemList[i].level < curItemLevel:
                return i
        
        return -1

    @staticmethod
    def findParentIds(itemList, curItemLevel):
        '''
        Get all Parent IDs of an item in the list
        '''
        value = ''
        for i in xrange(len(itemList) - 1, -1, -1):
            if itemList[i].level < curItemLevel:
                value = '{0}{1}'.format(itemList[i].id, value)
                return value
        
        return ''

    @staticmethod
    def findParentNames(itemList, curItemLevel):
        '''
        Get all Parent names of an item in the list
        '''
        value = ''
        for i in xrange(len(itemList) - 1, -1, -1):
            if itemList[i].level < curItemLevel:
                value = value
                return value
        
        return ''
    
    @staticmethod
    def splitChapterLine(line):
        '''
        Split the Chapter name
        '''
        items = line.split(' - ')
        
        if len(items) == 2:
            chapterName = items[0]
            chapterTitle = items[1]
        else:
            chapterName = line
            chapterTitle = ""
            
        return chapterName.strip(), chapterTitle.strip()

    @staticmethod
    def toTitleCase(s, exceptions):
        '''
        Change the Title name to simplified Title Case
        '''
        word_list = re.split(' ', s)
        final = [word_list[0].capitalize()]
        for word in word_list[1:]:
            final.append(word in exceptions and word or word.capitalize())
        
        return " ".join(final)
    @staticmethod
    def unzipEpub(zipsource):
        '''
        Unzip the EPUB file to a temp file
        '''
        filename = os.path.splitext(zipsource)[0].split(os.sep)[-1]
        baseDir = tempfile.mkdtemp()
        zipdest = os.path.join(baseDir, filename)
        os.makedirs(zipdest)
        
        unzipper = unzip.unzip()
        unzipper.verbose = False
        unzipper.percent = 100
        unzipper.extract(zipsource, zipdest)

        return baseDir, zipdest, filename + ".epub"

    @staticmethod
    def createArchive(zipDir, epubFile):
        '''
        Zip up a folder into the EPUB format
        '''
        if os.path.isfile(epubFile):
            os.remove(epubFile)
    
        zipArchive = zipfile.ZipFile(epubFile, 'w')
        root_len = len(os.path.abspath(zipDir))
        
        # Be sure to zip (uncompressed) the mimetype file first as
        # dictacted by the EPUB specification
        zipArchive.write(os.path.join(zipDir, 'mimetype'), 'mimetype', zipfile.ZIP_STORED)
        for root, zipDirs, files in os.walk(zipDir):
            archive_root = os.path.abspath(root)[root_len:]
            for f in files:
                if f.lower() != 'mimetype':
                    fullpath = os.path.join(root, f)
                    archive_name = os.path.join(archive_root, f)
                    zipArchive.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
        
        zipArchive.close()
        print 'Done.'
