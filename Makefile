build-docker:
	docker build -f Docker/dockerfile-local --tag coprocessor-llama Docker

build-docker-nocache:
	docker build --no-cache -f Docker/dockerfile-local --tag coprocessor-llama Docker

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
        -v $(shell pwd):/workspace:z \
	    coprocessor-llama
        # -v /$(USER_PREFIX)/$(shell whoami)/.gitconfig:/root/.gitconfig \
        #coprocessor-llama /bin/bash -c "source .coprocessor_env/bin/activate && /bin/bash"


clean:
	@rm -rf *.log *.jou *.str
