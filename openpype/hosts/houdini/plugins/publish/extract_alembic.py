import os

import pyblish.api
import openpype.api
from openpype.hosts.houdini.api.lib import render_rop


class ExtractAlembic(openpype.api.Extractor):

    order = pyblish.api.ExtractorOrder
    label = "Extract Alembic"
    hosts = ["houdini"]
    families = ["pointcache", "camera"]

    def process(self, instance):

        ropnode = instance[0]

        # Get the filename from the filename parameter
        output = ropnode.evalParm("filename")
        staging_dir = os.path.dirname(output)
        instance.data["stagingDir"] = staging_dir

        file_name = os.path.basename(output)

        # We run the render
        self.log.info("Writing alembic '%s' to '%s'" % (file_name,
                                                        staging_dir))

        render_rop(ropnode)

        if "representations" not in instance.data:
            instance.data["representations"] = []

        representation = {
            'name': 'abc',
            'ext': 'abc',
            'files': file_name,
            "stagingDir": staging_dir,
        }
        instance.data["representations"].append(representation)
