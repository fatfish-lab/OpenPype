from .item_entities import ItemEntity
from .constants import OverrideState
from .lib import (
    NOT_SET,
    DefaultsNotDefined
)


class ListEntity(ItemEntity):
    schema_types = ["list"]

    def __iter__(self):
        for item in self.children:
            yield item

    def append(self, item):
        child_obj = self.add_new_item()
        child_obj.set_override_state(self.override_state)
        child_obj.set_value(item)
        self.on_change()

    def extend(self, items):
        for item in items:
            self.append(item)

    def clear(self):
        self.children.clear()
        self.on_change()

    def pop(self, idx):
        item = self.children.pop(idx)
        self.on_change()
        return item

    def remove(self, item):
        for idx, child_obj in enumerate(self.children):
            if child_obj.value == item:
                self.pop(idx)
                return
        raise ValueError("ListEntity.remove(x): x not in ListEntity")

    def insert(self, idx, item):
        child_obj = self.add_new_item(idx)
        child_obj.set_override_state(self.override_state)
        child_obj.set_value(item)
        self.on_change()

    def add_new_item(self, idx=None):
        child_obj = self.create_schema_object(self.item_schema, self, True)
        if idx is None:
            self.children.append(child_obj)
        else:
            self.children.insert(idx, child_obj)
        return child_obj

    def item_initalization(self):
        self.valid_value_types = (list, )
        self.children = []

        item_schema = self.schema_data["object_type"]
        if not isinstance(item_schema, dict):
            item_schema = {"type": item_schema}
        self.item_schema = item_schema

        if not self.group_item:
            self.is_group = True

        # Value that was set on set_override_state
        self.initial_value = []

        # GUI attributes
        self.use_label_wrap = self.schema_data.get("use_label_wrap") or False
        # Used only if `use_label_wrap` is set to True
        self.collapsible = self.schema_data.get("collapsible") or True
        self.collapsed = self.schema_data.get("collapsed") or False

    def schema_validations(self):
        super(ListEntity, self).schema_validations()

        if self.is_dynamic_item and self.use_label_wrap:
            raise ValueError(
                "`ListWidget` can't have set `use_label_wrap` to True and"
                " be used as widget at the same time."
            )

        if self.use_label_wrap and not self.label:
            raise ValueError(
                "`ListWidget` can't have set `use_label_wrap` to True and"
                " not have set \"label\" key at the same time."
            )

        for child_obj in self.children:
            child_obj.schema_validations()

    def get_child_path(self, child_obj):
        result_idx = None
        for idx, _child_obj in enumerate(self.children):
            if _child_obj is child_obj:
                result_idx = idx
                break

        if result_idx is None:
            raise ValueError("Didn't found child {}".format(child_obj))

        return "/".join([self.path, str(result_idx)])

    def set_value(self, value):
        self.clear()
        for item in value:
            self.append(value)

    def on_change(self):
        value_is_modified = None
        if self.override_state is OverrideState.PROJECT:
            # Only value change
            if (
                self._has_project_override
                and self.project_override_value is not NOT_SET
            ):
                value_is_modified = (
                    self._current_value != self.project_override_value
                )

        if (
            self.override_state is OverrideState.STUDIO
            or value_is_modified is None
        ):
            if (
                self._has_studio_override
                and self.studio_override_value is not NOT_SET
            ):
                value_is_modified = (
                    self._current_value != self.studio_override_value
                )

        if value_is_modified is None:
            value_is_modified = self._current_value != self.default_value

        self.value_is_modified = value_is_modified

        for callback in self.on_change_callbacks:
            callback()
        self.parent.on_child_change(self)

    def on_child_change(self, child_obj):
        # TODO is this enough?
        if self.override_state is OverrideState.STUDIO:
            self._has_studio_override = self.child_has_studio_override
        elif self.override_state is OverrideState.PROJECT:
            self._has_project_override = self.child_has_project_override
        self.on_change()

    def on_value_change(self):
        raise NotImplementedError(self.__class__.__name__)

    def set_override_state(self, state):
        self.override_state = state

        while self.children:
            self.children.pop(0)

        if not self.has_default_value and state > OverrideState.DEFAULTS:
            raise DefaultsNotDefined(self)

        value = NOT_SET
        if self.override_state is OverrideState.PROJECT:
            if self.had_project_override:
                value = self.project_override_value
            self._has_project_override = self.had_project_override

        if value is NOT_SET or self.override_state is OverrideState.STUDIO:
            if self.had_studio_override:
                value = self.studio_override_value
            self._has_studio_override = self.had_studio_override

        if value is NOT_SET or self.override_state is OverrideState.DEFAULTS:
            if self.has_default_value:
                value = self.default_value
            else:
                value = self.value_on_not_set

        for item in value:
            child_obj = self.add_new_item()
            child_obj.update_default_value(item)
            if self.override_state is OverrideState.PROJECT:
                if self.had_project_override:
                    child_obj.update_project_values(item)
                elif self.had_studio_override:
                    child_obj.update_studio_values(item)

            elif self.override_state is OverrideState.STUDIO:
                if self.had_studio_override:
                    child_obj.update_studio_values(item)

        for child_obj in self.children:
            child_obj.set_override_state(self.override_state)

        self.initial_value = self.settings_value()

    @property
    def value(self):
        output = []
        for child_obj in self.children:
            output.append(child_obj.value)
        return output

    @property
    def has_unsaved_changes(self):
        if self.override_state is OverrideState.NOT_DEFINED:
            return False

        if self.override_state is OverrideState.DEFAULTS:
            if not self.has_default_value:
                return True

        elif self.override_state is OverrideState.STUDIO:
            if self.had_studio_override != self._has_studio_override:
                return True

            if not self._has_studio_override and not self.has_default_value:
                return True

        elif self.override_state is OverrideState.PROJECT:
            if self.had_project_override != self._has_project_override:
                return True

            if (
                not self._has_project_override
                and not self._has_studio_override
                and not self.has_default_value
            ):
                return True

        if self.child_is_modified:
            return True

        if self.settings_value() != self.initial_value:
            return True
        return False

    @property
    def child_is_modified(self):
        for child_obj in self.children:
            if child_obj.has_unsaved_changes:
                return True
        return False

    @property
    def child_has_studio_override(self):
        if self.override_state >= OverrideState.STUDIO:
            for child_obj in self.children:
                if child_obj.has_studio_override:
                    return True
        return False

    @property
    def child_has_project_override(self):
        if self.override_state is OverrideState.PROJECT:
            for child_obj in self.children:
                if child_obj.has_project_override:
                    return True
        return False

    def settings_value(self):
        if self.override_state is OverrideState.NOT_DEFINED:
            return NOT_SET

        if self.is_group:
            if self.override_state is OverrideState.STUDIO:
                if not self._has_studio_override:
                    return NOT_SET
            elif self.override_state is OverrideState.PROJECT:
                if not self._has_project_override:
                    return NOT_SET

        output = []
        for child_obj in self.children:
            output.append(child_obj.settings_value())
        return output

    def discard_changes(self):
        pass

    def remove_overrides(self):
        pass

    def reset_to_pype_default(self):
        pass

    def set_as_overriden(self):
        pass

    def set_studio_default(self):
        pass

    def update_default_value(self, value):
        self.has_default_value = value is not NOT_SET
        self.default_value = value

    def update_studio_values(self, value):
        self.had_studio_override = value is not NOT_SET
        self.studio_override_value = value

    def update_project_values(self, value):
        self.had_project_override = value is not NOT_SET
        self.project_override_value = value
