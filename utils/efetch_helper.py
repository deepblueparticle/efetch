#!/usr/bin/python
from bottle import abort
import magic
import os
import logging
from PIL import Image
from db_util import DBUtil
from yapsy.PluginManager import PluginManager

class EfetchHelper(object):
    """This class provides helper methods to be used in Efetch and its plugins"""
    global pymagic
    global my_magic
    global db_util
    global plugin_manager 
    global output_dir
    global curr_dir
    global icon_dir
    global resource_dir

    def __init__(self, curr_directory, output_directory, es_url=None):
        """Initializes the Efetch Helper"""
        global pymagic
        global my_magic
        global db_util
        global plugin_manager
        global output_dir
        global curr_dir
        global icon_dir
        global resource_dir

        #Setup directory references
        curr_dir = curr_directory
        output_dir = output_directory
        resource_dir = curr_dir + "/resources/"
        icon_dir = curr_dir + "/icons/"

        if not os.path.isdir(icon_dir):
            logging.error("Could not find icon directory " + icon_dir)
            sys.exit(2)

        #Elastic Search DB setup
        if es_url:
            db_util = DBUtil()
        else:
            db_util = DBUtil(es_url)
        
        #Plugin Manager Setup
        plugin_manager = PluginManager()
        plugin_manager.setPluginPlaces([curr_dir + "/plugins/"])
        self.reload_plugins()

        #Determine which magic lib to use
        try:
            my_magic = magic.Magic(mime = True)
            pymagic = True
        except:
            my_magic = magic.Magic(flags=magic.MAGIC_MIME_TYPE)
            pymagic = False

    def curr_dir(self):
        """Gets the current directory Efetch is running from"""
        return curr_dir

    def output_dir(self):
        """Gets Efetch's cache directory"""
        return output_dir

    def resource_dir(self):
        """Gets Efetch's resource directory"""
        return resource_dir

    def icon_dir(self):
        """Gets Efetch's icon directory"""
        return icon_dir

    def plugin_manager(self):
        """Gets the Yapsy Plugin Manager"""
        global plugin_amanger
        return plugin_manager

    def reload_plugins(self):
        """Reloads all Yapsy plugins"""
        plugin_manager.collectPlugins()
        for plugin in plugin_manager.getAllPlugins():
            plugin_manager.activatePluginByName(plugin.name)

    def db_util(self):
        """Gets the Efetch DB Util"""
        return db_util

    def get_mimetype(self, file_path):
        """Returns the mimetype for the given file"""
        if pymagic:
            return my_magic.from_file(file_path)
        else:
            return my_magic.id_filename(file_path)

    def cache_file(curr_file, create_thumbnail=True):
        """Caches the provided file and returns the files cached directory"""
        if curr_file['file_type'] == 'directory':
            return

        #TODO: Not everything will have an iid... so need to figure that out
        file_cache_path = output_dir + 'files/' + curr_file['iid'] + '/' + curr_file['name']
        file_cache_dir = output_dir + 'files/' + curr_file['iid'] + '/'
        thumbnail_cache_path = output_dir + 'thumbnails/' + curr_file['iid'] + '/' + curr_file['name']
        thumbnail_cache_dir = output_dir + 'thumbnails/' + curr_file['iid'] + '/'

        #Makesure cache directories exist 
        if not os.path.isdir(thumbnail_cache_dir):
            os.makedirs(thumbnail_cache_dir)
        if not os.path.isdir(file_cache_dir):
            os.makedirs(file_cache_dir)

        #If file does not exist cat it to directory
        if not os.path.isfile(file_cache_path):
            plugin_manager.getPluginByName(curr_file['driver']).icat(curr_file['offset'], curr_file['image_path'], curr_file['inode'], file_cache_path)

        #Uses extension to determine if it should create a thumbnail
        assumed_mimetype = self.guess_mimetype(str(curr_file['ext']).lower())

        #If the file is an image create a thumbnail
        if assumed_mimetype.startswith('image') and create_thumbnail and not os.path.isfile(thumbnail_cache_path):
            try:
                image = Image.open(file_cache_path)
                image.thumbnail("42x42")
                image.save(thumbnail_cache_path)
            except IOError:
                logging.warn("Failed to create thumbnail for " + curr_file['name'] + " at cached path " + file_cache_path)

        return file_cache_path

    def guess_mimetype(self, extension):
        """Returns the assumed mimetype based on the extension"""
        types_map = {
            'a'      : 'application/octet-stream',
            'ai'     : 'application/postscript',
            'aif'    : 'audio/x-aiff',
            'aifc'   : 'audio/x-aiff',
            'aiff'   : 'audio/x-aiff',
            'au'     : 'audio/basic',
            'avi'    : 'video/x-msvideo',
            'bat'    : 'text/plain',
            'bcpio'  : 'application/x-bcpio',
            'bin'    : 'application/octet-stream',
            'bmp'    : 'image/x-ms-bmp',
            'c'      : 'text/plain',
            # Duplicates :(
            'cdf'    : 'application/x-cdf',
            'cdf'    : 'application/x-netcdf',
            'cpio'   : 'application/x-cpio',
            'csh'    : 'application/x-csh',
            'css'    : 'text/css',
            'dll'    : 'application/octet-stream',
            'doc'    : 'application/msword',
            'dot'    : 'application/msword',
            'dvi'    : 'application/x-dvi',
            'eml'    : 'message/rfc822',
            'eps'    : 'application/postscript',
            'etx'    : 'text/x-setext',
            'exe'    : 'application/octet-stream',
            'gif'    : 'image/gif',
            'gtar'   : 'application/x-gtar',
            'h'      : 'text/plain',
            'hdf'    : 'application/x-hdf',
            'htm'    : 'text/html',
            'html'   : 'text/html',
            'ico'    : 'image/vnd.microsoft.icon',
            'ief'    : 'image/ief',
            'jpe'    : 'image/jpeg',
            'jpeg'   : 'image/jpeg',
            'jpg'    : 'image/jpeg',
            'js'     : 'application/javascript',
            'ksh'    : 'text/plain',
            'latex'  : 'application/x-latex',
            'm1v'    : 'video/mpeg',
            'man'    : 'application/x-troff-man',
            'me'     : 'application/x-troff-me',
            'mht'    : 'message/rfc822',
            'mhtml'  : 'message/rfc822',
            'mif'    : 'application/x-mif',
            'mov'    : 'video/quicktime',
            'movie'  : 'video/x-sgi-movie',
            'mp2'    : 'audio/mpeg',
            'mp3'    : 'audio/mpeg',
            'mp4'    : 'video/mp4',
            'mpa'    : 'video/mpeg',
            'mpe'    : 'video/mpeg',
            'mpeg'   : 'video/mpeg',
            'mpg'    : 'video/mpeg',
            'ms'     : 'application/x-troff-ms',
            'nc'     : 'application/x-netcdf',
            'nws'    : 'message/rfc822',
            'o'      : 'application/octet-stream',
            'obj'    : 'application/octet-stream',
            'oda'    : 'application/oda',
            'p12'    : 'application/x-pkcs12',
            'p7c'    : 'application/pkcs7-mime',
            'pbm'    : 'image/x-portable-bitmap',
            'pdf'    : 'application/pdf',
            'pfx'    : 'application/x-pkcs12',
            'pgm'    : 'image/x-portable-graymap',
            'pl'     : 'text/plain',
            'png'    : 'image/png',
            'pnm'    : 'image/x-portable-anymap',
            'pot'    : 'application/vnd.ms-powerpoint',
            'ppa'    : 'application/vnd.ms-powerpoint',
            'ppm'    : 'image/x-portable-pixmap',
            'pps'    : 'application/vnd.ms-powerpoint',
            'ppt'    : 'application/vnd.ms-powerpoint',
            'ps'     : 'application/postscript',
            'pwz'    : 'application/vnd.ms-powerpoint',
            'py'     : 'text/x-python',
            'pyc'    : 'application/x-python-code',
            'pyo'    : 'application/x-python-code',
            'qt'     : 'video/quicktime',
            'ra'     : 'audio/x-pn-realaudio',
            'ram'    : 'application/x-pn-realaudio',
            'ras'    : 'image/x-cmu-raster',
            'rdf'    : 'application/xml',
            'rgb'    : 'image/x-rgb',
            'roff'   : 'application/x-troff',
            'rtx'    : 'text/richtext',
            'sgm'    : 'text/x-sgml',
            'sgml'   : 'text/x-sgml',
            'sh'     : 'application/x-sh',
            'shar'   : 'application/x-shar',
            'snd'    : 'audio/basic',
            'so'     : 'application/octet-stream',
            'src'    : 'application/x-wais-source',
            'sv4cpio': 'application/x-sv4cpio',
            'sv4crc' : 'application/x-sv4crc',
            'swf'    : 'application/x-shockwave-flash',
            't'      : 'application/x-troff',
            'tar'    : 'application/x-tar',
            'tcl'    : 'application/x-tcl',
            'tex'    : 'application/x-tex',
            'texi'   : 'application/x-texinfo',
            'texinfo': 'application/x-texinfo',
            'tif'    : 'image/tiff',
            'tiff'   : 'image/tiff',
            'tr'     : 'application/x-troff',
            'tsv'    : 'text/tab-separated-values',
            'txt'    : 'text/plain',
            'ustar'  : 'application/x-ustar',
            'vcf'    : 'text/x-vcard',
            'wav'    : 'audio/x-wav',
            'wiz'    : 'application/msword',
            'wsdl'   : 'application/xml',
            'xbm'    : 'image/x-xbitmap',
            'xlb'    : 'application/vnd.ms-excel',
            # Duplicates :(
            'xls'    : 'application/excel',
            'xls'    : 'application/vnd.ms-excel',
            'xml'    : 'text/xml',
            'xpdl'   : 'application/xml',
            'xpm'    : 'image/x-xpixmap',
            'xsl'    : 'application/xml',
            'xwd'    : 'image/x-xwindowdump',
            'zip'    : 'application/zip',
        }
                
        if extension in types_map:
            return types_map[extension]
        else:
            return "" 
