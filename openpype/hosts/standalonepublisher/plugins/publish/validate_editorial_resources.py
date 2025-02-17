import pyblish.api
import openpype.api


class ValidateEditorialResources(pyblish.api.InstancePlugin):
    """Validate there is a "mov" next to the editorial file."""

    label = "Validate Editorial Resources"
    hosts = ["standalonepublisher"]
    families = ["clip", "trimming"]

    # make sure it is enabled only if at least both families are available
    match = pyblish.api.Subset

    order = openpype.api.ValidateContentsOrder

    def process(self, instance):
        self.log.debug(
            f"Instance: {instance}, Families: "
            f"{[instance.data['family']] + instance.data['families']}")
        check_file = instance.data["editorialSourcePath"]
        msg = f"Missing \"{check_file}\"."
        assert check_file, msg
