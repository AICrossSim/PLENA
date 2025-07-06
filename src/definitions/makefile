ifeq ($(MODE),)
MODE_ARG =
else
MODE_ARG = --mode=$(MODE)
endif

ifeq ($(CONFIG),)
CONFIG_ARG =
else
CONFIG_ARG = --config="$(CONFIG)"
endif

ifeq ($(PRECISION),)
PRECISION_ARG =
else
PRECISION_ARG = --precision="$(PRECISION)"
endif

set:
	python3 config.py $(CONFIG_ARG) $(PRECISION_ARG) $(MODE_ARG)
