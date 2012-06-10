# EPUB Studio #

**EPUB Studio** is a Python GUI application (using wxPython) designed to create or edit non-DRM EPUB volumes.  Think of it as a simplified [Calibre](http://calibre-ebook.com/) or [Sigil](http://code.google.com/p/sigil/) that focuses on simplicity.  This originally started as a C# .NET application to create EPUBs that I wrote to a) learn more about the EPUB format, and b) wrote because (at the time) there was not a good way of creating EPUBs from HTML files.

## Development Requirements ##
Cross-development using [Aptana Studio 3](http://www.aptana.com/) started on 32-bit Python 2.6.1 on both Mac OS X 10.6.6 and Windows 7 64-bit using wxPython 2.8.9 32-bit.

Current requirements:

- [Python](http://www.python.org/download/) v2.7.3
- [wxPython](http://wxpython.org/) v2.8.12.1 32-bit
- [wxFormBuilder](http://wxformbuilder.org/) v3.1.70
- [Mako](http://www.makotemplates.org/) v0.4.1
- [xmlpp](http://xmlpp.codeplex.com/) (v?) (included with changes to modify printing options)
- [unzip from Doug Tolton](http://code.activestate.com/recipes/252508-file-unzip/) v1.1 (included)
- [DirTreeCtrl](http://keeyai.com/) v0.9.0 (included)

This has not been test on a Linux distribution.

## How to Use ##
The application can be used to create an EPUB file from a single HTML file or it can be used to edit non-DRM EPUB files.  The application will enter the correct mode based on the file extension opened.

### Creating an EPUB ###
The application will parse the document meta data based on the following filename format (each section delimited by ' - ' ([space][dash][space]):

> {Book Name} - {Author Last, Author First} - {Publisher(s)} - {Year} - {Comma separated list of subjects}.html

The application expects an HTML file with up to 3 levels of chapters (based on &lt;H1&gt;, &lt;H2&gt;, and &lt;H3&gt;).  You can have other standard HTML tags as long as they are supported by your EPUB reader.  The application will automatically add a cover image if it is named:

> {Author Lastname (no spaces)}_{Title (no spaces)}.jpg

To change how the Chapter titles are rendered, you can edit the "chapter.xml" template found in the support folder.

Once happy with the EPUB, simply save it to disk!

### Editing an EPUB ###
Select the EPUB file from the "Open file..." dialog and the application will extract the contents of the EPUB to a temp folder.  You can make any necessary changes to the individual files and resave the non-DRM EPUB.

### Preferences ###
The **Preferences Dialog** allows you to store a ****TODO****.

## Future Plans, Roadmap ##
None at this time &mdash; other than hoping to learn from better Python programmers than myself.