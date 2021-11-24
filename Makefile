
PTYHON_VERSIONS := 3.7 3.8 3.9 3.10
envs := $(foreach v,$(PTYHON_VERSIONS),envs/$(v)-env)

all: $(envs)

# Don't remove any intermediate files
.SECONDARY:


# Create an env yaml based on pyprojects
binder/environment.yml:  pyproject.toml *.pyproject.toml
	beni --deps all $^ > $@

# Create a new one just for tests
envs/base.yml:  pyproject.toml
	beni --extras test $^ > $@

# Create a env yaml for a specific python version
envs/%.yml: envs/base.yml
	sed 's/python>=3.7/python=$*/g' $^ > $@

# Create a conda env for a python version
envs/%-env: envs/%.yml
	conda env create --force -f $^ -p $@

test: $(envs)
	pytest -d -x metadsl_python \
	$(foreach e,$(envs),--tx popen//python=$(e)/bin/python)
	

clean:
	rm -rf  envs/*-env envs/*.yml
