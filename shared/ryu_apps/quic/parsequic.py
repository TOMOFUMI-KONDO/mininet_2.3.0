import grpc
from parsequic_proto_python import parsequic_pb2_grpc as pqgrpc, parsequic_pb2 as pq


def run(data: bytes, host="localhost", port=8080):
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = pqgrpc.ParseQuicStub(channel)
    response = stub.Parse(pq.ParseQuicRequest(data=data))
    print("is_long_header: " + str(response.is_long_header))


if __name__ == "__main__":
    run(b"hello")
