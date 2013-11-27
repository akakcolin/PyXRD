#  Author: Roberto Cavada <roboogle@gmail.com>
#
#  Copyright (c) 2005 by Roberto Cavada
#
#  pygtkmvc is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  pygtkmvc is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free
#  Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
#  Boston, MA 02110, USA.
#
#  For more information on pygtkmvc see <http://pygtkmvc.sourceforge.net>
#  or email to the author Roberto Cavada <roboogle@gmail.com>.
#  Please report bugs to <roboogle@gmail.com>.

import inspect

from pyxrd.gtkmvc.support import metaclasses
from pyxrd.gtkmvc.support.log import logger
from pyxrd.gtkmvc.support.wrappers import ObsWrapperBase
from pyxrd.gtkmvc.observer import Observer, NTInfo
from pyxrd.gtkmvc.observable import Signal
from pyxrd.generic.utils import not_none

# Pass prop_name to this method?
WITH_NAME = True
WITHOUT_NAME = False 

class Model (Observer):
    """
    .. attribute:: __observables__
    
       Class attribute. A list or tuple of name strings. The metaclass
       :class:`~gtkmvc.support.metaclasses.ObservablePropertyMeta`
       uses it to create properties.
       
       *Value properties* have to exist as an attribute with an
       initial value, which may be ``None``.

       *Logical properties* require a getter and may have a setter method in
       the class.
    """

    __metaclass__ = metaclasses.ObservablePropertyMeta
    
    class Meta(object):
        """
            A MetadataModel class providing some basic functionality 
        """
        
        properties = []  # override this
                   
        @classmethod
        def get_column_properties(cls):
            if not hasattr(cls, "all_properties"):
                raise RuntimeError, "Meta class '%s' has not been initialized" \
                    " properly: 'all_properties' is not set!" % type(cls)
            else:
                cls._mem_columns = getattr(cls, "_mem_columns", None)
                if cls._mem_columns is None:
                    cls._mem_columns = [(prop.name, prop.data_type) for prop in cls.all_properties if prop.is_column]
                return cls._mem_columns
              
        @classmethod
        def get_storable_properties(cls):
            if not hasattr(cls, "all_properties"):
                raise RuntimeError, "Meta class '%s' has not been initialized" \
                    " properly: 'all_properties' is not set!" % type(cls)
            else:
                cls._mem_storables = getattr(cls, "_mem_storables", None)
                if cls._mem_storables is None:
                    cls._mem_storables = [(prop.name, not_none(prop.stor_name, prop.name)) for prop in cls.all_properties if prop.storable]
                return cls._mem_storables
       
        @classmethod
        def get_inheritable_properties(cls):
            if not hasattr(cls, "all_properties"):
                raise RuntimeError, "Meta class '%s' has not been initialized" \
                    " properly: 'all_properties' is not set!" % type(cls)
            else:
                cls._mem_inheritables = getattr(cls, "_mem_inheritables", None)
                if cls._mem_inheritables is None:
                    cls._mem_inheritables = [prop for prop in cls.all_properties if prop.inh_name]
                return cls._mem_inheritables
    
        @classmethod
        def get_refinable_properties(cls):
            if not hasattr(cls, "all_properties"):
                raise RuntimeError, "Meta class '%s' has not been initialized" \
                    " properly: 'all_properties' is not set!" % type(self)
            else:
                cls._mem_refinables = getattr(cls, "_mem_refinables", None)
                if cls._mem_refinables is None:
                    cls._mem_refinables = [prop for prop in cls.all_properties if prop.refinable]
                return cls._mem_refinables
    
        @classmethod
        def get_viewless_properties(cls):
            if not hasattr(cls, "all_properties"):
                raise RuntimeError, "Meta class '%s' has not been initialized" \
                    " properly: 'all_properties' is not set!" % type(self)
            else:
                cls._mem_viewless = getattr(cls, "_mem_viewless", None)
                if cls._mem_viewless is None:
                    cls._mem_viewless = [prop for prop in cls.all_properties if not prop.has_widget]
                return cls._mem_viewless
                        
        @classmethod
        def get_viewable_properties(cls):
            if not hasattr(cls, "all_properties"):
                raise RuntimeError, "Meta class '%s' has not been initialized" \
                    " properly: 'all_properties' is not set!" % type(self)
            else:
                cls._mem_viewables = getattr(cls, "_mem_viewables", None)
                if cls._mem_viewables is None:
                    cls._mem_viewables = [prop for prop in cls.all_properties if prop.has_widget]
                return cls._mem_viewables
        
        @classmethod
        def get_prop_intel_by_name(cls, name):
            cls._mem_properties = getattr(cls, "_mem_properties", None)
            if cls._mem_properties is None:
                cls._mem_properties = { prop.name: prop for prop in cls.all_properties }
            return cls._mem_properties[name]
                
        pass # end of class     

    def __init__(self):
        Observer.__init__(self)

        self.__observers = []

        # keys are properties names, values are pairs (method,
        # kwargs|None) inside the observer. kwargs is the keyword
        # argument possibly specified when explicitly defining the
        # notification method in observers, and it is used to build
        # the NTInfo instance passed down when the notification method
        # is invoked. If kwargs is None (special case), the
        # notification method is "old style" (property_<name>_...) and
        # won't be receiving the property name.
        self.__value_notifications = {}
        self.__instance_notif_before = {}
        self.__instance_notif_after = {}
        self.__signal_notif = {}

        for prop in self.get_properties(): self.register_property(prop)
        return

    def register_property(self, prop):
        """Registers an existing property to be monitored, and sets
        up notifiers for notifications"""
        if not self.__value_notifications.has_key(prop.name):
            self.__value_notifications[prop.name] = []
            pass

        # registers observable wrappers
        propval = getattr(self, prop.get_private_name(), None)

        if isinstance(propval, ObsWrapperBase):
            propval.__add_model__(self, prop.name)

            if isinstance(propval, Signal):
                if not self.__signal_notif.has_key(prop.name):
                    self.__signal_notif[prop.name] = []
                    pass
                pass
            else:
                if not self.__instance_notif_before.has_key(prop.name):
                    self.__instance_notif_before[prop.name] = []
                    pass
                if not self.__instance_notif_after.has_key(prop.name):
                    self.__instance_notif_after[prop.name] = []
                    pass
                pass
            pass

        return


    def has_property(self, name):
        """Returns true if given property name refers an observable
        property inside self or inside derived classes."""
        for prop in self.get_properties():
            if prop.name == name:
                return True

    def register_observer(self, observer):
        """Register given observer among those observers which are
        interested in observing the model."""
        if observer in self.__observers: return # not already registered

        assert isinstance(observer, Observer)
        self.__observers.append(observer)
        for prop in self.get_properties():
            self.__add_observer_notification(observer, prop)
            pass

        return


    def unregister_observer(self, observer):
        """Unregister the given observer that is no longer interested
        in observing the model."""
        assert isinstance(observer, Observer)

        if observer not in self.__observers: return
        for prop in self.get_properties():
            self.__remove_observer_notification(observer, prop)
            pass

        self.__observers.remove(observer)
        return


    def _reset_property_notification(self, prop, old=None):
        """Called when an assignment has been done that changes the
        type of a property or the instance of the property has been
        changed to a different instance. In this case it must be
        unregistered and registered again. Optional parameter old has
        to be used when the old value is an instance (derived from 
        ObsWrapperBase) which needs to unregisters from the model, via
        a call to method old.__remove_model__(model, prop_name)"""

        # unregister_property
        if isinstance(old, ObsWrapperBase):
            old.__remove_model__(self, prop.name)
            pass

        self.register_property(prop)

        for observer in self.__observers:
            self.__remove_observer_notification(observer, prop)
            self.__add_observer_notification(observer, prop)
            pass
        return


    def get_properties(self):
        """
        All observable properties accessible from this instance.

        :rtype: frozenset of strings
        """
        return self.Meta.all_properties


    def __add_observer_notification(self, observer, prop):
        """
        Find observing methods and store them for later notification.

        *observer* an instance.
        
        *prop_name* a string.

        This checks for magic names as well as methods explicitly added through
        decorators or at runtime. In the latter case the type of the notification
        is inferred from the number of arguments it takes.
        """
        value = getattr(self, prop.get_private_name(), None)

        # --- Some services ---
        def getmeth(format, numargs): # @ReservedAssignment
            name = format % prop.name
            meth = getattr(observer, name)
            args, varargs, _, _ = inspect.getargspec(meth)
            if not varargs and len(args) != numargs:
                logger.warn("Ignoring notification %s: exactly %d arguments"
                    " are expected", name, numargs)
                raise AttributeError
            return meth

        def add_value(notification, kw=None):
            pair = (notification, kw)
            if pair in self.__value_notifications[prop.name]: return
            logger.debug("Will call %s.%s after assignment to %s.%s",
                observer.__class__.__name__, notification.__name__,
                self.__class__.__name__, prop.name)
            self.__value_notifications[prop.name].append(pair)
            return

        def add_before(notification, kw=None):
            if (not isinstance(value, ObsWrapperBase) or
                isinstance(value, Signal)):
                return

            pair = (notification, kw)
            if pair in self.__instance_notif_before[prop.name]: return
            logger.debug("Will call %s.%s before mutation of %s.%s",
                observer.__class__.__name__, notification.__name__,
                self.__class__.__name__, prop.name)
            self.__instance_notif_before[prop.name].append(pair)
            return

        def add_after(notification, kw=None):
            if (not isinstance(value, ObsWrapperBase) or
                isinstance(value, Signal)):
                return
            pair = (notification, kw)
            if pair in self.__instance_notif_after[prop.name]: return
            logger.debug("Will call %s.%s after mutation of %s.%s",
                observer.__class__.__name__, notification.__name__,
                self.__class__.__name__, prop.name)
            self.__instance_notif_after[prop.name].append(pair)
            return

        def add_signal(notification, kw=None):
            if not isinstance(value, Signal): return
            pair = (notification, kw)
            if pair in self.__signal_notif[prop.name]: return
            logger.debug("Will call %s.%s after emit on %s.%s",
                observer.__class__.__name__, notification.__name__,
                self.__class__.__name__, prop.name)
            self.__signal_notif[prop.name].append(pair)
            return
        # ---------------------

        try: notification = getmeth("property_%s_signal_emit", 3)
        except AttributeError: pass
        else: add_signal(notification)

        try: notification = getmeth("property_%s_value_change", 4)
        except AttributeError: pass
        else: add_value(notification)

        try: notification = getmeth("property_%s_before_change", 6)
        except AttributeError: pass
        else: add_before(notification)

        try: notification = getmeth("property_%s_after_change", 7)
        except AttributeError: pass
        else: add_after(notification)

        # here explicit notification methods are handled (those which
        # have been statically or dynamically registered)
        type_to_adding_method = {
            'assign' : add_value,
            'before' : add_before,
            'after'  : add_after,
            'signal' : add_signal,
            }

        for meth in observer.get_observing_methods(prop.name):
            added = False
            kw = observer.get_observing_method_kwargs(prop.name, meth)
            for flag, adding_meth in type_to_adding_method.iteritems():
                if flag in kw:
                    added = True
                    adding_meth(meth, kw)
                    pass
                pass
            if not added: raise ValueError("In %s notification method %s is "
                                           "marked to be observing property "
                                           "'%s', but no notification type "
                                           "information were specified." %
                                           (observer.__class__,
                                            meth.__name__, prop.name))
            pass

        return

    def __remove_observer_notification(self, observer, prop):
        """
        Remove all stored notifications.
        
        *observer* an instance.
        
        *prop_name* a string.
        """

        def side_effect(seq):
            for meth, kw in reversed(seq):
                if meth.im_self is observer:
                    seq.remove((meth, kw))
                    yield meth

        for meth in side_effect(self.__value_notifications.get(prop.name, ())):
            logger.debug("Stop calling '%s' after assignment", meth.__name__)

        for meth in side_effect(self.__signal_notif.get(prop.name, ())):
            logger.debug("Stop calling '%s' after emit", meth.__name__)

        for meth in side_effect(self.__instance_notif_before.get(prop.name, ())):
            logger.debug("Stop calling '%s' before mutation", meth.__name__)

        for meth in side_effect(self.__instance_notif_after.get(prop.name, ())):
            logger.debug("Stop calling '%s' after mutation", meth.__name__)

        return

    def __notify_observer__(self, observer, method, *args, **kwargs):
        """This can be overridden by derived class in order to call
        the method in a different manner (for example, in
        multithreading, or a rpc, etc.)  This implementation simply
        calls the given method with the given arguments"""
        return method(*args, **kwargs)

    # -------------------------------------------------------------
    #            Notifiers:
    # -------------------------------------------------------------

    def notify_property_value_change(self, prop_name, old, new):
        """
        Send a notification to all registered observers.

        *old* the value before the change occured.
        """
        assert(self.__value_notifications.has_key(prop_name))
        for method, kw in self.__value_notifications[prop_name] :
            obs = method.im_self
            # notification occurs checking spuriousness of the observer
            if old != new or obs.accepts_spurious_change():
                if kw is None: # old style call without name
                    self.__notify_observer__(obs, method,
                                             self, old, new)
                elif 'old_style_call' in kw:  # old style call with name
                    self.__notify_observer__(obs, method,
                                             self, prop_name, old, new)
                else:
                    # New style explicit notification.
                    # notice that named arguments overwrite any
                    # existing key:val in kw, which is precisely what
                    # it is expected to happen
                    info = NTInfo('assign',
                                  kw, model=self, prop_name=prop_name,
                                  old=old, new=new)
                    self.__notify_observer__(obs, method,
                                             self, prop_name, info)
                    pass
                pass
            pass
        return

    def notify_method_before_change(self, prop_name, instance, meth_name,
                                    args, kwargs):
        """
        Send a notification to all registered observers.

        *instance* the object stored in the property.

        *meth_name* name of the method we are about to call on *instance*.
        """
        assert(self.__instance_notif_before.has_key(prop_name))
        for method, kw in self.__instance_notif_before[prop_name]:
            obs = method.im_self
            # notifies the change
            if kw is None: # old style call without name
                self.__notify_observer__(obs, method,
                                         self, instance,
                                         meth_name, args, kwargs)
            elif 'old_style_call' in kw:  # old style call with name
                self.__notify_observer__(obs, method,
                                         self, prop_name, instance,
                                         meth_name, args, kwargs)
            else:
                # New style explicit notification.
                # notice that named arguments overwrite any
                # existing key:val in kw, which is precisely what
                # it is expected to happen
                info = NTInfo('before',
                              kw,
                              model=self, prop_name=prop_name,
                              instance=instance, method_name=meth_name,
                              args=args, kwargs=kwargs)
                self.__notify_observer__(obs, method,
                                         self, prop_name, info)
                pass
            pass
        return

    def notify_method_after_change(self, prop_name, instance, meth_name,
                                   res, args, kwargs):
        """
        Send a notification to all registered observers.

        *args* the arguments we just passed to *meth_name*.

        *res* the return value of the method call.
        """
        assert(self.__instance_notif_after.has_key(prop_name))
        for method, kw in self.__instance_notif_after[prop_name]:
            obs = method.im_self
            # notifies the change
            if kw is None:  # old style call without name
                self.__notify_observer__(obs, method,
                                         self, instance,
                                         meth_name, res, args, kwargs)
            elif 'old_style_call' in kw:  # old style call with name
                self.__notify_observer__(obs, method,
                                         self, prop_name, instance,
                                         meth_name, res, args, kwargs)
            else:
                # New style explicit notification.
                # notice that named arguments overwrite any
                # existing key:val in kw, which is precisely what
                # it is expected to happen
                info = NTInfo('after',
                              kw,
                              model=self, prop_name=prop_name,
                              instance=instance, method_name=meth_name,
                              result=res, args=args, kwargs=kwargs)
                self.__notify_observer__(obs, method,
                                         self, prop_name, info)
                pass
            pass
        return

    def notify_signal_emit(self, prop_name, arg):
        """
        Emit a signal to all registered observers.

        *prop_name* the property storing the :class:`~gtkmvc.observable.Signal`
        instance.

        *arg* one arbitrary argument passed to observing methods.
        """
        assert(self.__signal_notif.has_key(prop_name))

        for method, kw in self.__signal_notif[prop_name]:
            obs = method.im_self
            # notifies the signal emit
            if kw is None: # old style call, without name
                self.__notify_observer__(obs, method,
                                         self, arg)
            elif 'old_style_call' in kw:  # old style call with name
                self.__notify_observer__(obs, method,
                                         self, prop_name, arg)
            else:
                # New style explicit notification.
                # notice that named arguments overwrite any
                # existing key:val in kw, which is precisely what
                # it is expected to happen
                info = NTInfo('signal',
                              kw,
                              model=self, prop_name=prop_name, arg=arg)
                self.__notify_observer__(obs, method,
                                         self, prop_name, info)
                pass
            pass
        return


    pass # end of class Model
# ----------------------------------------------------------------------