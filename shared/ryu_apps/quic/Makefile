.PHONY: build
build:
	python -m grpc_tools.protoc -I. \
			--python_out=. \
			--grpc_python_out=. \
			./parsequic.proto