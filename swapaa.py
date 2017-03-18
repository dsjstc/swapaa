#!/usr/bin/python3
# Swap.py
#
# Reverse the order of Artist and AlbumArtist in mp3 and flac files.
# Also cleans up non-unicode filenames.
# Run this on a COPY of your data.  It is very likely to screw up.
#

from mutagen.id3 import ID3, TPE1, TPE2
from mutagen.flac import FLAC
import sys
import os.path
import glob
from unidecode import unidecode
from pprint import pprint
import csv

#Globals for simplicity
class g:
	change=0
	test=0
	show=0
	recurse=0
	deunicode=0
	
	@staticmethod
	def haveaction():
		tot = 0
		tot += g.change
		tot += g.test
		tot += g.show
		tot += g.deunicode
		return tot	

#Functions
def main():
	basename = os.path.basename(sys.argv[0])
	if ( basename == "change.py" ):
		g.change=1
	if ( basename == "show.py" ):
		g.show=1
	if ( basename == "test.py" ):
		g.test=1

	for arg in sys.argv[1:]:
		parsearg(arg)
		
def parsearg(arg):
	if( arg == "-c" ):
		g.change = 1
		return
	if( arg == "-t" ) :
		g.test = 1
		return
	if( arg == "-s" ) :
		g.show = 1
		print("Path,Artist,AlbumArtist")
		return
	if( arg == "-r" ) :
		g.recurse = 1
		return
	if( arg == "-U" ) :
		g.deunicode = 1
		return
	if( arg == "-h" ):
		help()
		exit(0)
		
	if( g.haveaction() == 0):
		g.test = 1
		
	if( g.recurse ):
		for filename in glob.iglob("**/" + arg, recursive=True):
			doit(filename)
	else:
		doit(arg)

def help():
	helpstr = """
Help:
Swap.py [ args ] filespec

Action Arguments:
-c change position of Artist and AlbumArtist (copying if blank)
-t test files
-s show files with tags in CSV format
-U de-unicode filenames

Setting Arguments:
-r find filespec in *all* subdirectories
	 (NB that bash will expand a wildcard filespec BEFORE recursing)
"""
	print(helpstr)

def doit(arg):
	m = MusicFile(arg)
	m.process()

class MusicFile:
	def __init__(self, path):
		self.path = path
		self.filetype = "unknown"
		
		if( not os.path.exists(path) ):
			print( "No file: " + path)
			return
		
		if( not self.is_ascii(path) ):
			try:
				ppath = path.encode(sys.getfilesystemencoding())
				print( "Not ascii: ", path )
			except UnicodeEncodeError:
				ppath = unidecode(path)
				print( "Unicode error: ", ppath )
		
		basename = os.path.basename(path)
		p1, p2 = basename.rsplit(".", 1)
		p2 = p2.lower();
		if( p2 != "mp3" and p2 != "flac") :
			return
		self.filetype = p2
		
	def process(self):
		if( self.filetype == "unknown" ):
			return
		self.get()
		a = self.a
		aa = self.aa
		if( g.test ):
			self.test()
		if( g.deunicode ):
			self.deunicode()
		if( g.change ):
			if( not a and not aa ) :
				print( ("No Artist nor AlbumArtist: " + path) )
				return
			if ( not a ):
				a = aa
			if ( not aa ):
				aa = a
			self.aa = a
			self.a = aa
			self.save()
		if( g.show ):
			self.show()

	def deunicode(self):
		path = self.path
		if( self.is_ascii(path) ):
			return
		
		ppath = unidecode(path)

		print("Changing %s to %s", (path, ppath) )
		os.rename(path, ppath)	

	def test(self):
		path = self.path
		a = self.a
		aa = self.aa

		if ( not a ):
			print( "No artist " + path )
		if ( not aa ):
			print( "No album artist " + path )

		pprint (vars(self))

	@staticmethod	
	def is_ascii(s):
		return all(ord(c) < 128 for c in s)
	
	def show(self):
		path = self.path
		a = self.a
		aa = self.aa
		csvout = csv.writer(sys.stdout)
		#csvline = str.format( "%s,%s,%s" % (path, a, aa) )
		csvout.writerow((path, a, aa) )
			
#----------------------------------------------------------------------
# File handling
#----------------------------------------------------------------------		
	def get(self):
		if( self.filetype == "flac" ):
			self.getFlac()
		else:
			self.getMp3()

	def getFlac(self):
		cstr = ""
		audio = FLAC(self.path)
		a = aa = ''
		if "artist" in audio:
			a = audio["artist"][0]
		if "albumartist" in audio:
			aa= audio["albumartist"][0]
		self.flac = audio
		self.a = a
		self.aa = aa
			
	def getMp3(self):
		audio = ID3(self.path)
		a = aa = ''
		if 'TPE1' in audio:
			a = audio['TPE1'].text[0]
		if 'TPE2' in audio:
			aa= audio['TPE2'].text[0]
		else: 
			audio.add(TPE2(encoding=3, text=u"aa"))
		self.a = a
		self.aa = aa
		self.mp3 = audio

	def save(self):
		if( self.filetype == "flac" ):
			self.saveFlac()
		else:
			self.saveMp3()

	def saveFlac(self):
		audio = self.flac
		audio["artist"] = self.a
		audio["albumartist"] = self.aa
		audio.save()
		
	def saveMp3(self):
		audio = self.mp3
		aa = self.aa
		a = self.a
		audio['TPE1'].text[0] = a
		audio['TPE2'].text[0] = aa
		audio.save()

main()
