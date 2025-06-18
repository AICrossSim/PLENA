# Build Docker container
build-docker:
	docker build -f Docker/dockerfile-local --tag coprocessor-llama Docker; \

ifeq ($(shell uname),Darwin)
    USER_PREFIX=Users
else
    USER_PREFIX=home
endif

shell:
	docker run -it --shm-size 256m \
        --hostname coprocessor-llama \
        -w /workspace \
        -v /$(USER_PREFIX)/$(shell whoami)/.ssh:/root/.ssh \
        -v /$(USER_PREFIX)/$(shell whoami)/.gitconfig:/root/.gitconfig \
        -v $(shell pwd):/workspace:z \
	    coprocessor-llama
        #coprocessor-llama /bin/bash -c "source .coprocessor_env/bin/activate && /bin/bash"


clean:
	@rm -rf *.log *.jou *.str
