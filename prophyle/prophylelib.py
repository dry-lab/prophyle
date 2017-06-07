#! /usr/bin/env python3

"""Auxiliary ProPhyle functions.

Author: Karel Brinda <kbrinda@hsph.harvard.edu>

Licence: MIT
"""

import datetime
import ete3
import os
import psutil
import shutil
import subprocess
import sys
import time

log_file=None


def open_log(fn):
	"""Open a log file.

	Args:
		fn (str): File name.
	"""

	global log_file
	if fn is not None:
		d=os.path.dirname(fn)
		makedirs(d)
		log_file=open(fn,"a+")


def close_log():
	"""Close a log file.
	"""

	global log_file
	if log_file is not None:
		log_file.close()


def run_safe(command, output_fn=None, output_fo=None, err_msg=None, thr_exc=True):
	"""Run a shell command safely.

	Args:
		command (list of str): Command to execute.
		output_fn (str): Name of a file for storing the output.
		output_fo (fileobject): Output file object. If both params are None, the standard output is used.
		error_msg (str): Error message if the command fails.
		thr_exc (bool): Through exception if the command fails. error_msg or thr_exc must be set.

	Raises:
		RuntimeError: Command exited with a non-zero code.
	"""

	assert output_fn is None or output_fo is None
	assert err_msg is not None or thr_exc

	command_safe = []

	for part in command:
		part=str(part)
		if " " in part:
			part='"{}"'.format(part)
		command_safe.append(part)

	command_str=" ".join(command_safe)
	message("Running:", command_str)
	if output_fn is None:
		if output_fo is None:
			out_fo=sys.stdout
		else:
			out_fo=output_fo
	else:
		out_fo=open(output_fn,"w+")

	if out_fo==sys.stdout:
		p=subprocess.Popen("/bin/bash -e -o pipefail -c '{}'".format(command_str), shell=True)
	else:
		p=subprocess.Popen("/bin/bash -e -o pipefail -c '{}'".format(command_str), shell=True, stdout=out_fo)

	ps_p = psutil.Process(p.pid)

	max_rss = 0
	error_code=None
	while error_code is None:
		try:
			max_rss=max(max_rss, ps_p.memory_info().rss)
		except psutil.ZombieProcess:
			pass
		# wait 0.02 s
		time.sleep(0.02)
		error_code=p.poll()

	out_fo.flush()

	mem_mb=round(max_rss/(1024*1024.0), 1)

	if output_fn is not None:
		out_fo.close()

	if error_code==0 or error_code==141:
		message("Finished ({} MB used): {}".format(mem_mb, command_str))
	else:
		message("Unfinished, an error occurred (error code {}, {} MB used): {}".format(error_code, mem_mb, command_str))

		if err_msg is not None:
			print('Error: {}'.format(err_msg), file=sys.stderr)

		if thr_exc:
			raise RuntimeError("A command failed, see messages above.")

		sys.exit(1)


def message(*msg, upper=False, only_log=False):
	"""Print a ProPhyle message to stderr.

	Args:
		*msg: Message.
		upper (bool): Transform text to upper cases.
		only_log (bool): Don't print the message to screen (i.e., it would be only logged).
	"""

	global log_file

	dt=datetime.datetime.now()
	fdt=dt.strftime("%Y-%m-%d %H:%M:%S")

	if upper:
		msg=map(str,msg)
		msg=map(str.upper,msg)

	log_line='[prophyle] {} {}'.format(fdt, " ".join(msg))

	if not only_log:
		print(log_line, file=sys.stderr)
	if log_file is not None:
		log_file.write(log_line)
		log_file.write("\n")
		log_file.flush()


def load_nhx_tree(nhx_fn, validate=True):
	tree=ete3.Tree(
		nhx_fn,
		format=1
	)

	if validate:
		validate_prophyle_nhx_tree(tree)

	return tree


def save_nhx_tree(tree, nhx_fn):
	assert isinstance(tree, ete3.Tree)

	# make saving newick reproducible
	features=set()
	for n in tree.traverse():
		features|=n.features

	# otherwise some names stored twice – also as a special attribute
	features.remove("name")

	tree.write(
		features=sorted(features),
		format = 1,
		format_root_node = True,
		outfile = nhx_fn,
	)


