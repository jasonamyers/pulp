"""
This module contains transfer objects for encapsulating data passed into a
plugin method call. Objects defined in this module will have extra information
bundled in that is relevant to the plugin's state for the given entity.
"""
from pulp.server import constants


class Repository(object):
    """
    Contains repository data and any additional data relevant for the plugin to
    function.

    :ivar id: programmatic ID for the repository
    :type id: str

    :ivar display_name: user-friendly name describing the repository
    :type display_name: str or None

    :ivar description: user-friendly description of the repository
    :type description: str or None

    :ivar notes: arbitrary key-value pairs set and used by users to
                 programmatically describe the repository
    :type notes: dict or None

    :ivar working_dir: local (to the Pulp server) directory the plugin may use
          to store any temporary data required by the plugin; this directory
          is unique for each repository and plugin combination
    :type working_dir: str

    :ivar content_unit_counts: dictionary of unit types and the count of units
                               of that type associated with the repository.
    :type content_unit_counts: dict

    :param last_unit_added: UTC datetime of the last time a unit was added to the repository
    :type last_unit_added: datetime.datetime  with tzinfo

    :param last_unit_removed: UTC datetime of the last time a unit was removed from the repository
    :param last_unit_removed: datetime.datetime with tzinfo
    """

    def __init__(self, id, display_name=None, description=None, notes=None,
                 working_dir=None, content_unit_counts=None, last_unit_added=None,
                 last_unit_removed=None):
        self.id = id
        self.display_name = display_name
        self.description = description
        self.notes = notes
        self.working_dir = working_dir
        self.content_unit_counts = content_unit_counts or {}
        self.last_unit_added = last_unit_added
        self.last_unit_removed = last_unit_removed

    def __str__(self):
        return 'Repository [%s]' % self.id


class RelatedRepository(Repository):
    """
    When validating a plugin configuration, instances of this class will
    describe other repositories that share the same plugin type as the
    plugin being configured. This class will describe the basic repository
    metadata for one such repository and information on that repo's
    configuration for the plugin. If the repository has multiple associations
    to the given plugin type, a list of configurations will be returned.
    """

    def __init__(self, id, plugin_configs, display_name=None, description=None, notes=None):
        Repository.__init__(self, id, display_name, description, notes)
        self.plugin_configs = plugin_configs


class RepositoryGroup(object):
    """
    Contains repository group data and any additional data relevant for the
    plugin to function.

    @ivar id: programmatic ID for the repository group
    @type id: str

    @ivar display_name: user-friendly name describing the repository group
    @type display_name: str

    @ivar description: user-friendly description of the repository group
    @type description: str

    @ivar notes: arbitrary key-value pairs set and used by users to
                 programmatically describe the repository
    @type notes: dict

    @ivar working_dir: local (to the Pulp server) directory the plugin may use
          to store any temporary data required by the plugin; this directory
          is unique for each repository and plugin combination
    @type working_dir: str
    """

    def __init__(self, id, display_name, description, notes, repo_ids, working_dir=None):
        self.id = id
        self.display_name = display_name
        self.description = description
        self.notes = notes
        self.repo_ids = repo_ids
        self.working_dir = working_dir

    def __str__(self):
        return 'Repository Group [%s]' % self.id


class RelatedRepositoryGroup(RepositoryGroup):
    """
    When validating a plugin configuration, instances of this class will
    describe other repository groups that share the same plugin type as the
    plugin being configured. This class will describe the basic repository
    group metadata for each group and information on that repository group's
    configuration for the plugin. If the group has multiple associations to
    the given plugin type, a list of configurations will be returned.
    """

    def __init__(self, id, plugin_configs, display_name, description, notes, working_dir=None):
        super(RelatedRepositoryGroup, self).__init__(id, display_name,
                                                     description, notes,
                                                     working_dir)
        self.plugin_configs = plugin_configs


