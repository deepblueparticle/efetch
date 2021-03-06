"""
Simple directory tree view
"""

from yapsy.IPlugin import IPlugin
from jinja2 import Template
import json
import logging
import os

class Directory(IPlugin):

    def __init__(self):
        self.display_name = 'Navigate'
        self.popularity = 9
        self.cache = False
        self.fast = False
        self.action = False
        self.icon = 'fa-folder-o'

        self._file_plugin = 'analyze'
        self._dir_plugin = 'directory'
        self._evidence_plugin = 'directory'

        IPlugin.__init__(self)

    def activate(self):
        IPlugin.activate(self)
        return

    def deactivate(self):
        IPlugin.deactivate(self)
        return

    def check(self, evidence, path_on_disk):
        """Checks if the file is compatible with this plugin"""
        return True

    def mimetype(self, mimetype):
        """Returns the mimetype of this plugins get command"""
        return "text/plain"

    @staticmethod
    def human_readable_size(num, suffix='B'):
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1000.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1000.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def get(self, evidence, helper, path_on_disk, request):
        """Returns the result of this plugin to be displayed in a browser"""
        dir_table = []
        file_table = []

        # Templates
        row_template = Template("""
            <tr>
                <!-- {{ file_name }} -->
                <td style="padding-left: 24px;"><a href="/plugins/{{ plugin }}?{{ url_query }}" {{ target }}>
                    <img src="{{ icon }}" style="width:32px;height:32px;"
                    alt="{{ order }} {{ file_name }}"></a></td>
                <td><a href="/plugins/{{ plugin }}?{{ url_query }}" {{ target }}>{{file_name}}</a></td>
                <td>{{ mtime_no_nano }}</td>
                <td>{{ atime_no_nano }}</td>
                <td>{{ ctime_no_nano }}</td>
                <td>{{ crtime_no_nano }}</td>
                <td>{{ size }}</td>
                <td>
                    {{ analyze }}
                    {{ preview }}
                    {{ download }}
                </td>
            </tr>
        """)
        analyze_template = Template("""
                    <a href="/plugins/analyze?{{ url_query }}" target="_top" style="padding-right:10px">
                        <span class="fa-stack fa-md">
                            <i class="fa fa-square fa-stack-2x"></i>
                            <i class="fa fa-info-circle fa-stack-1x fa-inverse"></i>
                        </span>
                    </a>""")
        download_template = Template("""
                    <a href="/plugins/download?{{ url_query }}">
                        <span class="fa-stack fa-md">
                            <i class="fa fa-square fa-stack-2x"></i>
                            <i class="fa fa-download fa-stack-1x fa-inverse"></i>
                        </span>
                    </a>""")
        preview_template = Template("""
                    <a href="/plugins/preview?{{ url_query }}&redirect=True" target="_blank" style="padding-right:10px">
                        <span class="fa-stack fa-md">
                            <i class="fa fa-square fa-stack-2x"></i>
                            <i class="fa fa-eye fa-stack-1x fa-inverse"></i>
                        </span>
                    </a>""")

        # ORDER:
        #   1 - Up
        #   2 - Folders
        #   3 - Evidence and files

        # if ('volume_type' in evidence or 'storage_type' in evidence or 'compression_type' in evidence or \
        #        'archive_type' in evidence) and not evidence['mimetype'].startswith('application/vnd'):
        #     if u'archive_type' in evidence and u'ZIP' in evidence['archive_type']:
        #         initial_pathspec = [helper.pathspec_helper.get_zip_base_pathspec(evidence['pathspec'])]
        #     else:
        #         initial_pathspec = helper.pathspec_helper.get_new_base_pathspecs(evidence['pathspec'])

        # Forces volumes and partitions to be seen as expandable evidence
        force_expand = False

        # Moves the directory view up to the next expandable/directory pathspec
        #  and if the next one is '/' move up twice to the volume/partition root
        if not helper.is_expandable_evidence(evidence) and evidence['meta_type'] != 'Directory':
            evidence_parent = helper.pathspec_helper.get_parent_pathspec(evidence['pathspec'])
            evidence = helper.pathspec_helper.get_evidence_item(evidence_parent)
            return self.get(evidence, helper, path_on_disk, request)

        # Compressed files, only have 1 item
        if 'compression_type' in evidence:
            item_pathspec = helper.pathspec_helper.list_base_pathspecs(evidence)[0]['pathspec']
            items = [helper.pathspec_helper.get_evidence_item(item_pathspec)]
            initial_pathspec = evidence['pathspec']
        # Evidence
        elif helper.is_expandable_evidence(evidence):
            items = helper.pathspec_helper.list_base_pathspecs(evidence)

            # If moving up and only one item is there, go up (Prevents loop from next option)
            if len(items) == 1 and helper.get_request_value(request, 'up', False):
                evidence_parent = helper.pathspec_helper.get_parent_pathspec(evidence['pathspec'])
                try:
                    evidence = helper.pathspec_helper.get_evidence_item(evidence_parent)
                except RuntimeError:
                    # Manually move up to the parent if getting the evidence item fails
                    logging.warn('Failed to get parent pathspec evidence item, manually moving up another pathspec')
                    evidence_parent = json.loads(evidence_parent)['parent']
                    evidence = helper.pathspec_helper.get_evidence_item(json.dumps(evidence_parent))
                return self.get(evidence, helper, path_on_disk, request)
            # If only one item (volume/partition/etc) go ahead and expand it
            elif len(items) == 1:
                items = helper.pathspec_helper.list_directory(items[0]['pathspec'])
            else:
                force_expand = True

            initial_pathspec = evidence['pathspec']
        # Directories
        else:
            initial_pathspec = evidence['pathspec']

            while initial_pathspec and not getattr(helper.pathspec_helper._decode_pathspec(initial_pathspec), 'location', False):
                initial_pathspec = helper.pathspec_helper.get_encoded_parent_base_pathspec_manually(initial_pathspec)

            items = helper.pathspec_helper.list_directory(initial_pathspec)

        # Gets the List of sub items to display
        for item in items:
            # Compressed files do not have file_names, and get the parent name minus the last extension
            if 'compression_type' in evidence:
                if 'file_name' not in item or not item['file_name']:
                    item['file_name'] = os.path.splitext(evidence['file_name'])[0]
            # If the file does not have a file name set it to '-' for the link
            if 'file_name' not in item or not item['file_name']:
                item['file_name'] = '-'

            # Remove nanoseconds for readability, values will be available on the overview page
            for time in ['mtime', 'atime', 'ctime', 'crtime']:
                if time in item:
                    item[time + '_no_nano'] = item[time].split('.')[0].replace('T', ' ')

            # Make human readable size
            if 'size' in item:
                item['size'] = Directory.human_readable_size(int(item['size']))

            # Get the icon here to limit the number of calls
            if not force_expand:
                item['icon'] = helper.get_icon(item)
            else:
                item['icon'] = '/resources/icons/_evidence.png'

            # Render analyze link
            item['analyze'] = analyze_template.render(item)

            # Expandable evidence
            if helper.is_expandable_evidence(item) or force_expand:
                item['order'] = 3
                item['plugin'] = self._evidence_plugin
                item['download'] = download_template.render(item)
                item['preview'] = preview_template.render(item)
                file_table.append(row_template.render(item))
            # Directories
            elif item['meta_type'] == 'Directory':
                item['order'] = 2
                item['plugin'] = self._dir_plugin
                dir_table.append(row_template.render(item))
            # Files/Other
            else:
                item['order'] = 3
                item['target'] = 'target="_top"'
                item['plugin'] = self._file_plugin
                item['download'] = download_template.render(item)
                item['preview'] = preview_template.render(item)
                file_table.append(row_template.render(item))

        # Presorts the tables
        dir_table.sort()
        file_table.sort()

        # Gets the up directory option ".."
        parent_pathspec = helper.pathspec_helper.get_parent_pathspec(initial_pathspec)
        if parent_pathspec:
            try:
                parent_item = helper.pathspec_helper.get_evidence_item(parent_pathspec)
            # Manually move up to the parent if getting the evidence item fails
            except RuntimeError:
                logging.warn('Failed to get parent pathspec evidence item, manually moving up another pathspec')
                parent_pathspec = json.loads(parent_pathspec)['parent']
                parent_item = helper.pathspec_helper.get_evidence_item(json.dumps(parent_pathspec))
        if parent_pathspec and parent_item:
            parent_item['file_name'] = '..'
            parent_item['icon'] = '/resources/icons/_folder_up.png'
            parent_item['order'] = 1
            parent_item['plugin'] = self._dir_plugin
            parent_item['url_query'] = parent_item['url_query'] + '&up=True'
            dir_table.insert(0, row_template.render(parent_item))

        return '''
                <!DOCTYPE html>
                <html>
                <head>
                        <script src="/resources/jquery-1.11.3.min.js"></script>
                        <script src="/resources/jquery-ui-1.11.4/jquery-ui.min.js" type="text/javascript"></script>
                        <link rel="stylesheet" type="text/css" href="/resources/themes/icon.css">
                        <link rel="stylesheet" type="text/css" href="/resources/themes/jquery.dataTables.min.css">
                        <link rel="stylesheet" href="/resources/font-awesome/css/font-awesome.min.css">
                        <script type="text/javascript" src="/resources/jquery.dataTables.min.js"></script>
                        <script type="text/javascript" class="init">
                            jQuery.extend( jQuery.fn.dataTableExt.oSort, {
                                "alt-string-pre": function ( a ) {
                                    return a.match(/alt="(.*?)"/)[1].toLowerCase();
                                },

                                "alt-string-asc": function( a, b ) {
                                    return ((a < b) ? -1 : ((a > b) ? 1 : 0));
                                },

                                "alt-string-desc": function(a,b) {
                                    return ((a < b) ? 1 : ((a > b) ? -1 : 0));
                                }
                            } );
                            jQuery.fn.dataTable.ext.type.order['file-size-pre'] = function ( data ) {
                                var matches = data.match( /^(\d+(?:\.\d+)?)\s*([a-z]+)/i );
                                var multipliers = {
                                    b:  1,
                                    kb: 1000,
                                    kib: 1024,
                                    mb: 1000000,
                                    mib: 1048576,
                                    gb: 1000000000,
                                    gib: 1073741824,
                                    tb: 1000000000000,
                                    tib: 1099511627776,
                                    pb: 1000000000000000,
                                    pib: 1125899906842624
                                };

                                if (matches) {
                                    var multiplier = multipliers[matches[2].toLowerCase()];
                                    return parseFloat( matches[1] ) * multiplier;
                                } else {
                                    return -1;
                                };
                            };
                            $(document).ready(function() {
                                    $('#t01').DataTable({
                                            "paging": false,
                                            "info": false,
                                            "orderClasses": false,
                                            "searching": false,
                                            "columnDefs": [
                                                    { type: 'alt-string', targets: 0 },
                                                    { type: 'file-size', targets: 6 }
                                                ]
                                            }
                                    );
                            } );
                        </script>
                <style>
                    table.dataTable thead th {
                        position: relative;
                        background-image: none !important;
                    }
                    table.dataTable thead th.sorting:after,
                    table.dataTable thead th.sorting_asc:after,
                    table.dataTable thead th.sorting_desc:after {
                        position: absolute;
                        top: 12px;
                        right: 8px;
                        display: block;
                        font-family: FontAwesome;
                    }
                    table.dataTable thead th.sorting:after {
                        content: "\\f0dc";
                        color: #ddd;
                        font-size: 0.8em;
                        padding-top: 0.12em;
                    }
                    table.dataTable thead th.sorting_asc:after {
                        content: "\\f0de";
                    }
                    table.dataTable thead th.sorting_desc:after {
                        content: "\\f0dd";
                    }
                    table {
                        overflow-y: scroll;
                        width: 100%;
                    }
                    table, th, td {
                        border: 0px;
                        border-collapse: collapse;
                    }
                    th, td {
                        padding: 5px;
                        text-align: left;
                    }
                    table#t01 tr:nth-child(even) {
                        background-color: #fff;
                    }
                    table#t01 tr:nth-child(odd) {
                       background-color:#eee;
                    }
                    table#t01 th {
                        background-color: #444;
                        color: white;
                    }
                    html{
                        height: 100%;
                    }
                    body {
                        min-height: 100%;
                        margin: 0px;
                    }
                    a {
                        text-decoration: none;
                    }
                    a:link {
                        color: #0c006b;
                    }
                    a:visited {
                        color: #0c006b;
                    }
                    a:hover {
                        color: rgb(153, 193, 255);
                    }

                </style>
                </head>
                    <body>
                       <table id="t01" class="display">
                            <thead>
                            <tr>
                                <th>Icon</th>
                                <th>File Name</th>
                                <th>Modified</th>
                                <th>Accessed</th>
                                <th>Changed</th>
                                <th>Created</th>
                                <th>Size</th>
                                <th>Options</th>
                            </tr>
                            </thead>
                            <tbody>'''\
                            + '\n'.join(dir_table) + '\n'.join(file_table) + '</tbody><table>' + \
               '''  </body>
               </html>'''
