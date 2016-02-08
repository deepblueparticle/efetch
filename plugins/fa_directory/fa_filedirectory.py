"""
Simple file browser
"""

from yapsy.IPlugin import IPlugin
import os
import time

class FaFileDirectory(IPlugin):

    def __init__(self):
        IPlugin.__init__(self)

    def activate(self):
        IPlugin.activate(self)
        return

    def deactivate(self):
        IPlugin.deactivate(self)
        return

    def display_name(self):
        """Returns the name displayed in the webview"""
        return "File Directory"

    def check(self, evidence, path_on_disk):
        """Checks if the file is compatable with this plugin"""
        return True

    def mimetype(self, mimetype):
        """Returns the mimetype of this plugins get command"""
        return "text/plain"

    def popularity(self):
        """Returns the popularity which is used to order the apps from 1 (low) to 10 (high), default is 5"""
        return 0

    def parent(self):
        """Returns if the plugin accepts other plugins (True) or only files (False)"""
        return True

    def cache(self):
        """Returns if caching is required"""
        return False

    def get(self, evidence, helper, path_on_disk, request, children):
        """Returns a formatted directory listing for the given path"""
        #If path is a folder just set the view to it, if not use the files parent folder
        if evidence['meta_type'] == 'Directory':
            curr_folder = evidence
        else:
            curr_folder = helper.db_util.get_file(evidence['image_id'], evidence['dir'])

        listing = []

        if evidence['image_id'] in children:
            child_plugins = str(children).split(evidence['image_id'])[0]
        if not child_plugins:
            cuild_plugins = 'fa_fileanalyze/'
        
        if request.query_string:
            query_string = "?" + request.query_string
        else:
            query_string = ""
       
        show_dirs = False
        if 'show_dirs' in request.query:
            show_dirs = request.query['show_dirs'].lower() == 'true'

        #TODO: Change localtime to case time, specifically what is supplied to sleuthkit
        for item in helper.db_util.list_dir(curr_folder):
            source = item['_source']
            if show_dirs or source['meta_type'] != 'Directory':
                listing.append('    <tr>')
                listing.append('        <td><img src="/plugins/fa_thumbnail/' + source['pid'] + '" alt="' + source['meta_type'] + '-' + source['ext'] + '" title="' + source['meta_type'] + '-' + source['ext'] + '" style="width:32px;height:32px;"></td>')
                if source['meta_type'] == 'Directory':
                    listing.append('        <td><a href="/plugins/fa_filedirectory/' + child_plugins + source['pid'] + query_string + '" target="_self">' + source['name'] + "</a></td>")
                else:
                    listing.append('        <td><a href="/plugins/' + child_plugins + source['pid'] + query_string + '" target="file_dir_frame">' + source['name'] + "</a></td>")
                if ('mtime' in source):
                    listing.append("        <td>" + source['mtime'] + "</td>")
                else:
                    listing.append("        <td> - </td>")
                if ('atime' in source):
                    listing.append("        <td>" + source['atime'] + "</td>")
                else:
                    listing.append("        <td> - </td>")
                if ('ctime' in source):
                    listing.append("        <td>" + source['ctime'] + "</td>")
                else:
                    listing.append("        <td> - </td>")
                if ('crtime' in source):
                    listing.append("        <td>" + source['crtime'] + "</td>")
                else:
                    listing.append("        <td> - </td>")
                listing.append("        <td>" + str(source['file_size'][0]) + "</td>")
                listing.append("    </tr>")

        html = ""
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template = open(curr_dir + '/file_dir_template.html', 'r')
        html = str(template.read())
        template.close()
       
        html = html.replace('<!-- Table -->', '\n'.join(listing))

        if str(children).startswith(evidence['image_id']):
            html = html.replace('<!-- Home -->', "/plugins/" + child_plugins + children + query_string)
        else:
            html = html.replace('<!-- Home -->', "/plugins/" + children + query_string)


        return html

