"""
Uploads a file to Efetch
"""

from yapsy.IPlugin import IPlugin


class FaUpload(IPlugin):

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
        return "Upload"

    def check(self, curr_file, path_on_disk, mimetype, size):
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
        return False

    def cache(self):
        """Returns if caching is required"""
        return False

    def get(self, curr_file, helper, path_on_disk, mimetype, size, address, port, request, children):
        """Returns the result of this plugin to be displayed in a browser"""
        upload = False
        
        try:
            if request.query['upload'] and request.query['upload'] == 'True':
                upload = True
        except:
            pass
    
        if upload:
            return self.upload(helper, address, port, request)
        
        template = """
        <html>
        <head>
        <title>Upload</title>
        <style>
        form {
            position: absolute;
        }
        </style>
        </head>
        <body>
        <form action="/plugins/fa_upload/?upload=True" method="post" enctype="multipart/form-data">
        <fieldset>
            <legend>Upload a File</legend>
            Image ID:<br>
            <input type="text" name="name" />
            <br>
            <br>
            File:<br>
            <input type="file" name="data" />
            <br>
            <br>
            <br>
        <input type="submit" value="Start upload" />
        </fieldset>
        </form>
        </body>
        </html>
        """
        
        return template 
    
    def upload(self, helper, address, port, request):
        image = request.forms.name
        data = request.files.data
        if image and data and data.file:
            #raw = data.file.read() # This is dangerous for big files
            filename = data.filename
            data.save(helper.upload_dir + filename)
            return '<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url=http://' + address + ':' + port + '/plugins/fa_dfvfs/?image_id=' + image + '&offset=0&path=' + helper.upload_dir + filename + '" /></head></html>'
            #return "Hello %s! You uploaded %s" % (image, filename)
        return "You missed a field."