class Unit(object):
    """
    Contains information related to a single content unit. The unit may or
    may not exist in Pulp; this is meant simply as a way of linking together
    a number of pieces of data.

    @ivar type_id: ID of the unit's type
    @type type_id: str

    @ivar unit_key: natural key for the content unit
    @type unit_key: dict

    @ivar metadata: mapping of key/value pairs describing the unit
    @type metadata: dict

    @ivar storage_path: full path to where on disk the unit is stored, including the filename
    @type storage_path: str
    """

    def __init__(self, type_id, unit_key, metadata, storage_path):
        self.type_id = type_id
        self.unit_key = unit_key
        self.metadata = metadata

        # We want to ensure that all units have a pulp_user_metadata attribute in their metadata. If
        # not supplied, we want to default it to the empty dictionary.
        if constants.PULP_USER_METADATA_FIELDNAME not in self.metadata:
            self.metadata[constants.PULP_USER_METADATA_FIELDNAME] = {}

        self.storage_path = storage_path

        self.id = None

    def to_id_dict(self):
        """
        Returns a dict with the identity information (type ID and unit key) for this unit. The
        primary intention of this method is as a means to convert these units into a JSON
        serializable format.
        """

        return {'type_id': self.type_id, 'unit_key': self.unit_key}

    def __eq__(self, other):
        return (self.unit_key == other.unit_key) and (self.type_id == other.type_id)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return 'Unit [key=%s] [type=%s] [id=%s]' % (self.unit_key, self.type_id, self.id)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        """
        This should provide a consistent and unique hash where units of the same
        type and the same unit key will get the same hash value.
        """
        return hash(self.type_id + str(sorted(self.unit_key.items())))


class AssociatedUnit(Unit):
    """
    Adds association metadata on top of normal unit data.
    """

    def __init__(self, type_id, unit_key, metadata, storage_path, created, updated,
                 owner_type, owner_id):
        Unit.__init__(self, type_id, unit_key, metadata, storage_path)

        self.created = created
        self.updated = updated
        self.owner_type = owner_type
        self.owner_id = owner_id


class SyncReport(object):
    """
    Returned to the Pulp server at the end of a sync call. This is used by the
    plugin to describe what took place during the sync.

    :ivar success_flag:  if true, the sync was successful; false indicates a gracefully handled
                         failure
    :type success_flag:  bool
    :ivar added_count:   number of new units added during the sync
    :type added_count:   int
    :ivar updated_count: number of units updated during the sync
    :type updated_count: int
    :ivar removed_count: number of units unassociated from the repo during the sync
    :type removed_count: int
    :ivar summary:       arbitrary value that will be returned by default as the log for the sync
                         (should be short)
    :type summary:       just about any serializable object (likely str or dict)
    :ivar details:       potentially longer log that will have to be specifically retrieved through
                         the Pulp REST APIs
    :type details:       just about any serializable object (likely str or dict)
    """
    def __init__(self, success_flag, added_count, updated_count, removed_count, summary, details):
        self.success_flag = success_flag
        self.canceled_flag = False
        self.added_count = added_count
        self.updated_count = updated_count
        self.removed_count = removed_count
        self.summary = summary
        self.details = details


class PublishReport(object):
    """
    Returned to the Pulp server at the end of a publish call. This is used by the
    plugin to derive what took place during the publish run.

    @ivar success_flag: if true, the sync was successful; false indicates a
          gracefully handled failure
    @type success_flag: bool

    @ivar summary: arbitrary value that will be returned by default as the log
                   for the call (should be short)
    @type summary: just about any serializable object (likely str or dict)

    @ivar details: potentially longer log that will have to be specifically
                   retrieved through the Pulp REST APIs
    @type details: just about any serializable object (likely str or dict)
    """

    def __init__(self, success_flag, summary, details):
        self.success_flag = success_flag
        self.canceled_flag = False
        self.summary = summary
        self.details = details


class Consumer:
    """
    A profiled consumer.

    @ivar id: The consumer ID.
    @type id: str

    @param profiles: A dictionary of profiles keyed by content type.
    @type profiles: dict
    """

    def __init__(self, id, profiles):
        self.id = id
        self.profiles = profiles
