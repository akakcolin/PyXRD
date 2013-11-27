#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.utils import create_object_attribute_test

from pyxrd.phases.models import Phase
from pyxrd.specimen.models import Specimen
from pyxrd.project.models import Project
from pyxrd.mixture.models import Mixture

__all__ = [
    'TestMixture',
]

class TestMixture(unittest.TestCase):

    atom_type = None

    def setUp(self):
        self.project = Project(name="TestProject")
        self.mixture = Mixture(name="TestMixture", parent=self.project)

    def tearDown(self):
        del self.mixture
        del self.project

    def test_not_none(self):
        self.assertIsNotNone(self.mixture)

    def test_data_object(self):
        self.assertIsNotNone(self.mixture.data_object)

    test_name = create_object_attribute_test("mixture", "name", "Test Name")

    def test_parent(self):
        parent_project = Project(name="Parent2")
        self.mixture.parent = parent_project
        self.assertEqual(self.mixture.parent, parent_project)

    def test_add_phase_slot(self):
        index = self.mixture.add_phase_slot("TestPhase", 0.5)
        self.assertEqual(index, 0, "Adding a phase slot should return the correct index!")

    def test_add_specimen_slot(self):
        index = self.mixture.add_specimen_slot(None, 1.0, 0)
        self.assertEqual(index, 0, "Adding a specimen slot should return the correct index!")

    def test_add_order1(self):
        """Test if addition works when 1st specimen slot is added before 1st phase slot"""
        self.mixture.add_specimen_slot(None, 1.0, 0)
        self.assertEqual(len(self.mixture.specimens), 1)
        self.assertEqual(len(self.mixture.phases), 0)
        self.assertEqual(len(self.mixture.fractions), 0)
        self.assertEqual(self.mixture.phase_matrix.shape, (1, 0))
        self.mixture.add_phase_slot("TestPhase", 0.5)
        self.assertEqual(len(self.mixture.specimens), 1)
        self.assertEqual(len(self.mixture.phases), 1)
        self.assertEqual(len(self.mixture.fractions), 1)
        self.assertEqual(self.mixture.phase_matrix.shape, (1, 1))
        self.assertEqual(self.mixture.phase_matrix[0, 0], None)

    def test_add_order2(self):
        """Test if addition works when 1st phase slot is added before 1st specimen slot"""
        self.mixture.add_phase_slot("TestPhase", 0.5)
        self.assertEqual(len(self.mixture.specimens), 0)
        self.assertEqual(len(self.mixture.phases), 1)
        self.assertEqual(len(self.mixture.fractions), 1)
        self.assertEqual(self.mixture.phase_matrix.shape, (0, 1))
        self.mixture.add_specimen_slot(None, 1.0, 0)
        self.assertEqual(len(self.mixture.specimens), 1)
        self.assertEqual(len(self.mixture.phases), 1)
        self.assertEqual(len(self.mixture.fractions), 1)
        self.assertEqual(self.mixture.phase_matrix.shape, (1, 1))
        self.assertEqual(self.mixture.phase_matrix[0, 0], None)

    def test_add_multiple(self):
        """Test if addition for multiple phases and specimens works as expected"""
        self.mixture.add_phase_slot("TestPhase", 0.5)
        self.mixture.add_specimen_slot(None, 1.0, 0)
        self.mixture.add_specimen_slot(None, 1.0, 0)
        self.mixture.add_phase_slot("TestPhase2", 0.5)
        self.mixture.add_phase_slot("TestPhase3", 0.5)
        self.assertEqual(len(self.mixture.specimens), 2)
        self.assertEqual(len(self.mixture.phases), 3)
        self.assertEqual(len(self.mixture.fractions), 3)
        self.assertEqual(self.mixture.phase_matrix.shape, (2, 3))

    def test_del_phase_slot(self):
        """Test if deleting a phase works as expected"""
        self.mixture.add_phase_slot("TestPhase1", 0.1)
        self.mixture.add_phase_slot("TestPhase2", 0.1)
        self.mixture.del_phase_slot(1)
        self.assertEqual(len(self.mixture.phases), 1)
        self.assertEqual(len(self.mixture.fractions), 1)
        self.assertEqual(self.mixture.phase_matrix.shape, (0, 1))
        self.mixture.del_phase_slot(0)
        self.assertEqual(len(self.mixture.phases), 0)
        self.assertEqual(len(self.mixture.fractions), 0)
        self.assertEqual(self.mixture.phase_matrix.shape, (0, 0))

    def test_del_specimen_slot(self):
        """Test if deleting a specimen works as expected"""
        self.mixture.add_specimen_slot(None, 0.5, 0)
        self.mixture.add_specimen_slot(None, 0.5, 0)
        self.mixture.del_specimen_slot(1)
        self.assertEqual(len(self.mixture.specimens), 1)
        self.assertEqual(self.mixture.phase_matrix.shape, (1, 0))
        self.mixture.del_specimen_slot(0)
        self.assertEqual(len(self.mixture.specimens), 0)
        self.assertEqual(self.mixture.phase_matrix.shape, (0, 0))

    def test_del_phase_slot_by_name(self):
        self.mixture.add_phase_slot("TestPhase1", 0.1)
        self.mixture.del_phase_slot_by_name("TestPhase1")
        self.assertEqual(len(self.mixture.phases), 0)
        self.assertEqual(len(self.mixture.fractions), 0)
        self.assertEqual(self.mixture.phase_matrix.shape, (0, 0))

    def test_del_specimen_slot_by_object(self):
        dummy = Specimen(name="Test Specimen", parent=self.project)
        self.mixture.add_specimen_slot(dummy, 0.5, 0)
        self.mixture.del_specimen_slot_by_object(dummy)
        self.assertEqual(len(self.mixture.specimens), 0)
        self.assertEqual(self.mixture.phase_matrix.shape, (0, 0))

    def test_set_specimen(self):
        dummy = Specimen(name="Test Specimen", parent=self.project)
        self.mixture.add_specimen_slot(None, 0.5, 0)
        self.mixture.set_specimen(0, dummy)
        self.assertEqual(self.mixture.specimens[0], dummy)

    def test_unset_specimen(self):
        dummy = Specimen(name="Test Specimen", parent=self.project)
        self.mixture.add_specimen_slot(dummy, 0.5, 0)
        self.mixture.unset_specimen(dummy)
        self.assertEqual(self.mixture.specimens[0], None)

    def test_unset_phase(self):
        specimen = Specimen(name="Test Specimen", parent=self.project)
        self.mixture.add_specimen_slot(specimen, 0.5, 0)
        self.mixture.add_phase_slot("Test Phase1", 0.5)

        dummy = Phase(name="Test Phase", parent=self.project)
        self.mixture.set_phase(0, 0, dummy)
        self.mixture.unset_phase(dummy)
        self.assertEqual(self.mixture.phase_matrix[0, 0], None)

    # TODO:
    #  - set_data_object
    #  - optimize
    #  - apply_current_data_object
    #  - update
    #  - update_refinement_treestore
    #  - auto_restrict
    #  - randomize
    #  - get_refinement_method
    #  - setup_refine_options

    pass # end of class
