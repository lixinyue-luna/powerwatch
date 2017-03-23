"""Tests on resources like fuel thesaurus and concordance files."""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.pardir, os.pardir))
import powerwatch as pw


class TestFuelThesaurus(unittest.TestCase):

	def setUp(self):
		self.fuel_thesaurus = pw.make_fuel_thesaurus()

	def test_not_empty(self):
		self.assertNotEqual(len(self.fuel_thesaurus), 0)
		for fuel, alts in self.fuel_thesaurus.iteritems():
			self.assertNotEqual(len(alts), 0)

	def test_lower(self):
		for fuel, alts in self.fuel_thesaurus.iteritems():
			for alt_name in alts:
				self.assertFalse(alt_name.isupper(), "name should not be uppercase")

	def test_distinct_entries(self):
		unique_names = {} # dict because of fast lookup
		for fuel, alts in self.fuel_thesaurus.iteritems():
			for alt_name in alts:
				self.assertNotIn(alt_name, unique_names)
				unique_names[alt_name] = None

if __name__ == '__main__':
	unittest.main()