def validate_prophyle_nhx_tree(tree, verbose=True, throw_exceptions=True, output=sys.stderr):
	node_names=set()

	error=False

	existing_names=[]
	names_with_separator=[]

	without_name=[]
	empty_name=[]

	duplicates=[]

	for i,node in enumerate(tree.traverse("postorder")):
		noname=True
		try:
			nname=node.name
			noname=False
		except AttributeError:
			without_name.append((i,None))

		if not noname:
			if nname=='':
				empty_name.append((i,nname))
				error=True
			if nname in existing_names:
				duplicates.append((i,nname))
				error=True
			if "@" in nname:
				names_with_separator.append((i,nname))
				error=True
			existing_names.append((i,nname))

	def _format_node_list(node_list):
		return ", ".join(map(str,node_list))

	def _error_report(node_list, message):
		if len(node_list)>0:
			print("   * {} node(s) {}: {}".format(
					len(node_list),
					message,
					_format_node_list(node_list),
				),file=output)

	if verbose:
		if error:
			print("Errors:".format(),file=output)

		_error_report(without_name, "without name")
		_error_report(empty_name, "with empty name")
		_error_report(duplicates, "with a duplicate name")
		_error_report(names_with_separator, "with a name containing '@'")

	if throw_exceptions:
		if error:
			raise ValueError("Invalid tree. The format of the tree is not correct. See the messages above.")

	if error:
		return False
	else:
		return True


def file_sizes(*fns):
	"""Get file sizes in Bytes.

	Args:
		fns (str): File names.

	Returns:
		tuple(int): File sizes.
	"""
	return tuple( [os.stat(fn).st_size for fn in fns] )


def touch(*fns):
	"""Touch files.

	Args:
		*fns: Files.
	"""
	for fn in fns:
		if os.path.exists(fn):
			os.utime(fn, None)
		else:
			with open(fn, 'a'):
				pass


def rm(*fns):
	"""Remove files (might not exists).

	Args:
		*fns: Files.
	"""
	for fn in fns:
		try:
			os.remove(fn)
		except FileNotFoundError:
			pass


def cp_to_file(fn0, fn):
	"""Copy file to file.

	Args:
		fn0 (str): Source file.
		fn (str): Target file.
	"""

	# keep rewriting attributes
	shutil.copyfile(fn0, fn)


def cp_to_dir(fn0, d):
	"""Copy file to dir.

	Args:
		fn0 (str): Source file.
		d (str): Target dir.
	"""

	# keep rewriting attributes
	shutil.copy(fn0, d)


def makedirs(*ds):
	"""Make dirs recursively.

	Args:
		*ds: Dirs to create.
	"""
	for d in ds:
		if not os.path.isdir(d):
			cmd=['mkdir', '-p', d]
			run_safe(cmd)


def existing_and_newer(fn0, fn):
	"""Test if file fn exists and is newer than fn0. Raise an exception if fn0 does not exist.

	Args:
		fn0 (str): Old file.
		fn (str): New file (to be generated from fn0).
	"""

	assert os.path.isfile(fn0), "Dependency '{}' does not exist".format(fn0)

	if not os.path.isfile(fn):
		return False

	if os.path.getmtime(fn0)<=os.path.getmtime(fn):
		return True
	else:
		return False


def existing_and_newer_list(fn0_l, fn):
	"""Test if file fn exists and is newer than all files from fn0_l. Raise an exception if some fn0 file does not exist.

	Args:
		fn0 (str): Old file.
		fn (str): New file (to be generated from fn0).
	"""

	rs=[existing_and_newer(fn0, fn) for fn0 in fn0_l]
	some_false=False in rs
	return not some_false


def test_files(*fns,test_nonzero=False):
	"""Test if given files exist, and possibly if they are non-empty. If not, stop the program.

	Args:
		*fns: Files.
		test_nonzero (bool): Test if files have size greater than zero.

	Raises:
		AssertionError: File does not exist or it is empty.
	"""
	#print(fns)
	for fn in fns:
		assert os.path.isfile(fn), 'File "{}" does not exist'.format(fn)
		if test_nonzero:
			assert file_sizes(fn)[0], 'File "{}" has size 0'.format(fn)


if __name__ == "__main__":
	sys.exit(1)

