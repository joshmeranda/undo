RM := rm --verbose --recursive
CP := cp --verbose --recursive

VERSION := $(shell grep version setup.cfg | cut -d = -f 2 | xargs)

DISTRIBUTION_NAME := undo-${VERSION}
WHEEL := dist/${DISTRIBUTION_NAME}-py3-none-any.whl
DISTRIBUTION_TAR := ${DISTRIBUTION_NAME}.tar.gz

PY_SOURCES := $(shell find undo -name '*.py')

.PHONY: help
help:
	@echo 'USAGE: make TARGET'
	@echo

	@echo 'TARGETS:'
	@echo '  dist       create a distribution tar archive of the python wheel and undo'
	@echo '             files'

	@echo '  clean      clean the working directory of ALL unnecessary files (egg.info,'
	@echo '             dist, etc)'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# distribution targets                                                        #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

dist: ${DISTRIBUTION_TAR}

${DISTRIBUTION_TAR}: ${WHEEL} LICENSE README.md undos Makefile.dist
	mkdir --verbose ${DISTRIBUTION_NAME}

	${CP} --target-directory ${DISTRIBUTION_NAME} ${WHEEL} LICENSE README.md

	# setup the distribution tar Makefile
	cp Makefile.dist ${DISTRIBUTION_NAME}/Makefile
	sed -i '1i VERSION := ${VERSION}' ${DISTRIBUTION_NAME}/Makefile

	# move undo files into distribution directory with a flattened directory tree
	mkdir ${DISTRIBUTION_NAME}/undos
	find undos -name '*toml' -exec ${CP} --target-directory ${DISTRIBUTION_NAME}/undos '{}' +

	# create the tar
	tar --gzip --verbose --create --file ${DISTRIBUTION_TAR} ${DISTRIBUTION_NAME}

${WHEEL}: ${PY_SOURCES}
	python -m build --wheel

${PY_SOURCES}: # do nothing

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# clean targets                                                               #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

clean:
	find . -name __pycache__ -exec ${RM} '{}' +
	${RM} --force build dist undo.egg-info ${DISTRIBUTION_TAR} ${DISTRIBUTION_NAME}