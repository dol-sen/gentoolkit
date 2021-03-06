#!/usr/bin/python

"""Assign module
Functions used for determining the package the broken lib belongs to.
"""

from __future__ import print_function

import os
import re

import portage
from portage.versions import catpkgsplit
from portage import portdb
from portage.output import bold, red, yellow
from gentoolkit.helpers import get_installed_cpvs
from gentoolkit.package import Package

# Make all str conversions unicode
try:
	str = unicode
except NameError:
	pass

def assign_packages(broken, logger, settings):
	''' Finds and returns packages that owns files placed in broken.
		Broken is list of files
	'''
	assigned = set()
	if not broken:
		return assigned

	pkgset = set(get_installed_cpvs())

	# Map all files in CONTENTS database to package names
	fname_pkg_dict = {}
	for pkg in pkgset:
		contents = Package(pkg).parsed_contents()
		for fname in contents.keys():
			if contents[fname][0] == "obj":
				fname_pkg_dict[fname] = str(pkg)

	for fname in broken:
		realname = os.path.realpath(fname)
		if realname in fname_pkg_dict.keys():
			pkgname = fname_pkg_dict[realname]
		elif fname in fname_pkg_dict.keys():
			pkgname = fname_pkg_dict[fname]
		else:
			pkgname = None
		if pkgname and pkgname not in assigned:
			assigned.add(pkgname)
		if not pkgname:
			pkgname = "(none)"
		logger.info('\t' + fname + ' -> ' + bold(pkgname))

	return assigned

def get_best_match(cpv, cp, logger):
	"""Tries to find another version of the pkg with the same slot
	as the deprecated installed version.  Failing that attempt to get any version
	of the same app

	@param cpv: string
	@param cp: string
	@rtype tuple: ([cpv,...], SLOT)
	"""

	slot = portage.db[portage.root]["vartree"].dbapi.aux_get(cpv, ["SLOT"])
	logger.warn(yellow('Warning: ebuild "' + cpv + '" not found.'))
	logger.info('Looking for %s:%s' %(cp, slot))
	try:
		match = portdb.match('%s:%s' %(cp, slot))
	except portage.exception.InvalidAtom:
		match = None

	if not match:
		logger.warn(red('!!') + ' ' + yellow(
			'Could not find ebuild for %s:%s' %(cp, slot)))
		slot = ['']
		match = portdb.match(cp)
		if not match:
			logger.warn(red('!!') + ' ' +
				yellow('Could not find ebuild for ' + cp))
	return match, slot


def get_slotted_cps(cpvs, logger):
	"""Uses portage to reduce the cpv list into a cp:slot list and returns it
	"""

	cps = []
	for cpv in cpvs:
		parts = catpkgsplit(cpv)
		cp = parts[0] + '/' + parts[1]
		try:
			slot = portdb.aux_get(cpv, ["SLOT"])
		except KeyError:
			match, slot = get_best_match(cpv, cp, logger)
			if not match:
				logger.warn(red("Installed package: "
					"%s is no longer available" %cp))
				continue

		if slot[0]:
			cps.append(cp + ":" + slot[0])
		else:
			cps.append(cp)

	return cps



if __name__ == '__main__':
	print('Nothing to call here')
