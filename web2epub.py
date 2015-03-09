#!python
# -*- coding: utf-8 -*-

# web2epub is a command line tool to convert a set of web/html pages to epub.
# Copyright 2012 Rupesh Kumar

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED, ZipInfo
import urllib2
import sys
import os.path
import mimetypes
import time
import urlparse
import cgi
from readability.readability import Document
from BeautifulSoup import BeautifulSoup,Tag

class MyZipFile(ZipFile):
    def writestr(self, name, s, compress=ZIP_DEFLATED):
        zipinfo = ZipInfo(name, time.localtime(time.time())[:6])
        zipinfo.compress_type = compress
        ZipFile.writestr(self, zipinfo, s)


def url2epub(urls, title=None, author=None, outfile=None):
    nos = len(urls)
    cpath = 'data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=='
    ctype = 'image/gif'

    epub = MyZipFile(outfile, 'w', ZIP_DEFLATED)
    #Metadata about the book
    info = dict(title=title,
            author=author,
            rights='Copyright respective page authors',
            publisher='Rupesh Kumar',
            ISBN='978-1449921880',
            subject='Blogs',
            description='Articles extracted from blogs for archive purposes',
            date=time.strftime('%Y-%m-%d'),
            front_cover= cpath,
            front_cover_type = ctype
            )

    # The first file must be named "mimetype"
    epub.writestr("mimetype", "application/epub+zip", ZIP_STORED)
    # We need an index file, that lists all other HTML files
    # This index file itself is referenced in the META_INF/container.xml file
    epub.writestr("META-INF/container.xml", '''<container version="1.0"
        xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
        <rootfiles>
            <rootfile full-path="OEBPS/Content.opf" media-type="application/oebps-package+xml"/>
        </rootfiles>
        </container>''')

    # The index file is another XML file, living per convention
    # in OEBPS/content.opf
    index_tpl = u'''<package version="2.0"
        xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid">
        <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>%(title)s</dc:title>
        <dc:creator>%(author)s</dc:creator>
        <dc:language>en</dc:language>
        <dc:rights>%(rights)s</dc:rights>
        <dc:publisher>%(publisher)s</dc:publisher>
        <dc:subject>%(subject)s</dc:subject>
        <dc:description>%(description)s</dc:description>
        <dc:date>%(date)s</dc:date>
        <dc:identifier id="bookid">%(ISBN)s</dc:identifier>
        <meta name="cover" content="cover-image" />
        </metadata>
        <manifest>
          <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
          <item id="cover-image" href="%(front_cover)s" media-type="%(front_cover_type)s"/>
          <item id="css" href="stylesheet.css" media-type="text/css"/>
            %(manifest)s
        </manifest>
        <spine toc="ncx">
            <itemref idref="cover" linear="no"/>
            %(spine)s
        </spine>
        </package>'''

    toc_tpl = u'''<?xml version='1.0' encoding='utf-8'?>
        <!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
                 "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
        <ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
        <head>
        <meta name="dtb:uid" content="%(ISBN)s"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
      </head>
      <docTitle>
        <text>%(title)s</text>
      </docTitle>
      <navMap>
        %(toc)s
      </navMap>
    </ncx>'''

    stylesheet_tpl = '''
        p, body {
            font-weight: normal;
            font-style: normal;
            font-variant: normal;
            font-size: 1em;
            line-height: 2.0;
            text-align: left;
            margin: 0 0 1em 0;
            orphans: 2;
            widows: 2;
        }
        h1{
            color: blue;
        }
        h2 {
            margin: 5px;
        }
    '''

    manifest = ""
    spine = ""
    toc = ""

    for i,url in enumerate(urls):
        print "Reading url no. %s of %s --> %s " % (i+1,nos,url)

        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.65 Safari/537.36')]
        html= opener.open(url).read()

#        html = urllib.urlopen(url).read()
        readable_article = Document(html).summary().encode('utf-8')
        readable_title = Document(html).short_title()

        manifest += '<item id="article_%s" href="article_%s.html" media-type="application/xhtml+xml"/>\n' % (i+1,i+1)
        spine += '<itemref idref="article_%s" />\n' % (i+1)
        toc += '<navPoint id="navpoint-%s" playOrder="%s"> <navLabel> <text>%s</text> </navLabel> <content src="article_%s.html"/> </navPoint>' % (i+2,i+2,cgi.escape(readable_title),i+1)

        soup = BeautifulSoup(readable_article)
        #Add xml namespace
        soup.html["xmlns"] = "http://www.w3.org/1999/xhtml"
        #Insert header
        body = soup.html.body
        h1 = Tag(soup, "h1", [("class", "title")])
        h1.insert(0, cgi.escape(readable_title))
        body.insert(0, h1)

        #Add stylesheet path
        head = soup.find('head')
        if head is None:
            head = Tag(soup,"head")
            soup.html.insert(0, head)
        link = Tag(soup, "link", [("type","text/css"),("rel","stylesheet"),("href","stylesheet.css")])
        head.insert(0, link)
        article_title = Tag(soup, "title")
        article_title.insert(0, cgi.escape(readable_title))
        head.insert(1, article_title)

        #Download images
        for j,image in enumerate(soup.findAll("img")):
            #Convert relative urls to absolute urls
            if image.get("src"):
                imgfullpath = urlparse.urljoin(url, image["src"])
            elif image.get("data-src"):
                imgfullpath = image["data-src"]
            #Remove query strings from url
            imgpath = urlparse.urlunsplit(urlparse.urlsplit(imgfullpath)[:3]+('','',))
#            print "    Downloading image: %s %s" % (j+1, imgpath)
            imgfile = os.path.basename(imgpath)
            filename = 'article_%s_image_%s%s' % (i+1,j+1,os.path.splitext(imgfile)[1])
            if imgpath.lower().startswith("http"):
                epub.writestr('OEBPS/images/'+filename, urllib2.urlopen(imgpath).read())
                image['src'] = 'images/'+filename
                manifest += '<item id="article_%s_image_%s" href="images/%s" media-type="%s"/>\n' % (i+1,j+1,filename,mimetypes.guess_type(filename)[0])

        epub.writestr('OEBPS/article_%s.html' % (i+1), str(soup))

    info['manifest'] = manifest
    info['spine'] = spine
    info['toc']= toc
    if title == None:
        info['title'] = cgi.escape(readable_title)
    ebook_index =  index_tpl % info

    # Finally, write the index and toc
    epub.writestr('OEBPS/stylesheet.css', stylesheet_tpl)
    epub.writestr('OEBPS/Content.opf', ebook_index.encode('utf8'))
    toc = toc_tpl % info
    toc = toc.encode('utf8')
    epub.writestr('OEBPS/toc.ncx', toc)


if __name__ == '__main__':
    url2epub([sys.argv[1]], outfile='test.epub')
