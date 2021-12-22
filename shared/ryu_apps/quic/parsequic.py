import grpc
import parsequic_pb2_grpc as pqgrpc
import parsequic_pb2 as pq


def run(data: bytes, host="localhost", port=8080):
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = pqgrpc.ParseQuicStub(channel)
    r = stub.Parse(pq.ParseQuicRequest(data=data))
    print(
        f"isLongHeader:{r.isLongHeader} "
        f"type:{r.type} version:{pq.PacketType.Name(r.type)} "
        f"dstConnID:{r.dstConnID} "
        f"srcConnID:{r.srcConnID}\n"
    )


if __name__ == "__main__":
    run(b"hello")
