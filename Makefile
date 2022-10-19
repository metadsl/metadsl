flit-install:
	flit -f typez.pyproject.toml install --symlink
	flit install --symlink
	flit -f rewrite.pyproject.toml install --symlink
	flit -f core.pyproject.toml install --symlink
	flit -f visualize.pyproject.toml install --symlink
	flit -f llvm.pyproject.toml install --symlink
	flit -f numpy.pyproject.toml install --symlink
	flit -f python.pyproject.toml install --symlink
	flit -f all.pyproject.toml install --symlink