# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from random import choice
from warnings import warn

from mvc import Observer, PropIntel
from mvc.observers import ListObserver

from pyxrd.file_parsers.json_parser import JSONParser
from pyxrd.generic.io import storables, get_case_insensitive_glob
from pyxrd.refinement.refinables.mixins import RefinementGroup
from pyxrd.refinement.refinables.metaclasses import PyXRDRefinableMeta

from pyxrd.probabilities.models import get_correct_probability_model

from .abstract_phase import AbstractPhase
from .CSDS import DritsCSDSDistribution
from .component import Component

@storables.register()
class Phase(RefinementGroup, AbstractPhase):

    # MODEL INTEL:
    __metaclass__ = PyXRDRefinableMeta
    class Meta(AbstractPhase.Meta):
        properties = [
            PropIntel(name="based_on", data_type=object, label="Based on phase", is_column=True, has_widget=True, widget_type='custom'),
            PropIntel(name="sigma_star", data_type=float, label=u"σ* [°]", math_label="$\sigma^*$ [°]", is_column=True, has_widget=True, storable=True, refinable=True, minimum=0.0, maximum=90.0, inh_name="inherit_sigma_star", stor_name="_sigma_star", inh_from="based_on"),
            PropIntel(name="display_color", data_type=str, label="Display color", is_column=True, has_widget=True, widget_type='color', storable=True, inh_name="inherit_display_color", stor_name="_display_color", inh_from="based_on"),
            PropIntel(name="inherit_sigma_star", data_type=bool, label="Inh. sigma star", is_column=True, has_widget=True, storable=True),
            PropIntel(name="inherit_display_color", data_type=bool, label="Inh. display color", is_column=True, has_widget=True, storable=True),
            PropIntel(name="inherit_CSDS_distribution", data_type=bool, label="Inh. mean CSDS", is_column=True, has_widget=True, storable=True),
            PropIntel(name="CSDS_distribution", data_type=object, label="CSDS Distribution", is_column=True, has_widget=True, storable=True, refinable=True, widget_type="custom", inh_name="inherit_CSDS_distribution", stor_name="_CSDS_distribution", inh_from="based_on"),
            PropIntel(name="probabilities", data_type=object, label="Probabilities", is_column=True, has_widget=True, storable=True, refinable=True, widget_type="custom"),
            PropIntel(name="components", data_type=object, label="Components", is_column=True, has_widget=True, storable=True, refinable=True, widget_type="custom", class_type=Component),
        ]
        store_id = "Phase"
        file_filters = [
            ("Phase file", get_case_insensitive_glob("*.PHS")),
        ]

    _data_object = None
    @property
    def data_object(self):
        self._data_object.type = "Phase"
        self._data_object.valid_probs = (all(self.probabilities.P_valid) and all(self.probabilities.W_valid))

        if self._data_object.valid_probs:
            self._data_object.sigma_star = self.sigma_star
            self._data_object.CSDS = self.CSDS_distribution.data_object

            self._data_object.G = self.G
            self._data_object.W = self.probabilities.get_distribution_matrix()
            self._data_object.P = self.probabilities.get_probability_matrix()

            self._data_object.components = [None] * len(self.components)
            for i, comp in enumerate(self.components):
                self._data_object.components[i] = comp.data_object
        else:
            self._data_object.sigma_star = None
            self._data_object.CSDS = None
            self._data_object.G = None
            self._data_object.W = None
            self._data_object.P = None
            self._data_object.components = None

        return self._data_object

    project = property(AbstractPhase.parent.fget, AbstractPhase.parent.fset)

    # PROPERTIES:
    def get_inherit_CSDS_distribution(self): return self._CSDS_distribution.inherited
    def set_inherit_CSDS_distribution(self, value): self._CSDS_distribution.inherited = value

    _inherit_display_color = False
    def get_inherit_display_color(self): return self._inherit_display_color
    def set_inherit_display_color(self, value):
        with self.visuals_changed.hold_and_emit():
            self._inherit_display_color = bool(value)

    _inherit_sigma_star = False
    def get_inherit_sigma_star(self): return self._inherit_sigma_star
    def set_inherit_sigma_star(self, value):
        try:
            value = bool(value)
        except ValueError:
            pass
        else:
            if value != self._inherit_sigma_star:
                with self.data_changed.hold_and_emit():
                    self._inherit_sigma_star = value

    _based_on_index = None # temporary property
    _based_on_uuid = None # temporary property
    _based_on = None
    def get_based_on(self): return self._based_on
    def set_based_on(self, value):
        with self.data_changed.hold():
            if self._based_on is not None:
                self.relieve_model(self._based_on)
            if value == None or value.get_based_on_root() == self or value.parent != self.parent:
                value = None
            if value != self._based_on:
                self._based_on = value
                for component in self.components:
                    component.linked_with = None
                self.data_changed.emit()
            if self._based_on is not None:
                self.observe_model(self._based_on)
            else:
                for prop in self.Meta.get_inheritable_properties():
                    setattr(self, prop.inh_name, False)
                for prop in self.probabilities.Meta.get_inheritable_properties():
                    setattr(self.probabilities, prop.inh_name, False)

    def get_based_on_root(self):
        if self.based_on is not None:
            return self.based_on.get_based_on_root()
        else:
            return self

    # INHERITABLE PROPERTIES:
    _sigma_star = 12.0
    def get_sigma_star(self): return self._get_inheritable_property_value("sigma_star")
    def set_sigma_star(self, value):
        value = float(value)
        if self._sigma_star != value:
            with self.data_changed.hold_and_emit():
                self._sigma_star = value

    _CSDS_distribution = None
    def get_CSDS_distribution(self): return self._get_inheritable_property_value("CSDS_distribution")
    def set_CSDS_distribution(self, value):
        with self.data_changed.hold_and_emit():
            if self._CSDS_distribution:
                self.relieve_model(self._CSDS_distribution)
                self._CSDS_distribution.parent = None
            self._CSDS_distribution = value
            if self._CSDS_distribution:
                self._CSDS_distribution.parent = self
                self.observe_model(self._CSDS_distribution)


    _probabilities = None
    def get_probabilities(self): return self._get_inheritable_property_value("probabilities")
    def set_probabilities(self, value):
        with self.data_changed.hold_and_emit():
            if self._probabilities:
                self.relieve_model(self._probabilities)
                self._probabilities.parent = None
            self._probabilities = value
            if self._probabilities:
                self._probabilities.update()
                self._probabilities.parent = self
                self.observe_model(self._probabilities)

    _display_color = "#FFB600"
    def get_display_color(self): return self._get_inheritable_property_value("display_color")
    def set_display_color(self, value):
        if self._display_color != value:
            with self.visuals_changed.hold_and_emit():
                self._display_color = value

    components = []

    def get_G(self):
        if self.components is not None:
            return len(self.components)
        else:
            return 0
    G = property(get_G, AbstractPhase.G.fset) #@UndefinedVariable


    def get_R(self):
        if self.probabilities:
            return self.probabilities.R
    G = property(get_G, AbstractPhase.R.fset) #@UndefinedVariable

    # Flag indicating whether or not the links (based_on and linked_with) should
    # be saved as well.
    save_links = True

    # REFINEMENT GROUP IMPLEMENTATION:
    @property
    def refine_title(self):
        return self.name

    @property
    def refine_descriptor_data(self):
        return dict(
            phase_name=self.refine_title,
            component_name="*"
        )

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):

        my_kwargs = self.pop_kwargs(kwargs,
            "data_CSDS_distribution", "data_sigma_star", "data_components",
            "data_G", "G", "data_R", "R",
            "data_probabilities", "based_on_uuid", "based_on_index",
            "inherit_probabilities",
            *[names[0] for names in Phase.Meta.get_local_storable_properties()]
        )
        super(Phase, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.data_changed.hold():

            CSDS_distribution = self.get_kwarg(kwargs, None, "CSDS_distribution", "data_CSDS_distribution")
            self.CSDS_distribution = self.parse_init_arg(
                CSDS_distribution, DritsCSDSDistribution, child=True,
                default_is_class=True, parent=self
            )
            self.inherit_CSDS_distribution = self.get_kwarg(kwargs, False, "inherit_CSDS_distribution")

            self.display_color = self.get_kwarg(kwargs, choice(self.line_colors), "display_color")
            self.inherit_display_color = self.get_kwarg(kwargs, False, "inherit_display_color")

            self.sigma_star = self.get_kwarg(kwargs, self._sigma_star, "sigma_star", "data_sigma_star")
            self.inherit_sigma_star = self.get_kwarg(kwargs, False, "inherit_sigma_star")

            self.components = self.get_list(kwargs, [], "components", "data_components", parent=self)

            G = self.get_kwarg(kwargs, 1, "G", "data_G")
            R = self.get_kwarg(kwargs, 0, "R", "data_R")
            if G is not None and G > 0:
                for i in range(len(self.components), G):
                    new_comp = Component(name="Component %d" % (i + 1), parent=self)
                    self.components.append(new_comp)
                    self.observe_model(new_comp)

            # Observe components
            for component in self.components:
                self.observe_model(component)

            # Connect signals to lists and dicts:
            self._components_observer = ListObserver(
                self.on_component_inserted,
                self.on_component_removed,
                prop_name="components",
                model=self
            )

            self.probabilities = self.parse_init_arg(
                self.get_kwarg(kwargs, None, "probabilities", "data_probabilities"),
                get_correct_probability_model(R, G), default_is_class=True, child=True)
            self.probabilities.update() # force an update
            inherit_probabilities = kwargs.pop("inherit_probabilities", None)
            if inherit_probabilities is not None:
                for prop in self.probabilities.Meta.get_inheritable_properties():
                    setattr(self.probabilities, prop.inh_name, bool(inherit_probabilities))

            self._based_on_uuid = self.get_kwarg(kwargs, None, "based_on_uuid")
            self._based_on_index = self.get_kwarg(kwargs, None, "based_on_index")

    def __repr__(self):
        return "Phase(name='%s', based_on=%r)" % (self.name, self.based_on)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    def on_component_inserted(self, item):
        # Set parent and observe the new component (visuals changed signals):
        if item.parent != self: item.parent = self
        self.observe_model(item)

    def on_component_removed(self, item):
        with self.data_changed.hold_and_emit():
            # Clear parent & stop observing:
            item.parent = None
            self.relieve_model(item)

    @Observer.observe("data_changed", signal=True)
    def notify_data_changed(self, model, prop_name, info):
        if isinstance(model, Phase) and model == self.based_on:
            with self.data_changed.hold():
                # make sure inherited probabilities are up-to-date
                self.probabilities.update()
                self.data_changed.emit(arg="based_on")
        else:
            self.data_changed.emit()

    @Observer.observe("visuals_changed", signal=True)
    def notify_visuals_changed(self, model, prop_name, info):
        self.visuals_changed.emit()

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def resolve_json_references(self):
        # Set the based on and linked with variables:
        if hasattr(self, "_based_on_uuid") and self._based_on_uuid is not None:
            self.based_on = type(type(self)).object_pool.get_object(self._based_on_uuid)
            del self._based_on_uuid
        elif hasattr(self, "_based_on_index") and self._based_on_index is not None and self._based_on_index != -1:
            warn("The use of object indices is deprecated since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
            self.based_on = self.parent.phases.get_user_from_index(self._based_on_index)
            del self._based_on_index
        for component in self.components:
            component.resolve_json_references()
        with self.data_changed.hold():
            # make sure inherited probabilities are up-to-date
            self.probabilities.update()

    def _pre_multi_save(self, phases, ordered_phases):
        ## Override from base class

        if self.based_on != "" and not self.based_on in phases:
            self.save_links = False
        Component.export_atom_types = True
        for component in self.components:
            component.save_links = self.save_links

        # Make sure parent is first in ordered list:
        if self.based_on in phases:
            index = ordered_phases.index(self)
            index2 = ordered_phases.index(self.based_on)
            if index < index2:
                ordered_phases.remove(self.based_on)
                ordered_phases.insert(index, self.based_on)

    def _post_multi_save(self):
        ## Override from base class
        self.save_links = True
        for component in self.components:
            component.save_links = True
        Component.export_atom_types = False

    def json_properties(self):
        retval = super(Phase, self).json_properties()
        if not self.save_links:
            for prop in self.Meta.all_properties:
                if prop.inh_name:
                    retval[prop.inh_name] = False
            retval["based_on_uuid"] = ""
        else:
            retval["based_on_uuid"] = self.based_on.uuid if self.based_on else ""
        return retval

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def _update_interference_distributions(self):
        return self.CSDS_distribution.distrib

    pass # end of class
