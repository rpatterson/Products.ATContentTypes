#  ATContentTypes http://sf.net/projects/collective/
#  Archetypes reimplementation of the CMF core types
#  Copyright (c) 2003-2005 AT Content Types development team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""

"""
__author__  = ''
__docformat__ = 'restructuredtext'

from urllib import quote

from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from AccessControl import ClassSecurityInfo
from Acquisition import aq_parent
from OFS.Image import File

from Products.Archetypes.public import Schema
from Products.Archetypes.public import FileField
from Products.Archetypes.public import FileWidget
from Products.Archetypes.public import PrimaryFieldMarshaller
from Products.Archetypes.BaseContent import BaseContent
from Products.PortalTransforms.utils import TransformException

from Products.ATContentTypes.config import PROJECTNAME
from Products.ATContentTypes.config import MAX_FILE_SIZE
from Products.ATContentTypes.config import ICONMAP
from Products.ATContentTypes import Permissions as ATCTPermissions
from Products.ATContentTypes.types.ATContentType import registerATCT
from Products.ATContentTypes.types.ATContentType import ATCTFileContent
from Products.ATContentTypes.interfaces import IATFile
from Products.ATContentTypes.types.schemata import ATContentTypeSchema
from Products.ATContentTypes.types.schemata import relatedItemsField
from Products.ATContentTypes.types.schemata import urlUploadField
from Products.validation.validators.SupplValidators import MaxSizeValidator

ATFileSchema = ATContentTypeSchema.copy() + Schema((
    FileField('file',
              required=True,
              primary=True,
              languageIndependent=True,
              validators = MaxSizeValidator('checkFileMaxSize',
                                            maxsize=MAX_FILE_SIZE),
              widget = FileWidget(
                        #description = "Select the file to be added by clicking the 'Browse' button.",
                        #description_msgid = "help_file",
                        description = "",
                        label= "File",
                        label_msgid = "label_file",
                        i18n_domain = "plone",
                        show_content_type = False,)),
    ), marshall=PrimaryFieldMarshaller()
    )
ATFileSchema.addField(urlUploadField)
ATFileSchema.addField(relatedItemsField)


class ATFile(ATCTFileContent):
    """A Archetype derived version of CMFDefault's File"""

    schema         =  ATFileSchema

    content_icon   = 'file_icon.gif'
    meta_type      = 'ATFile'
    portal_type    = 'File'
    archetype_name = 'File'
    immediate_view = 'file_view'
    default_view   = 'file_view'
    suppl_views    = ()
    _atct_newTypeFor = {'portal_type' : 'CMF File', 'meta_type' : 'Portal File'}
    typeDescription= "Add the relevant details of the file to be added in the form below,\n" \
                     "select the file with the 'Browse' button, and press 'Save'."
    typeDescMsgId  = 'description_edit_file'
    assocMimetypes = ('application/*', 'audio/*', 'video/*', )
    assocFileExt   = ()
    cmf_edit_kws   = ()

    __implements__ = ATCTFileContent.__implements__, IATFile

    security       = ClassSecurityInfo()

    security.declareProtected(CMFCorePermissions.View, 'index_html')
    def index_html(self, REQUEST, RESPONSE):
        """Download the file
        """
        field = self.getPrimaryField()
        return field.download(self)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'setFile')
    def setFile(self, value, **kwargs):
        """Set id to uploaded id
        """
        self._setATCTFileContent(value, **kwargs)

    def __str__(self):
        """cmf compatibility
        """
        return self.get_data()

    security.declarePublic('getIcon')
    def getIcon(self, relative_to_portal=0):
        """Calculate the icon using the mime type of the file
        """
        field = self.getField('file')
        if not field or not self.get_size():
            # field is empty
            return BaseContent.getIcon(self, relative_to_portal)

        contenttype       = field.getContentType(self)
        contenttype_major = contenttype and contenttype.split('/')[0] or ''

        mtr   = getToolByName(self, 'mimetypes_registry', None)
        utool = getToolByName( self, 'portal_url' )

        if ICONMAP.has_key(contenttype):
            icon = quote(ICONMAP[contenttype])
        elif ICONMAP.has_key(contenttype_major):
            icon = quote(ICONMAP[contenttype_major])
        else:
            mimetypeitem = mtr.lookup(contenttype)
            if not mimetypeitem:
                return BaseContent.getIcon(self, relative_to_portal)
            icon = mimetypeitem[0].icon_path

        if relative_to_portal:
            return icon
        else:
            # Relative to REQUEST['BASEPATH1']
            res = utool(relative=1) + '/' + icon
            while res[:1] == '/':
                res = res[1:]
            return res

    security.declareProtected(CMFCorePermissions.View, 'icon')
    def icon(self):
        """for ZMI
        """
        return self.getIcon()

    security.declarePrivate('txng_get')
    def txng_get(self, attr=('SearchableText',)):
        """Special searchable text source for text index ng 2
        """
        if attr[0] != 'SearchableText':
            # only a hook for searchable text
            return

        source   = ''
        mimetype = 'text/plain'
        encoding = 'utf-8'

        # stage 1: get the searchable text and convert it to utf8
        sp    = getToolByName(self, 'portal_properties').site_properties
        stEnc = getattr(sp, 'default_charset', 'utf-8')
        st    = self.SearchableText()
        source+=unicode(st, stEnc).encode('utf-8')

        # get the file and try to convert it to utf8 text
        ptTool = getToolByName(self, 'portal_transforms')
        f  = self.getFile()
        if f:
            mt = f.getContentType()
            try:
                result = ptTool.convertTo('text/plain', str(f), mimetype=mt)
                if result:
                    data = result.getData()
                else:
                    data = ''
            except TransformException:
                data = ''
            source+=data

        return source, mimetype, encoding

    security.declarePrivate('cmf_edit')
    def cmf_edit(self, precondition='', file=None):
        if file is not None:
            self.setFile(file)

registerATCT(ATFile, PROJECTNAME)
